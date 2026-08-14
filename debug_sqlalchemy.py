import sys
import threading
import time
import traceback
import faulthandler

def watcher():
    time.sleep(3)
    print("Watcher: hanging! Stack traces:", file=sys.stderr, flush=True)
    faulthandler.dump_traceback()
    import os
    os._exit(1)

t = threading.Thread(target=watcher, daemon=True)
t.start()
print("importing...", flush=True)
import sqlalchemy
print("done importing", flush=True)
