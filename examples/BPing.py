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

# Ping another DTN Node (30 bundles)
# Convergence Layer: UDP
# This version of the script does NOT work in OpenC3 COSMOS

# Prerequisites:
# - DTN Tools packages installed on the machine that is doing the ping
# - DTN Node configured to receive ping bundles on the REMOTE_PORT listed below
# - DTN Node configured to forward bundles with destination EID = 1.2047 to the
#   IP address of the machine this script is executed on and the LOCAL_PORT listed below

import codecs
import time
import traceback
import warnings

from dtntools.dtngen.blocks import (
    BundleAgeBlock,
    CanonicalBlock,
    CompressedReportingBlock,
    CustodyTransferBlock,
    HopCountBlock,
    PayloadBlock,
    PayloadBlockSettings,
    PrevNodeBlock,
    PrimaryBlock,
    PrimaryBlockSettings,
    UnknownBlock,
)
from dtntools.dtngen.bundle import Bundle
from dtntools.dtngen.types import (
    EID,
    BlockPCFlags,
    BlockType,
    BundlePCFlags,
    CRCFlag,
    CRCType,
    CreationTimestamp,
    CREBData,
    CTEBData,
    HopCountData,
    StatusRRFlags,
    TypeWarning,
)

warnings.simplefilter("always")

remote_node_number = int(input("Select Remote Node Number: "))

print("Define primary and payload blocks")
primary_block_settings = PrimaryBlockSettings(
    version=7,
    control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
    crc_type=CRCType.CRC16_X25,
    dest_eid=EID({"uri": 2, "ssp": {"node_num": remote_node_number, "service_num": 2047}}),
    src_eid=EID({"uri": 2, "ssp": {"node_num": 1, "service_num": 1}}),
    rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 0}}),
    creation_timestamp={
        "time": "current",
        "sequence": {"start": 1},
    },
    lifetime=30000,
    crc=CRCFlag.CALCULATE,
)

payload_block_settings = PayloadBlockSettings(
    blk_type=BlockType.AUTO,
    blk_num=1,
    control_flags=0,
    crc_type=CRCType.CRC16_X25,
    payload={"min_size": 1000, "max_size": 1000},
    crc=CRCFlag.CALCULATE,
)

print("Creating a set of bundles")
generated_bundles = Bundle.generate(
    num_bundles=30,
    pri_settings=primary_block_settings,
    canon_settings=[payload_block_settings],
)

print("Converting bundles to bytes")
bundle_data = [x.to_bytes() for x in generated_bundles]

from dtncla.udp import UdpRxSocket, UdpTxSocket

DTN_IP = input("Enter IP address of DTN to ping (X.X.X.X): ")
DTN_PORT = 4556
LOCAL_IP = "0.0.0.0"
LOCAL_PORT = 4558

print("Configuring the Data Sender and Data Receiver")
data_sender = UdpTxSocket(DTN_IP, DTN_PORT)
data_receiver = UdpRxSocket(LOCAL_IP, LOCAL_PORT)

try:
    print("Connecting the Data Sender and Data Receiver")
    data_receiver.connect()
    data_sender.connect()

    print("BPinging the DTN Node")
    for x in bundle_data:
        data_sender.write(x)
        send_time = time.time()
        
        received_bundle = data_receiver.read(timeout=30)
        receive_time = time.time()

        roundtrip_time = (1000*(receive_time - send_time))

        decoded_bundle = Bundle.from_bytes(received_bundle)
        
        print("Bundle received from", DTN_IP,":",
             "seq=", decoded_bundle.pri_block.creation_timestamp.sequence,
             "rtt=", round(roundtrip_time,3),"ms")
        time.sleep(1)
        
    print(f"Bundles sent = {data_sender.get_packets_sent()}")
    print(f"Bundles received = {data_receiver.get_packets_received()}")
    
except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print("Disconnecting the Data Sender and Data Receiver")
    data_receiver.disconnect()
    data_sender.disconnect()
