# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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
#

# Standard Library Imports
import logging
from functools import reduce
import datetime

# Third Party Imports
import numpy as np
import tkinter as tk

# Local Imports
from aslm.controller.sub_controllers.widget_functions import validate_wrapper
from aslm.controller.sub_controllers.gui_controller import GUIController
from aslm.controller.sub_controllers.channel_setting_controller import (
    ChannelSettingController,
)
from aslm.controller.sub_controllers.tiling_wizard_controller import (
    TilingWizardController,
)

# View Imports that are not called on startup
from aslm.view.popups.tiling_wizard_popup import TilingWizardPopup

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ChannelsTabController(GUIController):
    """Controller for the channels tab in the main window

    Parameters
    ----------
    view : aslm.view.main_window_content.channels_tab.ChannelsTab
        The view for the channels tab
    parent_controller : aslm.controller.main_window_controller.MainWindowController
        The parent controller for the channels tab

    Attributes
    ----------
    view : aslm.view.main_window_content.channels_tab.ChannelsTab
        The view for the channels tab
    parent_controller : aslm.controller.main_window_controller.MainWindowController
        The parent controller for the channels tab
    is_save : bool
        Whether or not the current experiment is saved
    mode : str
        The current mode of the experiment
    in_initialization : bool
        Whether or not the controller is in initialization
    ...
    """

    def __init__(self, view, parent_controller=None):
        super().__init__(view, parent_controller)

        self.is_save = False
        self.mode = "stop"
        self.in_initialization = True

        # sub-controllers
        self.channel_setting_controller = ChannelSettingController(
            self.view.channel_widgets_frame,
            self,
            self.parent_controller.configuration_controller,
        )

        # add validation functions to spinbox
        # this function validate user's input (not from experiment file)
        # and will stop propagating errors to any 'parent' functions
        # the only thing is that when the user's input is smaller than the limits,
        # it will show inputs in red, but still let the function know the inputs changed
        # I can not block it since the Tkinter's working strategy

        validate_wrapper(self.view.stack_timepoint_frame.stack_pause_spinbox)
        validate_wrapper(
            self.view.stack_timepoint_frame.exp_time_spinbox, is_integer=True
        )

        # Get Widgets and Buttons from stack_acquisition_settings in view
        self.stack_acq_widgets = self.view.stack_acq_frame.get_widgets()
        self.stack_acq_vals = self.view.stack_acq_frame.get_variables()
        self.stack_acq_buttons = self.view.stack_acq_frame.get_buttons()

        # stack acquisition event binds
        self.stack_acq_vals["step_size"].trace_add("write", self.update_z_steps)
        self.stack_acq_vals["start_position"].trace_add("write", self.update_z_steps)
        self.stack_acq_vals["end_position"].trace_add("write", self.update_z_steps)
        self.stack_acq_vals["start_focus"].trace_add("write", self.update_z_steps) # TODO: could be remove later
        self.stack_acq_buttons["set_start"].configure(
            command=self.update_start_position
        )
        self.stack_acq_buttons["set_end"].configure(command=self.update_end_position)

        # stack acquisition_variables
        self.z_origin = 0
        self.focus_origin = 0
        self.stage_velocity = None
        self.filter_wheel_delay = None
        self.microscope_state_dict = None

        # laser/stack cycling event binds
        self.stack_acq_vals["cycling"].trace_add("write", self.update_cycling_setting)

        # time point setting variables
        self.timepoint_vals = {
            "is_save": self.view.stack_timepoint_frame.save_data,
            "timepoints": self.view.stack_timepoint_frame.exp_time_spinval,
            "stack_acq_time": self.view.stack_timepoint_frame.stack_acq_spinval,
            "stack_pause": self.view.stack_timepoint_frame.stack_pause_spinval,
            "experiment_duration": self.view.stack_timepoint_frame.total_time_spinval,
        }
        self.timepoint_vals[
            "timepoint_interval"
        ] = self.view.stack_timepoint_frame.timepoint_interval_spinval

        # timepoint event binds
        self.timepoint_vals["is_save"].trace_add("write", self.update_save_setting)
        self.timepoint_vals["timepoints"].trace_add(
            "write", lambda *args: self.update_timepoint_setting(True)
        )
        self.timepoint_vals["stack_pause"].trace_add(
            "write", lambda *args: self.update_timepoint_setting(True)
        )

        # multiposition
        self.is_multiposition = False
        self.is_multiposition_val = self.view.multipoint_frame.on_off
        self.view.multipoint_frame.save_check.configure(
            command=self.toggle_multiposition
        )
        self.view.quick_launch.buttons["tiling"].configure(
            command=self.launch_tiling_wizard
        )

        # Get Widgets from confocal_projection_settings in view
        self.conpro_acq_widgets = self.view.conpro_acq_frame.get_widgets()
        self.conpro_acq_vals = self.view.conpro_acq_frame.get_variables()

        # laser/stack cycling event binds
        self.conpro_acq_vals["cycling"].trace_add("write", self.update_cycling_setting)

        # confocal-projection event binds
        self.conpro_acq_vals["scanrange"].trace_add("write", self.update_scanrange)
        self.conpro_acq_vals["n_plane"].trace_add("write", self.update_plane_number)
        self.conpro_acq_vals["offset_start"].trace_add(
            "write", self.update_offset_start
        )
        self.conpro_acq_vals["offset_end"].trace_add("write", self.update_offset_end)

        # confocal-projection setting variables

        self.initialize()

    def update_offset_start(self, *args):
        """Update offset start value in the controller

        Parameters
        ----------
        *args
            Not used

        Returns
        -------
        None

        Examples
        --------
        >>> self.update_offset_start()
        """
        try:
            offset_start = float(self.conpro_acq_vals["offset_start"].get())
        except tk._tkinter.TclError:
            offset_start = 0
        self.microscope_state_dict["offset_start"] = offset_start
        logger.info(f"Controller updated offset start: {offset_start}")

    def update_offset_end(self, *args):
        """Update offset end value in the controller

        Parameters
        ----------
        *args
            Not used

        Returns
        -------
        None

        Examples
        --------
        >>> self.update_offset_end()
        """
        try:
            offset_end = float(self.conpro_acq_vals["offset_end"].get())
        except tk._tkinter.TclError:
            offset_end = 0
        self.microscope_state_dict["offset_end"] = offset_end
        logger.info(f"Controller updated offset end: {offset_end}")

    def update_plane_number(self, *args):
        """Update plane number value in the controller

        Parameters
        ----------
        *args
            Not used

        Returns
        -------
        None

        Examples
        --------
        >>> self.update_plane_number()
        """
        try:
            n_plane = float(self.conpro_acq_vals["n_plane"].get())
        except tk._tkinter.TclError:
            n_plane = 1
        self.microscope_state_dict["n_plane"] = n_plane
        logger.info(f"Controller updated plane number: {n_plane}")

    def update_scanrange(self, *args):
        """Update scan range value in the controller

        Parameters
        ----------
        *args
            Not used

        Returns
        -------
        None

        Examples
        --------
        >>> self.update_scanrange()
        """
        try:
            scanrange = float(self.conpro_acq_vals["scanrange"].get())
        except tk._tkinter.TclError:
            scanrange = 0
        self.microscope_state_dict["scanrange"] = scanrange
        logger.info(f"Controller updated scan range: {scanrange}")

    def initialize(self):
        """Initializes widgets and gets other necessary configuration

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> self.initialize()
        """
        config = self.parent_controller.configuration_controller

        self.stack_acq_widgets["cycling"].widget["values"] = ["Per Z", "Per Stack"]
        self.conpro_acq_widgets["cycling"].widget["values"] = ["Per Plane", "Per Stack"]
        self.stage_velocity = config.stage_setting_dict["velocity"]
        self.filter_wheel_delay = config.filter_wheel_setting_dict["filter_wheel_delay"]
        self.channel_setting_controller.initialize()
        self.set_spinbox_range_limits(config.configuration["configuration"]["gui"])
        self.show_verbose_info("channels tab has been initialized")

    def populate_experiment_values(self):
        """Distribute initial MicroscopeState values to this and sub-controllers and
        associated views.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> self.populate_experiment_values()
        """
        self.in_initialization = True
        self.microscope_state_dict = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]
        if self.microscope_state_dict["step_size"] < 0:
            self.microscope_state_dict["step_size"] = -self.microscope_state_dict["step_size"]
        self.set_info(self.stack_acq_vals, self.microscope_state_dict)
        self.set_info(self.conpro_acq_vals, self.microscope_state_dict)
        self.set_info(self.timepoint_vals, self.microscope_state_dict)

        # check configuration for multiposition settings
        self.is_multiposition_val.set(self.microscope_state_dict["is_multiposition"])
        self.toggle_multiposition()

        # validate
        self.view.stack_timepoint_frame.stack_pause_spinbox.validate()
        self.view.stack_timepoint_frame.exp_time_spinbox.validate()

        self.stack_acq_vals["cycling"].set(
            "Per Z"
            if self.microscope_state_dict["stack_cycling_mode"] == "per_z"
            else "Per Stack"
        )
        self.conpro_acq_vals["cycling"].set(
            "Per Plane"
            if self.microscope_state_dict["conpro_cycling_mode"] == "per_plane"
            else "Per Stack"
        )
        self.channel_setting_controller.populate_experiment_values(
            self.microscope_state_dict["channels"]
        )

        # after initialization
        self.in_initialization = False
        self.channel_setting_controller.in_initialization = False
        self.update_z_steps()

        self.show_verbose_info("Channels tab has been set new values")

    def set_spinbox_range_limits(self, settings):
        """This function will set the spinbox widget's values of from_, to, step

        Parameters
        ----------
        settings : dict
            dictionary of settings from configuration file

        Returns
        -------
        None

        Examples
        --------
        >>> self.set_spinbox_range_limits(settings)
        """
        temp_dict = {
            self.stack_acq_widgets["step_size"]: settings["stack_acquisition"][
                "step_size"
            ],
            self.stack_acq_widgets["start_position"]: settings["stack_acquisition"][
                "start_pos"
            ],
            self.stack_acq_widgets["end_position"]: settings["stack_acquisition"][
                "end_pos"
            ],
            self.view.stack_timepoint_frame.stack_pause_spinbox: settings["timepoint"][
                "stack_pause"
            ],
            self.view.stack_timepoint_frame.exp_time_spinbox: settings["timepoint"][
                "timepoints"
            ],
        }
        for idx, widget in enumerate(temp_dict):
            # Hacky Solution until stack time points are converted to LabelInput
            if idx < 3:
                widget.widget.configure(from_=temp_dict[widget]["min"])
                widget.widget.configure(to=temp_dict[widget]["max"])
                widget.widget.configure(increment=temp_dict[widget]["step"])
            else:
                widget.configure(from_=temp_dict[widget]["min"])
                widget.configure(to=temp_dict[widget]["max"])
                widget.configure(increment=temp_dict[widget]["step"])

        # channels setting
        self.channel_setting_controller.set_spinbox_range_limits(settings["channels"])

    def set_mode(self, mode):
        """Change acquisition mode.

        Parameters
        ----------
        mode : str
            acquisition mode

        Returns
        -------
        None

        Examples
        --------
        >>> self.set_mode(mode)
        """
        self.mode = mode
        self.channel_setting_controller.set_mode(mode)

        state = "normal" if mode == "stop" else "disabled"
        for key, widget in self.stack_acq_widgets.items():
            widget.widget["state"] = state
        self.view.stack_timepoint_frame.save_check["state"] = state
        self.view.stack_timepoint_frame.stack_pause_spinbox["state"] = state
        self.view.stack_timepoint_frame.exp_time_spinbox["state"] = state
        self.show_verbose_info("acquisition mode has been changed to", mode)

    def update_z_steps(self, *args):
        """Recalculates the number of slices that will be acquired in a z-stack.

        Requires GUI to have start position, end position, or step size changed.
        Sets the number of slices in the model and the GUI.
        Sends the current values to central/parent controller

        Parameters
        ----------
        args : dict
            Values is a dict as follows {'step_size':  'start_position': ,
                                         'end_position': ,'number_z_steps'}

        Returns
        -------
        None

        Examples
        --------
        >>> self.update_z_steps()
        """

        # won't do any calculation when initialization
        if self.in_initialization:
            return

        # Calculate the number of slices and set GUI
        try:
            # validate the spinbox's value
            start_position = float(self.stack_acq_vals["start_position"].get())
            end_position = float(self.stack_acq_vals["end_position"].get())
            step_size = float(self.stack_acq_vals["step_size"].get())
            if step_size < 0.001:
                self.stack_acq_vals["number_z_steps"].set(0)
                self.stack_acq_vals["abs_z_start"].set(0)
                self.stack_acq_vals["abs_z_end"].set(0)
                return
        except tk._tkinter.TclError:
            self.stack_acq_vals["number_z_steps"].set(0)
            self.stack_acq_vals["abs_z_start"].set(0)
            self.stack_acq_vals["abs_z_end"].set(0)
            return
        except (KeyError, AttributeError):
            logger.error("Error caught: updating z_steps")
            return

        # if step_size < 0.001:
        #     step_size = 0.001
        #     self.stack_acq_vals['step_size'].set(step_size)

        number_z_steps = int(
            np.ceil(np.abs((end_position - start_position) / step_size))
        )
        self.stack_acq_vals["number_z_steps"].set(number_z_steps)

        # Shift the start/stop positions by the relative position
        flip_flags = self.parent_controller.configuration_controller.stage_flip_flags
        if flip_flags["z"]:
            self.stack_acq_vals["abs_z_start"].set(self.z_origin + end_position)
            self.stack_acq_vals["abs_z_end"].set(self.z_origin + start_position)
        else:
            self.stack_acq_vals["abs_z_start"].set(self.z_origin + start_position)
            self.stack_acq_vals["abs_z_end"].set(self.z_origin + end_position)

        # update experiment MicroscopeState dict
        self.microscope_state_dict["start_position"] = start_position
        self.microscope_state_dict["end_position"] = end_position
        self.microscope_state_dict["step_size"] = step_size * (-1 if flip_flags["z"] else 1)
        self.microscope_state_dict["number_z_steps"] = number_z_steps
        self.microscope_state_dict["abs_z_start"] = self.stack_acq_vals[
            "abs_z_start"
        ].get()
        self.microscope_state_dict["abs_z_end"] = self.stack_acq_vals["abs_z_end"].get()
        try:
            self.microscope_state_dict["start_focus"] = self.stack_acq_vals[
                "start_focus"
            ].get()
        except:
            self.microscope_state_dict["start_focus"] = 0
        self.microscope_state_dict["end_focus"] = self.stack_acq_vals["end_focus"].get()
        self.microscope_state_dict["stack_z_origin"] = self.z_origin
        self.microscope_state_dict["stack_focus_origin"] = self.focus_origin

        self.update_timepoint_setting()
        self.show_verbose_info(
            "stack acquisition settings on channels tab have been changed and "
            "recalculated"
        )

    def update_start_position(self, *args):
        """Get new z starting position from current stage parameters.

        Parameters
        ----------
        args : dict
            Values is a dict as follows {'start_position': , 'abs_z_start': ,
            'stack_z_origin': }

        Returns
        -------
        None

        Examples
        --------
        >>> self.update_start_position()
        """

        # We have a new origin
        self.z_origin = self.parent_controller.configuration["experiment"][
            "StageParameters"
        ]["z"]
        self.focus_origin = self.parent_controller.configuration["experiment"][
            "StageParameters"
        ]["f"]

        flip_flags = self.parent_controller.configuration_controller.stage_flip_flags
        if flip_flags["z"]:
            self.stack_acq_vals["end_position"].set(0)
            self.stack_acq_vals["end_focus"].set(0)
        else:
            self.stack_acq_vals["start_position"].set(0)
            self.stack_acq_vals["start_focus"].set(0)

        # Propagate parameter changes to the GUI
        self.update_z_steps()

    def update_end_position(self, *args):
        """Get new z ending position from current stage parameters

        Parameters
        ----------
        args : dict
            Values is a dict as follows {'end_position': , 'abs_z_end': ,
            'stack_z_origin': }

        Returns
        -------
        None

        Examples
        --------
        >>> self.update_end_position()
        """
        # Grab current values
        z_end = self.parent_controller.configuration["experiment"]["StageParameters"][
            "z"
        ]
        focus_end = self.parent_controller.configuration["experiment"][
            "StageParameters"
        ]["f"]

        z_start = self.z_origin
        focus_start = self.focus_origin

        if z_end < z_start:
            # Sort so we are always going low to high
            z_start, z_end = z_end, z_start
            focus_start, focus_end = focus_end, focus_start

        # set origin to be in the middle of start and end
        self.z_origin = (z_start + z_end) / 2
        self.focus_origin = (focus_start + focus_end) / 2

        # Propagate parameter changes to the GUI
        flip_flags = self.parent_controller.configuration_controller.stage_flip_flags
        start_pos = z_start - self.z_origin
        end_pos = z_end - self.z_origin
        start_focus = focus_start - self.focus_origin
        end_focus = focus_end - self.focus_origin
        if flip_flags["z"]:
            start_pos, end_pos = end_pos, start_pos
            start_focus, end_focus = end_focus, start_focus
        self.stack_acq_vals["start_position"].set(start_pos)
        self.stack_acq_vals["start_focus"].set(start_focus)
        self.stack_acq_vals["end_position"].set(end_pos)
        self.stack_acq_vals["end_focus"].set(end_focus)
        self.update_z_steps()

    def update_cycling_setting(self, *args):
        """Update the cycling settings in the model and the GUI.

        You can collect different channels in different formats.
        In the perZ format: Slice 0/Ch0, Slice0/Ch1, Slice1/Ch0, Slice1/Ch1, etc
        in the perStack format: Slice 0/Ch0, Slice1/Ch0... SliceN/Ch0.  Then it repeats
        with Ch1

        Parameters
        ----------
        args : dict
            Values is a dict as follows {'cycling_setting': , 'cycling_setting': ,
                                         'stack_z_origin': }

        Returns
        -------
        None

        Examples
        --------
        >>> self.update_cycling_setting()
        """
        # won't do any calculation when initializing
        if self.in_initialization:
            return
        # update experiment MicroscopeState dict
        self.microscope_state_dict["stack_cycling_mode"] = (
            "per_stack"
            if self.stack_acq_vals["cycling"].get() == "Per Stack"
            else "per_z"
        )
        self.microscope_state_dict["conpro_cycling_mode"] = (
            "per_stack"
            if self.conpro_acq_vals["cycling"].get() == "Per Stack"
            else "per_plane"
        )

        # recalculate time point settings
        self.update_timepoint_setting()

        self.show_verbose_info("Cycling setting on channels tab has been changed")

    def update_save_setting(self, *args):
        """Tell the centrol/parent controller 'save_data' is selected.

        Does not do any calculation when initializing the software.

        Parameters
        ----------
        args : dict
            Values is a dict as follows {'save_data': , 'save_data': ,
                                         'stack_z_origin': }

        Returns
        -------
        None

        Examples
        --------
        >>> self.update_save_setting()
        """

        if self.in_initialization:
            return
        self.is_save = self.timepoint_vals["is_save"].get()
        # update experiment MicroscopeState dict
        self.microscope_state_dict["is_save"] = self.is_save
        self.parent_controller.execute("set_save", self.is_save)
        self.show_verbose_info("Save data option has been changed to", self.is_save)

    def update_timepoint_setting(self, call_parent=False):
        """Automatically calculates the stack acquisition time based on the number of
        time points, channels, and exposure time.

        TODO: Add necessary computation for 'Stack Acq.Time', 'Timepoint Interval',
        'Experiment Duration'?

        Does not do any calculation when initializing the software.
        Order of priority for perStack: timepoints > positions > channels > z-steps
                                        > delay
        ORder of priority for perZ: timepoints > positions > z-steps > delays > channels

        Parameters
        ----------
        call_parent : bool
            Tell parent controller that time point setting has changed.

        Returns
        -------
        None

        Examples
        --------
        >>> self.update_timepoint_setting()
        """

        if self.in_initialization:
            return
        channel_settings = self.microscope_state_dict["channels"]
        number_of_positions = (
            self.parent_controller.multiposition_tab_controller.get_position_num()
            if self.is_multiposition
            else 1
        )
        channel_exposure_time = []
        # validate the spinbox's value
        try:
            number_of_timepoints = int(float(self.timepoint_vals["timepoints"].get()))
            number_of_slices = int(self.stack_acq_vals["number_z_steps"].get())
            for channel_id in channel_settings.keys():
                channel = channel_settings[channel_id]
                if channel["is_selected"]:
                    channel_exposure_time.append(float(channel["camera_exposure_time"]))
            if len(channel_exposure_time) == 0:
                return
        except (tk._tkinter.TclError, ValueError):
            self.timepoint_vals["experiment_duration"].set("0")
            self.timepoint_vals["stack_acq_time"].set("0")
            return
        except (KeyError, AttributeError):
            logger.error("Error caught: updating timepoint setting")
            return

        perStack = self.stack_acq_vals["cycling"].get() == "Per Stack"

        # Initialize variable to keep track of how long the entire experiment will take.
        # Includes time, positions, channels...
        experiment_duration = 0

        # Initialize variable to calculate how long it takes to acquire a single volume
        # for all of the channels. Only calculate once at the beginning.
        stack_acquisition_duration = 0

        for position_idx in range(number_of_positions):
            # For multiple positions, need to account for the time necessary to move
            # the stages that distance. In theory, these positions would be
            # populated in that 'pandastable' or some other data structure.

            # Determine the largest distance to travel between positions.  Assume
            # all axes move the same velocity This assumes that we are in a
            # multi-position mode. Not yet implemented.
            # x1, y1, z1, theta1, f1, = position_start.values()
            # x2, y2, z1, theta2, f1 = position_end.values()
            # distance = [x2-x1, y2-y1, z2-z1, theta2-theta1, f2-f1]
            # max_distance_idx = np.argmax(distance)
            # Now if we are going to do this properly, we would need to do this for
            # all of the positions so that we can calculate the total experiment
            # time. Probably assemble a matrix of all the positions and then do
            # the calculations.

            stage_delay = 0  # distance[max_distance_idx]/self.stage_velocity
            # TODO False value.

            # If we were actually acquiring the data, we would call the function to
            # move the stage here.
            experiment_duration = experiment_duration + stage_delay

            for channel_idx in range(len(channel_exposure_time)):
                if perStack:
                    # In the perStack mode, we only need to account for the time
                    # necessary for the filter wheel to change between each
                    # image stack.
                    if channel_idx == 0 and position_idx == 0:
                        stack_acquisition_duration += (
                            channel_exposure_time[channel_idx] / 1000 * number_of_slices
                        )
                else:
                    if position_idx == 0:
                        stack_acquisition_duration += (
                            channel_exposure_time[channel_idx] / 1000 * number_of_slices
                        )

                experiment_duration += (
                    channel_exposure_time[channel_idx] / 1000 * number_of_slices
                )

            try:
                stack_pause = float(self.timepoint_vals["stack_pause"].get())
            except ValueError:
                stack_pause = 0
            experiment_duration = experiment_duration + stack_pause
        experiment_duration *= number_of_timepoints

        # Change the filter wheel here before the start of the acquisition.
        if len(channel_exposure_time) > 1:
            filter_wheel_change_times = number_of_timepoints * (
                1 if perStack else number_of_slices
            )
            experiment_duration += self.filter_wheel_delay * filter_wheel_change_times
        else:
            experiment_duration += self.filter_wheel_delay
        self.timepoint_vals["experiment_duration"].set(
            str(datetime.timedelta(seconds=experiment_duration))
        )
        self.timepoint_vals["stack_acq_time"].set(
            str(datetime.timedelta(seconds=stack_acquisition_duration))
        )

        # update experiment MicroscopeState dict
        self.microscope_state_dict["timepoints"] = number_of_timepoints
        self.microscope_state_dict["stack_pause"] = self.timepoint_vals[
            "stack_pause"
        ].get()
        # self.microscope_state_dict['timepoint_interval']
        self.microscope_state_dict["stack_acq_time"] = stack_acquisition_duration
        self.microscope_state_dict["experiment_duration"] = experiment_duration

        self.show_verbose_info(
            "timepoint settings on channels tab have been changed and recalculated"
        )

    def toggle_multiposition(self):
        """Toggle Multi-position Acquisition.

        Recalculates the experiment duration.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> self.toggle_multiposition()
        """
        self.is_multiposition = self.is_multiposition_val.get()
        self.microscope_state_dict["is_multiposition"] = self.is_multiposition
        self.update_timepoint_setting()
        self.show_verbose_info("Multi-position:", self.is_multiposition)

    def launch_tiling_wizard(self):
        """Launches tiling wizard popup.

        Will only launch when button in GUI is pressed, and will not duplicate.
        Pressing button again brings popup to top

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> self.launch_tiling_wizard()
        """

        if hasattr(self, "tiling_wizard_controller"):
            self.tiling_wizard_controller.showup()
            return
        tiling_wizard = TilingWizardPopup(self.view)
        self.tiling_wizard_controller = TilingWizardController(tiling_wizard, self)

    def set_info(self, vals, values):
        """Set values to a list of variables.

        Parameters
        ----------
        vals : list
            List of variables to set.
        values : list
            List of values to set to variables.

        Returns
        -------
        None

        Examples
        --------
        >>> self.set_info([self.timepoint_vals['timepoint_interval'],
                           self.timepoint_vals['stack_pause']], [1, 1])
        """
        for name in values.keys():
            if name in vals:
                vals[name].set(values[name])

    def execute(self, command, *args):
        """Execute Command in the parent controller.

        Parameters
        ----------
        command : str
            recalculate_timepoint, channel, move_stage_and_update_info,
            get_stage_position
        args : list
            List of arguments to pass to the command.

        Returns
        -------
        command : object
            Returns parent_controller.execute(command) if command = 'get_stage_position'

        Examples
        --------
        >>> self.execute('recalculate_timepoint')
        """
        if command == "recalculate_timepoint":
            # update selected channels num
            self.microscope_state_dict["selected_channels"] = reduce(
                lambda count, channel: count + (channel["is_selected"] is True),
                self.microscope_state_dict["channels"].values(),
                0,
            )
            self.update_timepoint_setting()
            # update framerate info in camera setting tab
            exposure_time = max(
                map(
                    lambda channel: float(channel["camera_exposure_time"])
                    if channel["is_selected"]
                    else 0,
                    self.microscope_state_dict["channels"].values(),
                )
            )
            self.parent_controller.camera_setting_controller.update_exposure_time(
                exposure_time
            )
        elif (command == "channel") or (command == "update_setting"):
            self.view.after(
                1000, lambda: self.parent_controller.execute(command, *args)
            )

        self.show_verbose_info("Received command from child", command, args)
