import threading
import logging
import importlib
import code
import time
import random
import string
import traceback
import os
import sys
import readline
import rlcompleter
import atexit
import psutil
import signal

def genid():
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))

class Node(threading.Thread):
    def handle_exception(self,e):
        global logging
        self.status="Exception"
        self.exception="".join(traceback.TracebackException.from_exception(e).format())
        logging.error("[%s]:\tNode encountered an Exception:\n%s"%(self.name,self.exception))
        if self.init not in self.except_non_fatal:
            self.init=1
    def suspend(self):
        global logging
        self.status="Suspended"
        logging.info("[%s]:\tNode has been suspended"%self.name)
        self.init=2
    def terminate(self):
        self.init=0
    def reload(self):
        self.init=3
    def interact(self):
        global logging
        ps1=sys.ps1
        ps2=sys.ps2
        sys.ps1='['+self.name+']>>> '
        sys.ps1='['+self.name+']... '
        vars=dict(globals(), **locals())
        readline.set_completer(rlcompleter.Completer(vars).complete)
        readline.parse_and_bind("tab:complete")
        code.interact(local=vars,banner='')
        sys.ps1=ps1
        sys.ps2=ps2
    def run(self):
        global logging
        loop_timer=time.time()
        while True:
            if self.init==0:
                self.status="Terminating"
                logging.info("[%s]:\tNode is shutting down"%self.name)
                if hasattr(self.module,'__deinit__'):
                    self.module.__deinit__()
                else:
                    logging.warning("[%s]:\tNode has no __deinit__ method"%self.name)
                del self.module
                self.module=None
                break
            elif self.init in [1,2]:
                time.sleep(self.poll_rate)
                continue
            elif self.init==3:
                try:
                    self.status="Loading"
                    logging.info("[%s]:\tLoading Module"%self.name)
                    if self.module!=None:
                        self.status="Reloading"
                        if hasattr(self.module,'__reinit__'):
                            self.module.__reinit__(self)
                        else:
                            logging.warning("[%s]:\tNode has no __reinit__ method"%self.name)
                        logging.info("[%s]:\tReloading Module"%self.name)
                        importlib.reload(self.module)
                    else:
                        if hasattr(self.module,'__reg__'):
                            self.status="Registering"
                            self.module.__reg__(self)
                        else:
                            logging.warning("[%s]:\tNode has no __reg__ method"%self.name)
                    try:
                        self.module = __import__(self.name)
                    except ModuleNotFoundError as err:
                        logging.error("[%s]:\tModule does not exist"%self.name)
                        self.status="Exception"
                        self.exception="Module does not exist!"
                        self.init=0
                        del self.module
                        self.module=None
                        break
                    self.mtime=os.stat(self.module.__file__).st_mtime
                    self.init=4
                except Exception as e:
                    self.exception_handler(e)
            elif self.init==4:
                try:
                    if not hasattr(self.module,'__init__'):
                        logging.error("[%s]:\tNode has no __init__ method"%self.name)
                        self.status="Exception"
                        self.exception="No __init__ method!"
                        self.init=0
                        del self.module
                        self.module=None
                        break
                    self.status="Initializing"
                    logging.info("[%s]:\tInitializing Node"%self.name)
                    self.module.__init__(self,logging)
                    self.init=5
                    loop_timer=time.time()
                    if not hasattr(self.module,'__loop__'):
                        logging.warning("[%s]:\tNode has no __loop__ method"%self.name)
                    else:
                        self.module.__loop__(self)
                        loop_timer=time.time()
                except Exception as e:
                    self.exception_handler(e)
                pass
            elif self.init==5:
                try:
                    self.status="Running"
                    if hasattr(self.module,'__loop__'):
                        if time.time()-loop_timer>=self.loop_interval:
                            loop_timer=time.time()
                            self.module.__loop__(self)
                except Exception as e:
                    self.exception_handler(e)
                pass
            if self.module and self.init==1 or self.init==5:
                mtime=os.stat(self.module.__file__).st_mtime
                if mtime!=self.mtime:
                    self.mtime=mtime
                    self.init=3
            time.sleep(self.poll_rate)
        self.status="Terminated"
        logging.warning("[%s]:\tNode has been Terminated"%self.name)
    def __init__(self,name):
        threading.Thread.__init__(self)
        self.init = 3                           # Int, Init Stage
        self.log = []                           # Module Log
        self.id = None                          # Unique 16 digit, AlphaNumeric String
        self.module = None                      # Imported module
        self.mtime = None                       # Time, File modified time for module, used to detect changed module.
        self.status = None                      # String, Formated Init State
        self.exception = None                   # String, Formatted Exception, after exception occurred.
        self.name = name                        # Str, Node Name
        self.poll_rate=0.1                      # Float, Delay after main thread loop
        self.loop_interval=0.1                  # Float, Delay after __loop__ calls
        self.except_non_fatal=[]                # [Int,], Init Stages that will not fall into exception state
        self.exception_handler=self.handle_exception # Func, Called when an excetpion occurs


