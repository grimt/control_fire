# modules to read from the flirc
from evdev import InputDevice, categorize, ecodes
from threading import Thread, Event
import Adafruit_DHT
import RPi.GPIO as GPIO

import sys
import time


ON = True
OFF = False

# Key definitions
REMOTE_KEY_RED = 2
REMOTE_KEY_GREEN = 3
REMOTE_KEY_YELLOW = 4
REMOTE_KEY_BLUE = 5 

# GPIO PINs
OUT_MEASURED_TEMP_RED_LED = 7
OUT_MEASURED_TEMP_GREEN_LED = 8
OUT_MEASURED_TEMP_YELLOW_LED = 23
OUT_MEASURED_TEMP_BLUE_LED = 24

OUT_DESIRED_TEMP_GREEN_LED = 25
OUT_DESIRED_TEMP_YELLOW_LED = 21
OUT_DESIRED_TEMP_BLUE_LED = 22

OUT_RELAY_PIN = 18

IN_MEASURE_TEMP_PIN = 4

DHT_22 = 22

def init_GPIO():
    GPIO.setwarnings(False)
    GPIO.setmode (GPIO.BCM)

    GPIO.setup (OUT_MEASURED_TEMP_RED_LED, GPIO.OUT)
    GPIO.setup (OUT_MEASURED_TEMP_GREEN_LED, GPIO.OUT)
    GPIO.setup (OUT_MEASURED_TEMP_YELLOW_LED, GPIO.OUT)
    GPIO.setup (OUT_MEASURED_TEMP_BLUE_LED, GPIO.OUT)
    GPIO.setup (OUT_DESIRED_TEMP_GREEN_LED, GPIO.OUT)
    GPIO.setup (OUT_DESIRED_TEMP_YELLOW_LED, GPIO.OUT)
    GPIO.setup (OUT_DESIRED_TEMP_BLUE_LED, GPIO.OUT)

    GPIO.setup(OUT_RELAY_PIN, GPIO.OUT)

#--------------------------------------- Class Definitions ----------------------------


class Fire:

    debug_level = 0
    required_temperature = 0
    measured_temperature = 0
    fire_state = 0 


    def __init__ (self):
        self.description = "A fire to heat the home"
        self.author = "Graeme Thomson"

    def debug_level_set (self, level):
        self.debug_level = level

    def print_debug_state(self):
        if self.debug_level >= 1:
            print ('Debug is ON level:' + str (self.debug_level))
        else:
            print ('Debug is OFF')
            
    def desired_temp_set (self, temp):
	self.required_temperature = temp
		
    def desired_temp_get (self):
	return self.required_temperature

    def measured_temp_set (self, temp):
        self.measured_temperature = temp

    def measured_temp_get (self):
        return self.measured_temperature

#--------------------------- End of Class Fire ----------------------


def switch_fire (off_or_on):
    if off_or_on == ON:
        GPIO.output (OUT_RELAY_PIN, True)
        if my_fire.debug_level >=1:
    	    print ("Fire is ON")
    else:
        GPIO.output (OUT_RELAY_PIN, False)
        if my_fire.debug_level >=1:
    	    print ("Fire is OFF")
  

def control_temperature (desired, actual):
    if desired == 0:
        switch_fire (OFF)
    elif desired == 999:
        switch_fire (ON)
    else:
        print ('Temperature logic here')

# Right now we are passing data between threads by writing to a file.
# This may change in the future. These abstractions allow for the
# data communication  method to change.


def set_desired_temp_led (key):
    # First set all the desired temp LEDs to off
    GPIO.output (OUT_DESIRED_TEMP_GREEN_LED, False)
    GPIO.output (OUT_DESIRED_TEMP_YELLOW_LED, False)
    GPIO.output (OUT_DESIRED_TEMP_BLUE_LED, False)

    if key == REMOTE_KEY_GREEN:
       GPIO.output (OUT_DESIRED_TEMP_GREEN_LED, True) 
    elif key == REMOTE_KEY_YELLOW:
        GPIO.output (OUT_DESIRED_TEMP_YELLOW_LED, True)
    elif key == REMOTE_KEY_BLUE:
        GPIO.output (OUT_DESIRED_TEMP_BLUE_LED, True)

