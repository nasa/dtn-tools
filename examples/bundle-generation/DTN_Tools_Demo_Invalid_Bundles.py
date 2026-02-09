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

# DTN Tools End To End Test (Off-nominal Bundles) using a DTN implementation configured as a Relay Node
# Demonstrates various ways to create invalid bundles
# Convergence Layer: UDP

# Prerequisites:
# - DTN Tools packages installed in COSMOS or for command line use
# - Remote IP address placeholder in the script replaced with actual IP address of DTN implementation
# - DTN implementation configured to receive on port 4556, and send bundles back on port 4558

import codecs
import copy
import os
import time
import traceback

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
    InvalidCBOR,
    RawData,
    StatusRRFlags,
    TypeWarning,
)
from dtntools.dtngen.utils import DtnTimeNowMs
from dtntools.dtncla.udp import UdpRxSocket, UdpTxSocket
from dtntools.dtncla.errors.inject import inject_errors

# SECTION 1: Creating test bundles

print("Defining valid bundle blocks")
primary_block = PrimaryBlock(
    version=7,
    control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
    crc_type=CRCType.CRC16_X25,
    dest_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 1}}),
    src_eid=EID({"uri": 2, "ssp": {"node_num": 101, "service_num": 1}}),
    rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 0}}),
    creation_timestamp=CreationTimestamp({"time": DtnTimeNowMs(), "sequence": 0}),
    lifetime=3600000,
    crc=CRCFlag.CALCULATE,
)

prev_node_block = PrevNodeBlock(
    blk_type=BlockType.AUTO,
    blk_num=2,
    control_flags=0,
    crc_type=CRCType.NONE,
    prev_eid=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
)

bundle_age_block = BundleAgeBlock(
    blk_type=BlockType.AUTO,
    blk_num=3,
    control_flags=BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC,
    crc_type=CRCType.NONE,
    bundle_age=108000,
)

hop_count_block = HopCountBlock(
    blk_type=BlockType.AUTO,
    blk_num=4,
    control_flags=BlockPCFlags.FRAG_REPLICATE,
    crc_type=CRCType.NONE,
    hop_data=HopCountData({"hop_limit": 15, "hop_count": 3}),
)

unknown_block = UnknownBlock(
    elements=
    [
        73,
        5,
        0,
        1,
        b'\x82\x02\x82\x18\x64\x0a',
        b'\x0c\x71'
    ]
)

payload_block = PayloadBlock(
    blk_type=BlockType.AUTO,
    blk_num=1,
    control_flags=0,
    crc_type=CRCType.CRC16_X25,
    payload=b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n",
    crc=CRCFlag.CALCULATE,
)

print("Defining invalid bundle blocks")
# Primary block with invalid BP version
primary_block_bad = PrimaryBlock(
    version=7.0,
    control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
    crc_type=CRCType.CRC16_X25,
    dest_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 1}}),
    src_eid=EID({"uri": 23, "ssp": {"node_num": 101, "service_num": 1}}),
    rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 0}}),
    creation_timestamp=CreationTimestamp({"time": DtnTimeNowMs(), "sequence": 0}),
    lifetime=3600000,
    crc=CRCFlag.CALCULATE,
)

# Primary block that will be used to introduce bad CBOR
primary_block_bad_CBOR = PrimaryBlock(
    version=7,
    control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
    crc_type=CRCType.CRC16_X25,
    dest_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 1}}),
    src_eid=EID({"uri": 23, "ssp": {"node_num": 101, "service_num": 1}}),
    rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 0}}),
    creation_timestamp=CreationTimestamp({"time": DtnTimeNowMs(), "sequence": 0}),
    lifetime=3600000,
    crc=CRCFlag.CALCULATE,
)

# Canonical block with incorrect number of elements
block_with_extra_element = UnknownBlock(
    elements=
    [
        73,
        5,
        0,
        1,
        2,
        b'\x82\x02\x82\x18\x64\x0a',
        b'\x0c\x71'
    ]
)

# Previous Node block with invalid control flags
prev_node_block_bad = PrevNodeBlock(
    blk_type=BlockType.AUTO,
    blk_num=2,
    control_flags=-20,
    crc_type=CRCType.NONE,
    prev_eid=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
)

# Payload block with invalid block number
payload_block_bad = PayloadBlock(
    blk_type=BlockType.AUTO,
    blk_num=22,
    control_flags=0,
    crc_type=CRCType.CRC16_X25,
    payload=b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n",
    crc=CRCFlag.CALCULATE,
)

