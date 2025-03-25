# DTN Tools Performance Test (250,000 bundles) - Sending Side
# Demonstrates sending a set of 50 bundles 5000 times with rate limiting
# Convergence Layer: UDP
# This version of the script does NOT work in OpenC3 COSMOS

# Prerequisites:
# - DTN Tools packages installed for command line use

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

print("Defining new primary and payload blocks")
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

payload_size = int(input("Choose payload size (in bytes): "))

payload_block_settings = PayloadBlockSettings(
    blk_type=BlockType.AUTO,
    blk_num=1,
    control_flags=0,
    crc_type=CRCType.CRC16_X25,
    payload={"min_size": payload_size, "max_size": payload_size},
    crc=CRCFlag.CALCULATE,
)

print("Creating the new set of bundles")
generated_bundles = Bundle.generate(
    num_bundles=50,
    pri_settings=primary_block_settings,
    canon_settings=[payload_block_settings],
)

print("Converting bundles to bytes")
bundle_data = [x.to_bytes() for x in generated_bundles]

print("Configuring the Data Sender")
send_to_ip = input("Enter IP address to send to (X.X.X.X): ")
rate_limit = int(input("Choose rate limit (in Mbps): "))
data_sender = UdpTxSocket(send_to_ip, 4556, bps_limit=(1000000 * rate_limit))

try:
    print("Connecting the Data Sender")
    data_sender.connect()

    loops = 0
    Start_Time = time.time()
    print(f"Sending Start Time = {Start_Time}")

    print("Sending bundles....")
    while loops < 5000:
        loops = loops + 1

        for x in bundle_data:
            data_sender.write(x)

    End_Time = time.time()
    print(f"Sending End Time = {End_Time}")

    time.sleep(5)

    print(f"Packets sent = {data_sender.get_packets_sent()}")

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print("Disconnecting the Data Sender")
    data_sender.disconnect()
