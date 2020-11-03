#!/usr/bin/env python3
#encoding: UTF-8

#----------------------------------------
# Parameters database definition
#----------------------------------------
MIN        = 0
DEFAULT    = 1
MAX        = 2
DIGIT      = 3
SIU_TO_RAW = 4
RAW_TO_SIU = 5
REGISTER   = 6
BYTES      = 7
DESC       = 8
UNIT       = 9

SIU_PROG       = 0
SIU_ACTIV      = 1
RAW_PROG       = 2
RAW_ACTIV      = 3

#----------------------------------------
# Build initial current params values
#----------------------------------------
def build_raw_params(params_desc):
  
  return { k: [v[DEFAULT], -1, v[SIU_TO_RAW](v[DEFAULT]), -1] for k,v in params_desc.items() if k != ""}
  
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

