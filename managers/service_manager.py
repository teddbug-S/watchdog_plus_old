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


import os
import glob

from .manager import Manager
from ..errors import NoServicesFound


class WatchDogService:
    """ Represents a watchdog service """
    def __init__(self, name, service_file, run_on_startup):
        self.name = name
        self.service_file = service_file
        self.run_on_startup = run_on_startup


class ServiceCollection(list):
    """
    A subclass of builtins.list to ensure uniqueness of items.
    """
    def __init__(self):
        super().__init__() # call super init

    def append(self, value):
        # check for already existing name
        for item in self:
            if item.name == value.name:
                raise AlreadyExists(f"service with name {item.name} already exists")
        # else append to collections
        super().append(value)


class ServiceManager(Manager):
    """
    A class to facilitate the creation, intialization, launching
    and managing of watchdog background services.
    """
    def __init__(self):
        self.services = ServiceCollection()
        # necessary files
        self.service_dir = '__watchservice__'
        self.__make_service_dir() # initialize service directory
        

    # Private methods KEEP OFF!

    def __make_service_dir(self) -> None:
        """ Tries to set up all folders and files for managing services """
        try:
            # make the services dir
            os.mkdir(self.service_dir)
        except FileExistsError:
           ...

    def __create_service(
        self, path: os.PathLike, name: str, service_file: str, handler) -> None:
        """ 
        Creates a service and schedules it with handler. 
        Args:
            path: path to monitor with service
            name: name of service
            service_file: name of the service_file 
            handler: set a custom event handler for the service

        Note that a service just adds the functionality of making an
        observer run in backgound and on start up, the rest of the functionality
        if from the observer manager and observers.
        """
        # instructions to create a service
        instructions = [
            # 'from sys import path as sys_path\n',
            # f"sys_path.append(__file__.removesuffix('/{service_file}'))\n",
            f'from {__name__} import {handler}\n' if handler else '',
            'from watchdog_plus.managers import ObserverManager\n\n\n',
            f'manager = ObserverManager(handler={handler})\n',
            f'manager.create_observer({path!r}, name={name!r})\n',
            f'manager.start_observer({name!r})\n',
        ]
        # open and write instructions to file
        with open(service_file, 'w') as service_file_w:
            service_file_w.writelines(instructions)


    def __launch_service(self, service: WatchDogService, output_file=None) -> None:
        """
        Launches a service
        Args:
            service: service to launch
            output_file: a file the service logs to.
        """
        output_file = service.name if not output_file else output_file
        # use superuser
        os.system(f'nohup python3 -u {service.service_file} > {output_file}.txt &')

    
    # Public methods KEEP ON!
    
    def _init_services(self) -> None:
        """ 
        Searches for existing services and initializes them to be ready for launching. 
        """
        # glob for service files
        service_files = glob.glob(os.path.join(self.service_dir, '*.wds')) 
        for service_file in service_files:
            # make a service object for each file
            name = os.path.splitext(os.path.basename(service_file))[0]
            service_ = WatchDogService(name, service_file, run_on_startup=False)
            if name.endswith('__true'):
                service_.run_on_startup = True
            # append to services
            self.services.append(service_)
        # raise error if no service files found
        if not service_files:
            raise NoServicesFound("no services found. You should consider creating some.")
    

    def create_service(self, path, run_on_startup = False, handler = None,):
        """ Creates a service """
        name = self.generate_name(path).lower() # generate a name for the service
        # generate a service file name based on some parameters
        # i.e append __true to file name if it should run on system start up
        service_file = os.path.join(
            self.service_dir,  f"{name}__true.wds" if run_on_startup else f"{name}.wds")
        self.__create_service(path, name, service_file, handler)
        # create and append a service object.
        self.services.append(WatchDogService(
            name, service_file, run_on_startup))


    def launch_service(self, name, output_file=None):
        """ Launches service by name """
        service = self.get_by_name(name, self.services)
        self.__launch_service(service)
