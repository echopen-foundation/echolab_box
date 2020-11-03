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
