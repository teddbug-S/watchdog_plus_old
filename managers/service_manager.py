import os
import glob

from .manager import Manager


class WatchDogService:

    def __init__(self, name, service_file, run_on_startup):
        self.name = name
        self.service_file = service_file
        self.run_on_startup = run_on_startup


class ServiceManager(Manager):

    def __init__(self):
        self.services = list()
        # necessary files
        self.service_dir = '__watchservice__'
        self.__make_service_dir() # initialize service directory
    
    def _init_services(self):
        services = glob.glob(os.path.join(self.service_dir, '*.py'))
        for service in services:
            # make a service object
            service_ = WatchDogService(service)
            if os.path.splitext(service)[0].endswith('__true'):
                # check if service runs on startup
                service_.run_on_startup = True
            # append to services
            self.services.append(service_)

    def __make_service_dir(self):
        """ Tries to set up all folders and files for managing services """
        try:
            # make the services dir
            os.mkdir(self.service_dir)
        except FileExistsError:
           ...

    def __create_service(self, path, name, service_file, handler):
        """ Creates a service and schedules it with handler. """
        # instructions to create a service
        instructions = [
            f'from {__name__} import {handler}\n' if handler else '',
            'from watchdog_plus.managers import ObserverManager\n',
            f'manager = ObserverManager(handler={handler})\n',
            f'manager.create_observer({path!r}, name={name!r})\n',
            f'manager.start_observer({name!r})\n',
        ]
        # open and write instructions to file
        with open(service_file, 'w') as service_file_w:
            service_file_w.writelines(instructions)
    
    def create_service(self, path, run_on_startup = False, handler = None,):
        """ Creates a service """
        name = self.generate_name(path).lower() # generate a name for the service
        # generate a service file name based on some parameters
        # i.e append __true to file name if it should run on system start up
        service_file = os.path.join(
            self.service_dir,  f"{name}__true.py" if run_on_startup else f"{name}.py")
        self.__create_service(path, name, service_file, handler)
        # create and append a service object.
        self.services.append(WatchDogService(
            name, service_file, run_on_startup))


    def __launch_service(self, service, output_file=None):
        """ Launches a service """
        output_file = service.name if not output_file else output_file
        # use superuser
        os.system(f'nohup python3 -u {service.service_file} > {output_file}.txt &')


    def launch_service(self, name, output_file=None):
        """ Launches service by name """
        service = self.get_by_name(name, self.services)
        self.__launch_service(service)
