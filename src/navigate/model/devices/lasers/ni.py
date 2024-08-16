# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard Library Imports
import logging

# Third Party Imports
import nidaqmx
from nidaqmx.errors import DaqError
from nidaqmx.constants import LineGrouping

# Local Imports
from navigate.model.devices.lasers.base import LaserBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class LaserNI(LaserBase):
    """LaserNI Class

    This class is used to control a laser connected to a National Instruments DAQ.
    """

    def __init__(self, microscope_name, device_connection, configuration, laser_id):
        """Initialize the LaserNI class.

        Parameters
        ----------
        microscope_name : str
            The microscope name.
        device_connection : object
            The device connection object.
        configuration : dict
            The device configuration.
        laser_id : str
            The laser id.
        """
        super().__init__(microscope_name, device_connection, configuration, laser_id)

        #: str: Modulation type of the laser - Analog or Digital.
        self.on_off_type = None

        # Digital out (if using mixed modulation mode)
        try:
            laser_do_port = self.device_config["onoff"]["hardware"]["channel"]

            #: float: The minimum digital modulation voltage.
            self.laser_min_do = self.device_config["onoff"]["hardware"]["min"]

            #: float: The maximum digital modulation voltage.
            self.laser_max_do = self.device_config["onoff"]["hardware"]["max"]

            #: object: The laser analog or digital modulation task.
            self.laser_do_task = nidaqmx.Task()

            if "/ao" in laser_do_port:
                # Artificial Digital Modulation via an Analog Port
                self.laser_do_task.ao_channels.add_ao_voltage_chan(
                    laser_do_port, min_val=self.laser_min_do, max_val=self.laser_max_do
                )
                self.on_off_type = "analog"

            else:
                # Digital Modulation via a Digital Port
                self.laser_do_task.do_channels.add_do_chan(
                    laser_do_port, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES
                )
                self.on_off_type = "digital"
        except (KeyError, DaqError) as e:
            self.laser_do_task = None
            if isinstance(e, DaqError):
                logger.exception(e)
                logger.debug(e.error_code)
                logger.debug(e.error_type)
                print(e)
                print(e.error_code)
                print(e.error_type)

        #: float: Current laser intensity.
        self._current_intensity = 0

        # Analog out
        try:
            laser_ao_port = self.device_config["power"]["hardware"]["channel"]

            #: float: The minimum analog modulation voltage.
            self.laser_min_ao = self.device_config["power"]["hardware"]["min"]

            #: float: The maximum analog modulation voltage.
            self.laser_max_ao = self.device_config["power"]["hardware"]["max"]

            #: object: The laser analog modulation task.
            self.laser_ao_task = nidaqmx.Task()
            self.laser_ao_task.ao_channels.add_ao_voltage_chan(
                laser_ao_port, min_val=self.laser_min_ao, max_val=self.laser_max_ao
            )
        except DaqError as e:
            logger.exception(e)
            logger.debug(e.error_code)
            logger.debug(e.error_type)
            print(e)
            print(e.error_code)
            print(e.error_type)

    def set_power(self, laser_intensity):
        """Sets the laser power.

        Parameters
        ----------
        laser_intensity : float
            The laser intensity.
        """
        try:
            scaled_laser_voltage = (int(laser_intensity) / 100) * self.laser_max_ao
            self.laser_ao_task.write(scaled_laser_voltage, auto_start=True)
            self._current_intensity = laser_intensity
        except DaqError as e:
            logger.exception(e)

    def turn_on(self):
        """Turns on the laser."""
        try:
            self.set_power(self._current_intensity)
            if self.laser_do_task is not None:
                if self.on_off_type == "digital":
                    self.laser_do_task.write(True, auto_start=True)
                elif self.on_off_type == "analog":
                    self.laser_do_task.write(self.laser_max_do, auto_start=True)
        except DaqError as e:
            logger.exception(e)

    def turn_off(self):
        """Turns off the laser."""
        try:
            tmp = self._current_intensity
            self.set_power(0)
            self._current_intensity = tmp
            if self.laser_do_task is not None:
                if self.on_off_type == "digital":
                    self.laser_do_task.write(False, auto_start=True)
                elif self.on_off_type == "analog":
                    self.laser_do_task.write(self.laser_min_do, auto_start=True)
        except DaqError as e:
            logger.exception(e)

    def close(self):
        """Close the NI Task before exit."""
        try:
            self.laser_ao_task.close()
        except Exception as e:
            logger.exception(e)

        try:
            self.laser_do_task.close()
        except Exception as e:
            logger.exception(e)
