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
"""
***********************************************************************
** Sends bundles to and receives bundles from HDTN Node 2 for Contact 2
***********************************************************************
"""
load_utility(f"<%= target_name %>/procedures/build_tests/dtngen_utils.py")
from dtncla.udp import UdpRxSocket, UdpTxSocket

dest_ip = "X.X.X.X"
dest_port = 4558
local_ip = "0.0.0.0"
local_port = 4559

num_bundles = 50

print("Configuring/connecting Data Sender and Data Receiver")
data_sender = UdpTxSocket(dest_ip, dest_port)
data_receiver = UdpRxSocket(local_ip, local_port)

data_sender.connect()
data_receiver.connect()

print(f"Sending {num_bundles} bundles to HDTN Node 2 dest 103")
DTNGenUtils.send_bundles(num_bundles, 103, data_sender)

print("Receiving bundles returned from HDTN Node 2")
DTNGenUtils.receive_bundles(num_bundles, data_receiver)

print("Disconnecting Data Sender and Data Receiver")
data_receiver.disconnect()
data_sender.disconnect()
