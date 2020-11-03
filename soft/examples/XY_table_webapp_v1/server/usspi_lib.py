#!/usr/bin/env python3
#encoding: UTF-8

import math
import threading
import time

#import RPi.GPIO as GPIO
try: import spidev
except: None

#########################################
# Devices interface library
#########################################

#========================================
# US-SPI US transducer driver
#========================================
usspi_w = None
usspi_r = None
read_period = 0
usspi_spec = {
# Parameters definition :
#   [0] - Minimum siu value
#   [1] - Initial siu value
#   [2] - Maximum siu value
#   [3] - Number of digits
#   [4] - Lambda function converting siu to raw value
#   [5] - US-SPI command to set this parameter
#   [6] - Size in bytes of the raw parameter
#----------------------------------------
# Initialize gain
#   gain_db : str : the value of gain to be sent to US-SPI (0 to 80 db)
#----------------------------------------
    "gain_db":[ 0, 30, 80, 0
              , lambda param: int(param*(875-65)/80+65)
              , 0, 2]
#----------------------------------------
# Initialize delay
#   delay_us : the value of the delay (beginning of sampling windows
#              the width of the sampling windows is fix at 200 microseconds
#----------------------------------------
  , "delay_us":[ 0, 1, 1000, 0
              , lambda param: int(param / 0.025)
              , 5, 2]
#----------------------------------------
# Initialize compression factor
#   comp : 0 -> sampling frequency 80 MHz, 1->40 MHz, 2->20MHz
# It returns the maximum amplitude of the echo in the sampling period
# /!\ Compression is available only if Filter=4=NoFilter AND SamplingFreq=1=80MHz
#----------------------------------------
  , "compression_factor":[ 0, 2, 2, 0
              , lambda param: int(param)
              , 3, 1]
#----------------------------------------
# Initialize tension
#   tension : the voltage of the transmitter pulse (between 10 and 250 Volts)
#----------------------------------------
  , "tension_v":[ 10, 20, 250, 0
              , lambda param: int(param*(98/180)+81.7)
              , 6, 1]
#----------------------------------------
# Initialize pulse width
#   freq : the frequency of the transmitter pulse in MHZ (between 1MHz and 20 MHz)
#          pulse will be period/2
#----------------------------------------
  , "freq_mhz":[ 1, 3.5, 20, 3
              , lambda param: int((1000/(2*param)-27)/6.5)
              , 7, 1]
#----------------------------------------
# Initialize pulse repetition frequency (PRF)
#   freq : the frequency of the line pulse in Hz (between 100Hz and 2kHz)
#          pulse will be period/2
#----------------------------------------
  , "prf_hz":[ 100, 100, 2000, 0
              , lambda param: int((1000000/param)/0.025)
              , 8, 3]
#----------------------------------------
# Initialize filter
#   filter : frequency of the filter (0=1.25MHz, 1=2.5MHz, 2=5MHz, 3=10MHz, 4=No filter)
#----------------------------------------
  , "filter_no":[ 0, 4, 4, 0
              , lambda param: int(param)
              , 14, 1]
#----------------------------------------
# Initialize nb_samples
#   nb_samples : number of samples to be acquired
#----------------------------------------
  , "nb_samples":[ 1, 1000, 4000, 0
              , lambda param: int(param)
              , -1, 0]
#----------------------------------------
# Initialize Transmission/ reflexion (single or dual crystals)
#   dual : 0 - single crystal, 1 - dual crystals
#----------------------------------------
  , "dual_transducer":[ 0, 0, 1, 0
              , lambda param: int(param)
              , 9, 1]
#----------------------------------------
# Initialize A-scan scale
#   scale : Scale of the A-scan in step of 25ns
#----------------------------------------
  , "ascan_scale":[ 0, 4000, 65532, 0
              , lambda param: int(param)
              , 10, 2]
#----------------------------------------
# Initialize polarity
#   pol : polarity
#----------------------------------------
  , "echo_polarity":[ 0, 50, 256, 0
              , lambda param: int(param)
              , 13, 1]
#----------------------------------------
# Initialize DAC
#   off : 0 ON, 1 OFF
#----------------------------------------
  , "dac_off":[ 0, 1, 1, 0
              , lambda param: int(param)
              , 11, 1]
#----------------------------------------
# Initialize sample auto-reload
#   sample_nb : When you will read the Xth samples, the US-Key will
#               store AUTOMATICALLY the current A-scan inside its FIFO
#----------------------------------------
  , "reload_on_sample":[ 0, 4000, 65532, 0
              , lambda param: int(param)
              , 4, 2]
  
#----------------------------------------
# Initialize Sampling Freq
#   sampling_freq : Sampling Freq : 0=160MHz / 1=80MHz / 2=40MHz
#----------------------------------------
  , "sampling_freq":[ 0, 1, 2, 0
              , lambda param: int(param)
              , 24, 1]
  
  }
