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


import glob
import os
import shlex
from signal import SIGKILL
from subprocess import run
from shutil import copy as shutil_copy
from collections import namedtuple
from importlib import import_module


class WatchdogServiceError(Exception):
    ...


# base class for all exceptions raised by a service


class ServicePIDNotFound(WatchdogServiceError):
    ...


# raised when service pid can't be returned


class ServiceNotRunning(WatchdogServiceError):
    ...


# raised when service pid can't be returned


class ServiceReloadError(WatchdogServiceError):
    ...


# raised when service file not found during a service reload


class ReadOnlyProperty(object):
    """A simple descriptor to make some properties readonly"""

    def __set_name__(self, owner, name):
        self.owner = owner
        self.name = name

    def __set__(self, obj, value):
        raise AttributeError("attribute is readonly.")


class ServiceName(ReadOnlyProperty):
    def __get__(self, obj, obj_type):
        if _name := getattr(obj, "_name"):
            name = _name
        else:
            path = getattr(obj, "path")
            name = path.strip("/").split("/")[-1]
        return name


class ReadOnly(ReadOnlyProperty):
    def __get__(self, obj, obj_type):
        result = getattr(obj, f"_{self.owner.__name__}__get_{self.name}")
        return result()


Autostart = namedtuple(
    "Autostart",
    [
        "Encoding",
        "Name",
        "Comment",
        "Icon",
        "Exec",
        "Terminal",
        "Type",
        "Categories",
        "X_GNOME_Autostart_enabled",
        "X_GNOME_Autostart_Delay",
    ],
)


