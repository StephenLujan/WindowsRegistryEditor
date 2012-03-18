# Application for python 3 with python for windows extension
# http://sourceforge.net/projects/pywin32/


from regedit import *
from tkinter import *
try:
    import thread
except ImportError:
    import _thread as thread

class App:
    def __init__(self, master):
        self.reg = RegEdit()
        frame = Frame(master)
        frame.pack()
        l = Label(frame, text="Find What:")
        l.grid(row=0, column=0)
        self.findString = StringVar()
        self.findEntry = Entry(frame, textvariable=self.findString)
        self.findEntry.grid(row=0, column=1)
        self.findButton = Button(frame, text="Find All", command=self.find)
        self.findButton.grid(row=0, column=2)

        l = Label(frame, text="Replace With:")
        l.grid(row=1, column=0)
        self.replaceString = StringVar()
        self.replaceEntry = Entry(frame, textvariable=self.replaceString)
        self.replaceEntry.grid(row=1, column=1)
        self.replaceButton = Button(frame, text="Replace All", command=self.replace)
        self.replaceButton.grid(row=1, column=2)

        l = Label(frame, text="Search Options:")
        l.grid(row=2, column=1)
        self.searchKeyName = IntVar()
        self.searchValueName = IntVar()
        self.searchValueData = IntVar()
        c = Checkbutton(frame, text="Key Names", variable=self.searchKeyName)
        c.grid(row=3, column=0)
        c = Checkbutton(frame, text="Value Names", variable=self.searchValueName)
        c.grid(row=3, column=1)
        c = Checkbutton(frame, text="Value Data", variable=self.searchValueData)
        c.grid(row=3, column=2)

    def _find(self):
        self.disable()
        self.reg.findAll(self.findString.get(), self.searchKeyName.get(),
                        self.searchValueName.get(), self.searchValueData.get())
        self.enable()

    def _replace(self):
        self.disable()
        self.reg.replaceAll(self.findString.get(), self.replaceString.get(),
                        self.searchKeyName.get(), self.searchValueName.get(),
                        self.searchValueData.get())
        self.enable()

    def find(self):
        thread.start_new_thread(self._find, ())

    def replace(self):
        thread.start_new_thread(self._replace, ())

    def disable(self):
        self.replaceButton.config(state = DISABLED)
        self.findButton.config(state = DISABLED)

    def enable(self):
        self.replaceButton.config(state = NORMAL)
        self.findButton.config(state = NORMAL)
root = Tk()
root.title("Registry Editor")

app = App(root)

root.mainloop()

#r.replaceAll("python test", "python success")
#r.findAll("Program Files")