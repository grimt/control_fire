# modules to read from the flirc
from evdev import InputDevice, categorize, ecodes
from threading import Thread, Event
import sys
import time


# Next: Move the code that reads the keys to a separate file. Put the desired temperature in this file. Maybe 0 = fire off.
#     : Leave this file for reading the temperature and maybe responding to web access - or mayb this will also be in a separate file.
#     : Define the Red, Gren, Yellow and Blue keys on Flirc so we can set temperatures.

ON = True
OFF = False

# Key definitions
STOP = 45
REMOTE_KEY_RED = 2
REMOTE_KEY_GREEN = 3
REMOTE_KEY_YELLOW = 4
REMOTE_KEY_BLUE = 5 


class Fire:

    debug = 0
    required_temperature = 0
    actual_temperature = 0

    def __init__ (self):
        self.description = "A fire to heat the home"
        self.author = "Graeme Thomson"

    def switch_debug_on (self):
        self.debug = 1

    def switch_debug_off (self):
        self.debug = 0

    def print_debug_state(self):
        if self.debug == 1:
            print ('Debug is ON')
        else:
            print ('Debug is OFF')



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

    f = open ('/tmp/temperature.txt','wt')
    f.write (str(desired_temperature))
    f.close ()


def read_remote (debug_on, started_evt ):
    started_evt.set()
    dev = InputDevice ('/dev/input/event0')
    if debug_on == 1:
        print (dev)
    for event in dev.read_loop():
    	#
        # type should always be 1 for a keypress
        # code is the numeric value of the key that has been pressed
        # value 0 = key up, 1 = key down, 2 = key hold

        if event.type == ecodes.EV_KEY:
            if debug_on == 1:
                print (categorize(event))
                print ( 'type: ' + str (event.type) + ' code: ' + str (event.code) + ' value ' + str (event.value))
            if event.value == 0:  # key up
                if event.code == REMOTE_KEY_RED or event.code == REMOTE_KEY_GREEN or event.code == REMOTE_KEY_YELLOW or event.code == REMOTE_KEY_BLUE:
                    write_temp_to_file(event.code) 
                    time.sleep(1)
                    

my_fire = Fire ()
 
my_fire.switch_debug_on ()

my_fire.print_debug_state ()

# Create the event object that will be used to signal startup
started_evt = Event()

# Launch the thread and pass the startup event
print('Launching read_remote')
t = Thread(target=read_remote, args=(my_fire.debug,started_evt))
t.start()

# Wait for the thread to start
started_evt.wait()
print('countdown is running')
# Infinite loop waiting for input from the flirc
while True:
    ticks = time.time()
    print ("Number of ticks since 12:00am, January 1, 1970:", ticks)
    time.sleep(2)
    
# Next write a task to loop, reading the file and printing the desired temperature
