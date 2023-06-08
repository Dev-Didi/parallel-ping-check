import sys
import os
import subprocess as sp
from slugify import slugify
from datetime import datetime
from time import sleep
from tkinter import *
from tkinter import ttk
from threading import Thread, Lock
import re
PLATFORM_PING_ARGS = {"win32": '-n', "linux": '-c'}
CURRENT_PLATFORM = sys.platform
PING_INDICATOR = PLATFORM_PING_ARGS[CURRENT_PLATFORM]
STOP_BOOL = False

address_strings = [] # list of address strings
address_set = {} # dictionary of address strings + their current status (WAITING< CONNECTED, DISCONNECTED etc)
addresses = [] # list of address instances
mutex_ping = Lock() # mutex for accessing the ping command (shouldn't be necessary but seemed buggy without)
mutex_log = Lock() # mutex for accessing the address_set 
mutex_file = Lock() # mutex to stop synchronous file read/writes 
class TestAddress:
    address = ""
    ping_count = 0
    time_log = []
    connected = False
    def __init__(self,address):
        self.address = address
        self.ping_count = 0
        self.time_log = [] ## make this a list of tuples (a,b,c) -> a = time -> b = response code (1 = problem, 0 = ok) -> c = ping rt (if applicable)

    def add_log(self,time, res,rt):
        self.time_log.append((time,res,rt))

    def write_log(self, path, mode='w'):
        response_string_map = {0: "Connection ok. rt: ",1: "Disconnected. rt: "}
        mutex_file.acquire(blocking=False)
        with open(path,mode) as f:
            for (t,r,rt) in self.time_log:
                try:
                    f.write(f"{t}:  {response_string_map[r]} {rt}ms.\n")
                except KeyError:
                    f.write(f"{t}:  Unexpected error {r}.\n")
            mutex_file.release()

    def ping(self):
        now = datetime.now()
        mutex_ping.acquire()
        try:
            response = sp.run(["ping",PING_INDICATOR,"1",self.address],capture_output=True, text=True)
        except:
            print(f"Something went wrong trying to ping {self.address}")
        finally:
            mutex_ping.release()

        now_string = now.strftime("%H:%M:%S")
        if response.returncode == 0:
            rt = re.findall('(.*)Average = ([0-9]*)ms',response.stdout)
            rt = rt[0][-1]
        else: 
            rt = "N/A "
        self.time_log.append((now_string,response.returncode,rt))
        self.ping_count += 1
        return response


def add_addr():
    ad = addr_in.get()
    ad_object = TestAddress(ad)
    addresses.append(ad_object)
    address_set[ad] = "READY \n"
    update_address_space()

def thread_ping(address : TestAddress, address_name):
    counter = 0
    global STOP_BOOL
    while not STOP_BOOL:
        res = address.ping()
        mutex_log.acquire()
        if res.returncode == 0:
            rt = re.findall('(.*)Average = ([0-9]*)ms',res.stdout)
            rt = rt[0][-1]
            address_set[address_name] = f"CONNECTED         ping: {rt}ms\n"
            sleep(1) 
        else:
            address_set[address_name] = "DISCONNECTED\n "
            sleep(3)
        if counter > 5:
            address.write_log(slugify(f"{address_name}-log-temp"))
            counter = 0
        mutex_log.release()
        counter += 1
    print("Stopping ping thread...")
    return 

def update_address_space():
    address_space.delete('1.0', END)
    for k in address_set:
        address_space.insert('1.0', k + "   " + address_set[k])

def thread_update():
    global STOP_BOOL
    while not STOP_BOOL:
        mutex_log.acquire()
        update_address_space()
        mutex_log.release()
        sleep(1)
    print("stopping logging thread...")


process_threads = []
def start():
    global STOP_BOOL
    STOP_BOOL = False
    # start multiprocess of pings for all the addresses in address. Continuously update the address_space 
    for s in address_set:
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





## This function is completely cursed.... I have no idea why it can't do a single thing I want it to. 
def stop():
    global STOP_BOOL
    STOP_BOOL = True
    for entry in address_set:
        address_set[entry] = "STOPPING... \n"
    update_address_space()
    for t in process_threads:
        t.kill()
    mutex_file.acquire()
    files = [f for f in os.listdir(os.getcwd()) if f[-9:] == "-log-temp" and os.path.isfile(os.path.join(os.getcwd(),f))]
    try:
        with open("log.txt", "w") as f: 
            for t in files:                                           
                with open(t,"r")as ff:
                    for line in ff:
                        if re.search("Disconnect",line) != None:
                            address_name = ff.name[:-9]
                            f.write(address_name + ":   " + line) 
               # os.remove(t)
    except:
        print("couldn't write log file...")
    finally:
        mutex_file.release()
    for entry in address_set:
        address_set[entry] = "READY \n"
    update_address_space()


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