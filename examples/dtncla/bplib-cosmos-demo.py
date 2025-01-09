import os
import time
import traceback

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
from dtntools.types import (
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

    # Encode the bundle
    encoded = bundle.to_bytes()
    return encoded


BPNODE_IP = "10.1.1.230"
BPNODE_PORT = 13704
LOCAL_IP = "0.0.0.0"
LOCAL_PORT = 13705

os.system("rm -f /bundles/looped_bundle.json")


# Proc Start here
data_receiver = UdpRxSocket(LOCAL_IP, LOCAL_PORT)
# Create data sender with inter-message delay of 1000 ms
data_sender = UdpTxSocket(BPNODE_IP, BPNODE_PORT, inter_msg_delay=1000)

try:
    wait()

    # Connect the data sender and receiver tools
    data_receiver.connect()
    data_sender.connect()

    # Uncomment this to get an unexpired bundle using the bplib CLI
    # incoming = data_receiver.read()
    # with open("/bundles/original_bundle.json", "w") as f:
    #     b = Bundle.from_bytes(incoming)
    #     f.write(b.to_json())
    #     raise RuntimeError("Purposely aborting")

    # Load a bundle from file
    #    original_bundle = Bundle.from_json_file("/bundles/original_bundle.json").to_bytes()
    original_bundle = create_test_bundle()

    # Send the bundles to BPNode, we are expecting it to be returned to us because
    # bpnode is configured to route this bundle back to us
    print("Sending Five bundles to the DTN Node")
    for _ in range(5):
        data_sender.write(original_bundle)

    # Receive bundles from the DTN Node
    print("Waiting for bundles to be looped back from the DTN Node")
    for _ in range(5):
        rx_bundle = data_receiver.read()

    # set rate limit
    print("Setting rate limit of 500 bps without clearing the inter-message delay")
    data_sender.set_rate_limit(500)

    print("Sending Five bundles to the DTN Node")
    for _ in range(5):
        data_sender.write(original_bundle)

    # Receive bundles from the DTN Node
    print("Waiting for bundles to be looped back from the DTN Node")
    for _ in range(5):
        rx_bundle = data_receiver.read()

    # Remove the limits
    print("Removing the rate limit and inter-message delay")
    data_sender.remove_inter_msg_delay()
    data_sender.remove_rate_limit()

    print("Sending Five bundles to the DTN Node")
    for _ in range(5):
        data_sender.write(original_bundle)

    # Receive bundles from the DTN Node
    print("Waiting for bundles to be looped back from the DTN Node")
    for _ in range(5):
        rx_bundle = data_receiver.read()

    # Decode the bundle and print as json
    print("Bundle received from Node, attempting to decode")
    decoded_bundle = Bundle.from_bytes(rx_bundle)
    if decoded_bundle:
        print(decoded_bundle.to_json())

    # Save bundle to json file
    if decoded_bundle:
        print("Writing bundle to JSON file")
        decoded_bundle.to_json_file(f"/bundles/looped_bundle.json")

    print(f"Packets sent = {data_sender.get_packets_sent()}")
    print(f"Packets received = {data_receiver.get_packets_received()}")

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    data_sender.remove_inter_msg_delay()
    data_sender.remove_rate_limit()
    data_receiver.disconnect()
    data_sender.disconnect()
