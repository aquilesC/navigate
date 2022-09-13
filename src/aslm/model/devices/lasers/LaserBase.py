"""
Laser Base Class
"""
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class LaserBase:
    def __init__(self, port):
        pass

    def set_power(self, power_level):
        pass

    def turn_on(self):
        pass

    def turn_off(self):
        pass

    def close(self):
        """
        # Close the port before exit.
        """
        pass

    def initialize_laser(self):
        """
        # Initialize lasers.
        # Sets the laser to the maximum power, and sets the mode to CW-APC.
        """
        pass
