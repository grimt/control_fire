import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode (GPIO.BCM)
GPIO.setup (7, GPIO.OUT)
GPIO.setup (8, GPIO.OUT)
GPIO.setup (23, GPIO.OUT)
GPIO.setup (24, GPIO.OUT)
 
GPIO.setup (25, GPIO.OUT)
GPIO.setup (21, GPIO.OUT)
GPIO.setup (22, GPIO.OUT)




#while True:
GPIO.output (7, True)
time.sleep (1)
    
GPIO.output (8, True)
time.sleep(1)
    
GPIO.output (23, True)
time.sleep(1)

GPIO.output (24, True)
time.sleep(1)


GPIO.output (25, True)
time.sleep (1)
    
GPIO.output (21, True)
time.sleep(1)
    
GPIO.output (22, True)
time.sleep(1)


GPIO.output (7, False)
time.sleep (1)
    
GPIO.output (8, False)
time.sleep(1)
    
GPIO.output (23, False)
time.sleep(1)

GPIO.output (24, False)
time.sleep(1)



GPIO.output (25, False)
time.sleep (1)
    
GPIO.output (21, False)
time.sleep(1)
    
GPIO.output (22, False)
time.sleep(1)


