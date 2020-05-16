#!/usr/bin/python3
import time
import sys
from datetime import datetime, timedelta
from subprocess import Popen, PIPE
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import FileModifiedEvent
import psutil

STATE_PATH =  '/opt/retropie/configs/all/desired_mode/'
STATE_FILE = 'value'

# Number of checkIfProcessRunning probes
RETROARCH_WAIT_PERIODS = 20

# Interval between probes (seconds)
RETROARCH_WAIT_INTERVAL = 0.5

# Presumed retroarch startup time
RETROARCH_SDL_WAIT = 3

# watcher sleep interval after handling event
WATCHDOG_SLEEP = 0


class MyHandler(FileSystemEventHandler):

    def __init__(self):
        print('Starting watcher...')
        self.last_modified = datetime.now()

    def runcmd(self, cmd):
        p0 = Popen("%s" % (cmd) , shell=True, stdout=PIPE, stderr=PIPE)
        out, err = p0.communicate()
        print(out.decode(sys.getdefaultencoding()).strip())
        print(err.decode(sys.getdefaultencoding()).strip())
        return out, err, p0.returncode;

    def checkIfProcessRunning(self, processName):
        for proc in psutil.process_iter():
            try:
                if processName.lower() in proc.name().lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False;

    def on_modified(self, event):
        print(event)
        if datetime.now() - self.last_modified < timedelta(seconds=WATCHDOG_SLEEP):
            return        
        if isinstance(event, FileModifiedEvent) and event.src_path == STATE_PATH + STATE_FILE :
            mode = open(STATE_PATH + STATE_FILE).read().strip()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            print("Desired mode state file modified")
            for i in range(1, RETROARCH_WAIT_PERIODS):
                if self.checkIfProcessRunning('retroarch'):
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
                    print(f"Retroarch started...setting desired display mode: '{mode}' in {RETROARCH_SDL_WAIT} seconds' ...")
                    time.sleep(RETROARCH_SDL_WAIT)
                    out, err, returncode = self.runcmd(mode)

                    if returncode == 0:
                        self.runcmd("fbset -depth 8; fbset -depth 32;")
                    else:
                        print(f"Failed: {err.decode(sys.getdefaultencoding()).strip()}" , file=sys.stderr)

                    break
                else:
                    print('Waiting for retroarch to start...')
                    self.runcmd("tvservice -s")
                    time.sleep(RETROARCH_WAIT_INTERVAL);

        

            

if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=STATE_PATH, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
