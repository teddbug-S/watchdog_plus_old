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


class EventLogger:
    """
    A simple non-tradiitional logger to log changes to file.
    """

    def __init__(self, file_, log_dir):
        try:
            os.mkdir(log_dir)
        except FileExistsError:
            ...
        finally:
            self.file_ = os.path.join(log_dir, file_)

    def read_current_data(self) -> dict:
        """Tries to read existing data from `self.file_`"""
        try:
            with open(self.file_) as file_r:
                data = json.load(file_r)
        except (FileNotFoundError, json.JSONDecodeError):
            # raise
            data = dict()
        return data

    def analyse_change(self, event, name) -> dict:
        """Analyses the event and makes creates a data dict"""
        data = self.read_current_data()
        if data:
            # append new change to existing one
            key = data.get(event.event_type)
            if changes := key.get(name, []):
                # change to set to handle duplicates
                changes = set(changes)
            else:
                changes = set()
            # add new path
            changes.add(event.src_path)
            key[name] = list(changes)
        else:
            # initialize each event type with an empty dict
            data = dict.fromkeys(
                ["created", "modified", "deleted", "moved", "closed"], dict()
            )
            # add new change to an event type
            data[event.event_type] = {name: [event.src_path]}

        return data

    def write_change(self, event, name):
        """Writes changes to file."""
        change = self.analyse_change(event, name)
        with open(self.file_, "w") as file_w:
            json.dump(change, file_w, indent=4)
