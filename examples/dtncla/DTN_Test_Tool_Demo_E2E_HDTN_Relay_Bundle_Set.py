# DTN Gen / DTN CLA End To End Test (Multiple Bundles) using HDTN as a Relay Node
# Includes use of Data Generator, Data Sender, Data Receiver, and Data Interpreter
# Demonstrates how to modify individual bundles in a set of bundles
# Convergence Layer: UDP

# Prerequisites:
# - DTN Gen / DTN CLA packages installed in COSMOS
# - HDTN running in relay mode (UDP) - configuration file: hdtn_udp_relay.json
# - Wireshark is capturing traffic on ports 4556 and 4558

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
        "time": {"start": 755533838904, "increment": 256},
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
    payload={"min_size": 48000, "max_size": 48000},
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


# SECTION 2: Sending the new bundles to HDTN and receiving them back from HDTN

from dtncla.udp import UdpRxSocket, UdpTxSocket

HDTN_IP = "10.2.13.191"
HDTN_PORT = 4556
LOCAL_IP = "0.0.0.0"
LOCAL_PORT = 4558

print("Configuring the Data Sender and Data Receiver")
data_sender = UdpTxSocket(HDTN_IP, HDTN_PORT)
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
