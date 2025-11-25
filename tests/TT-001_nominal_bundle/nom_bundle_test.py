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

# DTN Nominal Bundle Test


# prerequisites:
# - DTN Gen / DTN CLA packages installed (installed in COSMOS if using that)
# - HDTN running in relay mode (UDP) on target system - configuration file: hdtn_udp_relay.json
# - Wireshark is capturing traffic on ports 4556 and 4558


import sys, os
import codecs
import traceback

from dtntools import dtngen, dtncla

from dtntools.dtngen.blocks import (
    PrimaryBlock,
    BundleAgeBlock,
    HopCountBlock,
    PrevNodeBlock,
    CustodyTransferBlock,
    CompressedReportingBlock,
    PayloadBlock,
    CanonicalBlock,
    PayloadBlockSettings,
    PrimaryBlockSettings,
    UnknownBlock,
)

from dtntools.dtngen.bundle import Bundle


from dtntools.dtngen.types import (
    TypeWarning,
    BlockPCFlags,
    BlockType,
    BundlePCFlags,
    StatusRRFlags,
    CRCFlag,
    CRCType,
    EID,
    CreationTimestamp,
    HopCountData,
    CTEBData,
    CREBData,
    InvalidCBOR,
)


from dtntools.dtncla.udp import UdpRxSocket, UdpTxSocket


input_response = input("Enter IP address of HDTN to send to (X.X.X.X), enter 'end' to exit: ")
print("You entered: ", input_response)

if input_response == "end":
    sys.exit(0) # this 0 indicates a successful exit, this could have been a string but would indicate an error on exit

HDTN_IP   = input_response
HDTN_PORT = 4556
LOCAL_IP = "0.0.0.0"
LOCAL_PORT = 4558

print("HDTN Target: ", HDTN_IP, ":", HDTN_PORT)

# ADU's not yet implemented, skipping


