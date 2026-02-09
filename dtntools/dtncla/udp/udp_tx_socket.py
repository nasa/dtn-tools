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
import socket

from dtntools.dtncla.base import UnthreadedInterface

from .rate_limit import RateLimit


class UdpTxSocket(UnthreadedInterface):
    """Class to implement a UDP transmit-only socket."""

    SOCK_BUFLEN = int(2e6)

    def __init__(self, tx_addr, tx_port, bps_limit=None, inter_msg_delay=None):
        """Initialize the UdpTxSocket.

        :param str tx_addr: address of the node to send to
        :param int tx_port: port of the node to send to
        :param int bps_limit: (optional) bit-rate limit to set on the socket in bps
        :param float inter_msg_delay: (optional) inter-message delay to set in seconds

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpTxSocket

            socket = UdpTxSocket(tx_addr="127.0.0.1", tx_port=13708, bps_limit=1000e6, inter_msg_delay = 0.01)
        """
        super().__init__()
        self._tx_addr = tx_addr
        self._tx_port = tx_port
        self._packets_sent = 0

        self._rate_limit = RateLimit(
            bps_limit=bps_limit, inter_msg_delay=inter_msg_delay
        )

    def setup_interface(self):
        """Init the UdpTxSocket interface.

        .. note::
            This is not called by the user, it is called from UnthreadedInterface's connect() method.

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpTxSocket

            socket.setup_interface()
        """
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.SOCK_BUFLEN)
        if (
            self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        ) < self.SOCK_BUFLEN:
            raise RuntimeError(
                f"Failed to set socket buffer length to {self.SOCK_BUFLEN}. Check net.core.wmem_max setting."
            )

    def teardown_interface(self):
        """Tear down the UdpTxSocket interface. This is not called by the user, it is called from UnthreadedInterface's disconnect() method.

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpTxSocket

            socket.teardown_interface()
        """
        self._socket.close()

    def write(self, packet):
        """Write a packet to the socket.

        :param bytes packet: the packet to send

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpTxSocket

            socket = UdpTxSocket(tx_addr="127.0.0.1", tx_port=13708)

            # Send a packet
            packet = bytes([0xAA] * int(64e3))
            socket.write(packet)
        """
        if self.is_active():
            self._rate_limit.wait(len(packet))
            bytes_sent = self._socket.sendto(packet, (self._tx_addr, self._tx_port))
            self._rate_limit.update(bytes_sent)
            self._packets_sent += 1
        else:
            raise RuntimeError("Called write() on disconnected interface.")

    def set_bps_limit(self, bps_limit):
        """Set a bit-rate limit.

        :param int bps_limit: the bit-rate limit in bits per second

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpTxSocket

            # Set bps limit of 500 Mbps
            socket.set_bps_limit(500e6)
        """
        self._rate_limit.set_bps_limit(bps_limit)

    def remove_bps_limit(self):
        """Remove the bit-rate limit.

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpTxSocket

            socket.remove_bps_limit()
        """
        self._rate_limit.remove_bps_limit()

    def set_inter_msg_delay(self, inter_msg_delay):
        """Set an inter-message delay.

        :param float inter_msg_delay: the inter-message delay in seconds (floating point value)

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpTxSocket

            # Set inter-message delay of 10 ms
            socket.set_inter_msg_delay(0.01)
        """
        self._rate_limit.set_inter_msg_delay(inter_msg_delay)

    def remove_inter_msg_delay(self):
        """Remove the inter-message delay.

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpTxSocket

            socket.remove_inter_msg_delay()
        """
        self._rate_limit.remove_inter_msg_delay()

    def get_packets_sent(self):
        """Get count of packets sent.

        :return: The number of packets sent
        :rtype: int

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpTxSocket

            sentcount = socket.get_packets_sent()
        """
        return self._packets_sent

    def reset_packets_sent(self):
        """Reset count of packets sent to 0.

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpTxSocket

            socket.reset_packets_sent()
        """
        self._packets_sent = 0

    def get_bps(self):
        """Get current (measured) bits per second.

        :return: The current bps
        :rtype: float

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpTxSocket

            bps = socket.get_bps()
        """
        return self._rate_limit.get_bps()
