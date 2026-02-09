#
# NASA Docket No. GSC-19,559-1, and identified as "Delay/Disruption Tolerant Networking 
# (DTN) Bundle Protocol (BP) v7 Core Flight System (cFS) Application Build 7.0
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this 
# file except in compliance with the License. You may obtain a copy of the License at 
#
# http://www.apache.org/licenses/LICENSE-2.0 
#
# Unless required by applicable law or agreed to in writing, software distributed under 
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF 
# ANY KIND, either express or implied. See the License for the specific language 
# governing permissions and limitations under the License. The copyright notice to be 
# included in the software is as follows: 
#
# Copyright 2025 United States Government as represented by the Administrator of the 
# National Aeronautics and Space Administration. All Rights Reserved.
#
#
import threading
from abc import ABC, abstractmethod


class ThreadedInterface(ABC):
    """Base CLA class that implements reception logic in a separate thread."""

    def __init__(self):
        """Initialize the ThreadedInterface. This class is used as the base class for a socket."""
        self._stop_evt = threading.Event()
        self._thr = None

    def is_active(self):
        """Return True if the interface is active.

        *Usage:*

        .. code-block:: python

            active = socket.is_active()
        """
        return (self._thr) and (self._thr.is_alive())

    @abstractmethod
    def setup_interface(self):
        """Abstract method for setting up the interface. Must be defined by subclass."""
        pass

    @abstractmethod
    def teardown_interface(self):
        """Abstract method for tearing down the interface. Must be defined by subclass."""
        pass

    @abstractmethod
    def process_data(self):
        """Abstract method for processing the data. Must be defined by subclass."""
        pass

    def connect(self, timeout=None):
        """Connect the interface.

        :param float timeout: (optional) timeout in seconds

        *Usage:*

        .. code-block:: python

            socket.connect()
        """
        if not self.is_active():
            self.setup_interface()

            self._stop_evt.clear()
            start_evt = threading.Event()
            self._thr = threading.Thread(target=self._loop, args=(start_evt,))
            self._thr.start()
            start_evt.wait(timeout=timeout)

    def disconnect(self):
        """Disconnect the interface.

        *Usage:*

        .. code-block:: python

            socket.disconnect()
        """
        if self.is_active():
            self._stop_evt.set()
            self._thr.join()
            self._thr = None

            self.teardown_interface()

    def _loop(self, start_evt):
        start_evt.set()
        while not self._stop_evt.is_set():
            self.process_data()