class Init():
    def handle_exit(self,a=None,b=None):
            logging.info("[root]:\tTerminating Nodes")
            for m in self.modules.keys():
                self.modules[m].terminate()
            for m in self.modules.keys():
                self.modules[m].join()
            if os.path.isfile(self.pidfile):
                os.remove(self.pidfile)
            sys.exit()
    def interact(self):
        global logging
        ps1=">>> "
        ps2="... "
        if hasattr(sys,'ps1'):
            ps1=sys.ps1
        if hasattr(sys,'ps2'):
            ps2=sys.ps2
        sys.ps1='['+self.name+']>>> '
        sys.ps1='['+self.name+']... '
        vars=dict(globals(), **locals())
        readline.set_completer(rlcompleter.Completer(vars).complete)
        readline.parse_and_bind("tab:complete")
        code.interact(local=vars,banner='')
        sys.ps1=ps1
        sys.ps2=ps2
    def __init__(self,nodes):
        global logging
        self.modules={}
        self.name="Init"
        self.pidfile=os.path.splitext(os.path.abspath(sys.argv[0]))[0]+'.pid'
        self.pid=os.getpid()
        logging.info("[Init]:\tPID: %d"%self.pid)
        logging.basicConfig(format='[%(asctime)s.%(msecs)03d]%(message)s',level=logging.DEBUG,datefmt="%Y.%m.%d,%H:%M:%S")
        logging.info("[Init]:\tInitializing")
        psutil.Process(os.getpid()).nice(-2)
        if os.path.exists(self.pidfile):
            if not os.path.isfile(self.pidfile):
                logging.error("[Init]:\tPID file is Corrupt, Exiting")
                return
            if os.path.getsize(self.pidfile)==0:
                    logging.warning("[Init]:\tRemoving stale PID file")
                    os.remove(self.pidfile)
            else:
                with open(self.pidfile,'r') as f:
                    pid=int(f.read())
                    logging.info("[Init]:\tPID File: %d"%pid)
                if pid:
                    if psutil.pid_exists(pid):
                        logging.error("[Init]:\tAnother Instance is running, Exiting")
                        return
                    else:
                        logging.warning("[Init]:\tRemoving stale PID file")
                        os.remove(self.pidfile)
        atexit.register(self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGINT, self.handle_exit)
        if not os.path.exists(self.pidfile):
            logging.info("[Init]:\tCreating PID file")
            with open(self.pidfile,'w') as f:
                f.seek(0)
                f.write(str(self.pid))
                f.flush()
        logging.info("[Init]:\tInitializing Modules")
        for m in nodes:
            self.modules[m]=Node(m)
            self.modules[m].start()
            globals()[m]=self.modules[m]
        logging.info("[Init]:\tModules Initialized")
        logging.info("[Init]:\tInitialized")
