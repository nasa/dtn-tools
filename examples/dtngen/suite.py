import codecs
import copy
import traceback
import warnings

import cbor2

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

# Display every warning - by default it only shows the first warning of the type
# and message content, from a specific line of code. Or set it to "ignore" to
# not display any warnings or to "default" to get the default behavior
# (or comment out all simplefilter lines).
warnings.simplefilter("always")

# Use one or both of these instead to filter out that type of warning.
# TypeWarnings are warnings about types of __init__ parameters for blocks.
# UserWarnings are other warnings such as the block number of the PayloadBlock
# not being 1 or an unknown block type when decoding bytes or json. You can set
# them instead to "default" or "always" as above.
# warnings.simplefilter("ignore", TypeWarning)
# warnings.simplefilter("ignore", UserWarning)


def recv_candidate_bundle():
    """Simulate receiving a bundle from the network.

    .. note::
        This is a known-valid bundle.  It is being used in place of a data-receiver call so that bundle interpreter functionality can be demonstrated.
    """
    bplib_sample_bundle = "9f8907040182028218c801820282186401820282186401821b000000afe9537a38001a0036ee80420b19861849184900014682028218640a426747860101000154000000000000000c68656c6c6f20776f726c640a427a2fff"

    return bytes.fromhex(bplib_sample_bundle)

