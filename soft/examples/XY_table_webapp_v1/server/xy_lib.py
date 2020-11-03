#!/usr/bin/env python3
#encoding: UTF-8

import re
try: import serial
except: None
  
#########################################
# Devices interface library
#########################################

#========================================
# XY Table
#========================================

#----------------------------------------
# Initialize serial port
#----------------------------------------
def open_com(p):
    try:
        ser_port = serial.Serial(port=p, timeout=60, baudrate=115200)
    except SerialException:
        ser_port = None
    return ser_port

#----------------------------------------
# Initialize serial port
#----------------------------------------
def _xy_move_report(text, x, y):

  return { "msg_type":"xy_move_report"
         , "text":text
         , "x":x
         , "y":y
         }

#----------------------------------------
# Send only one G code to the xy table
#----------------------------------------
def _send_g(line, ser_port, async_report):

  if async_report: async_report(_xy_move_report(line + " ...", "", ""))
  try:
      ser_port.reset_input_buffer()
      ser_port.write((line + "\r\n").encode())
      resp = ser_port.readline().decode()
  except:
      resp = "X=-1 Y=-1"

  m = re.search('X=(.+) Y=(.+) ', resp)
  if m :
        x = m.group(1)
        y = m.group(2)
  else:
    x = ""
    y = ""

  if async_report: async_report(_xy_move_report(resp + "\n", x, y))
  return True

#----------------------------------------
# Send a block ok G code lines
#----------------------------------------
def send_g_lines(in_msg, context, async_report):
    ser_port = context["xy_com"]
    text_block = in_msg.get("lines")
    lines = text_block.splitlines()
    for line in lines:
        ok = _send_g(line, ser_port, async_report)

    return True
