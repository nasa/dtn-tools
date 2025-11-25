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
from random import gauss

# mu and sigma values for a normal guassian distribution
_mu = 0
_sigma = 1


def _next_bit(error_rate):
    """Randomly generate the next bit to inject an error into using a guassian distribution.

    :param int error_rate: frequency of bit errors specified as a minimum bit count

    :return: Count of bits until the next error
    :rtype: int

    *Usage:*

    .. code-block:: python

        bit_count = _next_bit(error_rate = 128)
    """
    rnum = abs(gauss(mu=_mu, sigma=_sigma))
    bitstonext = (error_rate * rnum) + error_rate
    return int(bitstonext)


def inject_errors(data_bytes, error_rate, filename=None):
    """Randomly inject bit errors with a guassian distribution into provided data bytes.

    :param bytes data_bytes: The bytes to inject errors into
    :param int error_rate: frequency of bit errors specified as a minimum bit count
    :param string filename: (optional) file to write the corrupted data to

    :return: The corrupted bytes
    :rtype: bytes

    *Usage:*

    .. code-block:: python

        from dtncla.errors.inject import inject_errors
        from dtngen.bundle import Bundle

        mybundle = Bundle.from_bytes_file("orig_bundle.bin")
        data = mybundle.to_bytes()
        error_bytes = inject_errors(data_bytes = data, error_rate = 128, filename="corrupted.bin")
    """
    corrupted = bytearray(data_bytes)
    data_length = len(corrupted)
    curr_bit = 0

    bits_to_next = _next_bit(error_rate)
    byte_to_corrupt = int((curr_bit + bits_to_next) / 8)

    while byte_to_corrupt < data_length:
        bit_to_corrupt = int(bits_to_next % 8)

        corrupted[byte_to_corrupt] = corrupted[byte_to_corrupt] ^ (
            1 << (7 - bit_to_corrupt)
        )

        curr_bit += bits_to_next
        bits_to_next = _next_bit(error_rate)
        byte_to_corrupt = int((curr_bit + bits_to_next) / 8)

    if filename:
        with open(filename, "wb") as bytes_file:
            bytes_file.write(corrupted)

    return bytes(corrupted)
