'''
off_nom_bundle_test.py

Validates DTNGen's ability to generate bad bundles with invalid CBOR encoded data
and bundles with missing blocks or missing elements in primary and canonical blocks
'''

set_line_delay(0)

import codecs
import subprocess
import time
import traceback
import warnings
import copy
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
    RawData,
)
from dtntools.dtngen.types import InvalidCBOR

warnings.simplefilter("always")


primary_block_ref = PrimaryBlock(
    version=7,
    control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
    crc_type=CRCType.NONE,
    dest_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 1}}),
    src_eid=EID({"uri": 2, "ssp": {"node_num": 101, "service_num": 1}}),
    rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
    creation_timestamp=CreationTimestamp({"time": 0, "sequence": 0}),
    lifetime=3600000,
    crc=CRCFlag.CALCULATE,
)

payload_block_ref = PayloadBlock(
    blk_type=BlockType.AUTO,
    blk_num=1,
    control_flags=0,
    crc_type=CRCType.NONE,
    payload=b'\xAA'*8,
    crc=CRCFlag.CALCULATE,
)


def check_invalid_cbor_bundle(major_type, add_info, payload_data):
    
    '''
    Creates and checks a bundle with an invalid CBOR item
    
        major_type      [0-7]
        add_info        [28-31]
        payload_data    any data consistent with major_type
    
    Primary block is unchanged, only payload in payload block
    '''
    
    # Create nominal bundle with payload_data
    payload_block_nom = copy.deepcopy(payload_block_ref)
    payload_block_nom.payload = payload_data

    bundle_nom = Bundle(pri_block=primary_block_ref, canon_blocks=[payload_block_nom])
    bundle_nom.to_json_file(f"/bundles/bundle_nom_{major_type}_{add_info}.json")
   
    bundle_hex_nom = bundle_nom.to_bytes().hex()
    print(f'bundle_hex_nom:\n{bundle_hex_nom}')


    # Create bundle with payload_data codded with invalid CBOR
    payload_block_inv = copy.deepcopy(payload_block_ref)
    payload_block_inv.payload = InvalidCBOR(payload_data,additional_info=add_info)

    bundle_inv = Bundle(pri_block=primary_block_ref, canon_blocks=[payload_block_inv])
    bundle_inv.to_json_file(f"/bundles/bundle_inv_{major_type}_{add_info}.json")

    bundle_hex_inv = bundle_inv.to_bytes().hex()
    print(f'bundle_hex_inv_cbor:\n{bundle_hex_inv}')
    
    
    # Look for invalid CBOR item code in the bundle    
    item_code = hex(major_type<<5 | additional_info).replace('0x','')
    
    pos = bundle_hex_inv.find(item_code)
    if pos > 0: 
        print(f'Expected CBOR item code: {item_code} \
        [nominal: {bundle_hex_nom[pos:pos+2]}] \
        found at position: {pos}')
    else:
        raise ValueError("Encoded item not found")


    print("Trying to regenerate the invalid bundle - errors/warnings expected")
    bundle_r = Bundle.from_bytes(bytes.fromhex(bundle_hex_inv))
    if bundle_r:
        raise ValueError("Invalid bundle parsed with no errors")
    


print("**********************************************************************")
print("1 - Invalid CBOR items - Rqmnt: 00125")
print("**********************************************************************")

'''
Not every combination of Major Type and "additional information" is checked.  
"additional information" is checked as below:
 - 31 for Major Type 0,1,6
 - 28-30 for at least one of the Major Types [0-7]
'''

sub_test=0
for major_type, additional_info, payload_data in [
        [0,29,100],
        [0,31,100],
        [1,29,-1],
        [1,31,-1],
        [2,30,b'\xAA'*100],
        [3,30,"ABCDEFGHIJKLMNOPQRSTUVWXYZ"],
        [4,28,[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]],
        [5,29,{"abc":1, "xyz":2}],
        [6,29,RawData(b'\xc2\x49\x01\x00\x00\x00\x00\x00\x00\x00\x00')],
        [6,31,RawData(b'\xc2\x49\x01\x00\x00\x00\x00\x00\x00\x00\x00')],
        [7,30,12346.789]
    ]:
    sub_test+=1
    print("----------------------------------------------------------------------")
    print(f'1.{sub_test} - Encoded item {major_type}_{additional_info}')
    print("----------------------------------------------------------------------")
    
    check_invalid_cbor_bundle(major_type, additional_info, payload_data)


print("**********************************************************************")
print("2 - Bundle with less than two blocks - - Rqmnt: 00125")
print("**********************************************************************")

print("----------------------------------------------------------------------")
print("2.1 Missing Canonical block")
print("----------------------------------------------------------------------")

