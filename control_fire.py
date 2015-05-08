# modules to read from the flirc
from evdev import InputDevice, categorize, ecodes
from threading import Thread, Event
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
OUT_MEASURED_TEMP_RED = 7
OUT_MEASURED_TEMP_GREEN = 8
OUT_MEASURED_TEMP_YELLOW = 23
OUT_MEASURED_TEMP_BLUE = 24

OUT_DESIRED_TEMP_GREEN = 17
OUT_DESIRED_TEMP_YELLOW = 21
OUT_DESIRED_TEMP_BLUE = 22

OUT_RELAY = 18

IN_MEASURE_TEMP = 4

#--------------------------------------- Class Definitions ----------------------------


class Fire:

    debug_level = 0
    required_temperature = 0
    actual_temperature = 0

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


#--------------------------- End of Class Fire ----------------------



def write_temp_to_file (key):
   
    if key == REMOTE_KEY_RED:
        desired_temperature = 0
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
        f.write (str(desired_temperature))
        f.close ()
    except IOError:
        if my_fire.debug_level >=2:
    	    print ("Cant open file")
    		


def read_remote (debug_on, started_evt ):
    started_evt.set()
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
                    write_temp_to_file(event.code) 
                    time.sleep(1)
                    

#---------------------------------------------------------------------------------


my_fire = Fire ()
 
my_fire.debug_level_set(2)

my_fire.print_debug_state ()

# Create the event object that will be used to signal startup
started_evt = Event()

# Launch the thread and pass the startup event
if my_fire.debug_level >=5:
    print('Launching read_remote')
t = Thread(target=read_remote, args=(my_fire.debug_level,started_evt))
t.start()

# Wait for the thread to start
started_evt.wait()
# Infinite loop waiting for input from the flirc
while True:
    try:
        f = open ('/tmp/temperature.txt','rt')
        temp = f.read ()
        f.close ()
        my_fire.desired_temp_set  (int(temp))
    except IOError:
        if my_fire.debug_level >=2:
    	    print ("Cant open file")
    		
    if my_fire.debug_level >= 2:
    	print(str (my_fire.desired_temp_get()))
	
    time.sleep(2)
    
