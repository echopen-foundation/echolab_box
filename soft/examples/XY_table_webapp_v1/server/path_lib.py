#!/usr/bin/env python3
#encoding: UTF-8

import json
import time
import datetime
import threading
import os
import xy_lib
import usspi_lib

#########################################
# Devices interface library
#########################################

path_spec = {#min def max isfloat
    "path_title": [ 0, "No name", 255, -1]
  , "path_width": [ 1, 10, 200, 1]
  , "path_length":[ 1, 50, 300, 1]
  , "path_x_step":[ 0.1,  5,  50, 1]
  , "path_y_step":[ 0.1,  1,  50, 1]
  , "path_speed":[ 100,  500,  100000, 0]
  , "path_scan_mode":[ 0,  0,  1, 0]
  , "path_adc_delay":[ 0,  0,  1000, 0]
}

#========================================
# Test path library
#========================================
path_cur_params = { "path_title":path_spec["path_title"][1]
                  , "path_width":path_spec["path_width"][1]
                  , "path_length":path_spec["path_length"][1]
                  , "path_x_step":path_spec["path_x_step"][1]
                  , "path_y_step":path_spec["path_y_step"][1]
                  , "path_speed":path_spec["path_speed"][1]
                  , "path_scan_mode":path_spec["path_scan_mode"][1]
                  , "path_adc_delay":path_spec["path_adc_delay"][1]
                  }

path_data = None
path_running = "stopped"

#----------------------------------------
# safe convert to int
#----------------------------------------
def safe_float(txt):
  try:
    i = float(txt)
  except:
    i = 0
  return i

#----------------------------------------
# Frame value between minv and maxv
#----------------------------------------
def frame(new, name, minv, maxv, cur):
  default = cur.get(name, "0")
  strv = new.get(name, default)
  v = safe_float(strv)
  v = v if v > minv else minv
  v = v if v < maxv else maxv
  return v

#----------------------------------------
# Frame str value between minv and maxv
#----------------------------------------
def frame_str(new, name, minv, maxv, cur):
  default = cur.get(name, "")
  strv = new.get(name, default)
  v=strv[:maxv]
  return v

#----------------------------------------
# Initialize a parameter
#----------------------------------------
def set_param(name, new, cur):
  global path_spec
  
  spec = path_spec[name]
  if spec[3]==0:  # Integer
    param = int(frame(new, name, spec[0], spec[2], cur))
  elif spec[3]>=1: # Float
    param = round(frame(new, name, spec[0], spec[2], cur), spec[3])
  elif spec[3]==-1: # String
    param = frame_str(new, name, spec[0], spec[2], cur)
    
  cur[name]= str(param)
 
#----------------------------------------
# re-read parameters
#----------------------------------------
def reread_params(ws_send_msg, report_action):
   
  out_msg = {"cmd":"report", "report_from":"path_lib.reread_params()", "report_action":report_action, "data":path_cur_params}
  ws_send_msg(out_msg)

#----------------------------------------
# Initialize path parameters
#----------------------------------------
def init_params(new_params, ws_send_msg, report_action):
  global path_cur_params
  
  set_param("path_title", new_params, path_cur_params)
  set_param("path_width", new_params, path_cur_params)
  set_param("path_length", new_params, path_cur_params)
  set_param("path_x_step", new_params, path_cur_params)
  set_param("path_y_step", new_params, path_cur_params)
  set_param("path_speed", new_params, path_cur_params)
  set_param("path_scan_mode", new_params, path_cur_params)
  set_param("path_adc_delay", new_params, path_cur_params)
  reread_params(ws_send_msg, report_action)

#----------------------------------------
# Reset path script
#----------------------------------------
def run_path_loop(context, ws_send_msg, report_action, dry_run):
  global path_running
  global path_data
  global path_cur_params
  
  xmin = 0
  xmax = safe_float(path_cur_params["path_length"])
  ymin = -safe_float(path_cur_params["path_width"])/2
  ymax = -ymin
  stepx = safe_float(path_cur_params["path_x_step"])
  stepy = safe_float(path_cur_params["path_y_step"])
  feed = safe_float(path_cur_params["path_speed"])
  scan_mode = safe_float(path_cur_params["path_scan_mode"])
  adc_delay = safe_float(path_cur_params["path_adc_delay"])

  n=0
  x=xmin
  y=ymin
  if dry_run:
    path_data = {"us_spi_params":usspi_lib.get_params(), "path_params":path_cur_params, "measures":[], "status":""}
  else:
    usspi_lib.set_delay_us(x*1.36+80)


  while x <= xmax and y <= ymax and path_running != "reset":
    if path_running=="paused":
      time.sleep(0.5)
    else:
      if dry_run:
        vmax=-1
        t_us=-1
        path_data["measures"] += [[]]
      else:
        # Move
        line = "G90\nG1 X"+str(round(x,2))+" Y"+str(round(y,2))+" F" +str(feed)
        ok = xy_lib.send_g_lines({"lines":line}, context, None)
        
        # Measure
        raw = usspi_lib.read_one_raw()
        t0 = time.clock()
        vmax0=0
        for v in raw:
          vabs = abs(v-128)*2
          vmax0 = max(vmax0,vabs)
