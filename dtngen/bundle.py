import traceback
import cbor2
import json

from .types import BlockType
from .blocks import Block, PayloadBlock, PrimaryBlock, PrevNodeBlock, \
    BundleAgeBlock, HopCountBlock
from .dtnjson import custom_decoder

class Bundle:
    """RFC9171 Bundle."""

    _block_lookup = {BlockType.BUNDLE_PAYLOAD: PayloadBlock, \
        BlockType.PREVIOUS_NODE: PrevNodeBlock, \
        BlockType.BUNDLE_AGE: BundleAgeBlock, \
        BlockType.HOP_COUNT: HopCountBlock}

    def __init__(self, pri_block, canon_blocks):
        """Initialize the bundle from a primary block and list of extension blocks.

        :param PrimaryBlock pri_block: The primary block of the bundle.
        :param list canon_blocks: A list of blocks derived from CanonicalBlock
        """
        self.pri_block = pri_block
        self.canon_blocks = canon_blocks

    @classmethod
    def get_block_cls(cls, block_type):
        """Return the class associated with the requested block type.

        :param int block_type: The block type to lookup
        :return: A subclass of CanonicalBlock if the block type was supported, or None if not supported
        """
        return 


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
            pri_block = PrimaryBlock.decode(cand_bundle[0])

            # Attempt to decode each extension block by matching the block type flags
            canon_blocks = []
            for block in cand_bundle[1:]:
                block_type = block[0]
                block_cls = cls._block_lookup.get(block_type, None)
                if block_cls:
                    canon_blocks.append(block_cls.decode(block))
                else:
                    print(f"WARNING: Unknown block type {block_type}. Skipping block.")

            return Bundle(pri_block, canon_blocks)

        except cbor2.CBORDecodeError:
            traceback.print_exc()
            return None

        except Exception:
            traceback.print_exc()
            return None

    @classmethod
    def from_bytes_file(cls, fname):
        with open(fname, "rb") as bytes_file:
            byte_string = bytes_file.read()
        return cls.from_bytes(byte_string)

    def to_bytes(self):
        """Encode the bundle using CBOR.

        :return: A CBOR-encoded bundle
        :rtype: bytearray
        """
        byte_string = self.pri_block.encode()
        for cblock in self.canon_blocks:
            byte_string = byte_string + cblock.encode()
        
        # return byte string wrapped by 0x9F and 0xFF to make it an indefinite
        # cbor array - cbor2 only does this for you if it's a long array
        return b'\x9f' + byte_string + b'\xff'

    def to_bytes_file(self, fname):
        with open(fname, "wb") as bytes_file:
            bytes_file.write(self.to_bytes())

    def to_json(self):
        """Encode the Bundle using json.

        :return: A json-encoded bundle
        :rtype: string
        """            
        json_string = '[' + self.pri_block.to_json() + ', '
        for cblock in self.canon_blocks[:-1]:
            json_string = json_string + cblock.to_json() + ", "
        json_string = json_string + self.canon_blocks[-1].to_json() + "]"
        
        # Pretty print the json
        parsed = json.loads(json_string)
        return json.dumps(parsed, indent=4)

    def to_json_file(self, fname):
        with open(fname, "w") as json_file:
            json_file.write(self.to_json())

    @classmethod
    def from_json(cls, jsonstr):
        jsondata = json.loads(jsonstr, object_hook=custom_decoder)
        pri_block = PrimaryBlock(*jsondata[0])

        canon_blocks = []
        for block in jsondata[1:]:
            block_type = block[0]
            block_cls = cls._block_lookup.get(block_type, None)
            if block_cls:
                if block_cls == HopCountBlock:
                    block = flatten(block)
                canon_blocks.append(block_cls(*block))
            else:
                print(f"WARNING: Unknown block type {block_type}. Skipping block.")
        
        return Bundle(pri_block, canon_blocks)

    @classmethod
    def from_json_file(cls, fname):
        with open(fname, "r") as json_file:
            json_string = json_file.read()
        return cls.from_json(json_string)
        

def flatten(non_flat_list):
    flat = []
    for e in non_flat_list:
        if type(e) == list:
                flat = flat + e
        else:
                flat.append(e)
    return flat
