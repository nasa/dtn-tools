import codecs

from dtngen import (
    EID,
    BlockPCFlags,
    BlockType,
    Bundle,
    BundleAgeBlock,
    BundlePCFlags,
    CRCFlag,
    CRCType,
    CreationTimestamp,
    HopCountBlock,
    PayloadBlock,
    PrevNodeBlock,
    PrimaryBlock,
)


def recv_candidate_bundle():
    """Simulate receiving a bundle from the network.

    .. note::
        This is a known-valid bundle.  It is being used in place of a data-receiver call so that bundle interpreter functionality can be demonstrated.
    """
    bplib_sample_bundle = "9f8907040182028218c801820282186401820282186401821b000000afe9537a38001a0036ee80420b19861849184900014682028218640a426747860101000154000000000000000c68656c6c6f20776f726c640a427a2fff"

    return bytes.fromhex(bplib_sample_bundle)


# Proc Start ###################################################################

# Step 1: "Receive" a Bundle from the data receiver tool
candidate_bundle = recv_candidate_bundle()

# Print the encoded bundle as a hex string
print(f'Original bundle:\n{codecs.encode(candidate_bundle,"hex")}\n')


# Step 2: Attempt to cbor decode the payload using the interpreter
bundle = Bundle.from_bytes(candidate_bundle)
if not bundle:
    raise ValueError("Bundle could not be parsed.")


# Step 3: Access fields within the bundle as required by the test
# Parsing Primary block
assert bundle.pri_block.version == 7
assert bundle.pri_block.control_flags == 4

# Parsing the payload
bplib_payload_str = bundle.canon_blocks[0].payload[8:].decode().strip()
assert bplib_payload_str == "hello world"


# Step 4: Re-encode the bundle
encoded = bundle.to_bytes()

# Print the encoded bundle as a hex string
print(f'Original Re-encoded:\n{codecs.encode(encoded,"hex")}\n')


# Step 5: Define new primary and canonical blocks
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
    blk_type=BlockType.PREVIOUS_NODE,
    blk_num=1,
    control_flags=0,
    crc_type=CRCType.CRC16_X25,
    prev_eid=EID({"uri": 2, "ssp": {"node_num": 300, "service_num": 2}}),
    crc=CRCFlag.CALCULATE,
)

bundle_age_block = BundleAgeBlock(
    blk_type=BlockType.BUNDLE_AGE,
    blk_num=2,
    control_flags=BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC,
    crc_type=CRCType.CRC16_X25,
    bundle_age=108000,
    crc=CRCFlag.CALCULATE,
)

hop_count_block = HopCountBlock(
    blk_type=BlockType.HOP_COUNT,
    blk_num=3,
    control_flags=BlockPCFlags.FRAG_REPLICATE,
    crc_type=CRCType.CRC16_X25,
    hop_limit=15,
    hop_count=3,
    crc=CRCFlag.CALCULATE,
)

payload_block = PayloadBlock(
    blk_type=BlockType.BUNDLE_PAYLOAD,
    blk_num=4,
    control_flags=0,
    crc_type=CRCType.CRC16_X25,
    payload=b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n",
    crc=CRCFlag.CALCULATE,
)

# Use them to create a bundle object
bundle = Bundle(
    pri_block=primary_block,
    canon_blocks=[prev_node_block, bundle_age_block, hop_count_block, payload_block],
)


# Step 6: Encode the bundle
encoded = bundle.to_bytes()

# Print the encoded bundle as a hex string
print(f'New bundle encoded:\n{codecs.encode(encoded,"hex")}\n')

# Write the bundle to a bytes file
filename = "bytesout.bin"
bundle.to_bytes_file(filename)

# Step 7: Decode the encoded bundle bytes
bfrombytes = Bundle.from_bytes(encoded)
if not bfrombytes:
    raise ValueError("Output bundle from bytes could not be parsed.")

