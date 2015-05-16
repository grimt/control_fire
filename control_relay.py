import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode (GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.output(18, True)
time.sleep (2)
GPIO.output (18, False)
