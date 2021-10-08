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

from handlers import EventHandler
from observers import ObserverPlus


# Methods for starting an observer

class StartMethods(Enum):
    THREAD = 1
    MULTIPROCESSES = 2


# A collection to keep observers
# and maintain uniqueness in their names

class ObserversCollection(list):
    def __init__(self):
        super().__init__() # call super init

    def append(self, value):
        # check for already existing name
        for item in self:
            if item.name == value.name:
                raise NameError(f"name conflict, an observer with the name {value.name!r} already exists.")
        # else append to collections
        super().append(value)



# The manager 

class ObserverManager:

    def __init__(self, 
        observer=ObserverPlus, handler=EventHandler()
    ):
        # some default classes
        self.observer_class = observer
        self.handler = handler

        # keep observers
        self.all_observers_ = ObserversCollection()

    # Some helper methods

    def get_by_name(self, name, collection):
        """ Returns an observer by it's name """
        observer_ = [i for i in collection if i.name == name ][0]
        return observer_

    def generate_name(self, path) -> str:
        """ Generates name for path """
        name = path.strip('/').split('/')[-1]
        return name

    def generate_names(self, paths):
        """ Generates names for paths and also 
        keeps track of the position of each name"""
        names, position_data, pos = list(), dict(), -1
        for path_ in paths:
            name = self.generate_name(path_)
            while name in names:
                pos -= 1
                name = self.generate_name(path_.removesuffix(f'/{name}'))
            names.append(name)
            position_data[name] = pos
        # write position data to file
        self.write_positions(position_data)
        # return names
        return names

    def write_positions(self, position_data):
        """ Writes position data to file """
        file_ = os.path.join(self.handle.logger.log_dir, 'position_data.json')
        with open(file_, 'w') as file_w:
            json.dump(position_data, file_w)


    # Private methods to do real work
    # use the public interfaces

    def __start_observer(self, observer_):
        """ Starts an observer """
        observer_.start()
        # keep observer ALIVE
        try:
            while True:
                observer_.join(1)
        except KeyboardInterrupt:
            # stop observer
            observer_.stop()
            observer_.join()

        # TODO: define a more stable way to stop an observer

    def __start_observers(self, observers_, start_method):
        """ Starts an iterable of observers all at once using 
        method specified in the `start_method` parameter. """

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

    def create_observer(self, path, name = None):
        """ Creates an schedules an observer """
        observer_ = self.observer_class()
        observer_.schedule(self.handler, path)
        # generate a new name from path if name not given
        observer_.name = name if name else self.generate_name(path)
        # returns an observer
        self.all_observers_.append(observer_)


    def create_observers(self, paths, names = None):
        """ Creates and schedules an observer for each path in `paths` """
        observers_ = (
            self.create_observer(path, name)
            for path, name in zip(paths, self.generate_names(paths))
        )
        # update created observers
        self.all_observers_.update(observers_)


    # Starting observers

    def start_observer(self, name):
        """ Start an observer using it's name """
        observer_ = self.get_by_name(name, self.all_observers_)
        self.__start_observer(observer_) # start the observer

    def start_observers(self, names, start_method=StartMethods.THREAD):
        """ Starts an iterable of observers """
        observers_ = [self.get_by_name(name, self.all_observers_) for name in names]
        # start observers
        self.__start_observers(observers_, start_method)
