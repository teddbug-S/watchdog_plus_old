# Watchdog Plus
A python package to built on top of [watchdog](https://github.com/gorakhargosh/watchdog) for extra functionality such
as monitoring multiple directory paths using processes or threads 
programmatically, easily create and schedule an observer, schedule observer services known
as WatchDogService to monitor paths in the background also providing you with APIs to 
manage the background process.

# Usage
## the Observer Manager
### Create and schedule an observer.
```python
from watchdog_plus.managers import ObserverManager

# path to monitor
path = "/home/teddbug/Desktop"

manager = ObserverManager()
# create an observer, this automatically schedules the observer with the default handler
desktop_watchdog = manager.create_observer(path, name="desktop_watchdog") # you can specify any name
# this way you start the observer natively 
desktop_watchdog.start()

# but you could also do for more functionality like specifying
# duration for the observer
manager.start_observer("desktop_observer", duration=20)
```
### Create and schedule observers
```python
from watchdog_plus.managers import ObserverManager, StartMethods

paths = [
    "home/teddbug/Desktop",
    "home/teddbug/Downloads",
    "home/teddbug/Videos"
]

manager = ObserverManager() # initiate the manager
# you can optionally provide names for each of the observers but
# names are also auto generated using the last directory name lower cased
manager.create_observers(paths)
# starting the observers
manager.start_observers(
    names=[name.split('/')[-1].lower() for name in paths],
    start_method=StartMethods.THREAD # use threading 
)
# you can simply just supply the names of only the observers you want to start

```

## WatchdogService
### create a watchdog service to monitor files in background
```python
from watchdog_plus.services import WatchdogService

# path to monitor
path = "/home/teddbug/Desktop"

service = WatchdogService(
    path=path,
    name=None, # not supplying a name to the service
    run_on_startup=False # could be enabled to allow service to run on system startup
)
# schedule with output file for logging and a handler could also be provided
service.schedule()
# start service
service.start()
```
