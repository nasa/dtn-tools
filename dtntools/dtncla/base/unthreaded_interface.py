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