bundle_no_canon = Bundle(pri_block=primary_block_ref)
bundle_no_canon.to_json_file(f"/bundles/bundle_no_canon.json")
print(f'bundle_hex_no_canon:\n{bundle_no_canon.to_bytes().hex()}')

print("----------------------------------------------------------------------")
print("2.2 Missing Primary block")
print("----------------------------------------------------------------------")

bundle_no_primary = Bundle(canon_blocks=[payload_block_ref])
bundle_no_primary.to_json_file(f"/bundles/bundle_no_primary.json")
print(f'bundle_hex_no_primary:\n{bundle_no_primary.to_bytes().hex()}')


print("**********************************************************************")
print("3 - Bundle with missing elements - - Rqmnt: 00125")
print("**********************************************************************")

# Generate bundle with nominal blocks
bundle_nominal = Bundle(pri_block=primary_block_ref, canon_blocks=[payload_block_ref])
bundle_nominal.to_json_file(f"/bundles/bundle_nominal.json")
bundle_hex_nominal = bundle_nominal.to_bytes().hex()
print(f'bundle_hex_nominal:\n{bundle_hex_nominal}')

print("----------------------------------------------------------------------")
print("3.1 Missing element in Primary block")
print("----------------------------------------------------------------------")

primary_block_inv = PrimaryBlock(
    version=7,
    control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
    #   crc_type=CRCType.NONE,
    dest_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 1}}),
    src_eid=EID({"uri": 2, "ssp": {"node_num": 101, "service_num": 1}}),
    rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
    creation_timestamp=CreationTimestamp({"time": 0, "sequence": 0}),
    lifetime=3600000,
    crc=CRCFlag.CALCULATE,
)

bundle_inv_primary = Bundle(pri_block=primary_block_inv, canon_blocks=[payload_block_ref])
bundle_inv_primary.to_json_file(f"/bundles/bundle_inv_primary.json")
bundle_hex_inv_primary = bundle_inv_primary.to_bytes().hex()
print(f'bundle_hex_inv_primary:\n{bundle_hex_inv_primary}')

if bundle_hex_inv_primary != bundle_hex_nominal:
    print("Bundle different from nominal as expected")
else:
    raise ValueError("Bundle not different from nominal")

print("----------------------------------------------------------------------")
print("3.2 Missing element in Payload block")
print("----------------------------------------------------------------------")

payload_block_inv = PayloadBlock(
    blk_type=BlockType.AUTO,
    blk_num=1,
    #   control_flags=0,
    crc_type=CRCType.NONE,
    payload=b'\xAA'*8,
    crc=CRCFlag.CALCULATE,
)

bundle_inv_payload = Bundle(pri_block=primary_block_ref, canon_blocks=[payload_block_inv])
bundle_inv_payload.to_json_file(f"/bundles/bundle_inv_payload.json")
bundle_hex_inv_payload = bundle_inv_payload.to_bytes().hex()
print(f'bundle_hex_inv_payload:\n{bundle_hex_inv_payload}')

if bundle_hex_inv_payload != bundle_hex_nominal:
    print("Bundle different from nominal as expected")
else:
    raise ValueError("Bundle not different from nominal")



print("**********************************************************************")
print("4 - Bundle with invalid elements - - Rqmnt: 00126, 00127")
print("**********************************************************************")

print("Trying to generate the bundle with invalid elements - errors/warnings expected")
primary_block_inv_elem = PrimaryBlock(
    version=-7,
    control_flags=-1,
    crc_type=-1,
    dest_eid=100,
    src_eid=EID({"uri": 2, "ssp": {"node_num": 101, "service_num": 1}}),
    rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
    creation_timestamp=CreationTimestamp({"time": 0, "sequence": 0}),
    lifetime=36000.00,
    crc=-20,
)

payload_block_inv_elem = PayloadBlock(
    blk_type=BlockType.AUTO,
    blk_num=-1,
    control_flags=-1,
    crc_type=-1,
    payload=b'\xAA'*8,
    crc=-30,
)

bundle_inv_elem = Bundle(pri_block=primary_block_inv_elem, canon_blocks=[payload_block_inv_elem])
bundle_inv_elem.to_json_file(f"/bundles/bundle_inv_elem.json")
bundle_hex_inv_elem = bundle_inv_elem.to_bytes().hex()


print("**********************************************************************")
print("Test 5 - Bundle with random data - Rqmnt: 00145")
print("**********************************************************************")

bundle_random = Bundle.generate_random(size=100, filename='/bundles/bundle_random.bin')
bundle_hex_random = bundle_random.hex()
print(f'bundle_hex_random:\n{bundle_hex_random}')

