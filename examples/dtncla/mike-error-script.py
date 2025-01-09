# DTN CLA Loopback Test (Multiple Bundles) using configurable (COSMOS) delay
# Includes use of Data Generator, Data Sender, Data Receiver, and Data Interpreter
# Convergence Layer: UDP

# Prerequisites:
# - DTN Gen / DTN CLA packages installed in COSMOS

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

warnings.simplefilter("always")

from dtntools.dtncla.errors.inject import inject_errors
from dtntools.dtncla.udp import UdpRxSocket, UdpTxSocket

print("Set Script Runner line delay")
# set_line_delay(0.000)

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
    payload={"min_size": 32000, "max_size": 32000},
    crc=CRCFlag.CALCULATE,
)

print("Creating the new set of bundles")
generated_bundles = Bundle.generate(
    num_bundles=200,
    pri_settings=primary_block_settings,
    canon_settings=[payload_block_settings],
)

print("Converting bundles to bytes")
bundle_data = [x.to_bytes() for x in generated_bundles]

print("Configuring the Data Sender and Data Receiver")
data_receiver = UdpRxSocket("0.0.0.0", 4556)
data_sender = UdpTxSocket("127.0.0.1", 4556)

try:
    print("Connecting the Data Sender and Data Receiver")
    data_receiver.connect()
    data_sender.connect()

    data_receiver.reset_packets_received()
    data_sender.reset_packets_sent()

    print("Sending the bundles to the DTN Node")
    for x in bundle_data:
        data_sender.write(x)

    print("Receiving the bundles returned from the DTN Node")
    for x in range(1, len(bundle_data) + 1):
        received_bundle = data_receiver.read()
        print(f"Packets received = {data_receiver.get_packets_received()}")

    print(f"Packets sent = {data_sender.get_packets_sent()}")
    assert data_sender.get_packets_sent() == 200
    print(f"Packets received = {data_receiver.get_packets_received()}")
    assert data_receiver.get_packets_received() == 200

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print("Disconnecting the Data Sender and Data Receiver")
    data_receiver.disconnect()
    data_sender.disconnect()
