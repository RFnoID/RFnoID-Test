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
                               stdout = subprocess.PIPE)
        x = str(tmp.communicate())
        shape = Rectangle(Point(self.padding,self.padding), 
                          Point(self.win_size,self.win_size))
        if "Done, 64 of 64 blocks read." in x:
            print "Read",re.search("Done*",x).group(0)
            color = "green"
        else:
            color = "red"
        shape.setOutline(color)
        shape.setFill(color)
        shape.draw(self.win)
        for i in range(2):
            try:
                self.win.getMouse()
            except GraphicsError, KeyboardInterrupt:
                raise SystemExit
        self.win.close()

def main():
    master = Tkinter.Tk()
    ds = DisShit(500,10)
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
