#!/usr/bin/env python3
#encoding: UTF-8

import lib_helpers as hlp

params_desc = {
#----------------------------------------
    "":( "MIN", "DEFAULT", "MAX", "DIGIT"
              , "SIU_TO_RAW"
              , "RAW_TO_SIU"
              , "REGISTER", "BYTES"
              ,"DESC"
              ,"UNIT")

#----------------------------------------
  , "sLED_rgb":( 0, 0x000100, 0x010101, 0
              , lambda siu: int(siu)
              , lambda raw: raw
              , 0xC1, 3
              , "Diagnostic RGB LED"
              , "rgb")

# #----------------------------------------
#   , "std_gain_db":( 0, 30, 80, 0
#               , lambda siu: int(siu/10*1000/4)
#               , lambda raw: ...
#               , 0, 2
#               , "Value of static gain"
#               , "dB")

#----------------------------------------
  , "sEEDAC_mV":( 0, 68, 1000, 0
              , lambda siu: int(siu/4)
              , lambda raw: raw*4
              , 0xEC, 1
              , "Voltage gain control: 0V to 1V"
              , "mV")

#----------------------------------------
  , "sEEPon_ns":( 0, 200, 2550, 0
              , lambda siu: int(siu/10)
              , lambda raw: raw*10
              , 0xE0, 1
              , "Lengh of Pon (pulse on)"
              , "ns")

#----------------------------------------
  , "sEEPonPoff_ns":( 0, 100, 2550, 0
              , lambda siu: int(siu/10)
              , lambda raw: raw*10
              , 0xD0, 1
              , "Lengh between Pon and Poff (pulse on/pulse off)"
              , "ns")

#----------------------------------------
  , "sEEPoff_ns":( 0, 2000, 0xFFFF*10, 0
              , lambda siu: int(siu/10)
              , lambda raw: raw*10
              , 0xE1, 2                     # 0xE1 MSB, 0xE2 LSB
              , "Lengh of Poff (pulse off)"
              , "ns")

#----------------------------------------
  , "sEEDelayACQ_ns":( 0, 7000, 0xFFFF*10, 0
              , lambda siu: int(siu/10)
              , lambda raw: raw*10
              , 0xE3, 2                     # 0xE5 MSB, 0xE6 LSB
              , "Lengh of Delay between Poff and Acq"
              , "ns")

#----------------------------------------
  , "sEEACQ_ns":( 0, 130000, 0xFFFF*10, 0
              , lambda siu: int(siu/10)
              , lambda raw: raw*10
              , 0xE5, 2                     # 0xE3 MSB, 0xE4 LSB
              , "Lengh of acquisition"
              , "ns")

#----------------------------------------
  , "sEEPeriod_ns":( 0, 1000, 0xFFFFFF*10, 0
              , lambda siu: int(siu/10)
              , lambda raw: raw*10
              , 0xE7, 3                     # 0xE7 MSB, 0xE8 ..., 0xE9 LSB
              , "Period of one cycle"
              , "ns")

#----------------------------------------
  , "sEETrigInternal":( 0, 0, 1, 0
              , lambda siu: int(siu)
              , lambda raw: raw
              , 0xEA, 1
              , "Software Trig : Auto clear"
              , "")

#----------------------------------------
  , "sEESingleCont":( 0, 0, 1, 0
              , lambda siu: int(siu)
              , lambda raw: raw
              , 0xEB, 1
              , "Continuous mode : 0: single mode, 1 continious mode"
              , "")

#----------------------------------------
  , "sEEADC_freq_MHz":( 0.251, 16, 64, 0
              , lambda siu: int(64/(1+siu))
              , lambda raw: 64/raw - 1
              , 0xED, 1
              , "Frequency of ADC acquisition"
              , "MHz")

#----------------------------------------
  , "sEETrigCounter":( 0, 10, 0xFF, 0
              , lambda siu: int(siu)
              , lambda raw: raw
              , 0xEE, 1
              , "How many cycles in countinuous mode"
              , "")

#----------------------------------------
  , "sEEpointerReset":( 0, 0, 1, 0
              , lambda siu: int(siu)
              , lambda raw: raw
              , 0xEF, 1
              , "Sofware memory reset: set to 1; auto clear"
              , "")

# #----------------------------------------
#   , "delay_us":( 0, 1, 1000, 0
#               , lambda param: int(param / 0.025)
#               , lambda param: ...
#               , 5, 2
#               ,"Value of the delay (beginning of sampling windows the width of the sampling windows is fix at 200 microseconds"
#               ,"µs")

# #----------------------------------------
#   , "compression_factor":( 0, 2, 2, 0
#               , lambda param: int(param)
#               , lambda param: ...
#               , 3, 1
#               ,"0 -> sampling frequency (ex 80 MHz) , 1->sf/2 (40 MHz), 2->sf/4 (20MHz). It returns the maximum amplitude of the echo in the sampling period /!\ Compression is available only if Filter=4(NoFilter) AND SamplingFreq=1(80MHz)"
#               ,"")

# #----------------------------------------
#   , "tension_v":( 10, 20, 250, 0
#               , lambda param: int(param*(98/180)+81.7)
#               , lambda param: ...
#               , 6, 1
#               ,"Voltage of the transmitter pulse"
#               ,"V")

# #----------------------------------------
#   , "freq_mhz":( 1, 3.5, 20, 3
#               , lambda param: int((1000/(2*param)-27)/6.5)
#               , lambda param: ...
#               , 7, 1
#               ,"Frequency of the transmitter pulse in MHZ (between 1MHz and 20 MHz) pulse will be period/2"
#               ,"MHz")

# #----------------------------------------
#   , "prf_hz":( 100, 100, 2000, 0
#               , lambda param: int((1000000/param)/0.025)
#               , lambda param: ...
#               , 8, 3
#               ,"Frequency of the line pulse in Hz (between 100Hz and 2kHz)"
#               ,"Hz")

# #----------------------------------------
#   , "filter_no":( 0, 4, 4, 0
#               , lambda param: int(param)
#               , lambda param: ...
#               , 14, 1
#               ,"Frequency of the filter (0=1.25MHz, 1=2.5MHz, 2=5MHz, 3=10MHz, 4=No filter)"
#               ,"")

# #----------------------------------------
#   , "nb_samples":( 1, 1000, 4000, 0
#               , lambda param: int(param)
#               , lambda param: ...
#               , -1, 0
#               ,"Number of samples to be acquired"
#               ,"")

# #----------------------------------------
#   , "dual_transducer":( 0, 0, 1, 0
#               , lambda param: int(param)
#               , lambda param: ...
#               , 9, 1
#               ,"Transmission/ reflexion (single or dual crystals) 0 - single crystal, 1 - dual crystals"
#               ,"")

# #----------------------------------------
#   , "ascan_scale":( 0, 4000, 65532, 0
#               , lambda param: int(param)
#               , lambda param: ...
#               , 10, 2
#               ,"Scale (duration) of the A-scan in step of 25ns"
#               ,"25ns")

# #----------------------------------------
#   , "echo_polarity":( 0, 50, 256, 0
#               , lambda param: int(param)
#               , lambda param: ...
#               , 13, 1
#               ,"Polarity"
#               ,"")

# #----------------------------------------
#   , "dac_off":( 0, 1, 1, 0
#               , lambda param: int(param)
#               , lambda param: ...
#               , 11, 1
#               ,"DAC for TGC 0 ON, 1 OFF"
#               ,"")

# #----------------------------------------
#   , "reload_on_sample":( 0, 4000, 65532, 0
#               , lambda param: int(param)
#               , lambda param: ...
#               , 4, 2
#               ,"Sample auto-reload : when you will read the Xth samples, the US-Key will store AUTOMATICALLY the current A-scan inside its FIFO"
#               ,"")
  
# #----------------------------------------
#   , "sampling_freq":( 0, 1, 2, 0
#               , lambda param: int(param)
#               , lambda param: ...
#               , 24, 1
#               ,"Sampling Freq : 0=160MHz / 1=80MHz / 2=40MHz"
#               ,"")
  
  }

raw_params =  hlp.build_raw_params(params_desc)
