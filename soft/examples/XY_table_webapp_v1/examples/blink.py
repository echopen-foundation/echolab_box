# Import des modules
import RPi.GPIO as GPIO
import time

# Initialisation de la numerotation et des E/S
GPIO.setmode(GPIO.BOARD)
GPIO.setup(37, GPIO.OUT, initial = GPIO.HIGH)

# On fait clignoter la LED
while True:
    GPIO.output(37, not GPIO.input(37))
    time.sleep(0.001)