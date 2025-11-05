import json
import os
import traceback
import warnings

import cbor2

from .blocks import (
    BundleAgeBlock,
    CompressedReportingBlock,
    CustodyTransferBlock,
    HopCountBlock,
    PayloadBlock,
    PrevNodeBlock,
    PrimaryBlock,
    UnknownBlock,
    AdminRecordBlock,
)
from .dtnjson import custom_decoder
from .types import BlockType,BundlePCFlags


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

    def __init__(self, pri_block=None, canon_blocks=None):
        r"""Initialize the bundle from a primary block and list of extension blocks.

        :param PrimaryBlock pri_block: (optional) The primary block of the bundle.
        :param list canon_blocks: (optional) A list of blocks derived from CanonicalBlock

        *Usage:*

        .. code-block:: python

            from dtngen.blocks import PrevNodeBlock, PayloadBlock, PrimaryBlock
            from dtngen.bundle import Bundle

            pblock = PrimaryBlock(
                version=7,
                control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
                crc_type=CRCType.CRC16_X25,
                dest_eid=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
                src_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
                rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
                creation_timestamp=CreationTimestamp({"time": 755533838904, "sequence": 0}),
                lifetime=3600000,
                crc=b"\\x0b\\x19",
            )

            prevnodeblk = PrevNodeBlock(
                blk_type=BlockType.AUTO,
                blk_num=2,
                control_flags=0,
                crc_type=CRCType.CRC16_X25,
                prev_eid=EID({"uri": 2, "ssp": {"node_num": 300, "service_num": 2}}),
                crc=CRCFlag.CALCULATE,
            )

            payloadblk = PayloadBlock(
                blk_type=BlockType.AUTO,
                blk_num=1,
                control_flags=0,
                crc_type=CRCType.CRC16_X25,
                payload=b"\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x0chello world\\n",
                crc=CRCFlag.CALCULATE,
            )

            mybundle = Bundle(
                pri_block = pblock,
                canon_blocks = [prevnodeblk, payloadblk]
            )
        """
        self.pri_block = pri_block
        self.canon_blocks = canon_blocks

    @classmethod
    def from_bytes(cls, cand_bundle):
        """Attempt to CBOR-decode and parse a bundle.

        :param bytes-like cand_bundle: candidate bundle to attempt parsing
        :return: The parsed bundle object
        :rtype: Bundle

        *Usage:*

        .. code-block:: python

            from dtngen.bundle import Bundle

            candidate_bytes = bytes.fromhex("9f8907040182028218c801820282186401820282186401821b000000afe9537a38001a0036ee80420b19860101000150d1bfe62e5da4b519fb68c18b7edb3611420c34ff")

            bundle_from_bytes = Bundle.from_bytes(candidate_bytes)
        """
        try:
            # Attempt to CBOR decode the bundle
            cand_bundle = cbor2.loads(cand_bundle)

            # Attempt to decode the primary block
            pri_block = None
            canon_blocks = None

            if isinstance(cand_bundle, list) and len(cand_bundle) >= 1:
                pri_block = PrimaryBlock.decode(cand_bundle[0])

                # Attempt to decode each extension block by matching the block type
                # flags
                canon_blocks = []
                for block in cand_bundle[1:]:
                    block_type = block[0]
                    block_cls = cls._block_lookup.get(block_type, None)
                    if block_cls:
                        if (block_type == BlockType.BUNDLE_PAYLOAD and 
                            pri_block.control_flags == BundlePCFlags.IS_ADMIN_RECORD):
                            canon_blocks.append(AdminRecordBlock.decode(block))
                        else:
                            canon_blocks.append(block_cls.decode(block))
                    else:
                        warnmsg = (
                            f"Unknown block type {block_type}. Adding as UnknownBlock."
                        )
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

        *Usage:*

        .. code-block:: python

            from dtngen.bundle import Bundle

            bundle_from_bytes_file = Bundle.from_bytes_file("/path/to/file/bundle.bin")
        """
        with open(fname, "rb") as bytes_file:
            byte_string = bytes_file.read()
        return cls.from_bytes(byte_string)

    def to_bytes(self):
        """Encode the bundle using CBOR.

        :return: A CBOR-encoded bundle
        :rtype: bytearray

        *Usage:*

        .. code-block:: python

            bytesout = mybundle.to_bytes()
        """
        byte_string = self.pri_block.encode() if self.pri_block is not None else b""

        if (
            self.canon_blocks is not None
            and isinstance(self.canon_blocks, list)
            and len(self.canon_blocks) >= 1
        ):
            for cblock in self.canon_blocks:
                byte_string = byte_string + cblock.encode()

        # return byte string wrapped by 0x9F and 0xFF to make it an indefinite
        # cbor array - cbor2 only does this for you if it's a long array
        return b"\x9f" + byte_string + b"\xff"

    def to_bytes_file(self, fname):
        """Write a Bundle to a binary file.

        :param str fname: The filename to write

        *Usage:*

        .. code-block:: python

            mybundle.to_bytes_file("/path/to/file/bundle.bin")
        """
        with open(fname, "wb") as bytes_file:
            bytes_file.write(self.to_bytes())

    def to_json(self):
        """Encode the Bundle to a json string.

        :return: A json-encoded bundle
        :rtype: str

        *Usage:*

        .. code-block:: python

            json_string = mybundle.to_json()
        """
        json_string = (
            "[" + self.pri_block.to_json() if self.pri_block is not None else "["
        )
        if (
            self.canon_blocks is not None
            and isinstance(self.canon_blocks, list)
            and len(self.canon_blocks) >= 1
        ):
            if self.pri_block is not None:
                json_string = json_string + ", "
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

        *Usage:*

        .. code-block:: python

            mybundle.to_json_file("/path/to/file/bundle.json")
        """
        with open(fname, "w") as json_file:
            json_file.write(self.to_json())

    @classmethod
    def from_json(cls, jsonstr):
        r"""Decode the Bundle from a json string.

        :param str jsonstr: The json string to decode
        :return: The decoded Bundle described in the json string
        :rtype: Bundle

        *Usage:*

        .. code-block:: python

            from dtngen.bundle import Bundle

            jsoncode = \"[json defining a bundle]\"

            bundle_from_json = Bundle.from_json(jsoncode)
        """
        jsondata = json.loads(jsonstr, object_hook=custom_decoder)

        pri_block = None
        canon_blocks = None

        if isinstance(jsondata, list) and len(jsondata) >= 1:
            # The blocks are dicts - get the block element values, skipping the
            # first one, "_block_class"
            pri_block = PrimaryBlock(*list(jsondata[0].values())[1:])

            canon_blocks = []
            for block in jsondata[1:]:
                block_vals = list(block.values())
                block_type = block_vals[1]
                block_cls = cls._block_lookup.get(block_type, None)
                if not block_cls.__name__ == block_vals[0]:
                    warnmsg = f"Encoded block class {block_cls.__name__} not equal to _block_class {block_vals[0]}."
                    warnings.warn(warnmsg)

                # Remove _block_class element
                block_vals = block_vals[1:]
                if block_cls:
                    if (
                        block_cls == HopCountBlock
                        or block_cls == CustodyTransferBlock
                        or block_cls == CompressedReportingBlock
                    ):
                        block_vals = _flatten(block_vals)
                    if block_cls == CompressedReportingBlock:
                        if (
                            len(block_vals) >= 4
                            and isinstance(block_vals[3], int)
                            and block_vals[3] >= 1
                            and block_vals[3] <= 2
                        ):
                            crc_val = block_vals[-1]
                            block_vals = block_vals[:-1]
                            canon_blocks.append(block_cls(*block_vals, crc=crc_val))
                        else:
                            canon_blocks.append(block_cls(*block_vals))
                    else:
                        canon_blocks.append(block_cls(*block_vals))
                else:
                    warnmsg = (
                        f"Unknown block type {block_type}. Adding as UnknownBlock."
                    )
                    warnings.warn(warnmsg)
                    canon_blocks.append(UnknownBlock.decode(block_vals))

        return Bundle(pri_block, canon_blocks)

    @classmethod
    def from_json_file(cls, fname):
        """Read a Bundle from a JSON file.

        :param str fname: The filename to read
        :return: The bundle described within the file
        :rtype: Bundle

        *Usage:*

        .. code-block:: python

            from dtngen.bundle import Bundle

            bundle_from_json_file = Bundle.from_json_file("/path/to/file/bundle.json")
        """
        with open(fname, "r") as json_file:
            json_string = json_file.read()
        return cls.from_json(json_string)

    @classmethod
    def generate(cls, pri_settings=None, canon_settings=None, num_bundles=1):
        """Generate one or more bundles based on the provided settings.

        :param PrimaryBlockSettings pri_settings: (optional) The settings for the primary block
        :param list canon_settings: (optional) List of canonical block settings instances
        :param int num_bundles: (optional) Number of bundles to generate - defaults to 1
        :return: list of generated bundles
        :rtype: list

        *Usage:*

        .. code-block:: python

            from dtngen.blocks import PrimaryBlockSettings, PayloadBlockSettings
            from dtngen.bundle import Bundle

            # PrimaryBlockSettings is like PrimaryBlock except the
            # creation_timestamp has generation settings for the time and
            # sequence instead of explicit values
            primaryblk_settings = PrimaryBlockSettings(
                version=7,
                control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
                crc_type=CRCType.CRC16_X25,
                dest_eid=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
                src_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
                rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
                creation_timestamp={
                    "time": {"start": 755533838904, "increment": 256},
                    "sequence": {"start": 0}
                },
                lifetime=3600000,
                crc=CRCFlag.CALCULATE,
            )

            # PayloadBlockSettings is like PayloadBlock except the payload has
            # the size (in bytes) of random payload to generate instead of a
            # specific payload
            payloadblk_settings = PayloadBlockSettings(
                blk_type=BlockType.AUTO,
                blk_num=1,
                control_flags=0,
                crc_type=CRCType.CRC16_X25,
                payload={"min_size": 1024, "max_size": 2048},
                crc=CRCFlag.CALCULATE,
            )

            generated_bundles = Bundle.generate(
                pri_settings = primaryblk_settings,
                canon_settings = [payloadblk_settings],
                num_bundles = 25
            )
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
                    canon_blocks.append(
                        curr_block_settings.generate(bundle_num=bundle_num)
                    )

            bundles.append(Bundle(pri_block, canon_blocks))
        return bundles

    @classmethod
    def generate_random(cls, size, filename=None):
        """Generate junk bundle data with the specified number of random bytes.

        :param int size: The size in bytes of the junk bundle to create
        :param str filename: (optional) filename to write the data to

        :return: The generated junk bundle data
        :rtype: bytes

        *Usage:*

        .. code-block:: python

            from dtngen.bundle import Bundle

            # The size is required and is the size in bytes of the junk bundle
            # to create. The filename is optional. If provided the bundle will
            # be written to that filename. In all cases the bundle is returned
            # as bytes, but in this example the return value is discarded.
            Bundle.generate_random(size=1024, filename="junk.bin")

            # If the filename is left out, no file will be written but the
            # junk bundle is returned as bytes
            junk_large = Bundle.generate_random(size=10*1024*1024)
        """
        junk_bytes = os.urandom(size)

        if filename and isinstance(filename, str):
            with open(filename, "wb") as bytes_file:
                bytes_file.write(junk_bytes)

        return junk_bytes

    def __eq__(self, other):
        return self.to_json() == other.to_json()

def _flatten(non_flat_list):
    flat = []
    for e in non_flat_list:
        if isinstance(e, list):
            flat = flat + e
        else:
            flat.append(e)
    return flat
