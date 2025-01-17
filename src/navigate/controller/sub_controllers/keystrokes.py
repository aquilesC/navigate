# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
import platform

# Third Party Imports

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.view.custom_widgets.validation import ValidatedEntry, ValidatedSpinbox

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class KeystrokeController(GUIController):
    """Keystroke controller"""

    def __init__(self, main_view, parent_controller):
        """Initialize the keystroke controller

        Parameters
        ----------
        main_view : MainView
            Main view
        parent_controller : MainController
            Main controller
        """
        super().__init__(main_view, parent_controller)

        # References to all sub frames
        #: tk.Frame: Camera View
        self.camera_view = main_view.camera_waveform.camera_tab  # Camera View

        #: tk.Frame: MIP View
        self.mip_view = main_view.camera_waveform.mip_tab  # MIP View

        # Multiposition Table
        #: MultipositionTable: Multiposition Table
        self.multi_table = main_view.settings.multiposition_tab.multipoint_list

        # Main view
        #: tk.Frame: Main view
        self.main_view = main_view.root

        #: tk.Notebook: Main tabs
        self.main_tabs = main_view.settings

        # Controllers for all sub frames
        #: CameraViewController: Camera View Controller
        self.camera_controller = parent_controller.camera_view_controller

        #: MIPSettingController: MIP Setting Controller
        self.mip_controller = parent_controller.mip_setting_controller

        #: MultipositionTableController: Multiposition Table Controller
        self.multi_controller = parent_controller.multiposition_tab_controller

        #: StageController: Stage Controller
        self.stage_controller = parent_controller.stage_controller

        """Keystrokes for Camera & MIP View"""
        # Left Click binding
        self.camera_view.canvas.bind("<Button-1>", self.camera_controller.left_click)
        self.mip_view.canvas.bind("<Button-1>", self.mip_controller.left_click)

        # MouseWheel Binding
        self.view.root.bind("<MouseWheel>", self.view.scroll_frame.mouse_wheel)
        self.camera_view.canvas.bind(
            "<Enter>", self.camera_controller_mouse_wheel_enter
        )
        self.camera_view.canvas.bind(
            "<Leave>", self.camera_controller_mouse_wheel_leave
        )
        self.mip_view.canvas.bind("<Enter>", self.mip_controller_mouse_wheel_enter)
        self.mip_view.canvas.bind("<Leave>", self.mip_controller_mouse_wheel_leave)

        # Right Click Binding
        if platform.system() == "Darwin":
            self.camera_view.canvas.bind(
                "<Button-2>", self.camera_controller.popup_menu
            )
            self.mip_view.canvas.bind("<Button-2>", self.mip_controller.popup_menu)
        else:
            self.camera_view.canvas.bind(
                "<Button-3>", self.camera_controller.popup_menu
            )
            self.mip_view.canvas.bind("<Button-3>", self.mip_controller.popup_menu)

        """Keystrokes for MultiTable"""
        #: MultiPositionTable: Multiposition Table
        self.mp_table = self.multi_table.pt
        self.mp_table.rowheader.bind(
            "<Double-Button-1>", self.multi_controller.handle_double_click
        )

        """Keystrokes for Main Window"""
        self.main_view.bind(
            "<Control-KeyRelease-j>", self.stage_controller.joystick_button_handler
        )
        self.main_view.bind("<Control-Key-1>", self.switch_tab)
        self.main_view.bind("<Control-Key-2>", self.switch_tab)
        self.main_view.bind("<Control-Key-3>", self.switch_tab)
        self.main_view.bind("<Control-Key-4>", self.switch_tab)
        self.main_view.bind_all("<Control-Key-z>", self.widget_undo)
        self.main_view.bind_all("<Control-Key-y>", self.widget_redo)

    def camera_controller_mouse_wheel_enter(self, event):
        """Mouse wheel binding for camera view

        Parameters
        ----------
        event : tkinter event
            Mouse wheel event
        """
        self.view.root.unbind("<MouseWheel>")  # get rid of scrollbar mousewheel
        if platform.system() != "Linux":
            self.camera_view.canvas.bind(
                "<MouseWheel>", self.camera_controller.mouse_wheel
            )
        else:
            self.camera_view.canvas.bind(
                "<Button-4>", self.camera_controller.mouse_wheel
            )
            self.camera_view.canvas.bind(
                "<Button-5>", self.camera_controller.mouse_wheel
            )

    def mip_controller_mouse_wheel_enter(self, event):
        """Mouse wheel binding for MIP view

        Parameters
        ----------
        event : tkinter event
            Mouse wheel event
        """
        self.view.root.unbind("<MouseWheel>")
        if platform.system() != "Linux":
            self.mip_view.canvas.bind("<MouseWheel>", self.mip_controller.mouse_wheel)
        else:
            self.mip_view.canvas.bind("<Button-4>", self.mip_controller.mouse_wheel)
            self.mip_view.canvas.bind("<Button-5>", self.mip_controller.mouse_wheel)

    def camera_controller_mouse_wheel_leave(self, event):
        """Mouse wheel binding for camera view

        Parameters
        ----------
        event : tkinter event
            Mouse wheel event
        """

        if platform.system() != "Linux":
            self.camera_view.canvas.unbind("<MouseWheel>")
        else:
            self.camera_view.canvas.unbind("<Button-4>")
            self.camera_view.canvas.unbind("<Button-5>")
        self.view.root.bind(
            "<MouseWheel>", self.view.scroll_frame.mouse_wheel
        )  # reinstate scrollbar mousewheel

    def mip_controller_mouse_wheel_leave(self, event):
        """Mouse wheel binding for MIP view

        Parameters
        ----------
        event : tkinter event
            Mouse wheel event
        """

        if platform.system() != "Linux":
            self.mip_view.canvas.unbind("<MouseWheel>")
        else:
            self.mip_view.canvas.unbind("<Button-4>")
            self.mip_view.canvas.unbind("<Button-5>")
        self.view.root.bind("<MouseWheel>", self.view.scroll_frame.mouse_wheel)

    def switch_tab(self, event):
        """Switches between tabs

        Parameters
        ----------
        event : tkinter event
            Tab key event
        """

        key_val = int(event.keysym)
        if (key_val > 0) and (self.main_tabs.index("end") >= key_val):
            self.main_tabs.select(key_val - 1)

    def widget_undo(self, event):
        """Undo widget changes

        Parameters
        ----------
        event : tkinter event
            Undo key event
        """
        if isinstance(event.widget, ValidatedEntry) or isinstance(
            event.widget, ValidatedSpinbox
        ):  # Add all widgets that you want to be able to undo here
            event.widget.undo(event)

    def widget_redo(self, event):
        """Redo widget changes

        Parameters
        ----------
        event : tkinter event
            Redo key event
        """

        if isinstance(event.widget, ValidatedEntry) or isinstance(
            event.widget, ValidatedSpinbox
        ):  # Add all widgets that you want to be able to undo here
            event.widget.redo(event)
