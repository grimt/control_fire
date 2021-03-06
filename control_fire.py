#!/usr/bin/env python

# modules to read from the flirc
from evdev import InputDevice, categorize, ecodes
from threading import Thread, Event
from Queue import Queue
import Adafruit_DHT
import RPi.GPIO as GPIO

import sys
import time
import datetime 

import logging
import logging.handlers

LOG_FILENAME = '/var/log/control_fire.log'
 
# Set up a specific logger with our desired output level
my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s  %(message)s')
 
# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler( LOG_FILENAME, maxBytes=20000, backupCount=5)  
handler.setFormatter(formatter)

my_logger.addHandler(handler)

my_logger.debug ('Start logging')
#
ON = True
OFF = False
TEMPERATURE_OFFSET = 2 # Account for temp sensor being close  to the fire

# The relay can be sticky - i.e. wont switch on if it's been off for some time.
# We keep a count of the number of seconds it has been off and toggle the
# relay when switching on if it has been off for more than 5 hours.

RELAY_TOGGLE_THRESHHOLD = 60 * 60 * 5 

DEBUG_LEVEL_0 = 0 # Debug off
DEBUG_LEVEL_1 = 1
DEBUG_LEVEL_2 = 2
DEBUG_LEVEL_6 = 6

# Key definitions
REMOTE_KEY_NONE = 0
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

#--------------------------------------- Class Definitions ----------------------------


class Fire:

    debug_level = 0
    required_temperature = 0
    measured_temperature = 0
    time_since_last_on = 0
    fire_state = OFF 

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


def toggle_on ():
    my_logger.debug ('Toggle fire ON as ' + str (my_fire.time_since_last_on) + ' seconds since last on')
    GPIO.output (OUT_RELAY_PIN, True)
    time.sleep(0.2)
    GPIO.output (OUT_RELAY_PIN, False)
    time.sleep(0.2)


def switch_fire (off_or_on):
    if off_or_on == ON:
        if my_fire.time_since_last_on > RELAY_TOGGLE_THRESHHOLD:
            toggle_on ()
        GPIO.output (OUT_RELAY_PIN, True)
        my_fire.fire_state = ON
        my_fire.time_since_last_on = 0
        update_fire_status (ON)
        if my_fire.debug_level >=1:
    	    print ("Fire is ON")
    else:
        GPIO.output (OUT_RELAY_PIN, False)
        my_fire.fire_state = OFF
        update_fire_status (OFF)
        if my_fire.debug_level >=1:
    	    print ("Fire is OFF")
 


def run_temp_hysteresis (desired, actual):
    if my_fire.debug_level >= 2:
        print ('Hysteresis: current state: ' + str (my_fire.fire_state) + ' desired: ' + str (desired) + ' actual: ' + str (actual))
    try:    
        if my_fire.fire_state == OFF:
            if float(actual) <= (desired - 1):
                switch_fire (ON)
                my_logger.debug ('Switch fire ON Desired: ' + str (desired) + ' Actual: ' + str (actual))
        else:
            if float (actual) >= (desired + 1):
                switch_fire (OFF)
                my_logger.debug ('Switch fire OFF Desired: ' + str (desired) + ' Actual: ' + str (actual))
    except ValueError:
        print ('ValueError exception: ' + str (actual))
        #my_logger.exception ('ValueError exception' + str (actual))

def control_temperature (desired, actual):
    # The first two checks are for override from the
    # red key on the remote.
    if desired == 0:
        if my_fire.fire_state == ON:
            switch_fire (OFF)
            my_logger.debug ('Switch fire OFF Desired: ' + str (desired) + ' Actual: ' + str (actual))
    elif desired == 999:
        if my_fire.fire_state == OFF:
            switch_fire (ON)
            my_logger.debug ('Switch fire ON Desired: ' + str (desired) + ' Actual: ' + str (actual))
    else:
        run_temp_hysteresis (desired, actual) 

# Right now we are passing data between threads by writing to a file.
# This may change in the future. These abstractions allow for the
# data communication  method to change.


def switch_on_desired_temp_led (key):
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

