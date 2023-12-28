import traceback
import cbor2

from .blocks import Block, BlockType, PayloadBlock, PrimaryBlock

class Bundle:
    """RFC9171 Bundle."""

    _block_lookup = {BlockType.BUNDLE_PAYLOAD: PayloadBlock}

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
    def decode(cls, cand_bundle):
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
            for i in range(1, len(cand_bundle)):
                block = cand_bundle[i]
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

    def encode(self):
        """Encode the bundle using CBOR.

        :return: A CBOR-encoded bundle
        :rtype: bytearray
        """
        pass
