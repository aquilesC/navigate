"""
ASLM camera communication classes.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

import tkinter.simpledialog as simple_dialog

class Debug_Module:
    def __init__(self, central_controller, menubar, verbose=False):
        self.central_controller = central_controller
        self.verbose = verbose
        
        menubar.add_command(label='ignored signal?', command=self.debug_ignored_signal)
        menubar.add_command(label='blocked queue?', command=None)
        menubar.add_command(label='update image size', command=None)
        menubar.add_command(label='get shannon value?', command=None)
        menubar.add_command(label='stop acquire', command=lambda: self.central_controller.execute('stop_acquire'))

    def debug_ignored_signal(self):
        signal_num = simple_dialog.askinteger('Input', 'How many signals you want to send out?', parent=self.central_controller.view)
        if not signal_num:
            print('no input!')
            return

        channel_num = len(self.central_controller.experiment.MicroscopeState['channels'].keys())
        signal_num = (signal_num // channel_num) * channel_num + channel_num
        
        def func():
            self.central_controller.model.run_command('debug', 'ignored_signals', 'live', self.central_controller.experiment.MicroscopeState,
                            signal_num, saving_info=self.central_controller.experiment.Saving)
            
            self.get_frames()

            image_num = self.central_controller.show_img_pipe_parent.recv()

            print('signal num:', signal_num, 'image num:', image_num)
        
        self.central_controller.threads_pool.createThread('camera',
                                    func)

    def get_frames(self):
        while True:
            image_id = self.central_controller.show_img_pipe_parent.recv()
            if self.verbose:
                print('receive', image_id)
            if image_id == 'stop':
                break
            if not isinstance(image_id, int):
                print('some thing wrong happened, stop the model!', image_id)
                self.central_controller.execute('stop_acquire')
            self.central_controller.camera_view_controller.display_image(
                self.central_controller.data_buffer[image_id])