usspi_cur_params = { "gain_db":usspi_spec["gain_db"][1]
                   , "delay_us":usspi_spec["delay_us"][1]
                   , "compression_factor":usspi_spec["compression_factor"][1]
                   , "tension_v":usspi_spec["tension_v"][1]
                   , "freq_mhz":usspi_spec["freq_mhz"][1]
                   , "prf_hz":usspi_spec["prf_hz"][1]
                   , "filter_no":usspi_spec["filter_no"][1]
                   , "dual_transducer":usspi_spec["dual_transducer"][1]
                   , "ascan_scale":usspi_spec["ascan_scale"][1]
                   , "echo_start_pos":"0"
                   , "echo_start_width":"10000"
                   , "echo_polarity":usspi_spec["echo_polarity"][1]
                   , "dac_off":usspi_spec["dac_off"][1]
                   , "reload_on_sample":usspi_spec["reload_on_sample"][1]
                   , "sampling_freq":usspi_spec["sampling_freq"][1]
                   , "nb_samples":usspi_spec["nb_samples"][1]
                   }

#----------------------------------------
# Extract bits 16..23 from an integer
#----------------------------------------
def bits_16_23(an_int):
  return (int(an_int) >> 16) & 0xFF

#----------------------------------------
# Extract bits 8..15 from an integer
#----------------------------------------
def bits_8_15(an_int):
  return (int(an_int) >> 8) & 0xFF

#----------------------------------------
# Extract bits 0..7 from an integer
#----------------------------------------
def bits_0_7(an_int):
  return int(an_int) & 0xFF

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
# Build bytes array
#----------------------------------------
def to_1b(an_int): return [  bits_0_7(an_int)]
def to_2b(an_int): return [ bits_8_15(an_int), bits_0_7(an_int)]
def to_3b(an_int): return [bits_16_23(an_int), bits_8_15(an_int), bits_0_7(an_int)]

#----------------------------------------
# Initialize SPI port
#----------------------------------------
def open_spi():
  global usspi_w
  global usspi_r

#  GPIO.setwarnings(False)
#  GPIO.setmode(GPIO.BOARD)
#  GPIO.setup(3, GPIO.OUT, initial = GPIO.LOW)
  try:
    usspi_w = spidev.SpiDev(0, 0)  
    usspi_w.max_speed_hz = 8000000 	# 1 MHz max, boosted to 8MHz !!!
    usspi_w.mode = 0b01 			# CPOL=0 CPHA=1
  except:
    usspi_w = None

  try:
    usspi_r = spidev.SpiDev(0, 1)  
    usspi_r.max_speed_hz = 8000000	# 1 MHz max, boosted to 8MHz !!!
    usspi_r.mode = 0b01 			# CPOL=0 CPHA=1 
  except:
     usspi_r = None

#----------------------------------------
# Write byte array on SPI port
#----------------------------------------
def write_spi(wBuffer):
  global usspi_w

  # print(wBuffer)
  if usspi_w:
    usspi_w.writebytes(wBuffer)

#----------------------------------------
# Write byte array on SPI port
#----------------------------------------
def read_spi(count):
  global usspi_r

  if usspi_r:
    return usspi_r.readbytes(count)
  else:
    return [math.sin(i/5)*100+128 for i in range(count)]

#----------------------------------------
# Initialize SPI port
#----------------------------------------
def close_spi():
  global usspi_w
  global usspi_r

  if usspi_w:
    usspi_w.close()
  if usspi_r:
    usspi_r.close()
#  GPIO.cleanup()

#----------------------------------------
# Initialize a parameter
#----------------------------------------
def set_param(name, new, cur):
  global usspi_spec
  
  spec = usspi_spec[name]
  if spec[3]==0:
    param = int(frame(new, name, spec[0], spec[2], cur))
  else:
    param = round(frame(new, name, spec[0], spec[2], cur), spec[3])
    
  cmd = spec[5]  # selection gain
  raw_param = spec[4](param)
  if (spec[6]==1): param_bytes = to_1b(raw_param)
  if (spec[6]==2): param_bytes = to_2b(raw_param)
  if (spec[6]==3): param_bytes = to_3b(raw_param)
  if (cmd >= 0): write_spi(param_bytes+[cmd])
  cur[name]= str(param)
 
