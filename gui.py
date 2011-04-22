#! /usr/bin/python
import subprocess, Tkinter, tkFont
import re
from graphics import *

master = Tkinter.Tk()

def check():
    tmp = subprocess.Popen('nfc-list', stdout = subprocess.PIPE)
    x = str(tmp.communicate())
    win = GraphWin()
    shape = Rectangle(Point(150,150), Point(50,50))
    if "UID" in x:
        print "Read",re.search("UID",x).group(0)
    if len(x) > 400:
        color = "green"
    else:
        color = "red"
    shape.setOutline(color)
    shape.setFill(color)
    shape.draw(win)
    for i in range(2):
        try:
            win.getMouse()
        except GraphicsError:
            raise SystemExit
    win.close()   

def main():
    customFont = tkFont.Font(family="system",size=16,weight="bold")
    button = Tkinter.Button(master,text="Start",command=check,font=customFont)
    button.pack(fill='both', expand=1, padx=20, pady=20)
    try:
        master.mainloop()
    except KeyboardInterrupt:
        print "Done"
        raise SystemExit

if __name__ == '__main__':
    main()
