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

# DTN Tools Performance Test (250,000 bundles) - Receiving Side
# Demonstrates receiving a set of 250,000 bundles
# Convergence Layer: UDP
# This version of the script works both in OpenC3 COSMOS and from command line

# Prerequisites:
# - DTN Tools packages installed for COSMOS or command line use
# - If running in COSMOS, uncomment the "set_line_delay(0.000)" line
# - Port 4556 is available for use

import time
import traceback
import warnings

from dtntools.dtncla.udp import UdpRxSocket, UdpTxSocket

warnings.simplefilter("always")

# Setting Script Runner line delay (comment out for command line execution)
# set_line_delay(0.000)

print("Configuring the Data Receiver")
data_receiver = UdpRxSocket("0.0.0.0", 4556)

print("Connecting the Data Receiver")
data_receiver.connect()

print("Receiving bundles...")
contact_start = time.time()

try:
    bundles_received = 0
    while bundles_received < 250000:
        data_receiver.read()
        bundles_received = data_receiver.get_packets_received()

    print("Disconnecting the Data Receiver")
    data_receiver.disconnect()

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print(f"Bundles received = {data_receiver.get_packets_received()}")