#  Nominal bundle creation
def nom_bundle_test(): 
    # testing a few ways to report what requirements are in this here
    print(";*******************************************************************************")
    print(";  Nominal Bundle Test")
    print(";  Verifying requirements:")
    print(";      DTN.TEST.00115: The Data Generator test tool shall create a configurable")
    print(";                      number of CBOR-encoded data bundles with a specified")
    print(";                      payload size")
    print(";      DTN.TEST.00120: Upon request, the Data Generator test tool shall set ")
    print(";                      bundle processing control flags to specified values.")
    print(";      DTN.TEST.00130: Upon request, the Data Generator test tool shall create")
    print(";                      one or more of the following canonical blocks for a ")
    print(";                      bundle:")
    print(";                          a. Age Block")
    print(";                          b. Hop Count Block")
    print(";                          c. Previous Node block")
    print(";                          d. Custody Transfer Extension Block (CTEB)")
    print(";                          e. Compressed Reporting Extension Block (CREB)")
    print(";                          f. Payload block.")
    print(";      DTN.TEST.00135: The Data Generator test tool shall set any data in the")
    print(";                      primary block or in any element of a canonical block")
    print(";                      (except the block-specific data) to the value specified")
    print(";                      by the user.")
    print(";      DTN.TEST.00140: The Data Generator test tool shall set any block-specific")
    print(";                      data to the value specified by the user for the following")
    print(";                      extension blocks:")
    print(";                          a. Age Block")
    print(";                          b. Hop Count Block")
    print(";                          c. Previous Node block")
    print(";                          d. Custody Transfer Extension Block (CTEB)")
    print(";                          e. Compressed Reporting Extension Block (CREB).")
    print("; NOTE: 141 is currently not implemented and thus not tested yet.")
    print(";      DTN.TEST.00141: The Data Generator test tool shall set any block-specific")
    print(";                      data in the payload block to the value specified by the")
    print(";                      user for administrative record bundles of the following")
    print(";                      types:")
    print(";                          - Bundle Status Reports (BSR)")
    print(";                          - Compressed Reporting Signals (CRS)")
    print(";                          - Custody Signals")
    print(";      DTN.TEST.00142: Upon request, the Data Generator test tool shall set the")
    print(";                      bundle payload length to a random value within a")
    print(";                      specified range.")
    print(";      DTN.TEST.00155: The Data Generator test tool shall write the created")
    print(";                      CBOR-encoded bundles to files (one file per data unit)")
    print(";                      and store them in a configurable location")
    print(";      DTN.TEST.00210: Upon request, the Data Sender test tool shall send")
    print(";                      CBOR-encoded bundles from a configurable location to a")
    print(";                      DTN Node.")
    print(";      DTN.TEST.00225 (partial): The Data Sender test tool shall send bundles to")
    print(";                      a DTN Node over the following convergence layers (TBR):")
    print(";                          - UDP")
    print(";                          - cFS Message Bus")
    print(";                          - TCPCL")
    print(";                          - EPP")
    print(";                          - LTP/UDP")
    print(";                          - LTP/EPP")
    print(";      DTN.TEST.00230: Upon request, the Data Sender test tool shall report the")
    print(";                      number of sent bundles.")
    print(";      DTN.TEST.00310 (partial): Upon request, the Data Receiver test tool shall")
    print(";                      receive bundles from a DTN Node over the following")
    print(";                      convergence layers (TBR):")
    print(";                          - UDP")
    print(";                          - cFS Message Bus")
    print(";                          - TCPCL")
    print(";                          - EPP")
    print(";                          - LTP/UDP")
    print(";                          - LTP/EPP")
    print(";      DTN.TEST.00315: The Data Receiver test tool shall write the received")
    print(";                      CBOR-encoded bundles to files (one file per data unit)")
    print(";                      that are stored in a configurable location.")
    print(";      DTN.TEST.00320: Upon request, the Data Receiver test tool shall report")
    print(";                      the number of received bundles.")
    print(";      DTN.TEST.00400: Upon request, the Data Interpreter test tool shall decode")
    print(";                      a stored CBOR-encoded data bundle, and respond with the")
    print(";                      decoded content of the bundle.")
    print(";      DTN.TEST.00410: Upon request, the Data Interpreter shall write the")
    print(";                      decoded bundle to a json file.")
    print(";*******************************************************************************")
    
    # Command the creation of various block with nominal parameters (Req 130):
    # - Primary block
    # - Age
    # - Hop Count
    # - Previous node
    # - Custody Transfer Extension Block (CTEB)
    # - Compressed Reporting Extension Block (CREB)
    # - Payload
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 1.0: Create Nominal Blocks (Reqs. 130, 135, 140)")
    print(  ";*******************************************************************************")
    print(  ";*******************************************************************************")
    print(  ";  Step 1.1: Create a Primary Block (Reqs 135)")
    print(  ";*******************************************************************************")
    print(  "") 
    primary_block = PrimaryBlock(
        version=7,
        control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
        crc_type=CRCType.CRC16_X25,
        dest_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 1}}),
        src_eid=EID({"uri": 2, "ssp": {"node_num": 101, "service_num": 1}}),
        rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        creation_timestamp=CreationTimestamp({"time": 755533838904, "sequence": 0}),
        lifetime=3600000,
        crc=CRCFlag.CALCULATE,
        # The CRC was changed to be auto-calculated after the bundle being flagged at HDTN with a crc error
        # the following CRC was what it reported this block as before switching. CRC errors will be tested eventually,
        # but not against the test tool
        # # crc=b"\xf4\x0a",
    )
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00135) Primary Block Created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 1.2: Create an Age Block (Reqs. 130, 135, 140)")
    print(  ";*******************************************************************************")
    print(  "") 
    
    age_block = BundleAgeBlock(
        blk_type=BlockType.AUTO,
        blk_num=2,
        control_flags=BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC,
        crc_type=CRCType.CRC16_X25,
        bundle_age=108000,
        crc=CRCFlag.CALCULATE,
    )
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Age Block Created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 1.3: Create a Hop Count Block (Reqs. 130, 135, 140)")
    print(  ";*******************************************************************************")
    print(  "") 
    
    hop_count_block = HopCountBlock(
        blk_type=BlockType.AUTO,
        blk_num=3,
        control_flags=BlockPCFlags.FRAG_REPLICATE,
        crc_type=CRCType.CRC16_X25,
        hop_data=HopCountData({"hop_limit": 15, "hop_count": 3}),
        crc=CRCFlag.CALCULATE,
    )
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Hop Count Block Created.")
    
    print("\n;*******************************************************************************")
    print(  ";  Step 1.4: Create a Previous node Block (Reqs. 130, 135, 140)")
    print(  ";*******************************************************************************")
    print(  "") 
    
    prev_node_block = PrevNodeBlock(
        blk_type=BlockType.AUTO,
        blk_num=6,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        prev_eid=EID({"uri": 2, "ssp": {"node_num": 300, "service_num": 2}}),
        crc=CRCFlag.CALCULATE,
    )
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Previous Node Block Created.")
    
    # This block of commented-out code is currently not supported by HDTN
    print("\n;*******************************************************************************")
    print(  ";  Step 1.5: Create a Custody Transfer Extension Block (CTEB) (Reqs. 130, 135, 140)")
    print(  ";*******************************************************************************")
    print(  "") 
    
    cte_block = CustodyTransferBlock(
        blk_type=BlockType.AUTO,
        blk_num=4,
        control_flags=BlockPCFlags.REP_UNPROC,
        crc_type=CRCType.CRC16_X25,
        cteb_data=CTEBData(
            {"trans_id": 10,
            "trans_series_id": 2,
            "req_orig_eid": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}})}
        ),
        crc=CRCFlag.CALCULATE,
    )
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Custody Transfer Extension Block Created.")
    
    print("\n;*******************************************************************************")
    print(  ";  Step 1.6: Create a Compressed Reporting Extension Block (CREB) (Reqs. 130, 135, 140)")
    print(  ";*******************************************************************************")
    print(  "") 
    
    cre_block = CompressedReportingBlock(
        blk_type=BlockType.AUTO,
        blk_num=5,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        creb_data=CREBData(
            {"bundle_seq_num": 1,
            "bundle_seq_id": 4,
            "rpt_request_flags": 0,
            "scope_node_id": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}}),
            "rpt_eid": EID({"uri": 2, "ssp": {"node_num": 305, "service_num": 2}})}
        ),
        crc=CRCFlag.CALCULATE,
    )
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Compressed Reporting Extension Block Created.")
    
    print("\n;*******************************************************************************")
    print(  ";  Step 1.7: Create the Payload Blocks (Reqs. 130, 135, 141(unsure on 141), 142)")
    print(  ";*******************************************************************************")
    print(  "") 
    
    payload_block1 = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x0cPrmiary Block Bundle\n",
        crc=CRCFlag.CALCULATE,
    )
    
    payload_block2 = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x0cAge Block Bundle\n",
        crc=CRCFlag.CALCULATE,
    )
    
    payload_block3 = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x0cHop Count Bundle\n",
        crc=CRCFlag.CALCULATE,
    )
    
    payload_block4 = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x0cPrevious Node Block Bundle\n",
        crc=CRCFlag.CALCULATE,
    )
    
    payload_block5 = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x0cCustody Transfer Extension Block Bundle\n",
        crc=CRCFlag.CALCULATE,
    )
    
    payload_block6 = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x0cCompressed Reporting Extension Block Bundle\n",
        crc=CRCFlag.CALCULATE,
    )
    
    payload_block7_settings = PayloadBlockSettings(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload={"min_size": 512, "max_size": 1536},
        crc=CRCFlag.CALCULATE,
    )
    payload_block7 = payload_block7_settings.generate(0)
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00142) Payload Blocks Created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 2.0: Create Bundles from each Block above (Req. 115)")
    print(  ";*******************************************************************************")
    print(  ";*******************************************************************************")
    print(  ";  Step 2.1: Create an Bundle with: Primary and Payload Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    pri_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[payload_block1]
    )
    
    print("--> Primary Bundle in json format:")
    print(pri_block_bundle.to_json())
    
    print(  "--> <*> (DTN.TEST.00115) Primary Bundle (Smallest Valid Bundle) Created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 2.2: Create an Bundle with: Primary, Age, and Payload Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    age_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[age_block, payload_block2]
    )
    
    print("--> Age Block Bundle in json format:")
    print(age_block_bundle.to_json())
    
    print(  "--> <*> (DTN.TEST.00115) Age Block Bundle Created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 2.3: Create an Bundle with: Primary, Hop Count, and Payload Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    hop_count_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[hop_count_block, payload_block3]
    )
    
    print("--> Hop Count Bundle in json format:")
    print(hop_count_block_bundle.to_json())
    
    print(  "--> <*> (DTN.TEST.00115) Hop Count Bundle Created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 2.4: Create an Bundle with: Primary, Previous Node, and Payload Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    prev_node_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[prev_node_block, payload_block4]
    )
    
    print("--> Previous Node Block Bundle in json format:")
    print(prev_node_block_bundle.to_json())
    
    print(  "--> <*> (DTN.TEST.00115) Previous Node Block Bundle Created.")
    
    
    # This block is currently not supported by HDTN, but does not flag an error
    print("\n;*******************************************************************************")
    print(  ";  Step 2.5: Create an Bundle with: Primary, CTE, and Payload Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    cte_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[cte_block, payload_block5]
    )
    
    print("--> Custody Transfer Extension Block Bundle in json format:")
    print(cte_block_bundle.to_json())
    
    print(  "--> <*> (DTN.TEST.00115) Custody Transfer Extension Block Bundle Created.")
    
    
    # This block is currently not supported by HDTN, but does not flag an error
    print("\n;*******************************************************************************")
    print(  ";  Step 2.6: Create a Bundle with: Primary, CRE, and Payload Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    cre_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[cre_block, payload_block6]
    )
    
    print("--> Compressed Reporting Extension Block Bundle in json format:")
    print(cre_block_bundle.to_json())
    
    print(  "--> <*> (DTN.TEST.00115) Compressed Reporting Extension Block Bundle Created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 2.7: Create a Bundle with all Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    all_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[age_block, hop_count_block, prev_node_block, cte_block, cre_block, payload_block7]
    )
    
    print("--> All Block Bundle in json format:")
    print(all_block_bundle.to_json())
    
    print(  "--> <*> (DTN.TEST.00115) All Block Bundle Created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 3.0: Encode each Bundle in Bytes.")
    print(  ";*******************************************************************************")
    print(  "") 
    
    initial_nominal_encoded_bundle = []
    bundle_text = []
    
    # building a list to iterate through when sending
    initial_nominal_encoded_bundle.append(pri_block_bundle.to_bytes()) 
    bundle_text.append("Prmiary Block Bundle")
    initial_nominal_encoded_bundle.append(age_block_bundle.to_bytes()) 
    bundle_text.append("Age Block Bundle")
    initial_nominal_encoded_bundle.append(hop_count_block_bundle.to_bytes()) 
    bundle_text.append("Hop Count Bundle")
    initial_nominal_encoded_bundle.append(prev_node_block_bundle.to_bytes()) 
    bundle_text.append("Previous Node Block Bundle")
    # This block is currently not supported by HDTN, but does not flag an error
    initial_nominal_encoded_bundle.append(cte_block_bundle.to_bytes()) 
    bundle_text.append("Custody Transfer Extension Block Bundle")
    # This block is currently not supported by HDTN, but does not flag an error
    initial_nominal_encoded_bundle.append(cre_block_bundle.to_bytes()) 
    bundle_text.append("Compressed Reporting Extension Block Bundle")
    initial_nominal_encoded_bundle.append(all_block_bundle.to_bytes()) 
    bundle_text.append("All Block Bundle")
    
    # Print the encoded bundles as a hex string
    print("Bundles encoded. Bundle list:")
    index = 0
    while index < len(initial_nominal_encoded_bundle):
        print(f"Encoded {bundle_text[index]}:\n{codecs.encode(initial_nominal_encoded_bundle[index],'hex')}\n")
        index += 1
    
    print(  "--> All Bundles Encoded in Bytes.")
    
    print("\n;*******************************************************************************")
    print(  ";  Step 3.1: Decode a Bundle from encoded bytes and compare to it's original.")
    print(  ";*******************************************************************************")
    print(  "") 
    
    # Decode the encoded bundle bytes
    # all_block_bundle
    decoded_from_bytes_initial_bundle = Bundle.from_bytes(initial_nominal_encoded_bundle[6])
    if not decoded_from_bytes_initial_bundle:
        raise ValueError("Output bundle from bytes could not be parsed.")
    
    # Verify that translating to and from bytes did not break anything
    if ( decoded_from_bytes_initial_bundle.to_json() != all_block_bundle.to_json() ):
        print(" <!> (DTN.TEST.00400) Decoded from Bytes Bundle does not equal pre-encode Bundle. The two bundles are listed below:")
        print("---> All Blocks Bundle:")
        print(all_block_bundle.to_json())
        print("---> De-Coded All Blocks Bundle:")
        print(decoded_from_bytes_initial_bundle.to_json())
        print(" <!> (DTN.TEST.00400) Decoded from Bytes Bundle does not equal pre-encode Bundle. The two bundles are listed above.")
    else:
        print(" <*> (DTN.TEST.00400) Decoded from Bytes Bundle Found to be equal to pre-encoded Bundle.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 4.0: Write each Bundle to a Bytes file (Req. 155).")
    print(  ";*******************************************************************************")
    print(  "") 
    
    nom_send_dir_bytes = "nom_bundles_to_send_bytes"
    
    # create the directory if it does not already exist.
    os.makedirs(nom_send_dir_bytes, exist_ok=True)

    # Write the bundles to bytes files (requirement 155)
    
    pri_block_encoded_bytes_filename = f"{nom_send_dir_bytes}/pri_block_initial_bytesout.bin"
    pri_block_bundle.to_bytes_file(pri_block_encoded_bytes_filename)
    print(  "--> Primary Bundle Bytes File Created.\n")
    
    age_block_encoded_bytes_filename = f"{nom_send_dir_bytes}/age_block_initial_bytesout.bin"
    age_block_bundle.to_bytes_file(age_block_encoded_bytes_filename)
    print(  "--> Age Block Bundle Bytes File Created.\n")
    
    hop_count_encoded_bytes_filename = f"{nom_send_dir_bytes}/hop_count_block_initial_bytesout.bin"
    hop_count_block_bundle.to_bytes_file(hop_count_encoded_bytes_filename)
    print(  "--> Hop Count Bundle Bytes File Created.\n")
    
    prev_node_encoded_bytes_filename = f"{nom_send_dir_bytes}/prev_node_block_initial_bytesout.bin"
    prev_node_block_bundle.to_bytes_file(prev_node_encoded_bytes_filename)
    print(  "--> Previous Node Bundle Bytes File Created.\n")
    
    cte_encoded_bytes_filename = f"{nom_send_dir_bytes}/cte_block_initial_bytesout.bin"
    cte_block_bundle.to_bytes_file(cte_encoded_bytes_filename)
    print(  "--> CTEB Bundle Bytes File Created.\n")
    
    cre_encoded_bytes_filename = f"{nom_send_dir_bytes}/cre_block_initial_bytesout.bin"
    cre_block_bundle.to_bytes_file(cre_encoded_bytes_filename)
    print(  "--> CREB Bundle Bytes File Created.\n")
    
    all_blocks_encoded_bytes_filename = f"{nom_send_dir_bytes}/all_blocks_initial_bytesout.bin"
    all_block_bundle.to_bytes_file(all_blocks_encoded_bytes_filename)
    print(  "--> All Blocks Bundle Bytes File Created.\n")
    
    print(  "--> <*> (DTN.TEST.00155) All Bundles Written to Byte Files.")
    
    print("\n;*******************************************************************************")
    print(  ";  Step 4.1: Read a Bundle from byte file and compare to original (Req. 155).")
    print(  ";*******************************************************************************")
    print(  "") 
    
    # Decode an encoded bundle byte file (all_blocks_encoded_bytes_filename)
    decoded_from_bytes_file_initial_bundle = Bundle.from_bytes_file(all_blocks_encoded_bytes_filename)
    if not decoded_from_bytes_file_initial_bundle:
        raise ValueError("Output bundle from file could not be parsed.")
    
    # Verify that translating to and from a bytes file did not break anything
    if ( decoded_from_bytes_file_initial_bundle.to_json() != all_block_bundle.to_json() ):
        print(" <!> (DTN.TEST.00155) Decoded from Bytes Bundle does not equal pre-encode Bundle. The two bundles are listed below:")
        print("---> All Blocks Bundle:")
        print(all_block_bundle.to_json())
        print("---> De-Coded All Blocks Bundle:")
        print(decoded_from_bytes_file_initial_bundle.to_json())
        print(" <!> (DTN.TEST.00155) Decoded from Bytes Bundle does not equal pre-encode Bundle. The two bundles are listed above.")
    else:
        print(" <*> (DTN.TEST.00155) Decoded from Bytes Bundle Found to be equal to pre-encoded Bundle.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 5.0: Write each Bundle to json files (Req. 155).")
    print(  ";*******************************************************************************")
    print(  "") 
    
    nom_send_dir_json = "nom_bundles_to_send_json"
    
    # create the directory if it does not already exist.
    os.makedirs(nom_send_dir_json, exist_ok=True)

    # Write the bundles to json files (requirement 155)
    
    pri_block_encoded_json_filename = f"{nom_send_dir_json}/pri_block_initial_jsonout.json"
    pri_block_bundle.to_json_file(pri_block_encoded_json_filename)
    print(  "--> Primary Bundle .json File Created.\n")
    
    age_block_encoded_json_filename = f"{nom_send_dir_json}/age_block_initial_jsonout.json"
    age_block_bundle.to_json_file(age_block_encoded_json_filename)
    print(  "--> Age Block Bundle .json File Created.\n")
    
    hop_count_encoded_json_filename = f"{nom_send_dir_json}/hop_count_block_initial_jsonout.json"
    hop_count_block_bundle.to_json_file(hop_count_encoded_json_filename)
    print(  "--> Hop Count Bundle .json File Created.\n")
    
    prev_node_encoded_json_filename = f"{nom_send_dir_json}/prev_node_block_initial_jsonout.json"
    prev_node_block_bundle.to_json_file(prev_node_encoded_json_filename)
    print(  "--> Previous Node Bundle .json File Created.\n")
    
    cte_block_encoded_json_filename = f"{nom_send_dir_json}/cte_block_initial_jsonout.json"
    cte_block_bundle.to_json_file(cte_block_encoded_json_filename)
    print(  "--> CTEB Bundle .json File Created.\n")
    
    cre_block_encoded_json_filename = f"{nom_send_dir_json}/cre_block_initial_jsonout.json"
    cre_block_bundle.to_json_file(cre_block_encoded_json_filename)
    print(  "--> CREB Bundle .json File Created.\n")
    
    all_blocks_encoded_json_filename = f"{nom_send_dir_json}/all_blocks_initial_jsonout.json"
    all_block_bundle.to_json_file(all_blocks_encoded_json_filename)
    print(  "--> All Blocks Bundle .json File Created.\n")
    
    print(  "--> (DTN.TEST.00155, DTN.TEST.00410) All Bundles Written to .json Files.")


    # set 155 to inspection and tell user to verify a random json file
    
    print("\n;*******************************************************************************")
    print(  ";  Step 5.1: Read a Bundle from .json file and compare to original (Req. 155).")
    print(  ";*******************************************************************************")
    print(  "") 
    
    # Decode an encoded bundle file (all_blocks_encoded_json_filename)
    decoded_from_json_file_initial_bundle = Bundle.from_json_file(all_blocks_encoded_json_filename)
    if not decoded_from_json_file_initial_bundle:
        raise ValueError("Output bundle from file could not be parsed.")
    
    # Verify that translating to and from a bytes file did not break anything
    if ( decoded_from_json_file_initial_bundle.to_json() != all_block_bundle.to_json() ):
        print(" <!> (DTN.TEST.00155) Decoded from Bytes Bundle does not equal pre-encode Bundle. The two bundles are listed below:")
        print("---> All Blocks Bundle:")
        print(all_block_bundle.to_json())
        print("---> De-Coded All Blocks Bundle:")
        print(decoded_from_json_file_initial_bundle.to_json())
        print(" <!> (DTN.TEST.00155) Decoded from Bytes Bundle does not equal pre-encode Bundle. The two bundles are listed above.")
    else:
        print(" <*> (DTN.TEST.00155) Decoded from Bytes Bundle Found to be equal to pre-encoded Bundle.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 6.0: Send each Bundle to HDTN and capture the looped-back bundle.")
    print(  ";*******************************************************************************")
    print(  "") 
    
    received_nominal_encoded_bundle = []
    
    # Sending the new bundles to HDTN and receiving them back from HDTN
    
    print("--> Configuring the Data Sender and Data Receiver")
    data_sender = UdpTxSocket(HDTN_IP, HDTN_PORT)
    data_receiver = UdpRxSocket(LOCAL_IP, LOCAL_PORT)
    
    try:
        print("--> Connecting the Data Sender and Data Receiver")
        data_receiver.connect()
        data_sender.connect()
        
        index = 0
        bundle_count = 0
        while index < len(initial_nominal_encoded_bundle):
        
            print(f"--> Sending {bundle_text[index]} to the DTN Node.")
            #data_sender.write(pri_block_bundle_encoded_initial)
            data_sender.write(initial_nominal_encoded_bundle[index])
            
            print(f"--> Waiting for the bundle to be looped back from the DTN Node")
            #rx_bundle = data_receiver.read()
            received_nominal_encoded_bundle.append(data_receiver.read())
            bundle_count += 1
            
            print(f"--> <*> (DTN.TEST.00210, DTN.TEST.00225(Partial), DTN.TEST.00310(Partial)) {bundle_count} bundles received from Node, attempting to decode")
            index += 1
        
    except KeyboardInterrupt:
        pass
    
    except Exception:
        print(traceback.format_exc())
    
    finally:
        print("--> Disconnecting the Data Sender and Data Receiver")
        data_receiver.disconnect()
        data_sender.disconnect()
    
    nomPacketsSent     = data_sender.get_packets_sent()
    nomPacketsReceived = data_receiver.get_packets_received()
    print(f'--> <*> (DTN.TEST.00230) Bundles sent     = {nomPacketsSent}')
    print(f'--> <*> (DTN.TEST.00320) Bundles received = {nomPacketsReceived}')
    
    if (nomPacketsReceived != nomPacketsSent):
        print("--> <!> Bundles Received does not equal Bundles Sent!")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 7.0: Decode and Verify the bundles that were received.")
    print(  ";*******************************************************************************")
    print(  "") 
    
    decoded_bundle = []
    nom_received_dir = "nominal_bundles_received"
    
    # create the directory if it does not already exist.
    os.makedirs(nom_received_dir, exist_ok=True)
    
    # decoded_bundle = Bundle.from_bytes(rx_bundle)
    decoded_bundle = [Bundle.from_bytes(x) for x in received_nominal_encoded_bundle]
    
    index = 0 
    while index < len(received_nominal_encoded_bundle):
        if decoded_bundle[index]:
            print(f"--> Looped back Bundle, {bundle_text[index]} (json format):")
            print(decoded_bundle[index].to_json())
            print(f"--> Writing looped back bundle, {bundle_text[index]}, to JSON file.")
            decoded_bundle[index].to_json_file(f"{nom_received_dir}/received_nominal_bundle{index:03}.json")
            print(f'--> <*> (DTN.TEST.00155, DTN.TEST.00315, DTN.TEST.00400, DTN.TEST.00410) Bundle "{bundle_text[index]}" written to JSON file: "{nom_received_dir}/received_nominal_bundle{index:03}.json".')
        index += 1
    
    
    # verify the primary header matches the one that is set in all bundles
    index = 0
    while index < len(decoded_bundle):
        if( decoded_bundle[index].pri_block.to_json() != primary_block.to_json() ):
            print(f" <!> (DTN.TEST.00120, DTN.TEST.00135) Decoded Received Bundle number {index}'s primary block does not equal the primary block set before sending:")
            print("---> Expected Primary Block:")
            print(primary_block.to_json())
            print(f"---> De-Coded Received Bundle number {index}'s primary block:")
            print(decoded_bundle[index].pri_block.to_json())
            print(" <!> (DTN.TEST.00120, DTN.TEST.00135) Review the blocks above for the mismatch.")
        else:
            print(f" <*> (DTN.TEST.00120, DTN.TEST.00135) Decoded Received Bundle number {index}'s primary block found to be equal to the primary block set before sending.")

        index += 1
    
    
    # that done, now pull out individual items to verify in individual bundles
    
    # find the payload block of the first bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[0].canon_blocks):
        if( decoded_bundle[0].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[0].canon_blocks[cbindex].payload != payload_block1.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 0's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of Primary Bundle:")
        print(payload_block1.to_json())
        print(f"---> De-Coded Received Bundle number 0's payload block:")
        print(decoded_bundle[0].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 0's payload block found to be equal to the payload block set before sending.")
    
    # There are no other items in the first buindle to check
    
    
    # find the payload block of the second bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[1].canon_blocks):
        if( decoded_bundle[1].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[1].canon_blocks[cbindex].payload != payload_block2.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 1's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of Age Block Bundle:")
        print(payload_block2.to_json())
        print(f"---> De-Coded Received Bundle number 1's payload block:")
        print(decoded_bundle[1].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 1's payload block found to be equal to the payload block set before sending.")
    
    
    # add in bundle 2's specific tests here
    # find the age block of the second bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[1].canon_blocks):
        if( decoded_bundle[1].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_AGE):
            break
        cbindex += 1

    # cbindex is expected to be at the age block now
    if( decoded_bundle[1].canon_blocks[cbindex].bundle_age != age_block.bundle_age ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 1's bundle_age does not equal the bundle_age set before sending:")
        print("---> Expected age_block of Age Block Bundle:")
        print(age_block.to_json())
        print(f"---> De-Coded Received Bundle number 1's Age Block:")
        print(decoded_bundle[1].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 1's bundle_age found to be equal to the bundle_age set before sending.")
    
    
    # find the payload block of the third bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[2].canon_blocks):
        if( decoded_bundle[2].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[2].canon_blocks[cbindex].payload != payload_block3.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 2's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of Hop Count Bundle:")
        print(payload_block3.to_json())
        print(f"---> De-Coded Received Bundle number 2's payload block:")
        print(decoded_bundle[2].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 2's payload block found to be equal to the payload block set before sending.")
    
    
    # add in bundle 3's specific tests here
    # find the Hop Count block of the third bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[2].canon_blocks):
        if( decoded_bundle[2].canon_blocks[cbindex].blk_type == BlockType.HOP_COUNT):
            break
        cbindex += 1
    
    # cbindex is expected to be at the Hop Count block
    if( decoded_bundle[2].canon_blocks[cbindex].hop_data.hop_count != (hop_count_block.hop_data.hop_count + 1) ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 2's hop_count does not equal the expected hop_count:")
        print(f"---> Expected hop_count of Hop Count Bundle: {hop_count_block.hop_data.hop_count + 1}")
        print("---> Full set hop count block (should be one less):")
        print(hop_count_block.to_json())
        print(f"---> hop_count of De-Coded Received Bundle: {decoded_bundle[2].canon_blocks[cbindex].hop_data.hop_count}")
        print(f"---> De-Coded Received Bundle number 2's Hop Count block:")
        print(decoded_bundle[2].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the values and blocks above for the error.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 2's hop_count found to be incremented as expected during loopback.")
    
    
    # find the payload block of the forth bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[3].canon_blocks):
        if( decoded_bundle[3].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[3].canon_blocks[cbindex].payload != payload_block4.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 3's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of Previous Node Bundle:")
        print(payload_block4.to_json())
        print(f"---> De-Coded Received Bundle number 3's payload block:")
        print(decoded_bundle[3].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 3's payload block found to be equal to the payload block set before sending.")
    
    
    # add in bundle 4's specific tests here
    # find the Previous Node block of the forth bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[3].canon_blocks):
        if( decoded_bundle[3].canon_blocks[cbindex].blk_type == BlockType.PREVIOUS_NODE):
            break
        cbindex += 1
    
    # cbindex is expected to be at the Previous Node block
    if( decoded_bundle[3].canon_blocks[cbindex].prev_eid.ssp["node_num"] != 10 ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 3's Previous Node not equal the node_num of the HDTN target:")
        print("---> Expected node_num of Previous Node Bundle: 10")
        print(f"---> De-Coded Received Bundle number 3's Previous Node block:")
        print(decoded_bundle[3].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the block above for the error.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 3's Previous Node block found to be equal to the expected node_num for HDTN target.")
    
    
    # the CTEB is currently not supported by HDTN, but it is not rejected, so we can make sure the loopback equals the sent at this time
    # find the payload block of the fifth bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[4].canon_blocks):
        if( decoded_bundle[4].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[4].canon_blocks[cbindex].payload != payload_block5.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 4's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of CTEB Bundle:")
        print(payload_block5.to_json())
        print(f"---> De-Coded Received Bundle number 4's payload block:")
        print(decoded_bundle[4].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 4's payload block found to be equal to the payload block set before sending.")
    
    
    # add in bundle 5's specific tests here
    # find the CTE block of the fifth bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[4].canon_blocks):
        if( decoded_bundle[4].canon_blocks[cbindex].blk_type == BlockType.CUST_TRANS_EXT):
            break
        cbindex += 1
    
    # cbindex is expected to be at the CTE block
    if( decoded_bundle[4].canon_blocks[cbindex].to_json() != cte_block.to_json() ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 4's CTEB does not equal the CTEB set before sending:")
        print("---> Expected CTEB of CTEB Bundle:")
        print(cte_block.to_json())
        print(f"---> De-Coded Received Bundle number 4's CTE block:")
        print(decoded_bundle[4].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 4's CTE block found to be equal to the CTE block set before sending.")
    
    
    # the CREB is currently not supported by HDTN, but it is not rejected, so we can make sure the loopback equals the sent at this time
    # find the payload block of the sixth bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[5].canon_blocks):
        if( decoded_bundle[5].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[5].canon_blocks[cbindex].payload != payload_block6.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 1's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of CREB Bundle:")
        print(payload_block6.to_json())
        print(f"---> De-Coded Received Bundle number 1's payload block:")
        print(decoded_bundle[5].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 5's payload block found to be equal to the payload block set before sending.")
    
    
    # add in bundle 6's specific tests here
    # find the CRE block of the sixth bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[5].canon_blocks):
        if( decoded_bundle[5].canon_blocks[cbindex].blk_type == BlockType.COMP_RPT_EXT):
            break
        cbindex += 1
    
    # cbindex is expected to be at the CRE block
    if( decoded_bundle[5].canon_blocks[cbindex].to_json() != cre_block.to_json() ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 5's CREB does not equal the CREB set before sending:")
        print("---> Expected CREB of CREB Bundle:")
        print(cre_block.to_json())
        print(f"---> De-Coded Received Bundle number 5's CRE block:")
        print(decoded_bundle[5].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 5's CRE block found to be equal to the CRE block set before sending.")
    
    
    # find the payload block of the seventh bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[6].canon_blocks):
        if( decoded_bundle[6].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[6].canon_blocks[cbindex].payload != payload_block7.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00142) Decoded Received Bundle number 6's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of All Blocks Bundle:")
        print(payload_block7.to_json())
        print(f"---> De-Coded Received Bundle number 6's payload block:")
        print(decoded_bundle[6].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00142) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00142) Decoded Received Bundle number 6's payload block found to be equal to the payload block set before sending.")
    
    
    # add in bundle 7's specific tests here (All Blocks)
    # find the age block of the seventh bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[6].canon_blocks):
        if( decoded_bundle[6].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_AGE):
            break
        cbindex += 1

    # cbindex is expected to be at the age block now
    if( decoded_bundle[6].canon_blocks[cbindex].bundle_age != age_block.bundle_age ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's bundle_age does not equal the bundle_age set before sending:")
        print("---> Expected age_block of Age Block Bundle:")
        print(age_block.to_json())
        print(f"---> De-Coded Received Bundle number 6's Age Block:")
        print(decoded_bundle[6].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's bundle_age found to be equal to the bundle_age set before sending.")
    
    
    # find the Hop Count block of the seventh bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[6].canon_blocks):
        if( decoded_bundle[6].canon_blocks[cbindex].blk_type == BlockType.HOP_COUNT):
            break
        cbindex += 1
    
    # cbindex is expected to be at the Hop Count block
    if( decoded_bundle[6].canon_blocks[cbindex].hop_data.hop_count != (hop_count_block.hop_data.hop_count + 1) ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's hop_count does not equal the expected hop_count:")
        print(f"---> Expected hop_count of Hop Count Bundle: {hop_count_block.hop_data.hop_count + 1}")
        print("---> Full set hop count block (should be one less):")
        print(hop_count_block.to_json())
        print(f"---> hop_count of De-Coded Received Bundle: {decoded_bundle[6].canon_blocks[cbindex].hop_data.hop_count}")
        print(f"---> De-Coded Received Bundle number 6's Hop Count block:")
        print(decoded_bundle[6].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the values and blocks above for the error.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's hop_count found to be incremented as expected during loopback.")
    
    
    # find the Previous Node block of the seventh bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[6].canon_blocks):
        if( decoded_bundle[6].canon_blocks[cbindex].blk_type == BlockType.PREVIOUS_NODE):
            break
        cbindex += 1
    
    # cbindex is expected to be at the Previous Node block
    if( decoded_bundle[6].canon_blocks[cbindex].prev_eid.ssp["node_num"] != 10 ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's Previous Node not equal the node_num of the HDTN target:")
        print("---> Expected node_num of Previous Node Bundle: 10")
        print(f"---> De-Coded Received Bundle number 6's Previous Node block:")
        print(decoded_bundle[6].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the block above for the error.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's node_num found to be equal to the expected node_num for HDTN target.")
    
    
    # the CTEB is currently not supported by HDTN, but it is not rejected, so we can make sure the loopback equals the sent at this time
    # find the CTE block of the seventh bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[6].canon_blocks):
        if( decoded_bundle[6].canon_blocks[cbindex].blk_type == BlockType.CUST_TRANS_EXT):
            break
        cbindex += 1
    
    # cbindex is expected to be at the CTE block
    if( decoded_bundle[6].canon_blocks[cbindex].to_json() != cte_block.to_json() ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's CTEB does not equal the CTEB set before sending:")
        print("---> Expected CTEB of CTEB Bundle:")
        print(cte_block.to_json())
        print(f"---> De-Coded Received Bundle number 6's CTE block:")
        print(decoded_bundle[6].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's CTE block found to be equal to the CTE block set before sending.")
    
    
    # the CREB is currently not supported by HDTN, but it is not rejected, so we can make sure the loopback equals the sent at this time
    # find the CRE block of the seventh bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[6].canon_blocks):
        if( decoded_bundle[6].canon_blocks[cbindex].blk_type == BlockType.COMP_RPT_EXT):
            break
        cbindex += 1
    
    # cbindex is expected to be at the CRE block
    if( decoded_bundle[6].canon_blocks[cbindex].to_json() != cre_block.to_json() ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's CREB does not equal the CREB set before sending:")
        print("---> Expected CREB of CREB Bundle:")
        print(cre_block.to_json())
        print(f"---> De-Coded Received Bundle number 6's CRE block:")
        print(decoded_bundle[6].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's CRE block found to be equal to the CRE block set before sending.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 8.0: Re-generate Blocks changing a few header fields (Req. 135).")
    print(  ";*******************************************************************************")
    print(  ";*******************************************************************************")
    print(  ";  Step 8.1: Re-generate Primary Block (Req. 135)")
    print(  ";*******************************************************************************")
    print(  "") 
    # the change for this Bundle: reducing the lifetime, and the CRC will be different due to that as well
    primary_block = PrimaryBlock(
        version=7,
        control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
        crc_type=CRCType.CRC16_X25,
        dest_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 1}}),
        src_eid=EID({"uri": 2, "ssp": {"node_num": 101, "service_num": 1}}),
        rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        creation_timestamp=CreationTimestamp({"time": 755533838904, "sequence": 0}),
        lifetime=3200000,  # was lifetime=3600000,
        crc=CRCFlag.CALCULATE #  this is not the previous value, just how to set the crc: crc=b"\xf4\x0a"
    )
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00135) Primary Block Re-created.")
    
    print("\n;*******************************************************************************")
    print(  ";  Step 8.2: Re-generate Age Block (Req. 135)")
    print(  ";*******************************************************************************")
    print(  "") 
    # changing the bundle_age, blk_num, and the CRC changes as well due to the values changing in the block
    age_block = BundleAgeBlock(
        blk_type=BlockType.AUTO,
        blk_num=4, # was blk_num=2,
        control_flags=BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC,
        crc_type=CRCType.NONE, # was: crc_type=CRCType.CRC16_X25,
        bundle_age=88000, # bundle_age=108000,
        # was(removed due to CRCType.NONE): crc=CRCFlag.CALCULATE, # will be different due to blk_num change
    )
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Age Block Re-created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 8.3: Re-generate Hop Count Block (Req. 135)")
    print(  ";*******************************************************************************")
    print(  "") 
    # changing the hop_data, crc_type, and the CRC changes as well due to the values changing in the block
    hop_count_block = HopCountBlock(
        blk_type=BlockType.AUTO,
        blk_num=3,
        control_flags=BlockPCFlags.FRAG_REPLICATE,
        crc_type=CRCType.CRC32_C, # was crc_type=CRCType.CRC16_X25,
        hop_data=HopCountData({"hop_limit": 6, "hop_count": 2}), # was: hop_data=HopCountData({"hop_limit": 15, "hop_count": 3}),
        crc=CRCFlag.CALCULATE,
    )
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Hop Count Block Re-created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 8.4: Re-generate Previous Node Block (Req. 135)")
    print(  ";*******************************************************************************")
    print(  "") 
    # changing the prev_eid, and the CRC changes as well due to the values changing in the block
    prev_node_block = PrevNodeBlock(
        blk_type=BlockType.AUTO,
        blk_num=6,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        prev_eid=EID({"uri": 2, "ssp": {"node_num": 222, "service_num": 2}}), # was prev_eid=EID({"uri": 2, "ssp": {"node_num": 300, "service_num": 2}}),
        crc=CRCFlag.CALCULATE,
    )
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Previous Node Block Re-created.")
    
    
    # This block is currently not supported by HDTN, but does not flag an error
    print("\n;*******************************************************************************")
    print(  ";  Step 8.5: Re-generate Custody Transfer Extension Block (CTEB) (Req. 135)")
    print(  ";*******************************************************************************")
    print(  "") 
    # changing the cteb_data, blk_num, and the CRC changes as well due to the values changing in the block
    # (HDTN esstially ignores this type of block, it is not supported, so these values may break it when it supports it)
    cte_block = CustodyTransferBlock(
        blk_type=BlockType.AUTO,
        blk_num=2, # this is changed from 4 because Age Block is now 4
        control_flags=BlockPCFlags.REP_UNPROC,
        crc_type=CRCType.CRC16_X25,
        cteb_data=CTEBData(
            {"trans_id": 7,
            "trans_series_id": 4,
            "req_orig_eid": EID({"uri": 2, "ssp": {"node_num": 202, "service_num": 2}})}
        ),
        # was:  
        # cteb_data=CTEBData(
        #     {"trans_id": 10,
        #     "trans_series_id": 2,
        #     "req_orig_eid": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}})}
        # ),
        crc=CRCFlag.CALCULATE,
    )
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Custody Transfer Extension Block Re-created.")
    
    
    # This block is currently not supported by HDTN, but does not flag an error
    print("\n;*******************************************************************************")
    print(  ";  Step 8.6: Re-generate Compressed Reporting Extension Block (CREB) (Req. 135)")
    print(  ";*******************************************************************************")
    print(  "") 
    # changing the creb_data, and the CRC changes as well due to the values changing in the block
    # (HDTN esstially ignores this type of block, it is not supported, so these values may break it when it supports it)
    cre_block = CompressedReportingBlock(
        blk_type=BlockType.AUTO,
        blk_num=5,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        creb_data=CREBData(
            {"bundle_seq_num": 2,
            "bundle_seq_id": 5,
            "rpt_request_flags": 0,
            "scope_node_id": EID({"uri": 2, "ssp": {"node_num": 123, "service_num": 2}}),
            "rpt_eid": EID({"uri": 2, "ssp": {"node_num": 125, "service_num": 3}})}
        ),
        # was:
        # creb_data=CREBData(
        #     {"bundle_seq_num": 1,
        #     "bundle_seq_id": 4,
        #     "rpt_request_flags": 0,
        #     "scope_node_id": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}}),
        #     "rpt_eid": EID({"uri": 2, "ssp": {"node_num": 305, "service_num": 2}})}
        # ),
        crc=CRCFlag.CALCULATE,
    )
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Compressed Reporting Extension Block Re-created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 8.7: Re-generate Payload Blocks (Req. 135)")
    print(  ";*******************************************************************************")
    print(  "") 
    
    # changing the payloads, and the CRC changes as well due to the values changing in the block
    payload_block1 = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x0cRe-generated Prmiary Block Bundle\n",
        crc=CRCFlag.CALCULATE,
    )
    
    payload_block2 = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x0cRe-generated Age Block Bundle\n",
        crc=CRCFlag.CALCULATE,
    )
    
    payload_block3 = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x0cRe-generated Hop Count Bundle\n",
        crc=CRCFlag.CALCULATE,
    )
    
    payload_block4 = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x0cRe-generated Previous Node Block Bundle\n",
        crc=CRCFlag.CALCULATE,
    )
    
    payload_block5 = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x0cRe-generated Custody Transfer Extension Block Bundle\n",
        crc=CRCFlag.CALCULATE,
    )
    
    payload_block6 = PayloadBlock(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload=b"\x00\x0cRe-generated Compressed Reporting Extension Block Bundle\n",
        crc=CRCFlag.CALCULATE,
    )
    
    # The nature of the .generate function is to change hte payload, so this is re-generated with a different payload.
    payload_block7_settings = PayloadBlockSettings(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload={"min_size": 512, "max_size": 1536},
        crc=CRCFlag.CALCULATE,
    )
    payload_block7 = payload_block7_settings.generate(0)
    
    print(  "--> <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00142) Payload Block Re-created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 9.0: Re-create Bundles from each Re-created Block above (Req. 115)")
    print(  ";*******************************************************************************")
    print(  ";*******************************************************************************")
    print(  ";  Step 9.1: Re-create the Bundle with: Primary and Payload Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    pri_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[payload_block1]
    )
    
    print("--> Re-created Primary Bundle in json format:")
    print(pri_block_bundle.to_json())
    
    print(  "--> Primary Bundle (Smallest Valid Bundle) Re-created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 9.2: Re-create the Bundle with: Primary, Age, and Payload Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    age_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[age_block, payload_block2]
    )
    
    print("--> Re-created Age Block Bundle in json format:")
    print(age_block_bundle.to_json())
    
    print(  "--> Age Block Bundle Re-created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 9.3: Re-create the Bundle with: Primary, Hop Count, and Payload Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    hop_count_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[hop_count_block, payload_block3]
    )
    
    print("--> Re-created Hop Count Bundle in json format:")
    print(hop_count_block_bundle.to_json())
    
    print(  "--> Hop Count Bundle Re-created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 9.4: Re-create the Bundle with: Primary, Previous Node, and Payload Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    prev_node_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[prev_node_block, payload_block4]
    )
    
    print("--> Re-created Previous Node Block Bundle in json format:")
    print(prev_node_block_bundle.to_json())
    
    print(  "--> Previous Node Block Bundle Re-created.")
    
    
    # This block is currently not supported by HDTN, but does not flag an error
    print("\n;*******************************************************************************")
    print(  ";  Step 9.5: Re-create the Bundle with: Primary, CTE, and Payload Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    cte_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[cte_block, payload_block5]
    )
    
    print("--> Re-created Custody Transfer Extension Block Bundle in json format:")
    print(cte_block_bundle.to_json())
    
    print(  "--> Custody Transfer Extension Block Bundle Re-created.")
    
    
    # This block is currently not supported by HDTN, but does not flag an error
    print("\n;*******************************************************************************")
    print(  ";  Step 9.6: Re-create the Bundle with: Primary, CRE, and Payload Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    cre_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[cre_block, payload_block6]
    )
    
    print("--> Re-created Compressed Reporting Extension Block Bundle in json format:")
    print(cre_block_bundle.to_json())
    
    print(  "--> Compressed Reporting Extension Block Bundle Re-created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 9.7: Re-create the Bundle Bundle with all Blocks")
    print(  ";*******************************************************************************")
    print(  "") 
    all_block_bundle = Bundle(
        pri_block=primary_block,
        canon_blocks=[age_block, hop_count_block, prev_node_block, cte_block, cre_block, payload_block7]
    )
    
    print("--> Re-created All Block Bundle in json format:")
    print(all_block_bundle.to_json())
    
    print(  "--> All Block Bundle Re-created.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 10.0: Encode each Bundle in Bytes.")
    print(  ";*******************************************************************************")
    print(  "") 
    
    recreated_nominal_encoded_bundle = []
    bundle_text = []
    
    # building a list to iterate through when sending
    recreated_nominal_encoded_bundle.append(pri_block_bundle.to_bytes()) 
    bundle_text.append("Re-created Primary Block Bundle")
    recreated_nominal_encoded_bundle.append(age_block_bundle.to_bytes()) 
    bundle_text.append("Re-created Age Block Bundle")
    recreated_nominal_encoded_bundle.append(hop_count_block_bundle.to_bytes()) 
    bundle_text.append("Re-created Hop Count Bundle")
    recreated_nominal_encoded_bundle.append(prev_node_block_bundle.to_bytes()) 
    bundle_text.append("Re-created Previous Node Block Bundle")
    # This block is currently not supported by HDTN, but does not flag an error
    recreated_nominal_encoded_bundle.append(cte_block_bundle.to_bytes()) 
    bundle_text.append("Re-created Custody Transfer Extension Block Bundle")
    # This block is currently not supported by HDTN, but does not flag an error
    recreated_nominal_encoded_bundle.append(cre_block_bundle.to_bytes()) 
    bundle_text.append("Re-created Compressed Reporting Extension Block Bundle")
    recreated_nominal_encoded_bundle.append(all_block_bundle.to_bytes()) 
    bundle_text.append("Re-created All Block Bundle")
    
    # Print the encoded bundles as a hex string
    #print(f'Primary bundle encoded:\n{codecs.encode(pri_block_bundle_encoded_initial,"hex")}\n')
    print("Re-created Bundles encoded. Bundle list:")
    index = 0
    while index < len(recreated_nominal_encoded_bundle):
        print(f"Encoded {bundle_text[index]}:\n{codecs.encode(recreated_nominal_encoded_bundle[index],'hex')}\n")
        index += 1
    
    print(  "--> All Bundles Encoded in Bytes.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 10.1: Decode a Bundle from encoded bytes and compare to it's original.")
    print(  ";*******************************************************************************")
    print(  "") 
    
    # Decode the all_block_bundle encoded bundle bytes
    decoded_from_bytes_recreated_bundle = Bundle.from_bytes(recreated_nominal_encoded_bundle[6])
    if not decoded_from_bytes_recreated_bundle:
        raise ValueError("Output bundle from bytes could not be parsed.")
    
    # Verify that translating to and from bytes did not break anything
    if ( decoded_from_bytes_recreated_bundle.to_json() != all_block_bundle.to_json() ):
        print(" <!> (DTN.TEST.00400) Decoded from Bytes Re-Created Bundle does not equal pre-encode Bundle. The two bundles are listed below:")
        print("---> All Blocks Bundle:")
        print(all_block_bundle.to_json())
        print("---> De-Coded All Blocks Bundle:")
        print(decoded_from_bytes_recreated_bundle.to_json())
        print(" <!> (DTN.TEST.00400) Decoded from Bytes Bundle does not equal pre-encode Bundle. The two bundles are listed above.")
    else:
        print(" <*> (DTN.TEST.00400) Decoded from Bytes Bundle Found to be equal to pre-encoded Bundle.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 11.0: Send each Bundle to HDTN and capture the looped-back bundle.")
    print(  ";*******************************************************************************")
    print(  "") 
    
    received_recreated_nominal_encoded_bundle = []
    
    # Sending the re-created bundles to HDTN and receiving them back from HDTN
    
    print("--> Configuring the Data Sender and Data Receiver")
    data_sender = UdpTxSocket(HDTN_IP, HDTN_PORT)
    data_receiver = UdpRxSocket(LOCAL_IP, LOCAL_PORT)
    
    try:
        print("--> Connecting the Data Sender and Data Receiver")
        data_receiver.connect()
        data_sender.connect()
        
        index = 0
        bundle_count = 0
        while index < len(recreated_nominal_encoded_bundle):
        
            print(f"--> Sending {bundle_text[index]} to the DTN Node.")
            #data_sender.write(pri_block_bundle_encoded_initial)
            data_sender.write(recreated_nominal_encoded_bundle[index])
            
            print(f"--> Waiting for the bundle to be looped back from the DTN Node")
            #rx_bundle = data_receiver.read()
            received_recreated_nominal_encoded_bundle.append(data_receiver.read())
            bundle_count += 1
            
            print(f"--> <*> (DTN.TEST.00210, DTN.TEST.00225(Partial), DTN.TEST.00310(Partial)) {bundle_count} bundles received from Node, attempting to decode")
            index += 1
        
    except KeyboardInterrupt:
        pass
    
    except Exception:
        print(traceback.format_exc())
    
    finally:
        print("--> Disconnecting the Data Sender and Data Receiver")
        data_receiver.disconnect()
        data_sender.disconnect()
    
    nomReCreatedPacketsSent     = data_sender.get_packets_sent()
    nomReCreatedPacketsReceived = data_receiver.get_packets_received()
    print(f'--> <*> (DTN.TEST.00230) Bundles sent     = {nomReCreatedPacketsSent}')
    print(f'--> <*> (DTN.TEST.00320) Bundles received = {nomReCreatedPacketsReceived}')
    
    if (nomReCreatedPacketsReceived != nomReCreatedPacketsSent):
        print("--> <!> Bundles Received does not equal Bundles Sent!")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 12.0: Decode and Verify the bundles that were received.")
    print(  ";*******************************************************************************")
    print(  "") 
    
    decoded_bundle = []
    recreated_received_dir = "recreated_nom_bundles_received"
    
    # create the directory if it does not already exist.
    os.makedirs(recreated_received_dir, exist_ok=True)
    
    # decoded_bundle = Bundle.from_bytes(rx_bundle)
    decoded_bundle = [Bundle.from_bytes(x) for x in received_recreated_nominal_encoded_bundle]
    
    index = 0 
    while index < len(received_recreated_nominal_encoded_bundle):
        if decoded_bundle[index]:
            print(f"--> Looped back Bundle, {bundle_text[index]} (json format):")
            print(decoded_bundle[index].to_json())
            print(f"--> Writing looped back bundle, {bundle_text[index]}, to JSON file.")
            decoded_bundle[index].to_json_file(f"{recreated_received_dir}/recreated_rcvd_nom_bundle{index:03}.json")
            print(f'--> <*> (DTN.TEST.00155, DTN.TEST.00315, DTN.TEST.00400, DTN.TEST.00410) Bundle "{bundle_text[index]}" written to JSON file: "{recreated_received_dir}/recreated_rcvd_nom_bundle{index:03}.json".')
        index += 1
    
    
    # verify the primary header matches the one that is set in all bundles
    index = 0
    while index < len(decoded_bundle):
        if( decoded_bundle[index].pri_block.to_json() != primary_block.to_json() ):
            print(f" <!> (DTN.TEST.00120, DTN.TEST.00135) Decoded Received Bundle number {index}'s primary block does not equal the primary block set before sending:")
            print("---> Expected Primary Block:")
            print(primary_block.to_json())
            print(f"---> De-Coded Received Bundle number {index}'s primary  block:")
            print(decoded_bundle[index].pri_block.to_json())
            print(" <!> (DTN.TEST.00120, DTN.TEST.00135) Review the blocks above for the mismatch.")
        else:
            print(f" <*> (DTN.TEST.00120, DTN.TEST.00135) Decoded Received Bundle number {index}'s primary block found to be equal to the primary block set before sending.")

        index += 1
    
    
    # that done, now pull out individual items to verify in individual bundles
    
    # find the payload block of the first bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[0].canon_blocks):
        if( decoded_bundle[0].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    # temp assert to make sure it is correct: (if the payload block could not be found in the first one then I'm doing something wrong)
    assert decoded_bundle[0].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD
    if( decoded_bundle[0].canon_blocks[cbindex].payload != payload_block1.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 0's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of Primary Bundle:")
        print(payload_block1.to_json())
        print(f"---> De-Coded Received Bundle number 0's payload block:")
        print(decoded_bundle[0].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 0's payload block found to be equal to the payload block set before sending.")
    
    # There are no other items in the first buindle to check
    
    
    # find the payload block of the second bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[1].canon_blocks):
        if( decoded_bundle[1].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[1].canon_blocks[cbindex].payload != payload_block2.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 1's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of Age Block Bundle:")
        print(payload_block2.to_json())
        print(f"---> De-Coded Received Bundle number 1's payload block:")
        print(decoded_bundle[1].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 1's payload block found to be equal to the payload block set before sending.")
    
    
    # add in bundle 2's specific tests here
    # find the age block of the second bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[1].canon_blocks):
        if( decoded_bundle[1].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_AGE):
            break
        cbindex += 1

    # cbindex is expected to be at the age block now
    if( decoded_bundle[1].canon_blocks[cbindex].bundle_age != age_block.bundle_age ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 1's bundle_age does not equal the bundle_age set before sending:")
        print("---> Expected age_block of Age Block Bundle:")
        print(age_block.to_json())
        print(f"---> De-Coded Received Bundle number 1's Age Block:")
        print(decoded_bundle[1].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 1's bundle_age found to be equal to the bundle_age set before sending.")
    
    
    # find the payload block of the third bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[2].canon_blocks):
        if( decoded_bundle[2].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[2].canon_blocks[cbindex].payload != payload_block3.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 2's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of Hop Count Bundle:")
        print(payload_block3.to_json())
        print(f"---> De-Coded Received Bundle number 2's payload block:")
        print(decoded_bundle[2].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 2's payload block found to be equal to the payload block set before sending.")
    
    
    # add in bundle 3's specific tests here
    # find the Hop Count block of the third bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[2].canon_blocks):
        if( decoded_bundle[2].canon_blocks[cbindex].blk_type == BlockType.HOP_COUNT):
            break
        cbindex += 1
    
    # cbindex is expected to be at the Hop Count block
    if( decoded_bundle[2].canon_blocks[cbindex].hop_data.hop_count != (hop_count_block.hop_data.hop_count + 1) ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 2's hop_count does not equal the expected hop_count:")
        print(f"---> Expected hop_count of Hop Count Bundle: {hop_count_block.hop_data.hop_count + 1}")
        print("---> Full set hop count block (should be one less):")
        print(hop_count_block.to_json())
        print(f"---> hop_count of De-Coded Received Bundle: {decoded_bundle[2].canon_blocks[cbindex].hop_data.hop_count}")
        print(f"---> De-Coded Received Bundle number 2's Hop Count block:")
        print(decoded_bundle[2].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the values and blocks above for the error.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 2's hop_count found to be incremented as expected during loopback.")
    
    
    # find the payload block of the forth bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[3].canon_blocks):
        if( decoded_bundle[3].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[3].canon_blocks[cbindex].payload != payload_block4.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 3's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of Previous Node Bundle:")
        print(payload_block4.to_json())
        print(f"---> De-Coded Received Bundle number 3's payload block:")
        print(decoded_bundle[3].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 3's payload block found to be equal to the payload block set before sending.")
    
    
    # add in bundle 4's specific tests here
    # find the Previous Node block of the forth bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[3].canon_blocks):
        if( decoded_bundle[3].canon_blocks[cbindex].blk_type == BlockType.PREVIOUS_NODE):
            break
        cbindex += 1
    
    # cbindex is expected to be at the Previous Node block
    if( decoded_bundle[3].canon_blocks[cbindex].prev_eid.ssp["node_num"] != 10 ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 3's Previous Node not equal the node_num of the HDTN target:")
        print("---> Expected node_num of Previous Node Bundle: 10")
        print(f"---> De-Coded Received Bundle number 3's Previous Node block:")
        print(decoded_bundle[3].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the block above for the error.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 3's Previous Node block found to be equal to the expected node_num for HDTN target.")
    
    
    # the CTEB is currently not supported by HDTN, but it is not rejected, so we can make sure the loopback equals the sent at this time
    # find the payload block of the fifth bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[4].canon_blocks):
        if( decoded_bundle[4].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[4].canon_blocks[cbindex].payload != payload_block5.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 4's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of CTEB Bundle:")
        print(payload_block5.to_json())
        print(f"---> De-Coded Received Bundle number 4's payload block:")
        print(decoded_bundle[4].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 4's payload block found to be equal to the payload block set before sending.")
    
    
    # add in bundle 5's specific tests here
    # find the CTE block of the fifth bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[4].canon_blocks):
        if( decoded_bundle[4].canon_blocks[cbindex].blk_type == BlockType.CUST_TRANS_EXT):
            break
        cbindex += 1
    
    # cbindex is expected to be at the CTE block
    if( decoded_bundle[4].canon_blocks[cbindex].to_json() != cte_block.to_json() ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 4's CTEB does not equal the CTEB set before sending:")
        print("---> Expected CTEB of CTEB Bundle:")
        print(cte_block.to_json())
        print(f"---> De-Coded Received Bundle number 4's CTE block:")
        print(decoded_bundle[4].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 4's CTE block found to be equal to the CTE block set before sending.")
    
    
    # the CREB is currently not supported by HDTN, but it is not rejected, so we can make sure the loopback equals the sent at this time
    # find the payload block of the sixth bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[5].canon_blocks):
        if( decoded_bundle[5].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[5].canon_blocks[cbindex].payload != payload_block6.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 1's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of CREB Bundle:")
        print(payload_block6.to_json())
        print(f"---> De-Coded Received Bundle number 1's payload block:")
        print(decoded_bundle[5].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135) Decoded Received Bundle number 5's payload block found to be equal to the payload block set before sending.")
    
    
    # add in bundle 6's specific tests here
    # find the CRE block of the sixth bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[5].canon_blocks):
        if( decoded_bundle[5].canon_blocks[cbindex].blk_type == BlockType.COMP_RPT_EXT):
            break
        cbindex += 1
    
    # cbindex is expected to be at the CRE block
    if( decoded_bundle[5].canon_blocks[cbindex].to_json() != cre_block.to_json() ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 5's CREB does not equal the CREB set before sending:")
        print("---> Expected CREB of CREB Bundle:")
        print(cre_block.to_json())
        print(f"---> De-Coded Received Bundle number 5's CRE block:")
        print(decoded_bundle[5].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 5's CRE block found to be equal to the CRE block set before sending.")
    
    
    # find the payload block of the seventh bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[6].canon_blocks):
        if( decoded_bundle[6].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_PAYLOAD):
            break
        cbindex += 1
    
    # cbindex is expected to be at the payload block
    if( decoded_bundle[6].canon_blocks[cbindex].payload != payload_block7.payload ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00142) Decoded Received Bundle number 6's payload does not equal the payload set before sending:")
        print("---> Expected Payload Block of All Blocks Bundle:")
        print(payload_block7.to_json())
        print(f"---> De-Coded Received Bundle number 6's payload block:")
        print(decoded_bundle[6].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00142) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00142) (DTN.TEST.00142) Decoded Received Bundle number 6's payload block found to be equal to the payload block set before sending.")
    
    
    # add in bundle 7's specific tests here (All Blocks)
    # find the age block of the seventh bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[6].canon_blocks):
        if( decoded_bundle[6].canon_blocks[cbindex].blk_type == BlockType.BUNDLE_AGE):
            break
        cbindex += 1

    # cbindex is expected to be at the age block now
    if( decoded_bundle[6].canon_blocks[cbindex].bundle_age != age_block.bundle_age ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's bundle_age does not equal the bundle_age set before sending:")
        print("---> Expected age_block of Age Block Bundle:")
        print(age_block.to_json())
        print(f"---> De-Coded Received Bundle number 6's Age Block:")
        print(decoded_bundle[6].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's bundle_age found to be equal to the bundle_age set before sending.")
    
    
    # find the Hop Count block of the seventh bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[6].canon_blocks):
        if( decoded_bundle[6].canon_blocks[cbindex].blk_type == BlockType.HOP_COUNT):
            break
        cbindex += 1
    
    # cbindex is expected to be at the Hop Count block
    if( decoded_bundle[6].canon_blocks[cbindex].hop_data.hop_count != (hop_count_block.hop_data.hop_count + 1) ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's hop_count does not equal the expected hop_count:")
        print(f"---> Expected hop_count of Hop Count Bundle: {hop_count_block.hop_data.hop_count + 1}")
        print("---> Full set hop count block (should be one less):")
        print(hop_count_block.to_json())
        print(f"---> hop_count of De-Coded Received Bundle: {decoded_bundle[6].canon_blocks[cbindex].hop_data.hop_count}")
        print(f"---> De-Coded Received Bundle number 6's Hop Count block:")
        print(decoded_bundle[6].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the values and blocks above for the error.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's hop_count found to be incremented as expected during loopback.")
    
    
    # find the Previous Node block of the seventh bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[6].canon_blocks):
        if( decoded_bundle[6].canon_blocks[cbindex].blk_type == BlockType.PREVIOUS_NODE):
            break
        cbindex += 1
    
    # cbindex is expected to be at the Previous Node block
    if( decoded_bundle[6].canon_blocks[cbindex].prev_eid.ssp["node_num"] != 10 ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's Previous Node not equal the node_num of the HDTN target:")
        print("---> Expected node_num of Previous Node Bundle: 10")
        print(f"---> De-Coded Received Bundle number 6's Previous Node block:")
        print(decoded_bundle[6].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the block above for the error.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's node_num found to be equal to the expected node_num for HDTN target.")
    
    
    # the CTEB is currently not supported by HDTN, but it is not rejected, so we can make sure the loopback equals the sent at this time
    # find the CTE block of the seventh bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[6].canon_blocks):
        if( decoded_bundle[6].canon_blocks[cbindex].blk_type == BlockType.CUST_TRANS_EXT):
            break
        cbindex += 1
    
    # cbindex is expected to be at the CTE block
    if( decoded_bundle[6].canon_blocks[cbindex].to_json() != cte_block.to_json() ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's CTEB does not equal the CTEB set before sending:")
        print("---> Expected CTEB of CTEB Bundle:")
        print(cte_block.to_json())
        print(f"---> De-Coded Received Bundle number 6's CTE block:")
        print(decoded_bundle[6].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's CTE block found to be equal to the CTE block set before sending.")
    
    
    # the CREB is currently not supported by HDTN, but it is not rejected, so we can make sure the loopback equals the sent at this time
    # find the CRE block of the seventh bundle
    cbindex = 0
    while cbindex < len(decoded_bundle[6].canon_blocks):
        if( decoded_bundle[6].canon_blocks[cbindex].blk_type == BlockType.COMP_RPT_EXT):
            break
        cbindex += 1
    
    # cbindex is expected to be at the CRE block
    if( decoded_bundle[6].canon_blocks[cbindex].to_json() != cre_block.to_json() ):
        print(f" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's CREB does not equal the CREB set before sending:")
        print("---> Expected CREB of CREB Bundle:")
        print(cre_block.to_json())
        print(f"---> De-Coded Received Bundle number 6's CRE block:")
        print(decoded_bundle[6].canon_blocks[cbindex].to_json())
        print(" <!> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Review the blocks above for the mismatch.")
    else:
        print(f" <*> (DTN.TEST.00120, DTN.TEST.00130, DTN.TEST.00135, DTN.TEST.00140) Decoded Received Bundle number 6's CRE block found to be equal to the CRE block set before sending.")
    
    
    print("\n;*******************************************************************************")
    print(  ";  Step 13.0: End of Test.")
    print(  ";*******************************************************************************")
    print(  "") 
    
    
    
    
    







# run the first test
nom_bundle_test()




    
    
    