#Think of tkinter as HTML, ttk as CSS, and Python as javascript
'''
A main window is created, followed by a root menubar. Then a content frame is created as a child of main window. Then a 2x2 grid of frames is created. Three total frames.
Three notebooks are added to each frame with their respecitive tabs. Each tab is actually a frame that will hold further widgets or info.
'''

from tkinter import *
from tkinter import ttk

#This starts the main window, and makes sure that any child widgets can be resized with the window
root_window = Tk()
root_window.minsize(1400,700)
root_window.columnconfigure(0,weight=1)
root_window.rowconfigure(0,weight=1)

#Menubar for root window
op_system = root_window.tk.call('tk', 'windowingsystem')
root_window.option_add('*tearOff', FALSE) #Prevents menu from being moved, makes it more modern
menubar = Menu(root_window)
root_window['menu'] = menubar

#####Adding Menu options

#File Menu
menu_file = Menu(menubar)
menubar.add_cascade(menu=menu_file, label='File')
menu_file.add_command(label='New')
menu_file.add_command(label='Open...')
menu_file.add_command(label='Close') #command=closeFile need this or some version to run action code
        #Recent Cascade menu inside File
menu_recent = Menu(menu_file)
menu_file.add_cascade(menu=menu_recent, label='Open Recent') #adds cascade menu
#Example of how to represent recent files
#for f in recent_files:
    #menu_recent.add_command(label=os.path.basename(f), command=lambda f=f: openFile(f))

#Edit Menu
menu_edit = Menu(menubar)
menu_edit.add_separator()
menubar.add_cascade(menu=menu_edit, label='Edit')
menu_edit.add_command(label='Copy')
menu_edit.add_command(label='Paste')


#A frame is needed first and this holds all content in the window, its parent is the root window, children will be other widgets. Padding is for aesthetics
content = ttk.Frame(root_window, padding=(5,5))

#####This creates the basic start of the layout for our GUI######

#Notebook 1 setup, packing a label to help distinguish
frame_left = ttk.Frame(content)
left_frame_label = ttk.Label(frame_left, text="Notebook #1")
left_frame_label.pack()

#Notebook 2 setup
frame_top_right = ttk.Frame(content)
top_right_frame_label = ttk.Label(frame_top_right, text="Notebook #2")
top_right_frame_label.pack()

#Notebook 3 setup
frame_bottom_right = ttk.Frame(content)
bottom_right_frame_label = ttk.Label(frame_bottom_right, text="Notebook #3")
bottom_right_frame_label.pack()


'''
Placing the notebooks using grid. While the grid is called on each frame it is actually calling 
the main window since those are the parent to the frames. The labels have already been packed into each respective
frame so can be ignored in the grid setup. This layout uses a 2x2 grid to start. 

       # 1   2
        #3   4 

The above is the grid "spots" the left frame will take spots 1 & 3 while top right takes
spot 2 and bottom right frame takes spot 4.
'''
#Gridding out foundational frames
content.grid(column=0, row=0, sticky=(N, S, E, W)) #Sticky tells which walls of gridded cell the widget should stick to
frame_left.grid(row=0, column=0, rowspan=2, sticky=(N, S, E, W))
frame_top_right.grid(row=0, column=1, sticky=(N, S, E, W))
frame_bottom_right.grid(row=1, column=1, sticky=(N, S, E, W))

#This dictates how to weight each piece of the grid, so that when the window is resized the notebooks get the proper screen space. 
# Content is the frame holding all the other frames that hold the notebooks to help modularize the code
content.columnconfigure(0, weight=1) #can add an arg called min or max size to give starting point for each frame
content.columnconfigure(1, weight=1) #weights are relative to each other so if there is a 3 and 1 the 3 weight will give that col/row 3 pixels for every one the others get
content.rowconfigure(0, weight=1)
content.rowconfigure(1,weight=1)


#Creating notebooks in each frame

#Putting notebook 1 into left frame
notebook_1 = ttk.Notebook(frame_left)
notebook_1.pack(anchor=W)
settings_tab = ttk.Frame(notebook_1) #Creating first tab in notebook1
adv_settings_tab = ttk.Frame(notebook_1)
#Adding tabs to notebook 1
notebook_1.add(settings_tab, text='Settings',sticky=NSEW)
notebook_1.add(adv_settings_tab, text='Advanced Settings', sticky=NSEW)

#Notebook 2 -> frame top right
notebook_2 = ttk.Notebook(frame_top_right)
notebook_2.pack(anchor=W)
camera_tab = ttk.Frame(notebook_2)
waveform_tab = ttk.Frame(notebook_2)
#Adding tabs to notebook 2
notebook_2.add(camera_tab, text='Camera View',sticky=NSEW)
notebook_2.add(waveform_tab, text='Waveform Settings', sticky=NSEW)

#Notebook 3 -> frame bottom right
notebook_3 = ttk.Notebook(frame_bottom_right)
notebook_3.pack(anchor=W)
blank_tab = ttk.Frame(notebook_3)
hold_tab = ttk.Frame(notebook_3)
#Adding tabs to notebook 3
notebook_3.add(blank_tab, text='Tab 1',sticky=NSEW)
notebook_3.add(hold_tab, text='Tab 2', sticky=NSEW)



root_window.mainloop()