print("Creating a nominal bundle containing all defined nominal blocks")
nominal_bundle = Bundle(
    pri_block=primary_block,
    canon_blocks=[
        prev_node_block,
        bundle_age_block,
        hop_count_block,
        unknown_block,
        payload_block,
    ],
)

test_bundle_1 = nominal_bundle.to_bytes()

print("Creating a bundle with random data and writing it to file")
test_bundle_2 = Bundle.generate_random(size=1095, filename='bundles/test_bundle_2')

print("Creating a bundle with invalid CBOR")
# Creating a bad CBOR encoded bundle block by modifying an existing block
orig_lifetime = primary_block_bad_CBOR.lifetime
primary_block_bad_CBOR.lifetime = InvalidCBOR(value=orig_lifetime, additional_info=31)

# Creating a bundle object
bad_cbor_bundle = Bundle(
    pri_block=copy.deepcopy(primary_block_bad_CBOR),
    canon_blocks=[
        prev_node_block,
        bundle_age_block,
        hop_count_block,
        unknown_block,
        payload_block,
    ],
)

# Encoding it to bytes, which contains the invalid CBOR encoding
test_bundle_3 = bad_cbor_bundle.to_bytes()
    
print("Creating a bundle with less than two CBOR blocks")
primary_only = Bundle(pri_block=primary_block)
test_bundle_4 = primary_only.to_bytes()

print("Creating a bundle with an extra CBOR element")
block_with_extra_element_bundle = Bundle(
    pri_block=primary_block,
    canon_blocks=[
        prev_node_block,
        bundle_age_block,
        hop_count_block,
        block_with_extra_element,
        payload_block,
    ],
)

test_bundle_5 = block_with_extra_element_bundle.to_bytes()

print("Creating a bundle with the payload block in the wrong position")
out_of_order_bundle = Bundle(
    pri_block=primary_block,
    canon_blocks=[
        prev_node_block,
        bundle_age_block,
        payload_block,
        hop_count_block,
        unknown_block,
        payload_block,
    ],
)
test_bundle_6 = out_of_order_bundle.to_bytes()

print("Creating a bundle with invalid primary block")
nominal_bundle = Bundle(
    pri_block=primary_block_bad,
    canon_blocks=[
        prev_node_block,
        bundle_age_block,
        hop_count_block,
        unknown_block,
        payload_block,
    ],
)

test_bundle_7 = nominal_bundle.to_bytes()

print("Creating a bundle with invalid previous node block")
nominal_bundle = Bundle(
    pri_block=primary_block,
    canon_blocks=[
        prev_node_block_bad,
        bundle_age_block,
        hop_count_block,
        unknown_block,
        payload_block,
    ],
)

test_bundle_8 = nominal_bundle.to_bytes()

print("Creating a bundle with invalid payload block")
nominal_bundle = Bundle(
    pri_block=primary_block,
    canon_blocks=[
        prev_node_block,
        bundle_age_block,
        hop_count_block,
        unknown_block,
        payload_block_bad,
    ],
)

test_bundle_9 = nominal_bundle.to_bytes()

print("Creating a bundle with random errors")
valid_bundle = nominal_bundle.to_bytes()
test_bundle_10 = inject_errors(data_bytes = valid_bundle, error_rate = 256)

   
# SECTION 2: Sending bundles to DTN Node and receiving them back

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

    print("Sending valid and invalid bundles to the DTN Node")

    data_sender.write(test_bundle_1)
    data_sender.write(test_bundle_2)
    data_sender.write(test_bundle_1)
    data_sender.write(test_bundle_3)
    data_sender.write(test_bundle_1)
    data_sender.write(test_bundle_4)
    data_sender.write(test_bundle_1)
    data_sender.write(test_bundle_5)
    data_sender.write(test_bundle_1)
    data_sender.write(test_bundle_6)
    data_sender.write(test_bundle_1)
    data_sender.write(test_bundle_7)
    data_sender.write(test_bundle_1)
    data_sender.write(test_bundle_8)
    data_sender.write(test_bundle_1)
    data_sender.write(test_bundle_9)
    data_sender.write(test_bundle_1)
    data_sender.write(test_bundle_10)
    data_sender.write(test_bundle_1)

    print("Receiving bundles from the DTN Node")
    rx_bundles = data_receiver.read_all()
    time.sleep(1)

    print(f"Packets sent = {data_sender.get_packets_sent()}")
    assert data_sender.get_packets_sent() == 19
    print(f"Packets received = {data_receiver.get_packets_received()}")
    assert data_receiver.get_packets_received() == 10
    

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print("Disconnecting the Data Sender and Data Receiver")
    data_receiver.disconnect()
    data_sender.disconnect()

