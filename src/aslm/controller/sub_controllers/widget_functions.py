"""
ASLM widget functions.

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

import re
import tkinter as Tk
from traceback import format_exception
import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)

REGEX_DICT = {
    'float': '(^-?$)|(^-?[0-9]+\.?[0-9]*$)',
    'float_nonnegative': '(^$)|(^[0-9]+\.?[0-9]*$)',
    'int': '^-?[0-9]*$',
    'int_nonnegative': '^[0-9]*$'
}

def validate_wrapper(widget, negative=False, is_entry=False, is_integer=False):
    """
    # this function will add validatecommand and invalidcommand to widgets
    # it supports float and integer, negative and nonnegative, entry and spinbox
    """
    def check_range_spinbox(value):
        """
        # this function used to validate wether the value is inside specified range.
        # this function used to validate spinbox widget.
        """
        valid = True
        if widget['from'] and float(value) < widget['from']:
            widget.configure(foreground='red')
        elif widget['to'] and float(value) > widget['to']:
            valid = False
        else:
            widget.configure(foreground='black')
        return valid

    def check_range_entry(value):
        """
        # this function used to validate wether the value is inside specified range.
        # this function used to validate entry widget
        """
        valid = True
        if widget.from_ and float(value) < widget.from_:
            widget.configure(foreground='red')
        elif widget.to and float(value) > widget.to:
            valid = False
        else:
            widget.configure(foreground='black')
        return valid
    
    # get the range validation function according to widget type
    if is_entry:
        check_range_func = check_range_entry
    else:
        check_range_func = check_range_spinbox

    # get the regex string
    float_or_integer = 'int' if is_integer else 'float'
    is_negative = '' if negative else '_nonnegative'
    match_string = REGEX_DICT[float_or_integer+is_negative]
        
    def check_float(value):
        """
        # this function binds to validatecommand
        """
        valid = re.match(match_string, value) is not None
        if negative and value == '-':
            widget.configure(foreground='red')
        elif valid and value:
            valid = check_range_func(value)
        return valid

    def show_error_func(is_entry=False):
        """
        # this function generate functions that bind to invalidcommand
        """
        def func():
            widget.configure(foreground="red")
            if not re.match(match_string, widget.get()):
                widget.set(0)
            elif widget.get() and widget['to'] and widget.get() != '-' and float(widget.get()) > widget['to']:
                widget.set(widget['to'])

        def entry_func():
            widget.configure(foreground="red")
            if not re.match(match_string, widget.get()):
                widget.delete(0, Tk.END)
                widget.insert(0, 0)
            elif widget.get() and widget.to and widget.get() != '-' and float(widget.get()) > widget.to:
                widget.delete(0, Tk.END)
                widget.insert(0, widget.to)

        if is_entry:
            return entry_func
        else:
            return func

    if is_entry:
        widget.from_ = None
        widget.to = None

    widget.configure(validate='all', validatecommand=(widget.register(check_float), '%P'))
    widget.configure(invalidcommand=show_error_func(is_entry))