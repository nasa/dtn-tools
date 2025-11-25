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
import time


class RateLimit:
    """Class to perform rate-limiting on a CLA."""

    SLEEP_INCR_DFL = 0.001  # seconds

    def __init__(self, bps_limit=None, inter_msg_delay=None, sleep_incr=None):
        """Initialize the rate limiter.

        :param int bps_limit: (optional) the bit-rate limit in bits per second
        :param float inter_msg_delay: (optional) the inter-message delay in seconds
        :param float sleep_incr: (optional) the time to sleep when sleeping

        *Usage:*

        .. code-block:: python

            from dtncla.udp import UdpRxSocket

            ratelimiter = RateLimit(bps_limit=500e6, inter_msg_delay=0.01, sleep_incr = 0.005)
        """
        self._bps_limit = bps_limit
        self._inter_msg_delay = inter_msg_delay
        self._sleep_incr = sleep_incr

        if not self._sleep_incr:
            self._sleep_incr = RateLimit.SLEEP_INCR_DFL
        self._reset_counting_state()

    def _reset_counting_state(self):
        self._first_run = time.time()
        self._bytes_sent = 0
        self._last_time = 0
        self._bps_curr = 0

    def update(self, bytes_sent):
        """Update the total bytes sent count, bps and last packet time.

        :param int bytes_sent: the number of bytes that were sent

        *Usage:*

        .. code-block:: python

            from .rate_limit import RateLimit

            rate_limit.update(bytes_sent_count)
        """
        self._bytes_sent += bytes_sent
        self._bps_curr = (self._bytes_sent * 8) / (time.time() - self._first_run)
        if self._inter_msg_delay:
            self._last_time = time.time()

    def wait(self, packet_size):
        """Wait until bps and/or inter-message delay limits are met.

        :param int packet_size: the number of bytes that will be sent

        *Usage:*

        .. code-block:: python

            from .rate_limit import RateLimit

            rate_limit.wait(packet_size)
        """
        ctime = time.time()

        if self._bps_limit:
            # Wait until the bit rate after sending the packet, will be below
            # the threshold
            offset_bits_sent = (self._bytes_sent + packet_size) * 8

            offset_bps = offset_bits_sent / (ctime - self._first_run)
            while offset_bps > self._bps_limit:
                time.sleep(self._sleep_incr)
                ctime = time.time()
                offset_bps = offset_bits_sent / (ctime - self._first_run)

        if self._inter_msg_delay:
            # Wait until the time since the last packet is greater than the
            # inter-message delay
            while ctime - self._last_time < self._inter_msg_delay:
                time.sleep(self._sleep_incr)
                ctime = time.time()

    def set_bps_limit(self, bps_limit):
        """Set a bit-rate limit.

        :param int bps_limit: the bit-rate limit in bits per second

        *Usage:*

        .. code-block:: python

            from .rate_limit import RateLimit

            rate_limit = RateLimit()

            # Set bit rate limit to 500 Mbps
            rate_limit.set_bps_limit(500e6)
        """
        self._bps_limit = bps_limit
        self._reset_counting_state()

    def remove_bps_limit(self):
        """Remove the bit-rate limit.

        *Usage:*

        .. code-block:: python

            from .rate_limit import RateLimit

            rate_limit = RateLimit(bps_limit = 500e6)
            rate_limit.remove_bps_limit()
        """
        self._bps_limit = None
        self._reset_counting_state()

    def set_inter_msg_delay(self, inter_msg_delay):
        """Set the inter-message delay.

        :param float inter_msg_delay: the inter-message delay in seconds (floating point value)

        *Usage:*

        .. code-block:: python

            from .rate_limit import RateLimit

            rate_limit = RateLimit()

            # Set inter-message delay of 10ms
            rate_limit.set_inter_msg_delay(0.01)
        """
        self._inter_msg_delay = inter_msg_delay
        self._reset_counting_state()

    def remove_inter_msg_delay(self):
        """Remove the inter-message delay.

        *Usage:*

        .. code-block:: python

            from .rate_limit import RateLimit

            rate_limit = RateLimit(inter_msg_delay = 0.01)
            rate_limit.remove_inter_msg_delay()
        """
        self._inter_msg_delay = None
        self._reset_counting_state()

    def get_bps(self):
        """Get current (measured) bits per second.

        :return: The current bps
        :rtype: float

        *Usage:*

        .. code-block:: python

            from .rate_limit import RateLimit

            rate_limit = RateLimit(bps_limit = 500e6)
            bps = rate_limit.get_bps()
        """
        return self._bps_curr
