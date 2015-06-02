# File to investigate rotating the logs

import logging
import logging.handlers

LOG_FILENAME = '/var/log/logging_rotatingfile_example.out'

# Set up a specific logger with our desired output level
my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s  %(message)s')

# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=20, backupCount=5)

handler.setFormatter(formatter)

my_logger.addHandler(handler)

# Log some messages
for i in range(20):
    my_logger.debug('i = %d' % i)
