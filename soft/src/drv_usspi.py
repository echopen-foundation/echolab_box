#!/usr/bin/env python3
#encoding: UTF-8

import time
import threading
import math
#import RPi.GPIO as GPIO
try: import spidev
except: None
import lib_helpers as hlp

#########################################
# Devices interface library
#########################################

#========================================
# US-SPI US transducer driver
#========================================
usspi_w = None
usspi_r = None
read_period = 0

params_desc = {
#----------------------------------------
    "":( "MIN", "DEFAULT", "MAX", "DIGIT"
              , "SIU_TO_RAW"
              , "RAW_TO_SIU"
              , "REGISTER", "BYTES"
              , "DESC"
              , "UNIT")

#----------------------------------------
  , "std_gain_db":( 0, 30, 80, 0
              , lambda siu: int(siu*(875-65)/80+65)
              , lambda raw: ...
              , 0, 2
              , "Value of static gain"
              , "dB")

#----------------------------------------
  , "gain_db":( 0, 30, 80, 0
              , lambda siu: int(siu*(875-65)/80+65)
              , lambda raw: ...
              , 0, 2
              , "Value of gain to be sent to US-SPI (0 to 80 db)"
              , "dB")

#----------------------------------------
  , "delay_us":( 0, 1, 1000, 0
              , lambda siu: int(siu / 0.025)
              , lambda raw: ...
              , 5, 2
              ,"Value of the delay (beginning of sampling windows the width of the sampling windows is fix at 200 microseconds"
              ,"µs")

#----------------------------------------
  , "compression_factor":( 0, 2, 2, 0
              , lambda siu: int(siu)
              , lambda raw: ...
              , 3, 1
              ,"0 -> sampling frequency (ex 80 MHz) , 1->sf/2 (40 MHz), 2->sf/4 (20MHz). It returns the maximum amplitude of the echo in the sampling period /!\ Compression is available only if Filter=4(NoFilter) AND SamplingFreq=1(80MHz)"
              ,"")

#----------------------------------------
  , "tension_v":( 10, 20, 250, 0
              , lambda siu: int(siu*(98/180)+81.7)
              , lambda raw: ...
              , 6, 1
              ,"Voltage of the transmitter pulse"
              ,"V")

#----------------------------------------
  , "freq_mhz":( 1, 3.5, 20, 3
              , lambda siu: int((1000/(2*siu)-27)/6.5)
              , lambda raw: ...
              , 7, 1
              ,"Frequency of the transmitter pulse in MHZ (between 1MHz and 20 MHz) pulse will be period/2"
              ,"MHz")

#----------------------------------------
  , "prf_hz":( 100, 100, 2000, 0
              , lambda siu: int((1000000/siu)/0.025)
              , lambda raw: ...
              , 8, 3
              ,"Frequency of the line pulse in Hz (between 100Hz and 2kHz)"
              ,"Hz")

#----------------------------------------
  , "filter_no":( 0, 4, 4, 0
              , lambda siu: int(siu)
              , lambda raw: ...
              , 14, 1
              ,"Frequency of the filter (0=1.25MHz, 1=2.5MHz, 2=5MHz, 3=10MHz, 4=No filter)"
              ,"")

#----------------------------------------
  , "nb_samples":( 1, 1000, 4000, 0
              , lambda siu: int(siu)
              , lambda raw: ...
              , -1, 0
              ,"Number of samples to be acquired"
              ,"")

#----------------------------------------
  , "dual_transducer":( 0, 0, 1, 0
              , lambda siu: int(siu)
              , lambda raw: ...
              , 9, 1
              ,"Transmission/ reflexion (single or dual crystals) 0 - single crystal, 1 - dual crystals"
              ,"")

#----------------------------------------
  , "ascan_scale":( 0, 4000, 65532, 0
              , lambda siu: int(siu)
              , lambda raw: ...
              , 10, 2
              ,"Scale (duration) of the A-scan in step of 25ns"
              ,"25ns")

#----------------------------------------
  , "echo_polarity":( 0, 50, 256, 0
              , lambda siu: int(siu)
              , lambda raw: ...
              , 13, 1
              ,"Polarity"
              ,"")

#----------------------------------------
  , "dac_off":( 0, 1, 1, 0
              , lambda siu: int(siu)
              , lambda raw: ...
              , 11, 1
              ,"DAC for TGC 0 ON, 1 OFF"
              ,"")

#----------------------------------------
  , "reload_on_sample":( 0, 4000, 65532, 0
              , lambda siu: int(siu)
              , lambda raw: ...
              , 4, 2
              ,"Sample auto-reload : when you will read the Xth samples, the US-Key will store AUTOMATICALLY the current A-scan inside its FIFO"
              ,"")
  
#----------------------------------------
  , "sampling_freq":( 0, 1, 2, 0
              , lambda siu: int(siu)
              , lambda raw: ...
              , 24, 1
              ,"Sampling Freq : 0=160MHz / 1=80MHz / 2=40MHz"
              ,"")
  
#----------------------------------------
  , "echo_start_pos":( 0, 0, 65535, 0
              , lambda siu: int(siu)
              , lambda raw: raw
              , 12, 2
              ,"?????"
              ,"")
  
#----------------------------------------
  , "echo_start_width":( 0, 10000, 65535, 0
              , lambda siu: int(siu)
              , lambda raw: raw
              , 12, 2
              ,"?????"
              ,"")
  
  }