def switch_on_measured_temp_led (temp):
    # First set all the desired temp LEDs to off

    GPIO.output (OUT_MEASURED_TEMP_RED_LED, False)
    GPIO.output (OUT_MEASURED_TEMP_GREEN_LED, False)
    GPIO.output (OUT_MEASURED_TEMP_YELLOW_LED, False)
    GPIO.output (OUT_MEASURED_TEMP_BLUE_LED, False)

    if temp >= 17 and temp <19:
        GPIO.output (OUT_MEASURED_TEMP_RED_LED, True) 
    elif temp >= 19 and temp < 20:
       GPIO.output (OUT_MEASURED_TEMP_GREEN_LED, True) 
    elif temp >= 20 and temp < 21:
        GPIO.output (OUT_MEASURED_TEMP_YELLOW_LED, True)
    elif temp >= 21:
        GPIO.output (OUT_MEASURED_TEMP_BLUE_LED, True)


# Functions to move date between threads using temporary  files.
# This mechanism may change

def write_fire_status_to_file (state):
    try:
        f = open ('/tmp/fire_status.txt', 'wt')
        if state == ON:
            f.write ('ON')
        else:
            f.write ('OFF')
        f.close ()

    except IOError:
        if my_fire.debug_level >= 2:
    	    print ("Cant open file fire_status.txt for writing")
        my_logger.exception ("Cant open file fire_status.txt for writing")



def read_desired_temp_from_file():
    temp = 0
    try:
        f = open ('/tmp/temperature.txt','rt')
        temp = f.read ()
        f.close ()
    except IOError:
        if my_fire.debug_level >=2:
            print ("Cant open file temperature.txt for reading")
        my_logger.exception("Cant open file temperature.txt for reading")

    return temp

def write_desired_temp_to_file (key):
   
    if key == REMOTE_KEY_RED:
        # The red remote button toggles the fire off/on irrespective of
        # temperature. This is represented in the file by:
        # on = 999
        # off = 0
        # To Toggle the temperature we must first read it from the file.
        desired_temperature = 0
        temp = read_desired_temp ()
        desired_temperature = int (temp)
        if desired_temperature == 0:
            desired_temperature = 999
        elif desired_temperature > 0:
            desired_temperature = 0
    
    elif key == REMOTE_KEY_GREEN:
        desired_temperature = 19
    elif key == REMOTE_KEY_YELLOW:
        desired_temperature = 20
    elif key == REMOTE_KEY_BLUE:
        desired_temperature = 21
    elif key == REMOTE_KEY_NONE:
        desired_temperature = 0

    try:
        f = open ('/tmp/temperature.txt','wt')
        f.write (str (desired_temperature))
        f.close ()
    except IOError:
        if my_fire.debug_level >= 2:
    	    print ("Cant open file temperature.txt for writing")
        my_logger.exception ("Cant open file temperature.txt for writing")

def read_measured_temp_from_file ():
    temp = my_fire.measured_temp_get() 
    try:
        f = open ('/tmp/measured_temperature.txt','rt')
        temp = f.read ()
        f.close ()
    except IOError:
        if my_fire.debug_level >=2:
    	    print ("Cant open file measured_temperature.txt for reading")
        my_logger.exception ("Cant open file measured_temperature.txt for reading")
 

    return temp


def write_measured_temp_to_file (temp):

    try:
        f = open ('/tmp/measured_temperature.txt','wt')
        f.write ('{0:0.1f}'.format(temp))
        f.close ()
    except IOError:
        if my_fire.debug_level >= 2:
            print ("Cant open file measured_temperature.txt for writing")
        my_logger.exception ("Cant open file measured_temperature.txt for writing")
		

# Higher level functions to move the temperature data between threads. Currently
# Try using queues to move the data 

def update_fire_status (state):
    write_fire_status_to_file (state)

def update_desired_temp (key_press):
    switch_on_desired_temp_led (key_press)
    write_desired_temp_to_file (key_press)
    # remote_read_q.put(key_press)

def update_measured_temp (temp):
    switch_on_measured_temp_led (temp)
    write_measured_temp_to_file (temp)

def read_measured_temp():
    return read_measured_temp_from_file()