def write_desired_temp_to_file (key):
   
    if key == REMOTE_KEY_RED:
        # The red remote button toggles the fire off/on irrespective of
        # temperature. This is represented in the file by:
        # on = 999
        # off = 0
        # To Toggle the temperature we must first read it from the file.
        desired_temperature = 0
        try:
            f = open ('/tmp/temperature.txt','rt')
            temp = f.read ()
            desired_temperature = int (temp)
            f.close ()
            if desired_temperature == 0:
                desired_temperature = 999
            elif desired_temperature > 0:
                desired_temperature = 0

        except IOError:
            if my_fire.debug_level >=2:
    	        print ("Cant open file")


    elif key == REMOTE_KEY_GREEN:
        desired_temperature = 18
    elif key == REMOTE_KEY_YELLOW:
        desired_temperature = 19
    elif key == REMOTE_KEY_BLUE:
        desired_temperature = 20
    else:
        desired_temperature = 0

    try:
        f = open ('/tmp/temperature.txt','wt')
        f.write (str (desired_temperature))
        f.close ()
    except IOError:
        if my_fire.debug_level >= 2:
    	    print ("Cant open file")

def read_measured_temp_from_file ():
    temp = '0'
    try:
        f = open ('/tmp/measured_temperature.txt','rt')
        temp = f.read ()
        f.close ()
    except IOError:
        if my_fire.debug_level >=2:
    	    print ("Cant open file")

    return temp


def write_measured_temp_to_file (temp):

    try:
        f = open ('/tmp/measured_temperature.txt','wt')
        f.write (str (temp))
        f.close ()
    except IOError:
        if my_fire.debug_level >= 2:
            print ("Cant open file")
    		

def set_desired_temp (key_press):
    set_desired_temp_led (key_press)
    write_desired_temp_to_file (key_press)

def set_measured_temp (temp):
    write_measured_temp_to_file (temp)

def get_measured_temp():
    return read_measured_temp_from_file()

def get_desired_temp_from_file():
    temp = 0
    try:
        f = open ('/tmp/temperature.txt','rt')
        temp = f.read ()
        f.close ()
    except IOError:
        if my_fire.debug_level >=2:
    	    print ("Cant open file")

    return temp

def get_desired_temp():
    return (get_desired_temp_from_file ())
   



def read_remote (debug_on, read_remote_evt):
    read_remote_evt.set()
    dev = InputDevice ('/dev/input/event0')
    if debug_on >= 5:
        print (dev)
    for event in dev.read_loop():
    	#
        # type should always be 1 for a keypress
        # code is the numeric value of the key that has been pressed
        # value 0 = key up, 1 = key down, 2 = key hold

        if event.type == ecodes.EV_KEY:
            if debug_on >= 5:
                print (categorize(event))
                print ( 'type: ' + str (event.type) + ' code: ' + str (event.code) + ' value ' + str (event.value))
            if event.value == 0:  # key up
                if event.code == REMOTE_KEY_RED or event.code == REMOTE_KEY_GREEN or event.code == REMOTE_KEY_YELLOW or event.code == REMOTE_KEY_BLUE:
                    set_desired_temp (event.code) 
                    time.sleep(1)



def read_temp (debug_on, read_temperature_evt):
    read_temperature_evt.set()
    while True:
        humidity, temperature = Adafruit_DHT.read(DHT_22,IN_MEASURE_TEMP_PIN )

        # Note that sometimes you won't get a reading and
        # the results will be null (because Linux can't
        # guarantee the timing of calls to read the sensor).  
        # If this happens try again!

        if humidity is not None and temperature is not None:
            if debug_on > 5:
                print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity)
                set_measured_temp (temperature)
        else:
            if debug_on > 5:
                print 'Failed to get reading. Try again!'
        time.sleep(2)

#---------------------------------------------------------------------------------


init_GPIO ()

my_fire = Fire ()
 
my_fire.debug_level_set(2)

my_fire.print_debug_state ()

# Create the event objects that will be used to signal startup
read_temperature_evt = Event()
read_remote_evt = Event()

# Launch the threads and pass the events
if my_fire.debug_level >=5:
    print('Launching read_remote')
t = Thread(target=read_remote, args=(my_fire.debug_level,read_remote_evt))
t.start()

if my_fire.debug_level >=5:
    print('Launching read_temperature')
t = Thread(target=read_temp, args=(my_fire.debug_level,read_temperature_evt))
t.start()



# Wait for the threads to start
read_remote_evt.wait()
read_temperature_evt.wait()

# Infinite loop waiting for input from the flirc
while True:

    temp = get_desired_temp ()
    my_fire.desired_temp_set  (int(temp))
  
    if my_fire.debug_level >= 2:
        print ('Desired: ' + str (my_fire.desired_temp_get()))
	 
    
    temp = get_measured_temp ()
    my_fire.measured_temp_set (temp)

    if my_fire.debug_level >= 2:
        print ('Measured: ' + str (my_fire.measured_temp_get()))

  
    control_temperature (my_fire.desired_temp_get(),my_fire.measured_temp_get()) 

    time.sleep(2)
    
