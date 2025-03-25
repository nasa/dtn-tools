# DTN Tools End To End Test (Single Bundle) using a DTN implementation configured as a Relay Node
# Demonstrates bundle creation, CBOR encoding, conversion to readable format, and verification of block elements
# Convergence Layer: UDP

# Prerequisites:
# - DTN Tools packages installed in COSMOS or for command line use
# - A "bundles" folder for storing bundles exists (modify path in the script as needed)
# - If the script is running from COSMOS, the "bundles" folder has been mapped in compose.yaml
# - Remote IP address placeholder in the script replaced with actual IP address of DTN implementation
# - DTN implementation configured to receive on port 4556, and send bundles back on port 4558

import codecs
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
    StatusRRFlags,
    TypeWarning,
)

# SECTION 1: Creating a new bundle


os.system("rm -f /bundles/original_bundle.json")

print("Define new primary, hop count, and payload blocks")
primary_block = PrimaryBlock(
    version=7,
    control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
    crc_type=CRCType.CRC16_X25,
    dest_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 1}}),
    src_eid=EID({"uri": 2, "ssp": {"node_num": 101, "service_num": 1}}),
    rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
    creation_timestamp=CreationTimestamp({"time": 795715474411, "sequence": 0}),
    lifetime=1577880000000,
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

print("Creating the original bundle")
bundle = Bundle(
    pri_block=primary_block,
    canon_blocks=[hop_count_block, payload_block],
)

print("Encoding the original bundle")
original_bundle = bundle.to_bytes()

print("Decoding the original bundle")
decoded_bundle = Bundle.from_bytes(original_bundle)

if decoded_bundle:
    print("Writing original bundle to JSON file")
    decoded_bundle.to_json_file(f"/bundles/original_bundle.json")


# SECTION 2: Sending the new bundles to DTN Node and receiving them back

from dtntools.dtncla.udp import UdpRxSocket, UdpTxSocket

REMOTE_IP = "X.X.X.X"
REMOTE_PORT = 4556
LOCAL_IP = "0.0.0.0"
LOCAL_PORT = 4558

os.system("rm -f /bundles/looped_bundle.json")

print("Configuring the Data Sender and Data Receiver")
data_sender = UdpTxSocket(REMOTE_IP, REMOTE_PORT)
data_receiver = UdpRxSocket(LOCAL_IP, LOCAL_PORT)

try:
    print("Connecting the Data Sender and Data Receiver")
    data_receiver.connect()
    data_sender.connect()

    print("Sending the bundle to the DTN Node")
    data_sender.write(original_bundle)

    print("Waiting for the bundle to be looped back from the DTN Node")
    rx_bundle = data_receiver.read()

    print("Bundle received from Node, attempting to decode")
    decoded_bundle = Bundle.from_bytes(rx_bundle)
    if decoded_bundle:
        print(decoded_bundle.to_json())

    if decoded_bundle:
        print("Writing looped back bundle to JSON file")
        decoded_bundle.to_json_file(f"/bundles/looped_bundle.json")

    print(f"Packets sent = {data_sender.get_packets_sent()}")
    print(f"Packets received = {data_receiver.get_packets_received()}")

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print("Disconnecting the Data Sender and Data Receiver")
    data_receiver.disconnect()
    data_sender.disconnect()


# SECTION 3: Verifying the received bundle

print("Verifying the received Primary block")
assert decoded_bundle.pri_block.version == 7
assert decoded_bundle.pri_block.control_flags == BundlePCFlags.MUST_NOT_FRAGMENT
assert decoded_bundle.pri_block.crc_type == CRCType.CRC16_X25
assert decoded_bundle.pri_block.dest_eid.uri == 2
assert decoded_bundle.pri_block.dest_eid.ssp["node_num"] == 103
assert decoded_bundle.pri_block.dest_eid.ssp["service_num"] == 1
assert decoded_bundle.pri_block.src_eid.uri == 2
assert decoded_bundle.pri_block.src_eid.ssp["node_num"] == 101
assert decoded_bundle.pri_block.src_eid.ssp["service_num"] == 1
assert decoded_bundle.pri_block.rpt_eid.uri == 2
assert decoded_bundle.pri_block.rpt_eid.ssp["node_num"] == 100
assert decoded_bundle.pri_block.rpt_eid.ssp["service_num"] == 1
assert decoded_bundle.pri_block.creation_timestamp.time == 795715474411
assert decoded_bundle.pri_block.creation_timestamp.sequence == 0
assert decoded_bundle.pri_block.lifetime == 1577880000000
assert decoded_bundle.pri_block.crc == b"\x03\x20"

print("Verifying the received Hop Count block")
assert decoded_bundle.canon_blocks[1].blk_type == BlockType.HOP_COUNT
assert decoded_bundle.canon_blocks[1].blk_num == 3
assert decoded_bundle.canon_blocks[1].control_flags == BlockPCFlags.FRAG_REPLICATE
assert decoded_bundle.canon_blocks[1].crc_type == CRCType.CRC16_X25
assert decoded_bundle.canon_blocks[1].hop_data.hop_limit == 15
assert decoded_bundle.canon_blocks[1].hop_data.hop_count == 4
assert decoded_bundle.canon_blocks[1].crc == b"\xaf\x32"

print("Verifying the received Payload block")
assert decoded_bundle.canon_blocks[2].blk_type == BlockType.BUNDLE_PAYLOAD
assert decoded_bundle.canon_blocks[2].blk_num == 1
assert decoded_bundle.canon_blocks[2].control_flags == 0
assert decoded_bundle.canon_blocks[2].crc_type == CRCType.CRC16_X25
assert (
    decoded_bundle.canon_blocks[2].payload
    == b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n"
)
bplib_payload_str = decoded_bundle.canon_blocks[2].payload[8:].decode().strip()
assert bplib_payload_str == "hello world"
assert decoded_bundle.canon_blocks[2].crc == b"\x7a\x2f"