#----------------------------------------
# Initialize echo_start ???
#   pos, width ...
#----------------------------------------
def set_echo_start(new, cur):
  
  param1 = int(frame(new, "echo_start_pos", 0, 65532, cur))
  param2 = int(frame(new, "echo_start_width", 0, 65532, cur))
  cmd = 12  # echo start, Echo-start=0 !!!!
  raw_param1 = int(param1)
  raw_param2 = int(param1)
  write_spi(to_2b(raw_param2)+to_2b(raw_param1)+[cmd])
  cur["echo_start_pos"]= str(param1)
  cur["echo_start_width"]= str(param2)
 
#----------------------------------------
# Initialize sample auto-reload
#   sample_nb : When you will read the Xth samples, the US-Key will
#               store AUTOMATICALLY the current A-scan inside its FIFO
#----------------------------------------
def set_sample_request():
  
  cmd = 2  # Sampling request
  write_spi([cmd])
  
#----------------------------------------
# Initialize sample auto-reload
#   count : number of samples to read from FIFO
#----------------------------------------
def get_samples():
  global usspi_cur_params
  
  count = int(usspi_cur_params["nb_samples"])
  return read_spi(count)[2:]
  
#----------------------------------------
# re-read parameters
#----------------------------------------
def reread_params(ws_send_msg, report_action):
   
  out_msg = {"cmd":"report", "report_from":"usspi_lib.reread_params()", "report_action":report_action, "data":usspi_cur_params}
  ws_send_msg(out_msg)

#----------------------------------------
# get parameters
#----------------------------------------
def get_params():
   
  return usspi_cur_params

#----------------------------------------
# Initialize US-SPI parameters
#----------------------------------------
def init_params(new_params, ws_send_msg, report_action):
  global usspi_cur_params
  
  set_param("gain_db", new_params, usspi_cur_params)
  set_param("delay_us", new_params, usspi_cur_params)
  set_param("compression_factor", new_params, usspi_cur_params)
  set_param("tension_v", new_params, usspi_cur_params)
  set_param("freq_mhz", new_params, usspi_cur_params)
  set_param("prf_hz", new_params, usspi_cur_params)
  set_param("filter_no", new_params, usspi_cur_params)
  set_param("dual_transducer", new_params, usspi_cur_params)
  set_param("nb_samples", new_params, usspi_cur_params)
  
  # Some initializations that must be done (not documented) for futures functions
  set_param("ascan_scale", new_params, usspi_cur_params)
  set_echo_start(new_params, usspi_cur_params)  # Echo-start=0 !!!!
  set_param("echo_polarity", new_params, usspi_cur_params)     # Echo-start=0 !!!!
  set_param("dac_off", new_params, usspi_cur_params)
  set_param("reload_on_sample", new_params, usspi_cur_params)
  set_param("sampling_freq", new_params, usspi_cur_params)
  
  reread_params(ws_send_msg, report_action)

#----------------------------------------
# Read raw data
#----------------------------------------
def continuous_read_raw(period, ws_send_msg, report_action):
  global read_period

  if read_period == 0:
    t = threading.Thread(target=read_raw_loop, args=(ws_send_msg, report_action))
    read_period = period
    t.start()
  else:
    read_period = period
    
#----------------------------------------
# Read raw data
#----------------------------------------
def read_raw_loop(ws_send_msg, report_action):
  global read_period

  while True:
    set_sample_request()
    time.sleep(0.01)
    resp = get_samples()
    out_msg = {"cmd":"report", "report_from":"usspi_lib.read_raw()", "report_action":report_action, "raw":resp}
    if ws_send_msg(out_msg) and read_period > 0 :
      time.sleep(read_period)
    else:
      break
    
#----------------------------------------
# Read raw data
#----------------------------------------
def read_one_raw():
  global read_period

  read_period = 0
  set_sample_request()
  time.sleep(0.01)
  return get_samples()
    
#----------------------------------------
# Read raw data
#----------------------------------------
def get_raw_data():
  return {"us_spi_params":get_params(), "measures":read_one_raw()}
    
#----------------------------------------
# Set 
#----------------------------------------
def set_delay_us(delay):
  global usspi_cur_params

  set_param("delay_us", {"delay_us": delay}, usspi_cur_params)