# Decode the encoded bundle file
bfromfile = Bundle.from_bytes_file(filename)
if not bfromfile:
    raise ValueError("Output bundle from file could not be parsed.")


# Step 8: Verify the bundle from file is identical to the input
# Parse Primary block
assert bfromfile.pri_block.version == 7
assert bfromfile.pri_block.control_flags == BundlePCFlags.MUST_NOT_FRAGMENT
assert bfromfile.pri_block.crc_type == CRCType.CRC16_X25

assert bfromfile.pri_block.dest_eid.uri == 2
assert bfromfile.pri_block.dest_eid.ssp["node_num"] == 200
assert bfromfile.pri_block.dest_eid.ssp["service_num"] == 1

assert bfromfile.pri_block.src_eid.uri == 2
assert bfromfile.pri_block.src_eid.ssp["node_num"] == 100
assert bfromfile.pri_block.src_eid.ssp["service_num"] == 1

assert bfromfile.pri_block.rpt_eid.uri == 2
assert bfromfile.pri_block.rpt_eid.ssp["node_num"] == 100
assert bfromfile.pri_block.rpt_eid.ssp["service_num"] == 1

assert bfromfile.pri_block.creation_timestamp.time == 755533838904
assert bfromfile.pri_block.creation_timestamp.sequence == 0

assert bfromfile.pri_block.lifetime == 3600000
assert bfromfile.pri_block.crc == b"\x0b\x19"

# Parse Previous Node block
assert bfromfile.canon_blocks[0].blk_type == BlockType.PREVIOUS_NODE
assert bfromfile.canon_blocks[0].blk_num == 1
assert bfromfile.canon_blocks[0].control_flags == 0
assert bfromfile.canon_blocks[0].crc_type == CRCType.CRC16_X25
assert bfromfile.canon_blocks[0].prev_eid.uri == 2
assert bfromfile.canon_blocks[0].prev_eid.ssp["node_num"] == 300
assert bfromfile.canon_blocks[0].prev_eid.ssp["service_num"] == 2
assert bfromfile.canon_blocks[0].crc == b"\x29\x49"

# Parse Bundle Age block
assert bfromfile.canon_blocks[1].blk_type == BlockType.BUNDLE_AGE
assert bfromfile.canon_blocks[1].blk_num == 2
assert (
    bfromfile.canon_blocks[1].control_flags
    == BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC
)
assert bfromfile.canon_blocks[1].crc_type == CRCType.CRC16_X25
assert bfromfile.canon_blocks[1].bundle_age == 108000
assert bfromfile.canon_blocks[1].crc == b"\x5e\x0f"

# Parse Hop Count block
assert bfromfile.canon_blocks[2].blk_type == BlockType.HOP_COUNT
assert bfromfile.canon_blocks[2].blk_num == 3
assert bfromfile.canon_blocks[2].control_flags == BlockPCFlags.FRAG_REPLICATE
assert bfromfile.canon_blocks[2].crc_type == CRCType.CRC16_X25
assert bfromfile.canon_blocks[2].hop_limit == 15
assert bfromfile.canon_blocks[2].hop_count == 3
assert bfromfile.canon_blocks[2].crc == b"\x60\xb9"

# Parse Payload block
assert bfromfile.canon_blocks[3].blk_type == BlockType.BUNDLE_PAYLOAD
assert bfromfile.canon_blocks[3].blk_num == 4
assert bfromfile.canon_blocks[3].control_flags == 0
assert bfromfile.canon_blocks[3].crc_type == CRCType.CRC16_X25
assert (
    bfromfile.canon_blocks[3].payload
    == b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n"
)
bplib_payload_str = bfromfile.canon_blocks[3].payload[8:].decode().strip()
assert bplib_payload_str == "hello world"
assert bfromfile.canon_blocks[3].crc == b"\x69\x56"


