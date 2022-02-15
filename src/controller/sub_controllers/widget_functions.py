import re
import tkinter as Tk
from traceback import format_exception

REGEX_DICT = {
    'float': '(^-?$)|(^-?[0-9]+\.?[0-9]*$)',
    'float_nonnegative': '(^$)|(^[0-9]+\.?[0-9]*$)',
    'int': '^-?[0-9]*$',
    'int_nonnegative': '^[0-9]*$'
}

def validate_wrapper(widget, negative=False, is_entry=False, is_integer=False):
    def check_range_spinbox(value):
        valid = True
        if widget['from'] and float(value) < widget['from']:
            widget.configure(foreground='red')
        elif widget['to'] and float(value) > widget['to']:
            valid = False
        else:
            widget.configure(foreground='black')
        return valid

    def check_range_entry(value):
        valid = True
        if widget.from_ and float(value) < widget.from_:
            widget.configure(foreground='red')
        elif widget.to and float(value) > widget.to:
            valid = False
        else:
            widget.configure(foreground='black')
        return valid
    
    if is_entry:
        check_range_func = check_range_entry
    else:
        check_range_func = check_range_spinbox

    float_or_integer = 'int' if is_integer else 'float'
    is_negative = '' if negative else '_nonnegative'
    match_string = REGEX_DICT[float_or_integer+is_negative]
        
    def check_float(value):
        valid = re.match(match_string, value) is not None
        if negative and value == '-':
            widget.configure(foreground='red')
        elif valid and value:
            valid = check_range_func(value)
        return valid

    def show_error_func(is_entry=False):
        def func():
            widget.configure(foreground="red")
            if not re.match(match_string, widget.get()):
                widget.set(0)
            elif widget.get() and widget.get() != '-' and float(widget.get()) > widget['to']:
                widget.set(widget['to'])

        def entry_func():
            widget.configure(foreground="red")
            if not re.match(match_string, widget.get()):
                widget.delete(0, Tk.END)
                widget.insert(0, 0)
            elif widget.get() and widget.get() != '-' and float(widget.get()) > widget.to:
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