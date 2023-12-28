from abc import abstractmethod, ABC

from .types import AdminRecordType
from .types import AdminRecord
from .types import BlockPCFlags
from .types import BlockType
from .types import BundlePCFlags
from .types import CreationTimestamp
from .types import CRCType
from .types import EID

class Block(ABC):
    """RFC9171 Block."""

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the block.

        :param list cand_block: A list of objects to be interpreted as a primary block.
        """
        # I initially tried @abstractmethod, but Python doesn't seem to enforce abstract
        # class methods until an object is instantiated. We have to throw this exception to guarantee all
        # classes dervived from block have a decode method.
        raise NotImplementedError(
            "Forgot to implement decode() in the derived class of Block"
        )


class CanonicalBlock(Block):
    """RFC9171 Extension Block Base Class."""

    def __init__(self, block_fields):
        """Initialize the extension block with the requested fields.

        :param dict block_fields: The extension block fields
        """
        self.type = block_fields["type"]
        self.number = block_fields["number"]
        self.control_flags = block_fields["control_flags"]
        self.crc_type = block_fields["crc_type"]

        # CRC

    @classmethod
    def decode_common(cls, cand_block):
        """Decode the fields common to all canonical blocks.

        :param list cand_block: A list representing the candidate canonical block
        """
        block_fields = {}
        block_fields["type"] = cand_block[0]
        block_fields["number"] = cand_block[1]
        block_fields["control_flags"] = cand_block[2]
        block_fields["crc_type"] = cand_block[3]

        return block_fields


class PayloadBlock(CanonicalBlock):
    """Class to represent RFC-9171 Payload Block."""

    def __init__(self, block_fields):
        """Initialze the payload block with the requested fields.

        :param dict block_fields: The payload block fields
        """
        super().__init__(block_fields)
        self.payload = block_fields["payload"]

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Payload Block.

        :params list cand_block: A list of objects to be interpreted as a payload block.
        """
        block_fields = {}
        canon_fields = CanonicalBlock.decode_common(cand_block)

        block_fields["payload"] = cand_block[4]

        return PayloadBlock({**canon_fields, **block_fields})


class PrimaryBlock(Block):
    """RFC9171 Primary Block."""

    def __init__(self, block_fields):
        """Initialize the primary block with the requested fields.

        :param dict block_fields: The primary block fields
        """
        self.version = block_fields["version"]
        self.control_flags = block_fields["control_flags"]
        self.crc_type = block_fields["crc_type"]
        self.dest_eid = block_fields["dest_eid"]
        self.src_eid = block_fields["src_eid"]
        self.report_eid = block_fields["report_eid"]
        self.creation_timestamp = block_fields["creation_timestamp"]
        self.lifetime = block_fields["lifetime"]

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Primary Block.

        :params list cand_block: A list of objects to be interpreted as a primary block.
        """
        block_fields = {}

        # TODO: Length checks

        # Version
        if cand_block[0] != 7:
            raise ValueError(
                f"Primary block: Expected BP Version 7, got {cand_block[0]}"
            )
        block_fields["version"] = cand_block[0]

        # TODO: Control Flags
        block_fields["control_flags"] = cand_block[1]

        # CRC-Type
        # TODO: CRC Validation needed
        block_fields["crc_type"] = cand_block[2]

        block_fields["dest_eid"] = EID.decode(cand_block[3])
        block_fields["src_eid"] = EID.decode(cand_block[4])
        block_fields["report_eid"] = EID.decode(cand_block[5])
        block_fields["creation_timestamp"] = CreationTimestamp.decode(cand_block[6])
        block_fields["lifetime"] = cand_block[7]

        # CRC

        return PrimaryBlock(block_fields)