# Step 9: Verify the bundle from bytes is identical to the input
# Parse Primary block
assert bfrombytes.pri_block.version == 7
assert bfrombytes.pri_block.control_flags == BundlePCFlags.MUST_NOT_FRAGMENT
assert bfrombytes.pri_block.crc_type == CRCType.CRC16_X25

assert bfrombytes.pri_block.dest_eid.uri == 2
assert bfrombytes.pri_block.dest_eid.ssp["node_num"] == 200
assert bfrombytes.pri_block.dest_eid.ssp["service_num"] == 1

assert bfrombytes.pri_block.src_eid.uri == 2
assert bfrombytes.pri_block.src_eid.ssp["node_num"] == 100
assert bfrombytes.pri_block.src_eid.ssp["service_num"] == 1

assert bfrombytes.pri_block.rpt_eid.uri == 2
assert bfrombytes.pri_block.rpt_eid.ssp["node_num"] == 100
assert bfrombytes.pri_block.rpt_eid.ssp["service_num"] == 1

assert bfrombytes.pri_block.creation_timestamp.time == 755533838904
assert bfrombytes.pri_block.creation_timestamp.sequence == 0

assert bfrombytes.pri_block.lifetime == 3600000
assert bfrombytes.pri_block.crc == b"\x0b\x19"

# Parse Previous Node block
assert bfrombytes.canon_blocks[0].blk_type == BlockType.PREVIOUS_NODE
assert bfrombytes.canon_blocks[0].blk_num == 1
assert bfrombytes.canon_blocks[0].control_flags == 0
assert bfrombytes.canon_blocks[0].crc_type == CRCType.CRC16_X25
assert bfrombytes.canon_blocks[0].prev_eid.uri == 2
assert bfrombytes.canon_blocks[0].prev_eid.ssp["node_num"] == 300
assert bfrombytes.canon_blocks[0].prev_eid.ssp["service_num"] == 2
assert bfrombytes.canon_blocks[0].crc == b"\x29\x49"

# Parse Bundle Age block
assert bfrombytes.canon_blocks[1].blk_type == BlockType.BUNDLE_AGE
assert bfrombytes.canon_blocks[1].blk_num == 2
assert (
    bfrombytes.canon_blocks[1].control_flags
    == BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC
)
assert bfrombytes.canon_blocks[1].crc_type == CRCType.CRC16_X25
assert bfrombytes.canon_blocks[1].bundle_age == 108000
assert bfrombytes.canon_blocks[1].crc == b"\x5e\x0f"

# Parse Hop Count block
assert bfrombytes.canon_blocks[2].blk_type == BlockType.HOP_COUNT
assert bfrombytes.canon_blocks[2].blk_num == 3
assert bfrombytes.canon_blocks[2].control_flags == BlockPCFlags.FRAG_REPLICATE
assert bfrombytes.canon_blocks[2].crc_type == CRCType.CRC16_X25
assert bfrombytes.canon_blocks[2].hop_limit == 15
assert bfrombytes.canon_blocks[2].hop_count == 3
assert bfrombytes.canon_blocks[2].crc == b"\x60\xb9"

# Parse Payload block
assert bfrombytes.canon_blocks[3].blk_type == BlockType.BUNDLE_PAYLOAD
assert bfrombytes.canon_blocks[3].blk_num == 4
assert bfrombytes.canon_blocks[3].control_flags == 0
assert bfrombytes.canon_blocks[3].crc_type == CRCType.CRC16_X25
assert (
    bfrombytes.canon_blocks[3].payload
    == b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n"
)
bplib_payload_str = bfrombytes.canon_blocks[3].payload[8:].decode().strip()
assert bplib_payload_str == "hello world"
assert bfrombytes.canon_blocks[3].crc == b"\x69\x56"

# Step 10 : Write the bundle to a json file, then read the json file into a new
# Bundle
filename = "jsonout.json"
bundle.to_json_file(filename)

