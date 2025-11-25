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

from dtntools.dtncla.udp import UdpRxSocket
from dtntools.dtngen.bundle import Bundle

LOCAL_IP = "127.0.0.1"
LOCAL_PORT = 13708

data_receiver = UdpRxSocket(LOCAL_IP, LOCAL_PORT)
data_receiver.connect()

packets = []

print("Listening for packets.")
try:
    last_cnt = data_receiver.get_packets_received()
    print("Start sender within 10 seconds...")
    time.sleep(10)

    print(
        "Receiver will stop once packets stop being received for 5 seconds. Press ctrl-c to stop early."
    )
    while last_cnt != data_receiver.get_packets_received():
        last_cnt = data_receiver.get_packets_received()
        print(last_cnt)
        packets = packets + data_receiver.read_all()
        time.sleep(10)

except KeyboardInterrupt:
    pass

finally:
    # Get any straggler packets
    packets = packets + data_receiver.read_all()

    print(f"\npackets received = {data_receiver.get_packets_received()}")
    print(f"packets count = {len(packets)}")
    data_receiver.disconnect()
    if len(packets) > 0:
        bundle = Bundle.from_bytes(packets[len(packets) - 1])
        print(f"bundle = {bundle}")
