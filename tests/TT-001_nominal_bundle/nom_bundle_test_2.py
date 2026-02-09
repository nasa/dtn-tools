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

##
## nom_bundle_test_2.py
##
## The majority of the nominal bundle creation verificaion is done in nom_bundle_test.
## This test verifies:
## - timestamp/sequence settings
## - payload size settings
##

set_line_delay(0)

import codecs
import subprocess
import time
import traceback
import warnings
from datetime import datetime

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


print("**********************************************************************")
print("Test 1 - Timestamp/Sequence settings - - Rqmnt: 00155(part)")
print("**********************************************************************")

print("----------------------------------------------------------------------")
print("Test 1.1 - time: {start: 760000000000, increment: 100}")
print("         sequence: {start: 10}")
print("----------------------------------------------------------------------")

primary_block_settings = PrimaryBlockSettings(
    version=7,
    control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
    crc_type=CRCType.NONE,
    dest_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 1}}),
    src_eid=EID({"uri": 2, "ssp": {"node_num": 101, "service_num": 1}}),
    rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
    creation_timestamp={
        "time": {"start": 760000000000, "increment": 100},
        "sequence": {"start": 10},
    },
    lifetime=3600000,
    #crc=CRCFlag.CALCULATE,
)

payload_block_settings = PayloadBlockSettings(
    blk_type=BlockType.AUTO,
    blk_num=1,
    control_flags=0,
    crc_type=CRCType.NONE,
    payload={"min_size": 20, "max_size": 20},
    #crc=CRCFlag.CALCULATE,
)

## Generate bundles (json files 1-5)

generated_bundles = Bundle.generate(
    num_bundles=5,
    pri_settings=primary_block_settings,
    canon_settings=[payload_block_settings],
)

for idx, x in enumerate(generated_bundles):
    x.to_json_file(f"/bundles/bundle_{idx+1}.json")

expected_time = 760000000000
increment = 100
expected_sequence = 10

print("Time Sequence: ")

status = True
for idx, x in enumerate(generated_bundles):
    decoded_bundle = Bundle.from_json_file(f'/bundles/bundle_{idx+1}.json')
    print (decoded_bundle.pri_block.creation_timestamp.time, 
           decoded_bundle.pri_block.creation_timestamp.sequence)
    
    if decoded_bundle.pri_block.creation_timestamp.time != expected_time or \
       decoded_bundle.pri_block.creation_timestamp.sequence != expected_sequence:
            status = False
            
    expected_time += increment
    expected_sequence += 1

if status:
   print ("Time and sequence as expected")
else:
   print ("ERROR - Time and sequence NOT as expected")



print("----------------------------------------------------------------------")
print('Test 1.2 - time: "current"   sequence: {"fixed": 25}')
print("----------------------------------------------------------------------")

primary_block_settings = PrimaryBlockSettings(
    version=7,
    control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
    crc_type=CRCType.NONE,
    dest_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 1}}),
    src_eid=EID({"uri": 2, "ssp": {"node_num": 101, "service_num": 1}}),
    rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
    creation_timestamp={
        "time": "current",
        "sequence": {"fixed": 25}
    },
    lifetime=3600000,
    #crc=CRCFlag.CALCULATE,
)

# The difference between DTN epoch and UTC epoch is 946684800000 ms
# dtn_time = int(datetime.datetime.now().timestamp() * 1000) - 946684800000

dtn_time = int(datetime.now().timestamp() * 1000) - 946684800000
print(f"Current DTN time: {dtn_time} ms")

## Generate bundles (json files 11-15)

generated_bundles = Bundle.generate(
    num_bundles=5,
    pri_settings=primary_block_settings,
    canon_settings=[payload_block_settings],
)

for idx, x in enumerate(generated_bundles):
    x.to_json_file(f"/bundles/bundle_{idx+11}.json")


print("Time Sequence: ")

status = True
for idx, x in enumerate(generated_bundles):
    decoded_bundle = Bundle.from_json_file(f'/bundles/bundle_{idx+11}.json')
    print (decoded_bundle.pri_block.creation_timestamp.time, 
           decoded_bundle.pri_block.creation_timestamp.sequence)
           
    if decoded_bundle.pri_block.creation_timestamp.time >= dtn_time+100 or \
       decoded_bundle.pri_block.creation_timestamp.sequence != 25:
           status = False

if status:
    print ("Time and sequence as expected")
else:
   print ("ERROR - Time and sequence NOT as expected")


print("**********************************************************************")
print("Test 2 - Payload size settings - Rqmnt: 00115")
print("**********************************************************************")

print("----------------------------------------------------------------------")
print('Test 2.1 - payload={min_size: 20, max_size: 20}')
print("----------------------------------------------------------------------")

if decoded_bundle.canon_blocks[0].blk_type != BlockType.BUNDLE_PAYLOAD:
    print("ERROR - Block is not Payload block")
else:
    payload_size = len(decoded_bundle.canon_blocks[0].payload)
    if payload_size == 20:
        print(f"Payload size: {payload_size} as expected")
    else:
        print(f"ERROR - Payload size: {payload_size} NOT as expected")


print("----------------------------------------------------------------------")
print('Test 2.2 - payload={min_size: 0, max_size: 10*1024*1024}')
print("----------------------------------------------------------------------")

payload_block_settings = PayloadBlockSettings(
    blk_type=BlockType.AUTO,
    blk_num=1,
    control_flags=0,
    crc_type=CRCType.NONE,
    payload={"min_size": 0, "max_size": 10*1024*1024},
    #crc=CRCFlag.CALCULATE,
)

## Generate bundles (json files 21-25)
## Verify payload sizes are beween 0 and 10MB, but different for each bundle

generated_bundles = Bundle.generate(
    num_bundles=5,
    pri_settings=primary_block_settings,
    canon_settings=[payload_block_settings],
)

payloads_same_size = True
for idx, x in enumerate(generated_bundles):
    x.to_json_file(f"/bundles/bundle_{idx+21}.json")

    decoded_bundle = Bundle.from_json_file(f'/bundles/bundle_{idx+21}.json')
    if decoded_bundle.canon_blocks[0].blk_type != BlockType.BUNDLE_PAYLOAD:
        print("ERROR - Block is not Payload block")
    else:
        payload_size = len(decoded_bundle.canon_blocks[0].payload)
        if payload_size >= 0 and payload_size <= 10*1024*1024:
            print(f"Payload size: {payload_size} - between 0 and 10MB as expected")
            if idx > 0:
                if payload_size != ps:
                    payloads_same_size = False
            ps = payload_size
        else:
            print(f"ERROR - Payload size: {payload_size} - NOT as expected")

if payloads_same_size:
    print(f"ERROR - Payload sizes are not different")
else:
    print(f"Payload sizes different as expected")
    
