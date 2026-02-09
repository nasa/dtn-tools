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
from abc import ABC, abstractmethod


class UnthreadedInterface(ABC):
    """Base CLA class that implements reception logic from the same thread as the caller."""

    def __init__(self):
        """Initialize the UnthreadedInterface. This class is used as the base class for a socket."""
        self._active = False

    def is_active(self):
        """Return True if the interface is active.

        *Usage:*

        .. code-block:: python

            active = socket.is_active()
        """
        return self._active

    @abstractmethod
    def setup_interface(self):
        """Abstract method for setting up the interface. Must be defined by subclass."""
        pass

    @abstractmethod
    def teardown_interface(self):
        """Abstract method for tearing down the interface. Must be defined by subclass."""
        pass

    def connect(self):
        """Connect the interface.

        *Usage:*

        .. code-block:: python

            socket.connect()
        """
        if not self.is_active():
            self.setup_interface()
            self._active = True

    def disconnect(self):
        """Disconnect the interface.

        *Usage:*

        .. code-block:: python

            socket.disconnect()
        """
        if self.is_active():
            self.teardown_interface()
            self._active = False
