# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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
#

from aslm.controller.sub_controllers.camera_setting_controller import CameraSettingController
import pytest

class TestCameraSettingController():
    
    @pytest.fixture(autouse=True)
    def setup_class(self, dummy_controller):
        c = dummy_controller
        v = dummy_controller.view
        
        self.camera_settings = CameraSettingController(v.settings.camera_settings_tab, c)
        
    
    def test_init(self):
        
        assert isinstance(self.camera_settings, CameraSettingController)
        
        # Setup, going to check what the default values widgets are set too
        microscope_name = self.camera_settings.parent_controller.configuration['experiment']['MicroscopeState']['microscope_name']
        camera_config_dict = self.camera_settings.parent_controller.configuration['configuration']['microscopes'][microscope_name]['camera']
        
        # Default Values
        assert self.camera_settings.default_pixel_size == camera_config_dict['pixel_size_in_microns']
        assert self.camera_settings.default_height == camera_config_dict['y_pixels']
        assert self.camera_settings.default_width == camera_config_dict['x_pixels']
        assert self.camera_settings.trigger_source == camera_config_dict['trigger_source']
        assert self.camera_settings.trigger_active == camera_config_dict['trigger_active']
        assert self.camera_settings.readout_speed == camera_config_dict['readout_speed']
        
        # Camera Mode
        assert list(self.camera_settings.mode_widgets['Sensor'].widget['values']) == ['Normal', 'Light-Sheet']
        assert str(self.camera_settings.mode_widgets['Sensor'].widget['state']) == 'readonly'
        assert self.camera_settings.mode_widgets['Sensor'].widget.get() == camera_config_dict['sensor_mode']
        
        # Readout Mode
        assert list(self.camera_settings.mode_widgets['Readout'].widget['values']) == [' ', 'Top-to-Bottom', 'Bottom-to-Top']
        assert str(self.camera_settings.mode_widgets['Readout'].widget['state']) == 'disabled'
        
        # Pixels
        assert str(self.camera_settings.mode_widgets['Pixels'].widget['state']) == 'disabled'
        assert self.camera_settings.mode_widgets['Pixels'].widget.get() == ''
        assert self.camera_settings.mode_widgets['Pixels'].widget.cget('from') == 1
        assert self.camera_settings.mode_widgets['Pixels'].widget.cget('to') == self.camera_settings.default_height / 2
        assert self.camera_settings.mode_widgets['Pixels'].widget.cget('increment') == 1
        
        # Framerate
        assert self.camera_settings.framerate_widgets['exposure_time'].widget.min == camera_config_dict['exposure_time_range']['min']
        assert self.camera_settings.framerate_widgets['exposure_time'].widget.max == camera_config_dict['exposure_time_range']['max']
        assert self.camera_settings.framerate_widgets['exposure_time'].get() == camera_config_dict['exposure_time']
        assert str(self.camera_settings.framerate_widgets['exposure_time'].widget['state']) == 'disabled'
        assert str(self.camera_settings.framerate_widgets['readout_time'].widget['state']) == 'disabled'
        assert str(self.camera_settings.framerate_widgets['max_framerate'].widget['state']) == 'disabled'
        
        # Set range value
        assert self.camera_settings.roi_widgets['Width'].widget.cget("to") == self.camera_settings.default_width
        assert self.camera_settings.roi_widgets['Width'].widget.cget("from") == 2
        assert self.camera_settings.roi_widgets['Width'].widget.cget("increment") == 2
        assert self.camera_settings.roi_widgets['Height'].widget.cget("to") == self.camera_settings.default_height
        assert self.camera_settings.roi_widgets['Height'].widget.cget("from") == 2
        assert self.camera_settings.roi_widgets['Height'].widget.cget("increment") == 2
        
        # Set binning options
        assert list(self.camera_settings.roi_widgets['Binning'].widget['values']) == ['{}x{}'.format(i, i) for i in range(1,5)]
        assert str(self.camera_settings.roi_widgets['Binning'].widget['state']) == 'readonly'
        
        # Center position
        assert self.camera_settings.roi_widgets['Center_X'].get() == self.camera_settings.default_width / 2
        assert self.camera_settings.roi_widgets['Center_Y'].get() == self.camera_settings.default_height / 2
        assert str(self.camera_settings.roi_widgets['Center_X'].widget['state']) == 'disabled'
        assert str(self.camera_settings.roi_widgets['Center_Y'].widget['state']) == 'disabled'
        
        # FOV
        assert str(self.camera_settings.roi_widgets['FOV_X'].widget['state']) == 'disabled'
        assert str(self.camera_settings.roi_widgets['FOV_Y'].widget['state']) == 'disabled'
        
    def test_attr(self):
        
        attrs = [ 'in_initialization', 'resolution_value', 'number_of_pixels', 'mode', 'solvent', 'mode_widgets', 'framerate_widgets', 'roi_widgets', 'roi_btns', 'default_pixel_size', 'default_width', 'default_height', 'trigger_source', 'trigger_active', 'readout_speed', 'pixel_event_id']
        
        for attr in attrs:
            assert hasattr(self.camera_settings, attr)
            

    def test_populate_experiment_values(self):
        
        # Populate widgets with values from experiment file and check
        self.camera_settings.populate_experiment_values()
        camera_setting_dict = self.camera_settings.parent_controller.configuration['experiment']['CameraParameters']
        

        # Checking values altered are correct
        assert dict(self.camera_settings.camera_setting_dict) == dict(self.camera_settings.parent_controller.configuration['experiment']['CameraParameters'])
        assert str(self.camera_settings.mode_widgets['Sensor'].get()) == camera_setting_dict['sensor_mode']
        if camera_setting_dict['sensor_mode'] == 'Normal':
            assert str(self.camera_settings.mode_widgets['Readout'].get()) == ''
            assert str(self.camera_settings.mode_widgets['Pixels'].get()) == ''
        elif camera_setting_dict['sensor_mode'] == 'Light-Sheet':
            assert str(self.camera_settings.mode_widgets['Readout'].get()) == self.camera_settings.camera_setting_dict['readout_direction']
            assert str(self.camera_settings.mode_widgets['Pixels'].get()) == self.camera_settings.camera_setting_dict['number_of_pixels']
            
        # ROI
        assert self.camera_settings.roi_widgets['Width'].get() == camera_setting_dict['x_pixels']
        assert self.camera_settings.roi_widgets['Height'].get() == camera_setting_dict['y_pixels']
        
        # Binning
        assert str(self.camera_settings.roi_widgets['Binning'].get()) == camera_setting_dict['binning']
        
        # Exposure Time
        channels = self.camera_settings.microscope_state_dict['channels']
        exposure_time = channels[list(channels.keys())[0]]['camera_exposure_time']
        assert self.camera_settings.framerate_widgets['exposure_time'].get() == exposure_time
        assert self.camera_settings.framerate_widgets['frames_to_average'].get() == camera_setting_dict['frames_to_average']
        assert self.camera_settings.in_initialization == False
        
    @pytest.mark.parametrize("mode", ['Normal', 'Light-Sheet'])    
    def test_update_experiment_values(self, mode):
        
        # Setup basic default experiment
        self.camera_settings.populate_experiment_values()
        

        # Setting up new values
        self.camera_settings.mode_widgets['Sensor'].set(mode)
        # if mode == 'Normal':
            # self.camera_settings.mode_widgets['Readout'].set('')
            # self.camera_settings.mode_widgets['Pixels'].set('')
        # if mode == 'Light-Sheet':
            # self.camera_settings.mode_widgets['Readout'].set('Top-to-Bottom')
            # self.camera_settings.mode_widgets['Pixels'].set(15)
        self.camera_settings.roi_widgets['Binning'].set('4x4')
        self.camera_settings.roi_widgets['Width'].set(1600)
        self.camera_settings.roi_widgets['Height'].set(1600)
        self.camera_settings.framerate_widgets['frames_to_average'].set(5)
        
        # Update and assert
        self.camera_settings.update_experiment_values()
        assert self.camera_settings.camera_setting_dict['sensor_mode'] == mode
        # if mode == 'Normal':
            # assert self.camera_settings.camera_setting_dict['readout_direction'] == ''
            # assert self.camera_settings.camera_setting_dict['number_of_pixels'] == ''
        # if mode == 'Light-Sheet':
            # assert self.camera_settings.camera_setting_dict['readout_direction'] == 'Top-to-Bottom'
            # assert int(self.camera_settings.camera_setting_dict['number_of_pixels']) == 15
        
        assert self.camera_settings.camera_setting_dict['binning'] == '4x4'
        assert self.camera_settings.camera_setting_dict['x_pixels'] == 1600
        assert self.camera_settings.camera_setting_dict['y_pixels'] == 1600
        assert self.camera_settings.camera_setting_dict['number_of_cameras'] == 1
        assert self.camera_settings.camera_setting_dict['pixel_size'] == self.camera_settings.default_pixel_size
        assert self.camera_settings.camera_setting_dict['frames_to_average'] == 5