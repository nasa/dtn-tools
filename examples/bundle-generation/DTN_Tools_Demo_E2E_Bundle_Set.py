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

# DTN Tools End To End Test (50 Bundles) using a DTN implementation configured as a Relay Node
# Demonstrates how to modify individual bundles in a set of bundles
# Demonstrates generation and of both valid (48) and invalid (2) bundles of different sizes
# Convergence Layer: UDP

# Prerequisites:
# - DTN Tools packages installed in COSMOS or for command line use
# - A "bundles" folder for storing bundles exists (modify path in the script as needed)
# - If the script is running from COSMOS, the "bundles" folder has been mapped in compose.yaml
# - Remote IP address placeholder in the script replaced with actual IP address of DTN implementation
# - DTN implementation configured to receive on port 4556, and send bundles back on port 4558

import codecs
import subprocess
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

# SECTION 1: Creating a new set of bundles


warnings.simplefilter("always")

print("Define new primary and payload blocks")
primary_block_settings = PrimaryBlockSettings(
    version=7,
    control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
    crc_type=CRCType.CRC16_X25,
    dest_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 1}}),
    src_eid=EID({"uri": 2, "ssp": {"node_num": 101, "service_num": 1}}),
    rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
    creation_timestamp={
        "time": "current",
        "sequence": {"start": 0},
    },
    lifetime=3600000,
    crc=CRCFlag.CALCULATE,
)

payload_block_settings = PayloadBlockSettings(
    blk_type=BlockType.AUTO,
    blk_num=1,
    control_flags=0,
    crc_type=CRCType.CRC16_X25,
    payload={"min_size": 700, "max_size": 1300},
    crc=CRCFlag.CALCULATE,
)

print("Creating the new set of bundles")
generated_bundles = Bundle.generate(
    num_bundles=50,
    pri_settings=primary_block_settings,
    canon_settings=[payload_block_settings],
)

print("Writing the generated bundles to json files")
for idx, x in enumerate(generated_bundles):
    print(x.to_json_file(f"/bundles/generated_bundle_{idx+1}.json"))

print("Modifying one bundle in the set")
generated_bundles[19].pri_block.lifetime = 1800000
generated_bundles[19].pri_block.crc = CRCFlag.CALCULATE

print("Making two bundles in the set invalid")
generated_bundles[4].pri_block.version = 5
generated_bundles[4].pri_block.crc = CRCFlag.CALCULATE
generated_bundles[34].canon_blocks[0].blk_num = "BAD"
generated_bundles[34].canon_blocks[0].crc = CRCFlag.CALCULATE

print("Writing the modified bundles to json files")
generated_bundles[4].to_json_file("/bundles/modified_bundle_5.json")
generated_bundles[19].to_json_file("/bundles/modified_bundle_20.json")
generated_bundles[34].to_json_file("/bundles/modified_bundle_35.json")

print("Converting bundles to bytes")
bundle_data = [x.to_bytes() for x in generated_bundles]


# SECTION 2: Sending the new bundles to DTN Node and receiving them back

from dtntools.dtncla.udp import UdpRxSocket, UdpTxSocket

REMOTE_IP = "X.X.X.X"
REMOTE_PORT = 4556
LOCAL_IP = "0.0.0.0"
LOCAL_PORT = 4558

print("Configuring the Data Sender and Data Receiver")
data_sender = UdpTxSocket(REMOTE_IP, REMOTE_PORT)
data_receiver = UdpRxSocket(LOCAL_IP, LOCAL_PORT)

try:
    print("Connecting the Data Sender and Data Receiver")
    data_receiver.connect()
    data_sender.connect()

    print("Sending the bundles to the DTN Node")
    for x in bundle_data:
        data_sender.write(x)

    print("Receiving the bundles returned from the DTN Node")
    for x in range(len(bundle_data)):
        received_bundle = data_receiver.read(timeout=5)

    print(f"Packets sent = {data_sender.get_packets_sent()}")
    assert data_sender.get_packets_sent() == 50
    print(f"Packets received = {data_receiver.get_packets_received()}")
    assert data_receiver.get_packets_received() == 48

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print("Disconnecting the Data Sender and Data Receiver")
    data_receiver.disconnect()
    data_sender.disconnect()
