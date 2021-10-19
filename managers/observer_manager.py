# MIT License
#
# Copyright (c) 2021 Divine Darkey
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import json
import os
from enum import Enum
from concurrent import futures

from .errors import AlreadyExists
from .manager import Manager
from ..handlers import EventHandler
from ..observers import ObserverPlus

# Methods for starting an observer

class StartMethods(Enum):
    THREAD = 1
    MULTIPROCESSES = 2


# A collection to keep observers
# and maintain uniqueness in their names

class ObserversCollection(list):
    """ A subclass of builtins.list to ensure unqiueness of items """
    def __init__(self):
        super().__init__() # call super init

    def append(self, value):
        # check for already existing name
        for item in self:
            if item.name == value.name:
                raise AlreadyExists(f"observer with name {item.name} already exists")
        # else append to collections
        super().append(value)


# The manager 

class ObserverManager(Manager):
    """ A class to manage, create, start and schedule observers. """
    def __init__(self, observer: ObserverPlus=None, handler=None):
        super().__init__()
        # some default classes
        self.observer_class = ObserverPlus if not observer else observer
        self.handler = EventHandler() if not handler else handler

        # keep observers
        self.all_observers_ = ObserversCollection()

    # Some helper method

    def write_positions(self, position_data):
        """ Writes position data to file """
        file_ = os.path.join(self.handle.logger.log_dir, 'position_data.json')
        with open(file_, 'w') as file_w:
            json.dump(position_data, file_w)


    # Private methods to do real work
    # use the public interfaces

    def __start_observer(self, observer_: ObserverPlus, duration: int) -> None:
        """ 
        Starts an observer 
        Args: 
            observer_ : an ObserverPlus object
            duration : number of seconds to keep observer alive default is forerver.
        """
        observer_.start()
        # keep observer ALIVE
        try:
            if duration:
                observer_.join(duration)
            else:
                while True:
                    observer_.join(1)
        except KeyboardInterrupt:
            # stop observer
            observer_.stop()
            observer_.join()

    def __start_observers(
        self, observers_: list[ObserverPlus], start_method: StartMethods) -> None:
        """ 
        Starts an list of observers all at once using 
        method specified in the `start_method` parameter.
        
        Args:
            observers_: a list of observers to start
            start_method: the concurrent method to use in launching the observers
                defaults to threads which is equivalent to StartMethods.THREAD
        """

        max_workers = len(observers_) # get max number of workers
        names = tuple(observer.name for observer in observers_) # get names of workers

        # do some real work ;)
        # using threads
        if start_method == StartMethods.THREAD:
            # initiate a thread pool executor max_workers equal to number of observers
            with futures.ThreadPoolExecutor(max_workers=max_workers) as thread_pool:
                # set name for each worker thread
                for worker, name in zip(thread_pool._threads, names):
                    worker.name = name
                # assign work
                thread_pool.map(self.__start_observer, observers_)

        # do some real work ;)
        # using processes
        elif start_method == StartMethods.MULTIPROCESSES:
            # initiate a thread pool executor max_workers equal to number of observers
            with futures.ProcessPoolExecutor(max_workers=max_workers) as process_pool:
                # set name for each worker process
                for process, name in zip(process_pool._processes , names):
                    process.name = name
                # assign work to each
                process_pool.map(self.__start_observer, observers_)

    # Public interfaces

    # Creating observers

    def create_observer(self, path: os.PathLike, name: str = None) -> None:
        """ 
        Creates an observer scheduled to monitor path with handler as `self.handler` 
        Args:
            path: path to monitor
            name: name to be given to the observer defaults to an auto-generated name.

        NOTE: all created observers are kept in `self.all_observers`.
        """
        observer_ = self.observer_class()
        observer_.schedule(self.handler, path)
        # generate a new name from path if name not given
        observer_.name = name if name else self.generate_name(path)
        # returns an observer
        self.all_observers_.append(observer_)


    def create_observers(self, paths: list[os.PathLike], names: list[str] = None) -> None:
        """ 
        Creates observers for each path with `self.create_observer`
        Args:
            paths: a list of paths to monitor
            names: a list of names to be assigned to each observer, 
                defaults to behaviour of `self.create_observers`. """
        observers_ = (
            self.create_observer(path, name)
            for path, name in zip(paths, self.generate_names(paths))
        )
        # update created observers
        self.all_observers_.update(observers_)


    # Starting observers

    def start_observer(self, name: str, duration = 0) -> None:
        """ Start an observer using it's name """
        observer_ = self.get_by_name(name, self.all_observers_)
        self.__start_observer(observer_, duration) # start the observer

    def start_observers(
        self, names: list[str], start_method: StartMethods=StartMethods.THREAD) -> None:
        """ Starts each observer that has name in the names arg, start method is threads. """
        observers_ = [self.get_by_name(name, self.all_observers_) for name in names]
        # start observers
        self.__start_observers(observers_, start_method)