def create_valid_bundle():
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

    cte_block = CustodyTransferBlock(
        blk_type=BlockType.AUTO,
        blk_num=4,
        control_flags=BlockPCFlags.REP_UNPROC,
        crc_type=CRCType.CRC16_X25,
        cteb_data=CTEBData(
            {
                "trans_id": 10,
                "trans_series_id": 2,
                "req_orig_eid": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}}),
            }
        ),
        crc=CRCFlag.CALCULATE,
    )

    cre_block = CompressedReportingBlock(
        blk_type=BlockType.AUTO,
        blk_num=5,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        creb_data=CREBData(
            {
                "bundle_seq_num": 1,
                "bundle_seq_id": 4,
                "rpt_request_flags": 0,
                "scope_node_id": EID(
                    {"uri": 2, "ssp": {"node_num": 303, "service_num": 1}}
                ),
                "rpt_eid": EID({"uri": 2, "ssp": {"node_num": 305, "service_num": 2}}),
            }
        ),
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
    return Bundle(
        pri_block=primary_block,
        canon_blocks=[
            prev_node_block,
            bundle_age_block,
            hop_count_block,
            cte_block,
            cre_block,
            payload_block,
        ],
    )

## TESTS BEGIN ##
def test_legacy_suite():
    # DO NOT ADD ANY MORE TESTS TO THIS FUNCTION #

    # Step 1: "Receive" a Bundle from the data receiver tool
    candidate_bundle = recv_candidate_bundle()

    # Print the encoded bundle as a hex string
    print(f'\nOriginal bundle:\n{codecs.encode(candidate_bundle,"hex")}\n')


    # Step 2: Attempt to cbor decode the payload using the interpreter
    bundle = Bundle.from_bytes(candidate_bundle)
    if not bundle:
        raise ValueError("Bundle could not be parsed.")


    # Step 3: Access fields within the bundle as required by the test
    # Parsing Primary block
    assert bundle.pri_block.version == 7
    assert bundle.pri_block.control_flags == 4

    # Parse the unknown block
    assert bundle.canon_blocks[0].elements[0] == 73
    assert bundle.canon_blocks[0].elements[1] == 73
    assert bundle.canon_blocks[0].elements[2] == 0
    assert bundle.canon_blocks[0].elements[3] == 1
    # The type-specific data is unknown but is doubly cbor encoded so appears as a
    # cbor encoded array
    assert bundle.canon_blocks[0].elements[4] == b"\x82\x02\x82\x18\x64\x0a"
    assert bundle.canon_blocks[0].elements[5] == b"\x67\x47"

    # Parsing the payload
    bplib_payload_str = bundle.canon_blocks[1].payload[8:].decode().strip()
    assert bplib_payload_str == "hello world"


    # Step 4: Re-encode the bundle
    encoded = bundle.to_bytes()

    # Print the encoded bundle as a hex string
    print(f'\nOriginal Re-encoded:\n{codecs.encode(encoded,"hex")}\n')

    # Verify that the output bundle matches the input bundle
    assert candidate_bundle == encoded

    cand_json_filename = "cand_bundle.json"
    bundle.to_json_file(cand_json_filename)


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

    cte_block = CustodyTransferBlock(
        blk_type=BlockType.AUTO,
        blk_num=4,
        control_flags=BlockPCFlags.REP_UNPROC,
        crc_type=CRCType.CRC16_X25,
        cteb_data=CTEBData(
            {
                "trans_id": 10,
                "trans_series_id": 2,
                "req_orig_eid": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}}),
            }
        ),
        crc=CRCFlag.CALCULATE,
    )

    cre_block = CompressedReportingBlock(
        blk_type=BlockType.AUTO,
        blk_num=5,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        creb_data=CREBData(
            {
                "bundle_seq_num": 1,
                "bundle_seq_id": 4,
                "rpt_request_flags": 0,
                "scope_node_id": EID(
                    {"uri": 2, "ssp": {"node_num": 303, "service_num": 1}}
                ),
                "rpt_eid": EID({"uri": 2, "ssp": {"node_num": 305, "service_num": 2}}),
            }
        ),
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
            cte_block,
            cre_block,
            payload_block,
        ],
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
    assert bfromfile.canon_blocks[0].blk_num == 6
    assert bfromfile.canon_blocks[0].control_flags == 0
    assert bfromfile.canon_blocks[0].crc_type == CRCType.CRC16_X25
    assert bfromfile.canon_blocks[0].prev_eid.uri == 2
    assert bfromfile.canon_blocks[0].prev_eid.ssp["node_num"] == 300
    assert bfromfile.canon_blocks[0].prev_eid.ssp["service_num"] == 2
    assert bfromfile.canon_blocks[0].crc == b"\x25\xd4"

    # Parse Bundle Age block
    assert bfromfile.canon_blocks[1].blk_type == BlockType.BUNDLE_AGE
    assert bfromfile.canon_blocks[1].blk_num == 2
    assert (
        bfromfile.canon_blocks[1].control_flags
        == BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC
    )
    assert bfromfile.canon_blocks[1].crc_type == CRCType.CRC16_X25
    assert bfromfile.canon_blocks[1].bundle_age == 108000
    assert bfromfile.canon_blocks[1].crc == b"\x3a\xed"

    # Parse Hop Count block
    assert bfromfile.canon_blocks[2].blk_type == BlockType.HOP_COUNT
    assert bfromfile.canon_blocks[2].blk_num == 3
    assert bfromfile.canon_blocks[2].control_flags == BlockPCFlags.FRAG_REPLICATE
    assert bfromfile.canon_blocks[2].crc_type == CRCType.CRC16_X25
    assert bfromfile.canon_blocks[2].hop_data.hop_limit == 15
    assert bfromfile.canon_blocks[2].hop_data.hop_count == 3
    assert bfromfile.canon_blocks[2].crc == b"\xf8\x13"

    # Parse Custody Transfer Extension block
    assert bfromfile.canon_blocks[3].blk_type == BlockType.CUST_TRANS_EXT
    assert bfromfile.canon_blocks[3].blk_num == 4
    assert bfromfile.canon_blocks[3].control_flags == BlockPCFlags.REP_UNPROC
    assert bfromfile.canon_blocks[3].crc_type == CRCType.CRC16_X25
    assert bfromfile.canon_blocks[3].cteb_data.trans_id == 10
    assert bfromfile.canon_blocks[3].cteb_data.trans_series_id == 2
    assert bfromfile.canon_blocks[3].cteb_data.req_orig_eid.uri == 2
    assert bfromfile.canon_blocks[3].cteb_data.req_orig_eid.ssp["node_num"] == 303
    assert bfromfile.canon_blocks[3].cteb_data.req_orig_eid.ssp["service_num"] == 1
    assert bfromfile.canon_blocks[3].crc == b"\x25\xc7"

    # Parse Compressed Reporting Extension block
    assert bfromfile.canon_blocks[4].blk_type == BlockType.COMP_RPT_EXT
    assert bfromfile.canon_blocks[4].blk_num == 5
    assert bfromfile.canon_blocks[4].control_flags == 0
    assert bfromfile.canon_blocks[4].crc_type == CRCType.CRC16_X25
    assert bfromfile.canon_blocks[4].creb_data.bundle_seq_num == 1
    assert bfromfile.canon_blocks[4].creb_data.bundle_seq_id == 4
    assert bfromfile.canon_blocks[4].creb_data.rpt_request_flags == 0
    assert bfromfile.canon_blocks[4].creb_data.scope_node_id.uri == 2
    assert bfromfile.canon_blocks[4].creb_data.scope_node_id.ssp["node_num"] == 303
    assert bfromfile.canon_blocks[4].creb_data.scope_node_id.ssp["service_num"] == 1
    assert bfromfile.canon_blocks[4].creb_data.rpt_eid.uri == 2
    assert bfromfile.canon_blocks[4].creb_data.rpt_eid.ssp["node_num"] == 305
    assert bfromfile.canon_blocks[4].creb_data.rpt_eid.ssp["service_num"] == 2
    assert bfromfile.canon_blocks[4].crc == b"\x66\xce"

    # Parse Payload block
    assert bfromfile.canon_blocks[5].blk_type == BlockType.BUNDLE_PAYLOAD
    assert bfromfile.canon_blocks[5].blk_num == 1
    assert bfromfile.canon_blocks[5].control_flags == 0
    assert bfromfile.canon_blocks[5].crc_type == CRCType.CRC16_X25
    assert (
        bfromfile.canon_blocks[5].payload
        == b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n"
    )
    bplib_payload_str = bfromfile.canon_blocks[5].payload[8:].decode().strip()
    assert bplib_payload_str == "hello world"
    assert bfromfile.canon_blocks[5].crc == b"\x7a\x2f"

    read_bytes = bfromfile.to_bytes()
    # Print the encoded bundle as a hex string
    print(f'read_bytes:\n{codecs.encode(read_bytes,"hex")}\n')

    bfrombytes2 = Bundle.from_bytes(read_bytes)
    if not bfrombytes2:
        raise ValueError("Output bundle from bytes could not be parsed.")

    assert read_bytes == encoded

    bfrombyte_json_filename = "bfrombyte.json"
    bfrombytes2.to_json_file(bfrombyte_json_filename)

    # Step 9: Verify the bundle from bytes is identical to the input
    read_bytes = bfrombytes.to_bytes()
    assert read_bytes == encoded


    # Step 10 : Write the bundle to a json file, then read the json file into a new
    # Bundle
    filename = "jsonout.json"
    bundle.to_json_file(filename)

    read_bundle = Bundle.from_json_file(filename)


    # Step 11: Verify the resulting bundle object is identical to the input
    read_bytes = read_bundle.to_bytes()
    # Print the encoded bundle as a hex string
    print(f'New bundle encoded again:\n{codecs.encode(read_bytes,"hex")}\n')
    assert read_bytes == encoded

    filename2 = "jsonout2.json"
    read_bundle.to_json_file(filename2)


    # Step 12: Define new primary and canonical blocks with missing elements
    primary_block = PrimaryBlock(
        version=7,
        #     control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
        #     crc_type=CRCType.CRC16_X25,
        dest_eid=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
        src_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        rpt_eid=EID({"uri": 2, "ssp": {"node_num": 300, "service_num": 1}}),
        creation_timestamp=CreationTimestamp({"time": 755533838904, "sequence": 0}),
        lifetime=3600000,
        crc=b"\x0b\x19",
    )

    prev_node_block = PrevNodeBlock(
        blk_type=BlockType.AUTO,
        blk_num=6,
        control_flags=0,
        #     crc_type=CRCType.CRC16_X25,
        #     prev_eid=EID({"uri": 2, "ssp": {"node_num": 300, "service_num": 2}}),
        crc=CRCFlag.CALCULATE,
    )

    bundle_age_block = BundleAgeBlock(
        blk_type=BlockType.AUTO,
        blk_num=2,
        #     control_flags=BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC,
        crc_type=CRCType.CRC16_X25,
        bundle_age=108000,
        crc=CRCFlag.CALCULATE,
    )

    hop_count_block = HopCountBlock(
        #     blk_type=BlockType.AUTO,
        blk_num=3,
        control_flags=BlockPCFlags.FRAG_REPLICATE,
        crc_type=CRCType.CRC16_X25,
        #     hop_data=HopCountData({"hop_limit": 15, "hop_count": 3}),
        hop_data=HopCountData({"hop_count": 3}),
        crc=CRCFlag.CALCULATE,
    )

    cte_block = CustodyTransferBlock(
        blk_type=BlockType.AUTO,
        blk_num=4,
        control_flags=BlockPCFlags.REP_UNPROC,
        crc_type=CRCType.CRC16_X25,
        cteb_data=CTEBData(
            {
                "trans_id": 10,
                #          "trans_series_id": 2,
                "req_orig_eid": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}}),
            }
        ),
        crc=CRCFlag.CALCULATE,
    )

    cre_block = CompressedReportingBlock(
        blk_type=BlockType.AUTO,
        blk_num=5,
        #     control_flags=0,
        crc_type=CRCType.CRC16_X25,
        creb_data=CREBData(
            {
                "bundle_seq_num": 1,
                "bundle_seq_id": 4,
                #         "rpt_request_flags": 0,
                #         "scope_node_id": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}}),
                "rpt_eid": EID({"uri": 2, "ssp": {"node_num": 305, "service_num": 2}}),
            }
        ),
        crc=CRCFlag.CALCULATE,
    )

    payload_block = PayloadBlock(
        blk_type=BlockType.AUTO,
        #     blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n",
        crc=CRCFlag.CALCULATE,
    )

    # Use them to create a bundle object
    bundle_with_errors = Bundle(
        pri_block=primary_block,
        canon_blocks=[
            prev_node_block,
            bundle_age_block,
            hop_count_block,
            cte_block,
            cre_block,
            payload_block,
        ],
    )

    error_json_filename = "errorjson.json"
    bundle_with_errors.to_json_file(error_json_filename)

    # Write it to binary
    error_bytes_filename = "errorbytes.bin"
    bundle_with_errors.to_bytes_file(error_bytes_filename)

    # Print the encoded bundle as a hex string
    errbundle_bin = bundle_with_errors.to_bytes()
    print(f'\nError block encoded:\n{codecs.encode(errbundle_bin,"hex")}\n')

    # Read it back in as a Bundle
    errbundle_frombin = Bundle.from_bytes_file(error_bytes_filename)


    # Step 13: Verify the bundle as read from binary, is as expected
    # Parse Primary block
    # the version is in the correct position
    assert errbundle_frombin.pri_block.version == 7

    # because control_flags and crc_type were left out, the dest_eid shifts into the
    # control_flags position and the EID, not typed as an EID, instead appears as an
    # array
    assert errbundle_frombin.pri_block.control_flags[0] == 2
    assert errbundle_frombin.pri_block.control_flags[1][0] == 200
    assert errbundle_frombin.pri_block.control_flags[1][1] == 1

    # Similarly the src_eid appears in the crc_type field
    assert errbundle_frombin.pri_block.crc_type[0] == 2
    assert errbundle_frombin.pri_block.crc_type[1][0] == 100
    assert errbundle_frombin.pri_block.crc_type[1][1] == 1

    # The rpt_eid is now in the dest_eid field, but since this field is an EID it is
    # properly typed as an EID, it is just the wrong one
    assert errbundle_frombin.pri_block.dest_eid.uri == 2
    assert errbundle_frombin.pri_block.dest_eid.ssp["node_num"] == 300
    assert errbundle_frombin.pri_block.dest_eid.ssp["service_num"] == 1

    # The creation_timestamp now is in the src_eid field and so can't be properly
    # typed as a CreationTimestamp. Instead again it appears as an array
    assert errbundle_frombin.pri_block.src_eid[0] == 755533838904
    assert errbundle_frombin.pri_block.src_eid[1] == 0

    # The lifetime is now in the rpt_eid field and is just the int
    assert errbundle_frombin.pri_block.rpt_eid == 3600000

    # Finally the CRC is in the creation_timestamp field and appears as bytes
    assert errbundle_frombin.pri_block.creation_timestamp == b"\x0b\x19"

    # The remaining fields (lifetime and crc) are now not set
    assert errbundle_frombin.pri_block.lifetime == None
    assert errbundle_frombin.pri_block.crc == None


    # Parse canonical blocks
    # Parse Previous Node block
    assert errbundle_frombin.canon_blocks[0].blk_type == BlockType.PREVIOUS_NODE
    assert errbundle_frombin.canon_blocks[0].blk_num == 6
    assert errbundle_frombin.canon_blocks[0].control_flags == 0

    # Because crc_type and prev_eid were left out, the CRC, which was set to
    # CRCFlag.CALCULATE (equal to -1), is now in the crc_type field. The CRC was
    # not calculated, so that CRC remained as -1 and is in this field
    assert errbundle_frombin.canon_blocks[0].crc_type == -1

    # The remaining fields were not set
    assert errbundle_frombin.canon_blocks[0].prev_eid == None
    assert errbundle_frombin.canon_blocks[0].crc == None


    # Parse Bundle Age block
    assert errbundle_frombin.canon_blocks[1].blk_type == BlockType.BUNDLE_AGE
    assert errbundle_frombin.canon_blocks[1].blk_num == 2

    # Because control_flags was left out, the crc_type is in the control_flags
    # field
    assert errbundle_frombin.canon_blocks[1].control_flags == 1

    # The type specific data (here it is the bundle_age) is doubly cbor encoded and
    # that is not expected in the crc_type field, so that bundle age appears here
    # as a cbor encoded integer 108000. This is an integer (major type 0) with
    # additional data 26 (binary 000 11010 = x1A), the 26 means the integer is 4
    # bytes long, which is 0x0001a5e0 = 108000.
    assert errbundle_frombin.canon_blocks[1].crc_type == b"\x1a\x00\x01\xa5\xe0"

    # The bundle age now contains the CRC
    assert errbundle_frombin.canon_blocks[1].bundle_age == b"\x39\xe2"

    # And the crc field is not set
    assert errbundle_frombin.canon_blocks[1].crc == None


    # Parse Hop Count block
    # Here the block type was left out, which pushes the blk_num (3) into the
    # blk_type field. 3 is not a valid block type. In this case the block is then
    # added as an UnknownBlock, in which the elements are an array of data
    assert errbundle_frombin.canon_blocks[2].elements[0] == 3
    # The second value is now the control_flags
    assert errbundle_frombin.canon_blocks[2].elements[1] == 1
    # The third value is the crc_type
    assert errbundle_frombin.canon_blocks[2].elements[2] == 1
    # The fourth value is the type-specific data (HopCountData). Normally this is
    # a two value int array, but in this case the hop_limit was left out, which
    # pushes the hop_count (3) into that position of the array. And since this is
    # doubly cbor encoded it appears in the 4th position as a cbor encoded 1 element
    # array (0x81) with the lone value 3
    assert errbundle_frombin.canon_blocks[2].elements[3] == b"\x81\x03"
    # Finally the CRC appears as the 5th element of the array
    assert errbundle_frombin.canon_blocks[2].elements[4] == b"\x88\xcd"
    # There are no other elements to the array


    # Parse Custody Transfer Extension block
    assert errbundle_frombin.canon_blocks[3].blk_type == BlockType.CUST_TRANS_EXT
    assert errbundle_frombin.canon_blocks[3].blk_num == 4
    assert errbundle_frombin.canon_blocks[3].control_flags == BlockPCFlags.REP_UNPROC
    assert errbundle_frombin.canon_blocks[3].crc_type == CRCType.CRC16_X25
    # Everything is as normal in this case until we get to the CTEBData where the
    # trans_series_id was left out. Because there are the wrong number of elements
    # it does not know it is CTEBData and instead is added as an array, with the
    # second element the req_orig_eid, but it ends up here as an array as well.
    assert errbundle_frombin.canon_blocks[3].cteb_data[0] == 10
    assert errbundle_frombin.canon_blocks[3].cteb_data[1][0] == 2
    assert errbundle_frombin.canon_blocks[3].cteb_data[1][1][0] == 303
    assert errbundle_frombin.canon_blocks[3].cteb_data[1][1][1] == 1
    # The CRC in this case is right where it should. No elements were left out of
    # the CTEB block, there was only an element left out of the type-specific data
    assert errbundle_frombin.canon_blocks[3].crc == b"\x96\xc0"


    # Parse Compressed Reporting Extension block
    assert errbundle_frombin.canon_blocks[4].blk_type == BlockType.COMP_RPT_EXT
    assert errbundle_frombin.canon_blocks[4].blk_num == 5
    # The control_flags were left out, so the crc_type ends up in the control_flags
    # field
    assert errbundle_frombin.canon_blocks[4].control_flags == 1
    # the CREBData ends up in the crc_type field and again since this is doubly
    # cbor encoded it appears as a cbor encoded array, in this case a fairly lengthy
    # one
    assert (
        errbundle_frombin.canon_blocks[4].crc_type
        == b"\x83\x01\x04\x82\x02\x82\x19\x01\x31\x02"
    )
    # And the CRC ends up in the creb_data field
    assert errbundle_frombin.canon_blocks[4].creb_data == b"\x05\x17"
    assert errbundle_frombin.canon_blocks[4].crc == None


    # Parse Payload block
    assert errbundle_frombin.canon_blocks[5].blk_type == BlockType.BUNDLE_PAYLOAD
    # The blk_num is left out, shifting the control_Flags into the blk_num
    assert errbundle_frombin.canon_blocks[5].blk_num == 0
    # The crc_type ends up in the control_flags field
    assert errbundle_frombin.canon_blocks[5].control_flags == 1
    # The payload ends up in the crc_type
    assert (
        errbundle_frombin.canon_blocks[5].crc_type
        == b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n"
    )
    # The crc ends up in the payload
    assert errbundle_frombin.canon_blocks[5].payload == b"\x8d\x29"
    # And the crc is not set
    assert errbundle_frombin.canon_blocks[5].crc == None

    errbundle_frombin_bin = errbundle_frombin.to_bytes()

    # Verify the binary output is identical
    assert errbundle_frombin_bin == errbundle_bin

    errjson_frombin_filename = "errorfrombin.json"
    errbundle_frombin.to_json_file(errjson_frombin_filename)


    # Step 14: Define new bundle with missing Primary block and only one canonical
    # block (resulting in one one block in the cbor indefinite array)
    bundle_with_no_primary = Bundle(
        canon_blocks=[payload_block],
    )

    no_primary_json_filename = "noprimary.json"
    bundle_with_no_primary.to_json_file(no_primary_json_filename)
    no_primary_bytes_filename = "noprimary.bin"
    bundle_with_no_primary.to_bytes_file(no_primary_bytes_filename)

    bundle_from_junk = Bundle.from_bytes_file(no_primary_bytes_filename)
    bundle_from_junk = Bundle.from_json_file(no_primary_json_filename)

    # Step 15: Define new bundle with no blocks at all
    bundle_with_no_blocks = Bundle()

    no_blocks_json_filename = "noblocks.json"
    bundle_with_no_blocks.to_json_file(no_blocks_json_filename)
    no_blocks_bytes_filename = "noblocks.bin"
    bundle_with_no_blocks.to_bytes_file(no_blocks_bytes_filename)

    bundle_from_junk = Bundle.from_bytes_file(no_blocks_bytes_filename)
    bundle_from_junk = Bundle.from_json_file(no_blocks_json_filename)


    # Step 16: Define new primary block with missing elements in subtypes
    primary_block = PrimaryBlock(
        version=7,
        control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
        crc_type=CRCType.CRC16_X25,
        dest_eid=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
        src_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        #     rpt_eid=EID({"uri": 2, "ssp": {"node_num": 300, "service_num": 1}}),
        rpt_eid=EID({"uri": 2, "ssp": {"service_num": 1}}),
        #     creation_timestamp=CreationTimestamp({"time": 755533838904, "sequence": 0}),
        creation_timestamp=CreationTimestamp({"time": 755533838904}),
        lifetime=3600000,
        crc=b"\x0b\x19",
    )

    # Use it to create a bundle object
    bundle_again = Bundle(
        pri_block=primary_block,
    )

    bundle_again_json_filename = "bundle_again.json"
    bundle_again.to_json_file(bundle_again_json_filename)

    # Write it to binary
    bundle_again_tobytes = bundle_again.to_bytes()
    print(f'\nbundle_again_tobytes:\n{codecs.encode(bundle_again_tobytes,"hex")}\n')

    # Read it back in as a Bundle
    again_frombytes = Bundle.from_bytes(bundle_again_tobytes)
    again_frombytes_tobytes = again_frombytes.to_bytes()

    assert again_frombytes_tobytes == bundle_again_tobytes

    # Step 17: Verify the bundle from bytes is as expected
    assert again_frombytes.pri_block.version == 7
    assert again_frombytes.pri_block.control_flags == BundlePCFlags.MUST_NOT_FRAGMENT
    assert again_frombytes.pri_block.crc_type == CRCType.CRC16_X25

    assert again_frombytes.pri_block.dest_eid.uri == 2
    assert again_frombytes.pri_block.dest_eid.ssp["node_num"] == 200
    assert again_frombytes.pri_block.dest_eid.ssp["service_num"] == 1

    assert again_frombytes.pri_block.src_eid.uri == 2
    assert again_frombytes.pri_block.src_eid.ssp["node_num"] == 100
    assert again_frombytes.pri_block.src_eid.ssp["service_num"] == 1

    # Because the EID was missing an element (node_num), it does not appear to be
    # an EID when interpreted from bytes, so the data is passed through as a
    # 2-element array with a one element array in it
    assert again_frombytes.pri_block.rpt_eid == [2, [1]]

    # Similarly the timestamp was missing the sequence element, so when read in it
    # is passed through as a one element array
    assert again_frombytes.pri_block.creation_timestamp == [755533838904]

    assert again_frombytes.pri_block.lifetime == 3600000
    assert again_frombytes.pri_block.crc == b"\x0b\x19"


    # Step 18: Create bundle with a dtn EID
    primary_block = PrimaryBlock(
        version=7,
        control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
        crc_type=CRCType.CRC16_X25,
        dest_eid=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
        src_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        rpt_eid=EID({"uri": 1, "ssp": "dtn:none"}),
        creation_timestamp=CreationTimestamp({"time": 755533838904, "sequence": 0}),
        lifetime=3600000,
        crc=b"\x0b\x19",
    )

    bundle_dtn = Bundle(
        pri_block=primary_block,
    )

    bundle_dtn_bytes = bundle_dtn.to_bytes()
    print(f'bundle_dtn_bytes:\n{codecs.encode(bundle_dtn_bytes,"hex")}\n')


    # Step 19: Create bundle with incorrect extension block types
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
        blk_type=BlockType.BUNDLE_AGE,
        blk_num=6,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        prev_eid=EID({"uri": 2, "ssp": {"node_num": 300, "service_num": 2}}),
        crc=CRCFlag.CALCULATE,
    )

    bundle_age_block = BundleAgeBlock(
        blk_type=BlockType.PREVIOUS_NODE,
        blk_num=2,
        control_flags=BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC,
        crc_type=CRCType.CRC16_X25,
        bundle_age=108000,
        crc=CRCFlag.CALCULATE,
    )

    hop_count_block = HopCountBlock(
        blk_type=BlockType.COMP_RPT_EXT,
        blk_num=3,
        control_flags=BlockPCFlags.FRAG_REPLICATE,
        crc_type=CRCType.CRC16_X25,
        hop_data=HopCountData({"hop_limit": 15, "hop_count": 3}),
        crc=CRCFlag.CALCULATE,
    )

    cte_block = CustodyTransferBlock(
        blk_type=BlockType.BUNDLE_PAYLOAD,
        blk_num=4,
        control_flags=BlockPCFlags.REP_UNPROC,
        crc_type=CRCType.CRC16_X25,
        cteb_data=CTEBData(
            {
                "trans_id": 10,
                "trans_series_id": 2,
                "req_orig_eid": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}}),
            }
        ),
        crc=CRCFlag.CALCULATE,
    )

    cre_block = CompressedReportingBlock(
        blk_type=BlockType.HOP_COUNT,
        blk_num=5,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        creb_data=CREBData(
            {
                "bundle_seq_num": 1,
                "bundle_seq_id": 4,
                "rpt_request_flags": 0,
                "scope_node_id": EID(
                    {"uri": 2, "ssp": {"node_num": 303, "service_num": 1}}
                ),
                "rpt_eid": EID({"uri": 2, "ssp": {"node_num": 305, "service_num": 2}}),
            }
        ),
        crc=CRCFlag.CALCULATE,
    )

    payload_block = PayloadBlock(
        blk_type=BlockType.CUST_TRANS_EXT,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n",
        crc=CRCFlag.CALCULATE,
    )

    # Use them to create a bundle object
    wrong_block_types_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[
            prev_node_block,
            bundle_age_block,
            hop_count_block,
            cte_block,
            cre_block,
            payload_block,
        ],
    )

    wrong_types_bytes = wrong_block_types_bundle.to_bytes()
    print(f'wrong_types_bytes:\n{codecs.encode(wrong_types_bytes,"hex")}\n')

    wrong_block_types_bundle.to_json_file("wrongtypes.json")
    wrong_types_bundle_back = Bundle.from_json_file("wrongtypes.json")
    wrong_types_bundle_back.to_json_file("wrongtypesback.json")

    from_wrong_bundle = Bundle.from_bytes(wrong_types_bytes)
    from_wrong_bundle_bytes = from_wrong_bundle.to_bytes()
    print(f'\nfrom_wrong_bundle_bytes:\n{codecs.encode(from_wrong_bundle_bytes,"hex")}\n')

    # The original bundle bytes and the bytes from the interpreted bytes should be
    # the same
    assert wrong_types_bytes == from_wrong_bundle_bytes

    # The blocks get interpreted as the wrong type blocks because the block types
    # were set incorrectly. In this case what was actually a PrevNodeBlock, and so
    # had an EID as the type-specific data, appears to be a BundleAgeBlock. Since
    # it's not expecting an EID, it does not get set as an EID instance, rather to
    # the array that an EID is represented as.
    assert isinstance(from_wrong_bundle.canon_blocks[0], BundleAgeBlock)
    assert from_wrong_bundle.canon_blocks[0].bundle_age == [2, [300, 2]]

    # Here it's the opposite. What was a BundleAgeBlock was set as a PrevNodeBlock.
    # When the bytes are read back in and it sees a PrevNodeBlock, the EID is
    # actually a bundle age (int), so it sets the prev_eid as the int
    assert isinstance(from_wrong_bundle.canon_blocks[1], PrevNodeBlock)
    assert from_wrong_bundle.canon_blocks[1].prev_eid == 108000

    # In this case the Hop Count Block was wrongly typed as a CompressedReportingBlock
    # When interpreting the bytes for the type-specific data it still looks like
    # CREBData because CREBData is an array of 1 to 5 elements, the first 3 of which
    # are ints, and the hop count data is 2 ints, so it creates a CREBData instance
    # and sets the first two elements to the HopCountData values, and the others
    # are set to None
    assert isinstance(from_wrong_bundle.canon_blocks[2], CompressedReportingBlock)
    assert isinstance(from_wrong_bundle.canon_blocks[2].creb_data, CREBData)
    assert from_wrong_bundle.canon_blocks[2].creb_data.bundle_seq_num == 15
    assert from_wrong_bundle.canon_blocks[2].creb_data.bundle_seq_id == 3
    assert from_wrong_bundle.canon_blocks[2].creb_data.rpt_request_flags == None
    assert from_wrong_bundle.canon_blocks[2].creb_data.scope_node_id == None
    assert from_wrong_bundle.canon_blocks[2].creb_data.rpt_eid == None

    # In this case what was a CustodyTransferBlock is set as a PayloadBlock. The
    # payload is expecting a byte string, but instead it's CTEBData. In the case of
    # the payload block, the payload is not doubly cbor encoded, unlike the
    # type-specific data of other canonical blocks, so it doesn't cbor decode this
    # "payload" and it is the byte string cbor representation of that CTEBData
    assert isinstance(from_wrong_bundle.canon_blocks[3], PayloadBlock)
    assert (
        from_wrong_bundle.canon_blocks[3].payload
        == b"\x83\x0a\x02\x82\x02\x82\x19\x01\x2f\x01"
    )

    # Here what was a CompressedReportingBlock is wrongly typed as a HopCountBlock.
    # The type-specific data ends up as the array representing the CREBData, in this
    # case a full 5-item CREBData
    assert isinstance(from_wrong_bundle.canon_blocks[4], HopCountBlock)
    assert from_wrong_bundle.canon_blocks[4].hop_data == [
        1,
        4,
        0,
        [2, [303, 1]],
        [2, [305, 2]],
    ]

    # Lastly what was a PayloadBlock is wrongly typed as a CustodyTransferBlock.
    # The cteb data ends up as the payload data. Payload data is not doubly cbor
    # encoded. When it tries to decode it a second time it fails and in this case
    # it passes through the original value, which is the payload byte string
    assert isinstance(from_wrong_bundle.canon_blocks[5], CustodyTransferBlock)
    assert (
        from_wrong_bundle.canon_blocks[5].cteb_data
        == b"\x00\x00\x00\x00\x00\x00\x00\x0chello world\n"
    )


    # Define primary block settings for generation - everything is like in creating
    # a primary block, except creation_timestamp is a dictionary with settings
    # options
    primary_block_settings = PrimaryBlockSettings(
        version=7,
        control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
        crc_type=CRCType.CRC16_X25,
        dest_eid=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
        src_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        creation_timestamp={
            "time": {"start": 755533838904, "increment": 256},
            "sequence": {"start": 0},
        },
        lifetime=3600000,
        crc=CRCFlag.CALCULATE,
    )

    # Payload block setting is like in creating a payload block, except for the
    # payload which is a dictionary with the size of payload to generate (in bytes)
    payload_block_settings = PayloadBlockSettings(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload={"min_size": 128, "max_size": 129},
        crc=CRCFlag.CALCULATE,
    )
    # At least make sure the payload_size field is correctly set
    gen_pay_len = len(payload_block_settings.generate(1).payload)
    assert gen_pay_len >= 128
    assert gen_pay_len <= 129


    # Bundles are then generated by the calling the Bundle @classmethod generate
    # with the count and the primary and canonical block settings from above. An
    # list is returned with the specified number of bundles
    generated_bundles = Bundle.generate(
        num_bundles=3,
        pri_settings=primary_block_settings,
        # The canon_settings is an array of settings instances. You could create
        # bundles with multiple canonical blocks by providing multiple settings
        # instances, though currently only the payload block is supported. You can
        # create bundles erroneously with multiple payload blocks or even no blocks
        canon_settings=[payload_block_settings],
    )

    print(f"\n{len(generated_bundles)} generated bundles:")
    print("-------------------------------")
    for x in generated_bundles:
        encoded = x.to_bytes()
        print(f'{codecs.encode(encoded,"hex")}\n')
    #     print(x.to_json())


    # Another example, but with the bundle timestamped with the current DTN time at
    # time of generation, and a fixed sequence value. For the payload we use the
    # maximum payload size.
    primary_block_settings = PrimaryBlockSettings(
        version=7,
        control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
        crc_type=CRCType.CRC16_X25,
        dest_eid=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
        src_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        creation_timestamp={"time": "current", "sequence": {"fixed": 5}},
        lifetime=3600000,
        crc=CRCFlag.CALCULATE,
    )

    payload_block_settings = PayloadBlockSettings(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload={"min_size": 10 * 1024 * 1024, "max_size": 10 * 1024 * 1024},
        crc=CRCFlag.CALCULATE,
    )

    generated_bundles = Bundle.generate(
        num_bundles=3,
        # Optional delay in seconds (can be floating point) between generation of
        # each bundle. The delay time is not exact. Useful for generating multiple
        # bundles using DTN time with larger time between them. Defaults to 0
        # seconds. With the size of payload we are generating there is already a
        # short delay, this delay value just makes it a little larger.
        pri_settings=primary_block_settings,
        canon_settings=[payload_block_settings],
    )

    print(f"\n{len(generated_bundles)} generated bundles:")
    print("-------------------------------")
    for x in generated_bundles:
        print(f"Payload size: {len(x.canon_blocks[0].payload)} bytes")
        print(f"Creation Time: {x.pri_block.creation_timestamp.time}\n")


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

    # Create a payload block with payload that is not bytes (which is invalid)
    payload_block = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=1,
        payload=0x1234,
        crc="hello",
    )

    # Use it to create a bundle object
    badpayloadbundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[payload_block],
    )

    # get it as bytes
    badpayloadbundlebytes = badpayloadbundle.to_bytes()
    print(f'badpayloadbundlebytes =\n{codecs.encode(badpayloadbundlebytes,"hex")}')

    # decode it and get as bytes again
    badpayloadbundleback = Bundle.from_bytes(badpayloadbundlebytes)
    badpayloadbundlebytesagain = badpayloadbundleback.to_bytes()
    print(
        f'\nbadpayloadbundlebytesagain =\n{codecs.encode(badpayloadbundlebytesagain,"hex")}'
    )

    # Make sure they are the same
    assert badpayloadbundlebytes == badpayloadbundlebytesagain

    # Verify that the payload is (incorrectly) a CBOR encoded unsigned integer
    # instead of a byte string
    ba = bytearray(badpayloadbundlebytesagain)
    print(f'\nbadpayload = {codecs.encode(ba[47:50], "hex")}')
    assert ba[47] == 0x19  # A CBOR unsigned int in two bytes (additional info 25)
    assert ba[48] == 0x12
    assert ba[49] == 0x34

    # Generate a junk random bundle (random data unit) and print it out as hex
    junk_bundle = Bundle.generate_random(size=256)
    print(f'\njunk_bundle = {codecs.encode(junk_bundle, "hex")}\n')

    # Generate a junk random bundle of maximum size and write it to a binary file.
    # Note that it also is returned from the method, but here we do not do anything
    # with it
    Bundle.generate_random(size=10 * 1024 * 1024, filename="junk.bin")


    # Create a Primary Block with invalid CBOR encoding of the lifetime. Here the
    # additional info is changed to 31, which because this is major type 0 (unsigned
    # integer) is an invalid additional info value. Note that you set "value" to the
    # valid value. "additional_info" is the invalid additional info value you want
    # to set to make it invalid. To make it invalid, it needs to be 28-30 or 31.

    # First create a good PrimaryBlock:
    primary_block = PrimaryBlock(
        version=7,
        control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
        crc_type=CRCType.CRC16_X25,
        dest_eid=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
        src_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        rpt_eid=EID({"uri": 2, "ssp": {"node_num": 300, "service_num": 1}}),
        creation_timestamp=CreationTimestamp({"time": 755533838904, "sequence": 0}),
        lifetime=3600000,
        crc=CRCFlag.CALCULATE,
    )

    # Use it to create a good bundle object
    good_cbor_bundle = Bundle(
        pri_block=copy.deepcopy(primary_block),
    )

    # Encode it to bytes, which contains the good CBOR encoding
    good_cbor_encoded = good_cbor_bundle.to_bytes()

    # Now create the bad cbor encoded bundle by modifying the good one.
    orig_lifetime = primary_block.lifetime
    primary_block.lifetime = InvalidCBOR(value=orig_lifetime, additional_info=31)

    # Use it to create a bundle object
    bad_cbor_bundle = Bundle(
        pri_block=copy.deepcopy(primary_block),
    )

    # Encode it to bytes, which contains the invalid CBOR encoding
    bad_cbor_encoded = bad_cbor_bundle.to_bytes()
    bad_cbor_bundle.to_bytes_file("bad_cbor_bundle.bin")

    print(f'\ngood_cbor = {codecs.encode(good_cbor_encoded, "hex")}')
    print(f' bad_cbor = {codecs.encode(bad_cbor_encoded, "hex")}')
    print(
        "                                                                                    ^^^^^^^^^^\n"
    )

    # Write it to json, read it back in, write it back out
    bad_cbor_bundle.to_json_file("bad_cbor_bundle.json")
    bad_cbor_again = Bundle.from_json_file("bad_cbor_bundle.json")
    bad_cbor_again.to_json_file("bad_cbor_again.json")

    # Attempt to decode the bytes, which will fail with a CBOR decode value error
    print("\nAttempt to decode the bad encoding. This should fail:\n")
    try:
        Bundle.from_bytes(bad_cbor_encoded)
    except cbor2.CBORDecodeValueError:
        traceback.print_exc()

    print()

    # Another example, with bad CBOR encoding of an EID. CBOR encoded EIDs are an
    # array (major type 4) - in this case additional info 31 would be a valid value,
    # so we set the additional info to 30, which is an invalid value for an array.

    # Restore the lifetime and then change the dest_eid to be invalid
    primary_block.lifetime = orig_lifetime
    orig_dest_eid = primary_block.dest_eid
    primary_block.dest_eid = InvalidCBOR(value=orig_dest_eid, additional_info=30)

    # Use it to create a bundle object
    bad_cbor_bundle_2 = Bundle(
        pri_block=copy.deepcopy(primary_block),
    )

    # Encode it to bytes, which contains the invalid CBOR encoding
    bad_cbor_encoded = bad_cbor_bundle_2.to_bytes()

    # Write it to json, read it back in, write it back out
    bad_cbor_bundle_2.to_json_file("bad_cbor_bundle_2_2.json")
    bad_cbor_again = Bundle.from_json_file("bad_cbor_bundle_2_2.json")
    bad_cbor_again.to_json_file("bad_cbor_again_2.json")

    # Attempt to decode the bytes, which should fail with a CBOR decode value error
    print("\nAttempt to decode the bad encoding. This should fail:\n")
    try:
        Bundle.from_bytes(bad_cbor_encoded)
    except cbor2.CBORDecodeValueError:
        traceback.print_exc()

    print()

    # To demonstrate the checks, attempt to create an EID with an invalid additional
    # info of 31, which as noted above is NOT invalid, so this produces a ValueError
    # on creation.
    try:
        invalid_eid = (
            InvalidCBOR(
                value=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
                additional_info=31,
            ),
        )
    except ValueError:
        traceback.print_exc()

    print()

    # Lastly, for all types, the only invalid values are 28-30 or 31, so attempting
    # to set the invalid additional_info to a different number, 27 in this case,
    # also produces a ValueError on creation.
    try:
        invalid_eid = (
            InvalidCBOR(
                value=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
                additional_info=27,
            ),
        )
    except ValueError:
        traceback.print_exc()

    another_bad_bundle = copy.deepcopy(good_cbor_bundle)

    # replace the lifetime (3600000 = 0x0036ee80), which in cbor is encoded as major
    # type 0, additional info 26 (0x1a) and then 4 bytes for the value, with the
    # same encoding, but missing the last byte
    another_bad_bundle.pri_block.lifetime = RawData(b"\x1a\x00\x36\xee")

    # Testing encoding as json and from json
    another_bad_json = another_bad_bundle.to_json()
    another_bad_from_json = Bundle.from_json(another_bad_json)
    another_bad_json_from_json = another_bad_from_json.to_json()
    assert another_bad_json == another_bad_json_from_json

    # Encode as bytes and print comparison to the good bundle
    another_bad_encoded = another_bad_bundle.to_bytes()

    print(f'\ngood_cbor = {codecs.encode(good_cbor_encoded, "hex")}')
    print(f' bad_cbor = {codecs.encode(another_bad_encoded, "hex")}')
    print(
        "                                                                                    ^^^^^^^^^^"
    )

    # Try to decode the bundle. It should fail with a premature end-of-stream error.
    print("Attempt to decode the bad encoding. This should fail:\n")
    try:
        another_bad_decoded = Bundle.from_bytes(another_bad_encoded)
    except cbor2.CBORDecodeEOF:
        traceback.print_exc()

    print("\nDone")


def test_bundle_eq_operator():
    # These two bundles should be equivalent because they're created by the same
    # generator function 'create_valid_bundle'
    bundle_a = create_valid_bundle()
    bundle_b = create_valid_bundle()
    assert bundle_a == bundle_b

if __name__ == "__main__":
    test_legacy_suite()
    test_bundle_eq_operator()