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

# DTN Tools Concurrent Contact Test - Contact 2 Sender
# Demonstrates support of concurrent contacts for a DTN implementation configured as a Relay Node
# Convergence Layer: UDP
# This script does NOT work in OpenC3 COSMOS

# Prerequisites:
# - DTN Tools packages installed for command line use
# - Remote IP address placeholder in the script replaced with actual IP address of DTN implementation
# - DTN implementation configured to receive on port 4559

import codecs
import time
import traceback
import warnings

from dtntools.dtncla.udp import UdpRxSocket, UdpTxSocket
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

# Setting Script Runner line delay (comment out for command line execution)
# set_line_delay(0.000)

print("Contact #2: Defining new primary and payload blocks")
primary_block_settings = PrimaryBlockSettings(
    version=7,
    control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
    crc_type=CRCType.CRC16_X25,
    dest_eid=EID({"uri": 2, "ssp": {"node_num": 101, "service_num": 2}}),
    src_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 2}}),
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
    payload={"min_size": 4000, "max_size": 4000},
    crc=CRCFlag.CALCULATE,
)

print("Contact #2: Creating the new set of bundles")
generated_bundles = Bundle.generate(
    num_bundles=40,
    pri_settings=primary_block_settings,
    canon_settings=[payload_block_settings],
)

print("Contact #2: Converting bundles to bytes")
bundle_data_1 = [x.to_bytes() for x in generated_bundles]
bundle_data_2 = [x.to_bytes() for x in generated_bundles]

print("Contact #2: Configuring the Data Sender")
data_sender = UdpTxSocket("X.X.X.X", 4559, bps_limit=40000000)

try:
    print("Contact #2: Connecting the Data Sender")
    data_sender.connect()

    loop1 = 0
    Start_Time = time.ctime()
    print(f"Contact #2: Sending Start Time = {Start_Time}")

    print("Contact #2: Sending bundles....")
    while loop1 < 1000:
        loop1 = loop1 + 1

        for x in bundle_data_1:
            data_sender.write(x)

    time.sleep(45)

    data_sender.set_bps_limit(30000000)
    loop2 = 0

    while loop2 < 500:
        loop2 = loop2 + 1

        for y in bundle_data_2:
            data_sender.write(y)

    End_Time = time.ctime()
    print(f"Contact #2: Sending End Time = {End_Time}")

    time.sleep(5)

    print(f"Contact #2: Packets sent = {data_sender.get_packets_sent()}")

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print("Contact #2: Disconnecting the Data Sender")
    data_sender.disconnect()