#        time.sleep(max(0, 0.02-(time.clock()-t0))) # wait until 2 acq cycles @ 100Hz
#        raw = usspi_lib.read_one_raw()
#        vmax1=0
#        for v in raw:
#          vabs = abs(v-128)*2
#          vmax1 = max(vmax1,vabs)
#        vmax = min(vmax0, vmax1)      # remove glitches
        vmax = vmax0
        t_us=x*1.36/1000000

      path_data["measures"][n] = [n,x,y,vmax,t_us]
      path_data["status"] = str(n+1)+"/"+str(len(path_data["measures"]))

      # Next step
      n +=1
      if (scan_mode==0):  # scan vertically
        y += stepy
        if y < ymin or y > ymax:
          stepy = -stepy
          y += stepy
          x += stepx
          if not(dry_run):
            usspi_lib.set_delay_us(x*1.36+adc_delay) 
            # Report vertical line
            out_msg = {"cmd":"report", "report_from":"path_lib.reset_path()", "report_action":report_action, "data":path_data}
            if not ws_send_msg(out_msg) : break
      else:  # scan horizontally
        x += stepx
        if x < xmin or x > xmax:
          stepx = -stepx
          x += stepx
          y += stepy
          if not(dry_run):
            # Report vertical line
            out_msg = {"cmd":"report", "report_from":"path_lib.reset_path()", "report_action":report_action, "data":path_data}
            if not ws_send_msg(out_msg) : break
        usspi_lib.set_delay_us(x*1.36+adc_delay) # Update delay for next horizontal point

  if (path_running != "reset" and not(dry_run)): db_write()   # test normaly terminated, save file

  out_msg = {"cmd":"report", "report_from":"path_lib.reset_path()", "report_action":report_action, "data":path_data}
  ws_send_msg(out_msg)
  path_running="stopped"

#----------------------------------------
# Start path script task
#----------------------------------------
def run_path(context, ws_send_msg, report_action, dry_run):
  global path_running

  if dry_run and (path_running != "stopped"):
    path_running = "reset"
    time.sleep(1)

  if path_running == "stopped":
    path_running = "running"
    t = threading.Thread(target=run_path_loop, args=(context, ws_send_msg, report_action, dry_run))
    t.start()
  else:
    path_running = "running"
    
#----------------------------------------
# Reset path script
#----------------------------------------
def pause_path(ws_send_msg, report_action):
  global path_running

  path_running = "paused"

#----------------------------------------
# Reset path script
#----------------------------------------
def reread_path(ws_send_msg, report_action):
  global path_data

  out_msg = {"cmd":"report", "report_from":"path_lib.reread_path()", "report_action":report_action, "data":path_data}
  ws_send_msg(out_msg)

#----------------------------------------
# Get path data
#----------------------------------------
def get_path_data():
  global path_data

  return path_data

#----------------------------------------
# List path db items
#----------------------------------------
def db_list(ws_send_msg, report_action):

  files = sorted(os.listdir("db")+["","",""], reverse=True)[:9]
  db =  {"path_data_mem"+str(i+1):files[i] for i in range(len(files))}
  out_msg = {"cmd":"report", "report_from":"path_lib.db_list()", "report_action":report_action, "data":db}
  ws_send_msg(out_msg)

#----------------------------------------
# db_load
#----------------------------------------
def db_reload(item, ws_send_msg, report_action):
  global path_data

  files = files = sorted(os.listdir("db")+["","",""], reverse=True)[:9]
  with open("db/" + files[item-1]) as json_file:
      path_data = json.load(json_file)
      json_file.close()

  out_msg = {"cmd":"report", "report_from":"path_lib.db_reload()", "report_action":report_action, "data":path_data}
  ws_send_msg(out_msg)

#----------------------------------------
# db_write_file
#----------------------------------------
def db_write():
  global path_data

  date = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M ")
  with open("db/" + date + path_data["path_params"]["path_title"] + ".json", 'w') as json_file:
      json.dump(path_data, json_file)
      json_file.close()
