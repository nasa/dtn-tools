import json
import traceback

import cbor2
import warnings
import time

from .blocks import (
    BundleAgeBlock,
    HopCountBlock,
    PayloadBlock,
    PrevNodeBlock,
    CustodyTransferBlock,
    CompressedReportingBlock,
    PrimaryBlock,
    UnknownBlock,
)
from .dtnjson import custom_decoder
from .types import BlockType


class Bundle:
    """RFC9171 Bundle."""

    _block_lookup = {
        BlockType.BUNDLE_PAYLOAD: PayloadBlock,
        BlockType.PREVIOUS_NODE: PrevNodeBlock,
        BlockType.BUNDLE_AGE: BundleAgeBlock,
        BlockType.HOP_COUNT: HopCountBlock,
        BlockType.CUST_TRANS_EXT: CustodyTransferBlock,
        BlockType.COMP_RPT_EXT: CompressedReportingBlock,
    }

    def __init__(self, pri_block = None, canon_blocks = None):
        """Initialize the bundle from a primary block and list of extension \
            blocks.

        :param PrimaryBlock pri_block: The primary block of the bundle.
        :param list canon_blocks: A list of blocks derived from CanonicalBlock
        """
        self.pri_block = pri_block
        self.canon_blocks = canon_blocks

    @classmethod
    def from_bytes(cls, cand_bundle):
        """Attempt to CBOR-decode and parse a bundle.

        :param bytes-like cand_bundle: candidate bundle to attempt parsing
        :return: The parsed bundle object
        :rtype: Bundle
        """
        try:
            # Attempt to CBOR decode the bundle
            cand_bundle = cbor2.loads(cand_bundle)

            # Attempt to decode the primary block
            pri_block = None
            canon_blocks = None
            
            if isinstance(cand_bundle, list) and len(cand_bundle) >=1:
                pri_block = PrimaryBlock.decode(cand_bundle[0])
    
                # Attempt to decode each extension block by matching the block type
                # flags
                canon_blocks = []
                for block in cand_bundle[1:]:
                    block_type = block[0]
                    block_cls = cls._block_lookup.get(block_type, None)
                    if block_cls:
                        canon_blocks.append(block_cls.decode(block))
                    else:
                        warnmsg = f'Unknown block type {block_type}. Adding as UnknownBlock.'
                        warnings.warn(warnmsg)
                        canon_blocks.append(UnknownBlock.decode(block))

            return Bundle(pri_block, canon_blocks)

        except cbor2.CBORDecodeError:
            traceback.print_exc()
            return None

        except Exception:
            traceback.print_exc()
            return None

    @classmethod
    def from_bytes_file(cls, fname):
        """Read a Bundle from a binary file.

        :param str fname: The filename to read
        :return: The bundle described within the file
        :rtype: Bundle
        """
        with open(fname, "rb") as bytes_file:
            byte_string = bytes_file.read()
        return cls.from_bytes(byte_string)

    def to_bytes(self):
        """Encode the bundle using CBOR.

        :return: A CBOR-encoded bundle
        :rtype: bytearray
        """
        byte_string = self.pri_block.encode() if self.pri_block is not None \
            else b''
        
        if self.canon_blocks is not None \
                and isinstance(self.canon_blocks, list) \
                and len(self.canon_blocks) >= 1:
            for cblock in self.canon_blocks:
                byte_string = byte_string + cblock.encode()

        # return byte string wrapped by 0x9F and 0xFF to make it an indefinite
        # cbor array - cbor2 only does this for you if it's a long array
        return b"\x9f" + byte_string + b"\xff"

    def to_bytes_file(self, fname):
        """Write a Bundle to a binary file.

        :param str fname: The filename to write
        """
        with open(fname, "wb") as bytes_file:
            bytes_file.write(self.to_bytes())

    def to_json(self):
        """Encode the Bundle to a json string.

        :return: A json-encoded bundle
        :rtype: str
        """
        json_string = "[" + self.pri_block.to_json() \
            if self.pri_block is not None else "["
        if self.canon_blocks is not None \
                and isinstance(self.canon_blocks, list) \
                and len(self.canon_blocks) >= 1:
            if self.pri_block is not None:
                json_string = json_string  + ", "
            for cblock in self.canon_blocks[:-1]:
                json_string = json_string + cblock.to_json() + ", "
            json_string = json_string + self.canon_blocks[-1].to_json() + "]"
        else:
            json_string = json_string + "]"

        # Pretty print the json
        parsed = json.loads(json_string)
        return json.dumps(parsed, indent=4)

    def to_json_file(self, fname):
        """Encode the Bundle to a json file.

        :param str fname: The filename to write
        """
        with open(fname, "w") as json_file:
            json_file.write(self.to_json())

    @classmethod
    def from_json(cls, jsonstr):
        """Decode the Bundle from a json string.

        :param str jsonstr: The json string to decode
        :return: The decoded Bundle described in the json string
        :rtype: Bundle
        """
        jsondata = json.loads(jsonstr, object_hook=custom_decoder)

        pri_block = None
        canon_blocks = None
        
        if isinstance(jsondata, list) and len(jsondata) >=1:
            pri_block = PrimaryBlock(*jsondata[0])
    
            canon_blocks = []
            for block in jsondata[1:]:
                block_type = block[0]
                block_cls = cls._block_lookup.get(block_type, None)
                if block_cls:
                    if block_cls == HopCountBlock \
                            or block_cls == CustodyTransferBlock \
                            or block_cls == CompressedReportingBlock:
                        block = _flatten(block)
                    if block_cls == CompressedReportingBlock:
                        if len(block) >= 4 and isinstance(block[3], int) \
                            and block[3] >= 1 and block[3] <= 2:
                                crc_val = block[-1]
                                block = block[:-1]
                                canon_blocks.append(block_cls(*block, crc=crc_val))
                        else:
                            canon_blocks.append(block_cls(*block))
                    else:
                        canon_blocks.append(block_cls(*block))
                else:
                    warnmsg = f'Unknown block type {block_type}. Adding as UnknownBlock.'
                    warnings.warn(warnmsg)
                    canon_blocks.append(UnknownBlock.decode(block))

        return Bundle(pri_block, canon_blocks)

    @classmethod
    def from_json_file(cls, fname):
        """Read a Bundle from a JSON file.

        :param str fname: The filename to read
        :return: The bundle described within the file
        :rtype: Bundle
        """
        with open(fname, "r") as json_file:
            json_string = json_file.read()
        return cls.from_json(json_string)

    @classmethod
    def generate(cls, pri_settings=None, canon_settings=None, num_bundles=1):
        """Generate one or more bundles based on the provided settings.

        :param PrimaryBlockSettings pri_settings: The settings for the primary \
            block - can be None
        :param list canon_settings: List of canonical block settings instances \
            - can be None
        :param int num_bundles: Number of bundles to generate
        :return: list of generated bundles
        :rtype: list
        """
        bundles = []
        for bundle_num in range(num_bundles):
            pri_block = None
            canon_blocks = None
            
            if pri_settings is not None:
                # Generate Primary Block
                pri_block = pri_settings.generate(bundle_num=bundle_num)
            
            if canon_settings is not None:
                canon_blocks = []
                # generate Canonical Blocks
                for curr_block_settings in canon_settings:
                    canon_blocks.append(curr_block_settings.generate(bundle_num=bundle_num))
            
            bundles.append(Bundle(pri_block, canon_blocks))
        return bundles
        

def _flatten(non_flat_list):
    flat = []
    for e in non_flat_list:
        if isinstance(e, list):
            flat = flat + e
        else:
            flat.append(e)
    return flat
