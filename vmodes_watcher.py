#!/usr/bin/python3
import time
import sys
from datetime import datetime, timedelta
from subprocess import Popen, PIPE
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import FileModifiedEvent
import psutil

state_path =  '/opt/retropie/configs/all/desired_mode/'
state_file = 'value'


class MyHandler(FileSystemEventHandler):
   
    def __init__(self):
        print('Starting watcher...')
        self.last_modified = datetime.now()    

    def checkIfProcessRunning(self, processName):
        for proc in psutil.process_iter():
            try:
                if processName.lower() in proc.name().lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False;

    def on_modified(self, event):
        if datetime.now() - self.last_modified < timedelta(seconds=1):
            return        
        if isinstance(event, FileModifiedEvent) and event.src_path == state_path + state_file :
            for i in range(1, 10):
                if self.checkIfProcessRunning('retroarch'):
                    mode = open(state_path + state_file).read().strip()
                    print(f"Setting desired display mode: '{mode}' ...")
                    time.sleep(2)
                    p0 = Popen("tvservice -c '%s'" % (mode) , shell=True, stdout=PIPE, stderr=PIPE)
                    out, err = p0.communicate()

                    if p0.returncode == 0:
                        print(out.decode(sys.getdefaultencoding()).strip())
                        p0 = Popen("fbset -depth 8; fbset -depth 32;", shell=True, stdout=PIPE, stderr=PIPE)
                        out, err = p0.communicate()
                    else:
                        print(f"Failed: {err.decode(sys.getdefaultencoding()).strip()}" , file=sys.stderr)
                    break
                else:
                    print('Waiting for retroarch to start...')
                    time.sleep(1);


            

if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=state_path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
