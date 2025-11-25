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

# DTN Tools Concurrent Contact Test - Contact 2 Receiver
# Demonstrates support of concurrent contacts for a DTN implementation configured as a Relay Node
# Convergence Layer: UDP
# This script does NOT work in OpenC3 COSMOS

# Prerequisites:
# - DTN Tools packages installed for command line use
# - DTN implementation configured to send to port 4557 on the machine this script is executed from

import time
import traceback
import warnings

from dtntools.dtncla.udp import UdpRxSocket, UdpTxSocket

warnings.simplefilter("always")

# Setting Script Runner line delay (comment out for command line execution)
# set_line_delay(0.000)

print("Contact #2: Configuring the Data Receiver")
data_receiver = UdpRxSocket("0.0.0.0", 4557)

print("Contact #2: Connecting the Data Receiver")
data_receiver.connect()

print("Contact #2: Receiving bundles...")
contact_start = time.time()

try:
    while time.time() < contact_start + 150:
        print(f"Contact #2: {data_receiver.get_packets_received()}")
        data_receiver.read_all()
        time.sleep(10)

    print("Contact #2: Disconnecting the Data Receiver")
    data_receiver.disconnect()

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print(f"Contact #2: Bundles received = {data_receiver.get_packets_received()}")
