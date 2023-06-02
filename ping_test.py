import os
from datetime import datetime
from time import sleep
import tkinter as tk 
def main(): 
    print_resp = True
    total_noresp = 0
    counter = 0
    times = []
    while True:
        sleep(1)
        response = os.system("ping -n 1 www.bbc.co.uk > null")
        if response != 0:
            now = datetime.now()
            now_string = now.strftime("%H:%M:%S")
            print(f"connection lost at {now_string}")
            times.append(now_string)
            total_noresp += 1
            with open("results.txt","w") as f:
                f.write("".join(times))
            sleep(5) 
            print_resp = True
        else:
            if print_resp:
                print(response)
                print_resp = False
        counter += 1
        print(end='\x1b[2K'*(len(times)+2))
        print(f"total failed responses after {counter} requests: {total_noresp}")
        print("times failed:")
        for t in times:
            print(t)
        # ret_string = "\r" * (len(times) + 2)
        # print(ret_string)

if __name__ == "__main__":
    main()