class WatchdogService:
    """
    WatchdogService provides interface for monitoring filesystem
    events from background by creating a background process that
    does the filesystem monitoring using watchdog. Provides
    interface to manage the process.
    """

    name = ServiceName()
    launch_command = ReadOnly()
    pid = ReadOnly()

    def __init__(self, path, name=None, run_on_startup=False, service_dir=None):
        self.run_on_startup = run_on_startup
        self.path = path
        self.is_active = False
        self._service_dir = service_dir
        self._name = name

    @property
    def service_dir(self):
        """A directory to keep service files"""
        if self._service_dir:
            try:
                os.mkdir(self._service_dir)
            except FileExistsError:
                ...
        else:
            self._service_dir = os.curdir
        return self._service_dir

    @property
    def service_file_abs(self) -> str:
        """Returns absolute service filename path"""
        path_ = os.path.abspath(self.service_file)
        return path_

    @property
    def service_file(self) -> str:
        """Generates service filename"""
        filename = os.path.join(
            self.service_dir,
            "{}_service_true.py" if self.run_on_startup else "{}_service.py",
        )
        # return filename
        return filename.format(shlex.quote(self.name.lower()))

    @property
    def output_file(self) -> str:
        """Generates output filename"""
        filename = f"{self.name.lower()}.txt"
        return filename

    @property
    def output_file_abs(self) -> str:
        """Returns absolute service filename path"""
        path_ = os.path.abspath(self.output_file)
        return path_

    @property
    def system_autostart_dir(self):
        """System directory where autostart configurations are stored"""
        filename = f"{os.environ['HOME']}/.config/autostart"
        return filename

    @property
    def autostart_file(self):
        """Autostart file path."""
        # make available only if run_on_startup is true
        if not self.run_on_startup:
            raise AttributeError(
                f"WatchdogService object with 'run_on_startup = False'"
                " has no attribute 'autostart_file' "
            )
        filename = os.path.join(
            self.service_dir, f"{self.name.lower()}_autostart.desktop"
        )
        return filename

    @property
    def autostart_config(self):
        """auto-start configuration of the service"""
        # make available only if run_on_startup is true
        if not self.run_on_startup:
            raise AttributeError(
                f"WatchdogService object with 'run_on_startup = False'"
                " has no attribute 'autostart' "
            )
        autostart = Autostart(
            Encoding="UTF-8",
            Name=self.name,
            Comment="WatchdogService for monitoring filesystem events",
            Icon="gnome-info",
            Exec=self.__get_launch_command(
                service_file=self.service_file_abs, output_file=self.output_file_abs
            ),
            Terminal="false",
            Type="Application",
            Categories="",
            X_GNOME_Autostart_enabled="true",
            X_GNOME_Autostart_Delay="0",
        )

        return autostart

    def autostart_from_file(self, file_):
        """Gets autostart configurations from file"""
        if not self.run_on_startup:
            raise AttributeError(
                f"WatchdogService object with 'run_on_startup = False'"
                "has no attribute 'autostart_from_file' "
            )
        data = {}
        # open autostart file
        with open(file_) as file_w:
            for line in file_w.readlines():
                if "=" in line:  # check for keys & values
                    key, value = line.split("=")
                    data[key] = value
        # use data to configure autostart
        self.configure_autostart(**data)

    def __write_autostart(self) -> None:
        """Writes autostart file"""
        header = "[Desktop Entry]\n"  # opening header
        # open file
        with open(self.autostart_file, "w") as autostart_file_w:
            autostart_file_w.write(header)
            # lines to write to file
            lines = [
                f"{key.replace('_', '-')}={value}\n"
                for key, value in self.autostart_config._asdict().items()
            ]
            autostart_file_w.writelines(lines)

    def __copy_to_system(self):
        """Moves autostart file to system autostart directory"""
        src, dest = self.autostart_file, self.system_autostart_dir
        # copy to system path
        shutil_copy(src, dest)

    def __get_launch_command(self, service_file=None, output_file=None) -> str:
        """Command used to launch service"""
        service_file = self.service_file if not service_file else service_file
        output_file = self.output_file if not output_file else output_file
        launch_command = " ".join(
            [
                "nohup",  # disables hang up signals sent to service file
                "python3",  # python3
                "-u",  # force the stdout and stderr streams to be unbuffered
                f"{shlex.quote(service_file)}",
                f" > {shlex.quote(output_file)} &",
            ]
        )
        return launch_command

    def __get_pid(self) -> int:
        """Returns pid of service"""
        # initialise command
        command = shlex.join(["ps", "-fU", shlex.quote(os.environ["USER"])])
        output = run(command, text=True, capture_output=True, shell=True).stdout
        # search for the process
        pattern = f"python3 -u ./{self.name.lower()}_service"
        try:
            match = [line for line in output.splitlines() if pattern in line][0]
            pid = int(match.split()[1])
        except (IndexError, ValueError):
            raise ServicePIDNotFound(
                f"the pid of service {self.name.lower()!r} not found, is it running?"
            )
        else:
            return pid

    def __schedule(self, handler, output_file) -> None:
        """Set up a service"""
        # instructions to create a service
        handler_import = f"from {__name__} import {handler}\n" if handler else ""
        instructions = f"""
# Generated by Watchdog Plus Service
{handler_import}
from watchdog_plus.managers import ObserverManager

# path to monitor
path = {self.path!r}

manager = ObserverManager(handler={handler})  # observer manager
manager.create_observer({self.path!r}, name={self.name!r})
# launch observer
manager.start_observer({self.name!r})
"""
        # i.e. append __true to file name if it should run on system start up
        # open and write instructions to file
        if self.run_on_startup:
            # write autostart file if service should run on startup
            self.__write_autostart()
            self.__copy_to_system()
        with open(self.service_file, "w") as service_file_w:
            service_file_w.write(instructions)

    @classmethod
    def from_service_file(cls, name):
        """Creates a service object from undeleted service file"""
        # load service file
        service_file = glob.glob(f"{name}_service_*.py")
        autostart_file = glob.glob(f"{name}_autostart.desktop")

        if service_file:
            service_file = service_file[0]
            # get path from service file
            path = getattr(import_module(service_file), "path")
            run_on_startup = True if service_file.endswith("true.py") else False
            # create service object
            service = cls(path, run_on_startup=run_on_startup)
            # additional setups for service with run_on_startup true
            if run_on_startup and autostart_file:
                service.autostart_from_file(autostart_file[0])
            else:
                # write new autostart file
                getattr(service, "__WatchDogService__write_autostart")()

            return service
        else:
            raise ServiceReloadError(f"can't find service file for {name}")

    def schedule(self, output_file=None, handler=None):
        """Schedule service with handler and path"""
        if not output_file:
            output_file = self.output_file
        # schedule
        self.__schedule(handler=handler, output_file=output_file)

    def configure_autostart(self, **parameters):
        """Configures autostart with parameters in the parameters argument"""
        autostart = self.autostart_config
        # set attribute of autostart to provided keys
        for key, value in parameters.items():
            if key == "x_gnome_autostart_enabled":
                continue
            elif key == "x_gnome_autostart_delay":
                value = str(value)  # convert back to string
            # set autostart keys
            setattr(autostart, key, value)

    def clean_files(self) -> None:
        """Deletes created service files on exit"""
        try:
            os.remove(self.service_file)
            os.remove(self.output_file)
            if self.run_on_startup:
                os.remove(self.autostart_file)
        except Exception as e:
            print(e)

    def start(self) -> None:
        """Start service"""
        command = self.launch_command
        os.system(command)
        # set is_active to True
        self.is_active = True

    def stop(self) -> None:
        """Stops service by sending a SIGKILL signal to it's pid"""
        if self.is_active:
            # send a kill signal
            self.send_signal(SIGKILL)
            self.is_active = False
        else:
            raise ServiceNotRunning(f"can't call stop on an inactive service.")

    def clean_stop(self) -> None:
        """Stops service also deletes files created."""
        self.stop()  # stop the service
        self.clean_files()

    def send_signal(self, signal) -> None:
        """Send a signal to service"""
        os.kill(self.pid, signal)
