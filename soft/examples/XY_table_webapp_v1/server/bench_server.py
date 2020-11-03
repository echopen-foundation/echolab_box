#!/usr/bin/env python3
#encoding: UTF-8

import os
import json
import bottle
from bottle import route, run, request, abort, Bottle ,static_file, template
from gevent import monkey; monkey.patch_all()
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from time import sleep
import random
import threading
import base64

import xy_lib
import usspi_lib
import path_lib
  
#########################################
# HTTP and Websocket server
#########################################
wsock = None
wsock_inuse = False
context = {"xy_com":None}
app = Bottle()

#----------------------------------------
# Send a dumped json on a websocket
#----------------------------------------
def ws_send_msg(msg):
  global wsock
  global wsock_inuse

  if msg :
    msg_json = json.dumps(msg, separators=(',',':'))
    # print(msg_json[:256]) # DEBUG
    i=0
    while wsock_inuse:
      sleep(0.1)
      i += 1
      if i > 30 : return False
    
    wsock_inuse = True
    try:
      wsock.send(msg_json)
    except WebSocketError:
      wsock_inuse = False
      return False
    
    wsock_inuse = False
    return True
  
  else:
    return True
#----------------------------------------
# Asynchronous report function
#----------------------------------------
def async_report(msg):
  return ws_send_msg(msg)

#----------------------------------------
# ws://localhost/ws
#----------------------------------------
@app.route('/ws')
def handle_websocket():
  global nb_trace
  global playing
  global wsock
  
  wsock = request.environ.get('wsgi.websocket')
  wsock_inuse = False
  if not wsock:
    abort(400, 'Expected WebSocket request.')
  while True:
    try:
      in_msg_json = wsock.receive()
      print(in_msg_json)
      if not in_msg_json : break
      in_msg = json.loads(in_msg_json)
      out_msg = {}
      msg_type = in_msg.get("msg_type")
      cmd = in_msg.get("cmd")
      
      if msg_type == "eval":
        expr = in_msg.get("expression")
        full_expr = expr.replace("(...)","(in_msg, context, async_report)")
        ok = eval(full_expr)
      
      elif cmd == "usspi_lib.init_params()":
        new_params = in_msg["new_params"]
        report_action = in_msg["report_action"]
        ok = usspi_lib.init_params(new_params, ws_send_msg, report_action)

      elif cmd == "usspi_lib.reread_params()":
        report_action = in_msg["report_action"]
        ok = usspi_lib.reread_params(ws_send_msg, report_action)

      elif cmd == "usspi_lib.read_raw()":
        report_action = in_msg["report_action"]
        period=in_msg["period"]
        ok = usspi_lib.continuous_read_raw(period, ws_send_msg, report_action)

      elif cmd == "path_lib.init_params()":
        new_params = in_msg["new_params"]
        report_action = in_msg["report_action"]
        ok = path_lib.init_params(new_params, ws_send_msg, report_action)

      elif cmd == "path_lib.reread_params()":
        report_action = in_msg["report_action"]
        ok = path_lib.reread_params(ws_send_msg, report_action)

      elif cmd == "path_lib.reset_path()":
        report_action = in_msg["report_action"]
        ok = path_lib.run_path(context, ws_send_msg, report_action, True)

      elif cmd == "path_lib.run_path()":
        report_action = in_msg["report_action"]
        ok = path_lib.run_path(context, ws_send_msg, report_action, False)

      elif cmd == "path_lib.pause_path()":
        report_action = in_msg["report_action"]
        ok = path_lib.pause_path(ws_send_msg, report_action)

      elif cmd == "path_lib.reread_path()":
        report_action = in_msg["report_action"]
        ok = path_lib.reread_path(ws_send_msg, report_action)

      elif cmd == "path_lib.db_list()":
        report_action = in_msg["report_action"]
        ok = path_lib.db_list(ws_send_msg, report_action)

      elif cmd == "path_lib.db_reload()":
        report_action = in_msg["report_action"]
        item=in_msg["item"]
        ok = path_lib.db_reload(item,ws_send_msg, report_action)

      else:
        print("Not understood !")        

      if not ws_send_msg(out_msg) : break
      
        
    except WebSocketError:
      break

#----------------------------------------
# http://localhost/
# http://localhost/index.html
#----------------------------------------
@app.route('/')
@app.route('/index.html')
def send_index_tpl(filename="index.html"):
  print("send_template('"+filename+"')")
  bottle.TEMPLATES.clear()
  return template('index', filename=filename)

#----------------------------------------
# http://localhost/path_data.json
#----------------------------------------
@app.route('/path_data.json')
def send_path_data(filename="path_data.json"):
  print("send_path_data('"+filename+"')")
  pdata = path_lib.get_path_data()
  return pdata

#----------------------------------------
# http://localhost/raw_data.json
#----------------------------------------
@app.route('/raw_data.json')
def send_raw_data(filename="raw_data.json"):
  print("send_raw_data('"+filename+"')")
  rdata = usspi_lib.get_raw_data()
  return rdata

#----------------------------------------
# http://localhost/.../filename.ext
#----------------------------------------
@app.route('/<filename:path>')
def send_static(filename):
  print("send_static('"+filename+"')")
  return static_file(filename, root='.')

#========================================
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
host = "0.0.0.0"
port = 80
context["xy_com"] = xy_lib.open_com("/dev/ttyAMA0") # For Raspberry Pi zero X, "COMxx" on Windows PC
usspi_lib.open_spi()

server = WSGIServer((host, port), app, handler_class=WebSocketHandler)
print ("access @ http://%s:%s/websocket.html" % (host,port))
server.serve_forever()