raw_params =  hlp.build_raw_params(params_desc)

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
  global params_desc
  
  spec = params_desc[name]
  if spec[hlp.DIGIT]==0:
    param = int(hlp.frame(new, name, spec[hlp.MIN], spec[hlp.MAX], cur))
  else:
    param = round(hlp.frame(new, name, spec[hlp.MIN], spec[hlp.MAX], cur), spec[hlp.DIGIT])
    
  cmd = spec[hlp.REGISTER]  # selection gain
  raw_param = spec[hlp.SIU_TO_RAW](param)
  if (spec[hlp.BYTES]==1): param_bytes = hlp.to_1b(raw_param)
  if (spec[hlp.BYTES]==2): param_bytes = hlp.to_2b(raw_param)
  if (spec[hlp.BYTES]==3): param_bytes = hlp.to_3b(raw_param)
  if (cmd >= 0): write_spi(param_bytes+[cmd])
  cur[name]= str(param)
 
#----------------------------------------
# Initialize echo_start ???
#   pos, width ...
#----------------------------------------
def set_echo_start(new, cur):
  
  param1 = int(hlp.frame(new, "echo_start_pos", 0, 65535, cur))
  param2 = int(hlp.frame(new, "echo_start_width", 0, 65535, cur))
  cmd = 12  # echo start, Echo-start=0 !!!!
  raw_param1 = int(param1)
  raw_param2 = int(param2) #  ???? int(param1)
  write_spi(hlp.to_2b(raw_param2)+hlp.to_2b(raw_param1)+[cmd])
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
  global raw_params
  
  count = int(raw_params["nb_samples"])
  return read_spi(count)[2:]
  
#----------------------------------------
# re-read parameters
#----------------------------------------
def reread_params(ws_send_msg, report_action):
   
  out_msg = {"cmd":"report", "report_from":"usspi_lib.reread_params()", "report_action":report_action, "data":raw_params}
  ws_send_msg(out_msg)

#----------------------------------------
# get parameters
#----------------------------------------
def get_params():
   
  return raw_params

#----------------------------------------
# Initialize US-SPI parameters
#----------------------------------------
def init_params(new_params, ws_send_msg, report_action):
  global raw_params
  
  set_param("gain_db", new_params, raw_params)
  set_param("delay_us", new_params, raw_params)
  set_param("compression_factor", new_params, raw_params)
  set_param("tension_v", new_params, raw_params)
  set_param("freq_mhz", new_params, raw_params)
  set_param("prf_hz", new_params, raw_params)
  set_param("filter_no", new_params, raw_params)
  set_param("dual_transducer", new_params, raw_params)
  set_param("nb_samples", new_params, raw_params)
  
  # Some initializations that must be done (not documented) for futures functions
  set_param("ascan_scale", new_params, raw_params)
  set_echo_start(new_params, raw_params)  # Echo-start=0 !!!!
  set_param("echo_polarity", new_params, raw_params)     # Echo-start=0 !!!!
  set_param("dac_off", new_params, raw_params)
  set_param("reload_on_sample", new_params, raw_params)
  set_param("sampling_freq", new_params, raw_params)
  
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
  global raw_params

  set_param("delay_us", {"delay_us": delay}, raw_params)
