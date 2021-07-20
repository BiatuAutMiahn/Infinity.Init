[Function]
```
Defines a Node; A Python Thread wrapper. Within the thread, a module is loaded,
and basic functions are provided such as exception handling, live reload, and shared memory.
```


[Python Module Setup]
```
git clone https://github.com/BiatuAutMiahn/Infinity.Init Infinity
```


[Example.py]
```
import Infinity
Init=Infinity.Init(["templ"])
Init.interact()
```

[templ.py]
```
Magic = "8hMrQ4Xq8oQl4Ecx"  # A 16 digit AlphaNumeric String
Alias = "Test"              # Intended to be registered into globals(); TODO.
node=None                   # Global Place holders
logging=None                # ..

# Called before _loop_
def __init__(n,l):
    global node
    global logging
    node=n
    logging=l
    node.id=Magic
    logging.info("["+node.name+"]:\tInitialized")

# Called before node is reloaded after modification
def __reinit__(self):
  pass

# Called before node is terminated
def __deinit__(self)
  pass
  
# Called at intervals; default is 0.1s
def __loop__(self):
  pass
```

[Node Attributes]
```
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
```

[Node Methods]
```
handle_exception(self,e)
suspend(self) # Only stops __loop__
terminate(self)
reload(self)
interact(self)
run(self)

```
