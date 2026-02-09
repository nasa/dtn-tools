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
import codecs
import subprocess
import time
import traceback

from dtntools.dtncla.errors.inject import inject_errors
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


def create_test_bundle():
    """Create a test bundle."""
    primary_block = PrimaryBlock(
        version=7,
        control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
        crc_type=CRCType.CRC16_X25,
        dest_eid=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
        src_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        creation_timestamp=CreationTimestamp({"time": 755533838904, "sequence": 0}),
        lifetime=3600000,
        crc=b"\x0b\x19",
    )

    prev_node_block = PrevNodeBlock(
        blk_type=BlockType.AUTO,
        blk_num=6,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        prev_eid=EID({"uri": 2, "ssp": {"node_num": 300, "service_num": 2}}),
        crc=CRCFlag.CALCULATE,
    )

    bundle_age_block = BundleAgeBlock(
        blk_type=BlockType.AUTO,
        blk_num=2,
        control_flags=BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC,
        crc_type=CRCType.CRC16_X25,
        bundle_age=108000,
        crc=CRCFlag.CALCULATE,
    )

    hop_count_block = HopCountBlock(
        blk_type=BlockType.AUTO,
        blk_num=3,
        control_flags=BlockPCFlags.FRAG_REPLICATE,
        crc_type=CRCType.CRC16_X25,
        hop_data=HopCountData({"hop_limit": 15, "hop_count": 3}),
        crc=CRCFlag.CALCULATE,
    )

    payload_block = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n",
        crc=CRCFlag.CALCULATE,
    )

    # Use them to create a bundle object
    bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[
            prev_node_block,
            bundle_age_block,
            hop_count_block,
            payload_block,
        ],
    )

    return bundle


# Proc Start here
data_receiver = UdpRxSocket("127.0.0.1", 13704)
data_sender = UdpTxSocket("127.0.0.1", 13704)

try:
    data_receiver.connect()
    data_sender.connect()

    test_bundle = create_test_bundle()
    encoded = test_bundle.to_bytes()

    # Write it to json and binary files
    test_bundle.to_bytes_file("orig_bundle.bin")
    test_bundle.to_json_file("orig_bundle.json")

    corrupt_bundle = inject_errors(
        data_bytes=encoded,
        error_rate=128,
        filename=f"corrupt_bundle_{int(time.time() * 1000)}.bin",
    )

    # Send a bundle to the DTN Node
    print("Sending a corrupted bundle to the DTN Node")
    data_sender.write(corrupt_bundle)

    # Receive a bundle from the DTN Node
    print("Waiting for bundle from the DTN Node")
    rx_bundle = data_receiver.read()

    # Attempt to decode the bundle and output as json - this may not work due to
    # the error bits or will at least have warnings and incorrect data types
    print("Bundle received, attempting to decode")
    decoded_bundle = Bundle.from_bytes(rx_bundle)
    if decoded_bundle:
        print(decoded_bundle.to_json())

    # Save bundle to json file
    if decoded_bundle:
        print("Writing bundle to JSON file")
        decoded_bundle.to_json_file(f"corrupt_bundle_{int(time.time() * 1000)}.json")

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    data_receiver.disconnect()
    data_sender.disconnect()
