import sys
import os
import subprocess as sp
from datetime import datetime
from time import sleep
from tkinter import *
from tkinter import ttk
from threading import Thread, Lock
import re
PLATFORM_PING_ARGS = {"win32": '-n', "linux": '-c'}
CURRENT_PLATFORM = sys.platform
PING_INDICATOR = PLATFORM_PING_ARGS[CURRENT_PLATFORM]


address_strings = []
address_set = {}
addresses = [] 
mutex = Lock()
class TestAddress:
    address = ""
    ping_count = 0
    time_log = []
    connected = False
    def __init__(self,address):
        self.address = address
        self.ping_count = 0
        self.time_log = [] ## make this a list of tuples (a,b) -> a = time -> b = response code (1 = problem, 0 = ok)

    def add_log(self,time, res):
        self.time_log.append((time,res))

    def write_log(self, path, mode='w'):
        response_string_map = {0: "Connection ok.",1: "Disconnected."}
        with open(path,mode) as f:
            for (t,r) in self.time_log:
                try:
                    f.write(f"{t}:  {response_string_map[r]}.\n")
                except KeyError:
                    f.write(f"{t}:  Unexpected error {r}.\n")

    def ping(self):
        now = datetime.now()
        mutex.acquire()
        try:
            response = sp.run(["ping",PING_INDICATOR,"1",self.address])
        except:
            print(f"Something went wrong trying to ping {self.address}")
        finally:
            mutex.release()

        now_string = now.strftime("%H:%M:%S")
        self.time_log.append((now_string,response.returncode))
        self.ping_count += 1
        return response


def add_addr():
    ad = addr_in.get()
    ad_object = TestAddress(ad)
    addresses.append(ad_object)
    address_space.insert('1.0',ad + "\n")

def thread_ping(address : TestAddress, address_name):
    counter = 0
    while not stop_bool:
        res = address.ping()
        if res.returncode == 0:
            address_set[address_name] = "CONNECTED \n"
            sleep(1) 
        else:
            address_set[address_name] = "DISCONNECTED\n "
            sleep(3)
        if counter > 5:
            address.write_log(f"{address_name}_LOG_TEMP")
            counter = 0
        counter += 1


def thread_update():
    while not stop_bool:
        address_space.delete('1.0', END)
        for k in address_set:
            address_space.insert('1.0', k + "   " + address_set[k])
        sleep(1)


process_threads = []
def start():
    stop_bool = False
    # start multiprocess of pings for all the addresses in address. Continuously update the address_space 
    address_strings = address_space.get("1.0",'end-1c').split('\n')
    for s in address_strings:
        if len(s) > 1:
            address_set[s] = "WAITING\n"
    
    address_space.delete('1.0', END)
    for k in address_set:
        address_space.insert('1.0',k + "   " + address_set[k])

    process_threads = [None] * (len(addresses) + 1) # one added for the gui management

    for i in range(len(addresses)):
        process_threads[i] = Thread(target=thread_ping, args=(addresses[i],addresses[i].address))
        process_threads[i].start()
    process_threads[-1] = Thread(target=thread_update)
    process_threads[-1].start()



stop_bool = False

## This function is completely cursed.... I have no idea why it can't do a single thing I want it to. 
def stop():
    stop_bool = True
    sleep(5) # this is a shit way of trying to make sure no more writing is being done to the files before compilation:
    files = [f for f in os.listdir(os.getcwd()) if f[-9:] == "_LOG_TEMP" and os.path.isfile(os.path.join(os.getcwd(),f))]
    with open("log.txt", "w") as f: 
        for t in files:                                           
            with open(t,"r")as ff:
                for line in ff:
                    if re.search("Disconnect",line) != None:
                        f.write(line + "    " + f[:-9]) 
            os.remove(t)
            

def on_closing():
    root.destroy()
if __name__ == "__main__":
    ## main()

    root = Tk()
    root.title("Ping-Check")
    root.geometry("500x600")

    addr_in = Entry(root)
    add_addr_button = Button(root, text = "add", command = add_addr)

    address_space = Text(root, height= 30, width= 50)

    start_button = Button(root, text = "Start", command=start)

    stop_button = Button(root, text = "Stop", command = stop)

    address_space.grid(row = 2, column = 2, padx = 10, sticky = W)

    addr_in.grid(row = 1 , column = 2, ipadx = 50)
    add_addr_button.grid(row = 1, column = 3, ipadx = 50)
    start_button.grid(row = 3, column = 3, padx = 10, sticky= W)
    stop_button.grid(row = 4, column = 3, padx = 10, sticky= W)
    root.protocol("WM_DELETE_WINDOWS", on_closing)
    root.mainloop()