def read_desired_temp():
    return (read_desired_temp_from_file ())
    #return (read_remote_q.get())

def read_remote (debug_on):

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
                    update_desired_temp (event.code) 
                    time.sleep(1)



def read_temp (debug_on):
    # Read the temperature from the DHT22 temperature sensor.
    
    while True:
        humidity, temperature = Adafruit_DHT.read(DHT_22,IN_MEASURE_TEMP_PIN )

        # Note that sometimes you won't get a reading and
        # the results will be null (because Linux can't
        # guarantee the timing of calls to read the sensor).  
        # If this happens try again!

        if humidity is not None and temperature is not None:
            if debug_on > 5:
                print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity)
            #my_logger.info ('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
            temperature = temperature - TEMPERATURE_OFFSET
            update_measured_temp (temperature)
            time.sleep(10)
        else:
            if debug_on > 5:
                print 'Failed to get reading. Try again!'
            #my_logger.info('Failed to read temp')
            time.sleep(2)

def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end
        
def check_time (debug_on):
	# The fire should be switched off unless it is between 4pm and 10pm
	# This task will check the time at half hour intervals and switch the
	# fire off unless the time is within the range specified above.
	# Note the fire can be switched on again by the remote but it will
	# be switched off again in the next half hour
	
	while True:
            if my_fire.fire_state == ON: 
	        localtime = datetime.datetime.time(datetime.datetime.now())
	        start = datetime.time(16, 0, 0) # 4pm
	        end = datetime.time(22, 0, 0) # 10pm
	
	        if not (time_in_range (start, end, localtime)):
	            # switch the fire off
                    my_logger.debug ('Switch fire OFF as outside time range, at: ' + str (localtime))
                    if my_fire.debug_level >= 2:
                        print('Switch fire OFF as outside time range at: ' + str(localtime))
		    update_desired_temp (REMOTE_KEY_NONE)
		    switch_fire(OFF)	
	
            time.sleep (60 * 15) # check again in 15 minutes
	
#---------------------------------------------------------------------------------

# Main thread:

# Init the hardware
init_GPIO ()

# Instantiate the main class
my_fire = Fire ()

update_desired_temp (REMOTE_KEY_NONE)
switch_fire(OFF)
my_logger.debug ('Switch fire OFF Initial condition ')
# Set the debug level
my_fire.debug_level_set(DEBUG_LEVEL_2)

my_fire.print_debug_state ()

# Create and lanch the threads

# read_remote_q = Queue()

if my_fire.debug_level >=5:
    print('Launching read_remote')

t1 = Thread(target=read_remote, args=(my_fire.debug_level,))
t1.daemon = True

t1.start()

if my_fire.debug_level >=5:
    print('Launching read_temperature')

t2 = Thread(target=read_temp, args=(my_fire.debug_level,))
t2.daemon = True

t2.start()

if my_fire.debug_level >=5:
    print('Check time')
    
t3 = Thread(target=check_time, args=(my_fire.debug_level,))
t3.daemon = True

t3.start()


# Infinite loop reading data from the other threads and running the
# control algorithm.
try:
    while True:

        temp = read_desired_temp ()
        my_fire.desired_temp_set  (int(temp))
  
        if my_fire.debug_level >= 2:
             print ('Desired: ' + str (my_fire.desired_temp_get()))
	 
    
        temp = read_measured_temp ()
        my_fire.measured_temp_set (temp)

        if my_fire.debug_level >= 2:
            print ('Measured: ' + str (my_fire.measured_temp_get()))
            print ('State: ' + str(my_fire.fire_state))
  
        control_temperature (my_fire.desired_temp_get(), my_fire.measured_temp_get()) 

        if my_fire.fire_state == OFF:
            my_fire.time_since_last_on += 1

        time.sleep(1)
# TODO - make this exception more specific
except KeyboardInterrupt:
    # switch off all LEDs
    update_desired_temp(REMOTE_KEY_NONE)
    switch_on_measured_temp_led(0)
    switch_fire(OFF)
    my_logger.debug ('Switch fire OFF Program Terminates')
    print ('DONE!!!')
