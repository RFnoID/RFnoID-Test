#! /usr/bin/python
import subprocess, Tkinter, tkFont
import re
from graphics import *

class DisShit():
    def __init__(self,win_size,padding):
        self.win_size = win_size
        self.padding = padding
        self.win = GraphWin(title="Success of the Read",
                            width=padding+win_size,
                            height=padding+win_size)
    def check(self):
        tmp = subprocess.Popen(['nfc-mfclassic','r','a','a.mfd'],
                               stdout = subprocess.PIPE,
                               stderr = None)
        x = str(tmp.communicate())
        shape = Rectangle(Point(self.padding,self.padding), 
                          Point(self.win_size,self.win_size))
        if "Done" in x:
            color = "green"
        else:
            color = "red"
        shape.setOutline(color)
        shape.setFill(color)
        shape.draw(self.win)
        if self.win.getMouse():
            self.check()
        self.win.close()

def main():
    master = Tkinter.Tk()
    ds = DisShit(700,10)
    customFont = tkFont.Font(family="system",size=16,weight="bold")
    button = Tkinter.Button(master,text="Start",
                            command=ds.check,
                            font=customFont)
    button.pack(fill='both',
                expand=0,
                padx=10,
                pady=10)
    try:
        master.mainloop()
    except KeyboardInterrupt:
        raise SystemExit

if __name__ == '__main__':
    main()
