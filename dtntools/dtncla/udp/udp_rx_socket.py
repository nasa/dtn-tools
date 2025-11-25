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
import queue
import socket

from dtntools.dtncla.base import ThreadedInterface


class UdpRxSocket(ThreadedInterface):
    """Class to implement a bound/listening UDP socket."""

    RX_LOOP_TIMEOUT = 0.1  # 100 milliseconds internal loop timeout
    RECV_LEN = 65536
    SOCK_BUFLEN = int(2e6)

    def __init__(self, rx_addr, rx_port):
        """Initialize the UdpRxSocket.

        :param str tx_addr: address of the listening (this) node
        :param int tx_port: port to listen on

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpRxSocket

            socket = UdpRxSocket(tx_addr="127.0.0.1", tx_port=13708)
        """
        super().__init__()
        self._rx_addr = rx_addr
        self._rx_port = rx_port
        self._rx_queue = queue.Queue()
        self._packets_received = 0

    def setup_interface(self):
        """Init the UdpRxSocket interface.

        .. note::
            This is not called by the user, it is called from ThreadedInterface's connect() method.

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpRxSocket

            socket.setup_interface()
        """
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((self._rx_addr, self._rx_port))
        self._socket.settimeout(UdpRxSocket.RX_LOOP_TIMEOUT)

        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.SOCK_BUFLEN)
        if (
            self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        ) < self.SOCK_BUFLEN:
            raise RuntimeError(
                f"Failed to set socket buffer length to {self.SOCK_BUFLEN}. Check net.core.rmem_max setting."
            )

    def teardown_interface(self):
        """Tear down the UdpRxSocket interface.

        .. note::
            This is not called by the user, it is called from ThreadedInterface's disconnect() method.

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpRxSocket

            socket.teardown_interface()
        """
        self._socket.close()

    def process_data(self):
        """Read from the socket and add the read packet to the RX queue.

        .. note::
            This is not called by the user, it is called from ThreadedInterface's _loop() method.

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpRxSocket

            socket.process_data()
        """
        try:
            packet = self._socket.recv(UdpRxSocket.RECV_LEN)
            self._rx_queue.put_nowait(packet)
            self._packets_received += 1
        except socket.timeout:
            pass

    def read(self, timeout=None):
        """Get a packet from the RX queue.

        :param float timeout: (optional) timeout in seconds
        :returns: bytearray if a packet is available, or None if timeout occurred
        :rtype: byteslike

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpRxSocket

            packet = socket.read(timeout = 5.0)
        """
        if self.is_active():
            try:
                return self._rx_queue.get(timeout=timeout)
            except queue.Empty:
                return None
        else:
            raise RuntimeError("Called read() on disconnected interface.")

    def read_all(self):
        """Empty the rx queue and return the read packets.

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpRxSocket

            packets = socket.read_all()
        """
        if self.is_active():
            # Put the read items into a list
            read_list = []
            try:
                while True:
                    read_list.append(self._rx_queue.get(block=False))
            except queue.Empty:
                pass

            return read_list
        else:
            raise RuntimeError("Called read_all() on disconnected interface.")

    def get_packets_received(self):
        """Get count of packets received.

        :return: The number of packets received
        :rtype: int

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpRxSocket

            rcvdcount = socket.get_packets_received()
        """
        return self._packets_received

    def reset_packets_received(self):
        """Reset count of packets received to 0.

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpRxSocket

            socket.reset_packets_received()
        """
        self._packets_received = 0