read_bundle = Bundle.from_json_file(filename)


# Step 11: Verify the resulting bundle object is identical to the input
# Parse Primary block
assert read_bundle.pri_block.version == 7
assert read_bundle.pri_block.control_flags == BundlePCFlags.MUST_NOT_FRAGMENT
assert read_bundle.pri_block.crc_type == CRCType.CRC16_X25

assert read_bundle.pri_block.dest_eid.uri == 2
assert read_bundle.pri_block.dest_eid.ssp["node_num"] == 200
assert read_bundle.pri_block.dest_eid.ssp["service_num"] == 1

assert read_bundle.pri_block.src_eid.uri == 2
assert read_bundle.pri_block.src_eid.ssp["node_num"] == 100
assert read_bundle.pri_block.src_eid.ssp["service_num"] == 1

assert read_bundle.pri_block.rpt_eid.uri == 2
assert read_bundle.pri_block.rpt_eid.ssp["node_num"] == 100
assert read_bundle.pri_block.rpt_eid.ssp["service_num"] == 1

assert read_bundle.pri_block.creation_timestamp.time == 755533838904
assert read_bundle.pri_block.creation_timestamp.sequence == 0

assert read_bundle.pri_block.lifetime == 3600000
assert read_bundle.pri_block.crc == b"\x0b\x19"

# Parse Previous Node block
assert read_bundle.canon_blocks[0].blk_type == BlockType.PREVIOUS_NODE
assert read_bundle.canon_blocks[0].blk_num == 1
assert read_bundle.canon_blocks[0].control_flags == 0
assert read_bundle.canon_blocks[0].crc_type == CRCType.CRC16_X25
assert read_bundle.canon_blocks[0].prev_eid.uri == 2
assert read_bundle.canon_blocks[0].prev_eid.ssp["node_num"] == 300
assert read_bundle.canon_blocks[0].prev_eid.ssp["service_num"] == 2
assert read_bundle.canon_blocks[0].crc == b"\x29\x49"

# Parse Bundle Age block
assert read_bundle.canon_blocks[1].blk_type == BlockType.BUNDLE_AGE
assert read_bundle.canon_blocks[1].blk_num == 2
assert (
    read_bundle.canon_blocks[1].control_flags
    == BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC
)
assert read_bundle.canon_blocks[1].crc_type == CRCType.CRC16_X25
assert read_bundle.canon_blocks[1].bundle_age == 108000
assert read_bundle.canon_blocks[1].crc == b"\x5e\x0f"

# Parse Hop Count block
assert read_bundle.canon_blocks[2].blk_type == BlockType.HOP_COUNT
assert read_bundle.canon_blocks[2].blk_num == 3
assert read_bundle.canon_blocks[2].control_flags == BlockPCFlags.FRAG_REPLICATE
assert read_bundle.canon_blocks[2].crc_type == CRCType.CRC16_X25
assert read_bundle.canon_blocks[2].hop_limit == 15
assert read_bundle.canon_blocks[2].hop_count == 3
assert read_bundle.canon_blocks[2].crc == b"\x60\xb9"

# Parse Payload block
assert read_bundle.canon_blocks[3].blk_type == BlockType.BUNDLE_PAYLOAD
assert read_bundle.canon_blocks[3].blk_num == 4
assert read_bundle.canon_blocks[3].control_flags == 0
assert read_bundle.canon_blocks[3].crc_type == CRCType.CRC16_X25
assert (
    read_bundle.canon_blocks[3].payload
    == b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n"
)
bplib_payload_str = read_bundle.canon_blocks[3].payload[8:].decode().strip()
assert bplib_payload_str == "hello world"
assert read_bundle.canon_blocks[3].crc == b"\x69\x56"

read_bytes = read_bundle.to_bytes()

# Print the encoded bundle as a hex string
print(f'Read bundle encoded:\n{codecs.encode(read_bytes,"hex")}\n')
