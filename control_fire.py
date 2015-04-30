# modules to read from the flirc
from evdev import InputDevice, categorize, ecodes
import time


# Next: Move the code that reads the keys to a separate file. Put the desired temperature in this file. Maybe 0 = fire off.
#     : Leave this file for reading the temperature and maybe responding to web access - or mayb this will also be in a separate file.
#     : Define the Red, Gren, Yellow and Blue keys on Flirc so we can set temperatures.

ON = True
OFF = False

# Key definitions
STOP = 45

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
            print 'Debug is ON'
        else:
            print 'Debug is OFF'

my_fire = Fire ()
 
my_fire.switch_debug_on ()

my_fire.print_debug_state ()

dev = InputDevice ('/dev/input/event0')

if my_fire.debug == 1:
  print dev
# Infinite loop waiting for input from the flirc
while True:
    ticks = time.time()
    print "Number of ticks since 12:00am, January 1, 1970:", ticks
    for event in dev.read_loop():
    	#
        # type should always be 1 for a keypress
        # code is the numeric value of the key that has been pressed
        # value 0 = key up, 1 = key down, 2 = key hold

        if event.type == ecodes.EV_KEY:
            if my_fire.debug == 1:
                print (categorize(event))
                print 'type: ' + str (event.type) + ' code: ' + str (event.code) + ' value ' + str (event.value)
	    if event.value == 0: # key up
	        break
    if event.code == STOP: # stop key on remote
        break
