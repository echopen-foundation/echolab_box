#!/usr/bin/python3
import RPi.GPIO as GPIO
import spidev
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(3, GPIO.OUT, initial = GPIO.LOW)


usspi_w = spidev.SpiDev(0, 0)  
usspi_w.max_speed_hz = 100000 	# 0.1 MHz
usspi_w.mode = 0b01 			# CPOL=0 CPHA=1 

usspi_r = spidev.SpiDev(0, 1)  
usspi_r.max_speed_hz = 100000	# 0.1 MHz
usspi_r.mode = 0b01 			# CPOL=0 CPHA=1 
tr=0

# 1) Gainc contains the value of gain to be sent to US-SPI (0 to 80 db)
gainc = 40 		# db
calculation_gain = gainc*(875-65)/80+65
msb=int(calculation_gain/256) 	#msb
lsb=int(calculation_gain-int(calculation_gain/256)*256) #lsb wBuffercmd(2)=0 'selection gain
cmd = 0	#selection gain
wBuffercmd = [msb, lsb, cmd]
print("1 - Gain programming : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

# 2) “Delayc” contains the value of the delay (beginning of sampling windows
#    the width of the sampling windows is fix at 200 microseconds)
delayc = 0	# µs
calculation_delay = delayc / 0.025 #25 nS step
msb=int(calculation_delay/256) 	#msb
lsb=int(calculation_delay-int(calculation_delay/256)*256) #lsb
cmd = 5	# delay
wBuffercmd = [msb, lsb, cmd]
print("2 - Delay programming : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

# 3) “Consfactorcomp” contains the compression factor
consfactcomp = 6		# 80MHz / (2^cf), 4 -> 5MHz
lsb=consfactcomp
cmd = 3	# delay
wBuffercmd = [lsb, cmd]
print("3 - Compression factor programming : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

# 4) Tensionc contains the voltage of the transmitter pulse (between 10 and 250 Volts)
tensionc = 20		# V
lsb=int(tensionc*(98/180)+81.7)
cmd = 6	# Transmitter voltage
wBuffercmd = [lsb, cmd]
print("4 - Transmitter voltage : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

# 5) Conslargeur contains the frequency of the transmitter pulse in MHZ (between 1MHz and 20 MHz)
conslargeur = 3.5 # 3.5 # MHz
lsb=int((1000/(2*conslargeur)-27)/6.5) #convert the pulse frequency in width and scale it
cmd = 7	# transmitter pulse
wBuffercmd = [lsb, cmd]
print("5 - transmitter pulse : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

# 6) Consfreqrec contains the frequency of the pulse repetition (between 100Hz and 2 KHz)
consfreqrec =100		# Hz
calculation_consfreqrec = (1000000/consfreqrec)/0.025
b2=int(calculation_consfreqrec/65536)
b1=int((calculation_consfreqrec-b2*65536)/256)
b0=int(calculation_consfreqrec-b1*256-b2*65536)
cmd = 8	# PRF
wBuffercmd = [b2, b1, b0, cmd]
print("6 - Repetition frequency (PRF) : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

# 7) f contains the frequency of the filter (0=1.25MHz, 1=2.5MHz, 2=5MHz, 3=10MHz, 4=No filter)
f = 4
lsb = f
cmd = 14	# Filter
wBuffercmd = [lsb, cmd]
print("7 - Filter : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

# 8) Transmission/ reflexion (single or dual crystals)
tr = 0 # 0 - single crystal, 1 - dual crystals
lsb = tr
cmd = 9 # Mode
wBuffercmd = [lsb, cmd]
print("7 - Transmission/ reflexion : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

# 9) Some initializations that must be done (not documented) for futures functions
consechascan = 4000
msb = int(consechascan/256)
lsb = consechascan - msb*256
cmd = 10 # selectionechascan
wBuffercmd = [msb, lsb, cmd]
print("9.1 - selectionechascan : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

pos=0
duree=10000
msb1 = int(duree/256)
lsb1 = duree - msb1*256
msb2 = int(pos/256)
lsb2 = pos - msb2*256
cmd = 12 # echo start
wBuffercmd = [msb1, lsb1, msb2, lsb2, cmd]
print("9.2 - echo start : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

polarite=50
lsb = polarite
cmd = 13 # Polarité
wBuffercmd = [lsb, cmd]
print("9.3 - Polarité : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

DAC= 1 # 0 ON, 1 OFF
lsb = DAC
cmd = 11 # DAC on/off
wBuffercmd = [lsb, cmd]
print("9.4 - /DAC : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

nbpts = 4000
msb = int(nbpts/256)
lsb = nbpts - msb*256
cmd = 4 # selectionechascan
wBuffercmd = [msb, lsb, cmd]
print("9.5 - Sampling request #1 : " + str(wBuffercmd))
usspi_w.writebytes(wBuffercmd)

while (True):
	GPIO.output(3, GPIO.HIGH)

	#10) Signal (RF) acquisition
	wBuffercmd = [2]
	print("10 - Signal (RF) acquisition : " + str(wBuffercmd))
	resp = usspi_w.writebytes(wBuffercmd)

	#time.sleep(1/consfreqrec*2)
	time.sleep(0.2)
	resp = usspi_r.readbytes(512)
	print(resp)

	GPIO.output(3, GPIO.LOW)
	#time.sleep(1)

usspi_w.close()
usspi_r.close()
GPIO.cleanup()
