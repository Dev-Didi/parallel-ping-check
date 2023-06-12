import matplotlib.pyplot as plt
from datetime import datetime
import re
import os
import numpy as np

class DataEntry:
    time = None
    site = ""
    machine_name = ""
    ping = 0
    def __init__(self, str_time,site,machine_name,rt):
        self.time = convert_time(str_time)
        self.site = site
        self.machine_name = machine_name
        self.ping = rt

    def __lt__(self, other):
        return(self.get_time() < other.get_time())        

    def __eq__(self,other):
        return ((self.get_time(),self.get_site(),self.get_machine()) == 
                (other.get_time(),other.get_site(),other.get_machine()))
    
    def get_time(self):
        return self.time

    def get_site(self):
        return self.site
    
    def get_machine(self):
        return self.machine_name
    
    def get_ping(self):
        return self.ping
        
def convert_time(str_time):
    date_obj = datetime.strptime(str_time, "%H:%M:%S")
    return date_obj
    
def convert_file(fname,machine_name):
    file_entries = []
    with open(fname,"r") as f:
        for line in f:
            rt = re.findall('(.*)rt:  ([0-9]*)ms',line)
            if rt == []:
                rt = 0
            else:
                rt = rt[0][-1]
            file_entries.append(DataEntry(line[:8],fname[:-9],machine_name, int(rt)))

    file_entries.sort()
    return file_entries

def convert_all_files(dir):
    file_entries = {}
    for f in os.listdir(dir):
        if f.endswith("temp"):
            file_entries[f[:-9]] = convert_file(dir+f,os.path.dirname(dir))
    return file_entries

def draw_single(entries,colour = "red",name = "N/A",subplot=None):
    times = []
    pings = []
    for i in range(len(entries))[::5]:
        times.append(entries[i].get_time())
        pings.append(entries[i].get_ping())
    if subplot == None:
        plt.plot(times,pings, color = colour, label=name)
    else:
        subplot[0][subplot[1][0],subplot[1][1]].plot(times,pings, color = colour, label=name)
    plt.legend()


def draw_machine(entries, mname, subplot=None):
    colours = ["red","green","blue","pink","yellow","black","purple"]
    plt.title(mname)
    count = 0
    for k in entries:
        print(k)
        draw_single(entries[k], colours[count%len(colours)],k,subplot)
        count += 1

def draw_day(dir_path):
    full_day_set = {} 
    for dir in os.listdir(dir):
        converted = convert_all_files(dir)
        full_day_set[dir] = converted

    plot_count = len(full_day_set)
    col_count = int(np.sqrt(plot_count))
    row_count = int(np.ceil(plot_count / float(col_count)))
    fig, axs = plt.subplots(col_count,row_count)
    col_counter = 0
    row_counter = 0
    for machine in full_day_set:
        draw_machine(full_day_set[machine],machine,(axs,[col_counter,row_counter]))
        if col_counter == col_count -1:
            row_counter += 1
            col_counter = 0
        else:
            col_counter +=1

if __name__ == "__main__":
    file_entries = {} 
    dir = "C:\\Users\\DanielBrown\\Scripting\\python\\parallel-ping-check\\output\\ping_results\\12JUNE\\level2_desktop_ethernet\\"
    for f in os.listdir(dir):
        if f.endswith("temp"):
            file_entries[f[:-9]] = convert_file(dir+f,os.path.dirname(dir))
    print(os.path.basename(dir[:-1]))
    draw_machine(file_entries,os.path.basename(dir[:-1]))
    plt.show()