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
RETROARCH_WAIT_PERIODS = 200

# Interval between probes (seconds)
RETROARCH_WAIT_INTERVAL = 0.1

STATUS_CMD = 'tvservice -s'


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

    def on_modified(self, event):
        print(event)
        if isinstance(event, FileModifiedEvent) and event.src_path == STATE_PATH + STATE_FILE :
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            print("Desired mode state file modified")
            for i in range(1, RETROARCH_WAIT_PERIODS):
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
                time.sleep(RETROARCH_WAIT_INTERVAL)
                out, err, returncode = self.runcmd(STATUS_CMD)

                if returncode != 0:
                    print(f"Failed: {err.decode(sys.getdefaultencoding()).strip()}" , file=sys.stderr)
        
            

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
