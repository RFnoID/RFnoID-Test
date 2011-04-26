import subprocess, Tkinter, tkFont
from graphics import *

master = Tkinter.Tk()

def check():
    tmp = subprocess.Popen('nfc-list', stdout = subprocess.PIPE)
    x = tmp.communicate()
    print x
    win = GraphWin()
    shape = Rectangle(Point(150,150), Point(50,50))
    if len(x) > 100:
        color = "green"
    else:
        color = "red"
    shape.setOutline(color)
    shape.setFill(color)
    shape.draw(win)
    for i in range(2):
        win.getMouse()
    win.close()   

def main():
    customFont = tkFont.Font(family="system",size=16,weight="bold")
    button = Tkinter.Button(master,text="Start",command=check,font=customFont)
    button.pack(fill='both', expand=1, padx=20, pady=20)
    master.mainloop()

if __name__ == '__main__':
    try:
        main()
    except:
        print "Done"
        raise SystemExit
