from abc import abstractmethod, ABC

from .types import AdminRecordType
from .types import AdminRecord
from .types import BlockPCFlags
from .types import BlockType
from .types import BundlePCFlags
from .types import CreationTimestamp
from .types import CRCType
from .types import EID
from .types import calc_crc
from .types import CRCFlag
from .types import default_encoder
from .dtnjson import custom_encoder, custom_decoder
import cbor2
import json

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

    def __init__(self, blk_type, blk_num, control_flags, crc_type, crc=None):
        """Initialize the extension block with the requested fields.

        :param dict block_fields: The extension block fields
        """
        self.blk_type = blk_type
        self.blk_num = blk_num
        self.control_flags = control_flags
        self.crc_type = crc_type
        self.crc = crc

        # CRC

    @classmethod
    def decode_common(cls, cand_block):
        """Decode the fields common to all canonical blocks.

        :param list cand_block: A list representing the candidate canonical block
        """
        block_fields = {}
        block_fields["blk_type"] = cand_block[0]
        block_fields["blk_num"] = cand_block[1]
        block_fields["control_flags"] = cand_block[2]
        block_fields["crc_type"] = cand_block[3]
        if len(cand_block) == 6:
            block_fields["crc"] = cand_block[5]

        return block_fields


class PrevNodeBlock(CanonicalBlock):
    """Class to represent RFC-9171 Previous Node Block."""

    def __init__(self, blk_type, blk_num, control_flags, crc_type, prev_eid, \
        crc = None):
        """Initialze the previous node block with the requested fields.

        :param dict block_fields: The payload block fields
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.prev_eid = prev_eid

    def encode(self):
        """Encode the PrevNodeBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """            
        match self.crc:
            case None:
                return cbor2.dumps([self.blk_type, self.blk_num, \
                    self.control_flags, self.crc_type, self.prev_eid], \
                    default=default_encoder)
            case CRCFlag.CALCULATE:
                self.crc = calc_crc(self.crc_type, [self.blk_type, \
                    self.blk_num, self.control_flags, self.crc_type, \
                    self.prev_eid])

        return cbor2.dumps([self.blk_type, self.blk_num, self.control_flags, \
            self.crc_type, self.prev_eid, self.crc], \
            default=default_encoder)

    def to_json(self):
        """Encode the PrevNodeBlock block using json.

        :return: A json-encoded block
        :rtype: string
        """            
        match self.crc:
            case None:
                return json.dumps([self.blk_type, self.blk_num, \
                    self.control_flags, self.crc_type, self.prev_eid], \
                    default=custom_encoder)
            case CRCFlag.CALCULATE:
                self.crc = calc_crc(self.crc_type, [self.blk_type, \
                    self.blk_num, self.control_flags, self.crc_type, \
                    self.prev_eid])

        return json.dumps([self.blk_type, self.blk_num, self.control_flags, \
            self.crc_type, self.prev_eid, self.crc], \
            default=custom_encoder)


    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Payload Block.

        :params list cand_block: A list of objects to be interpreted as a Previous Node block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        return PrevNodeBlock(**canon_fields, \
            prev_eid = EID.decode(cand_block[4]))
        

class BundleAgeBlock(CanonicalBlock):
    """Class to represent RFC-9171 Bundle Age Block."""

    def __init__(self, blk_type, blk_num, control_flags, crc_type, bundle_age, \
        crc = None):
        """Initialze the payload block with the requested fields.

        :param dict block_fields: The payload block fields
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.bundle_age = bundle_age

    def encode(self):
        """Encode the BundleAgeBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        match self.crc:
            case None:
                return cbor2.dumps([self.blk_type, self.blk_num, \
                    self.control_flags, self.crc_type, self.bundle_age], \
                    default=default_encoder)
            case CRCFlag.CALCULATE:
                self.crc = calc_crc(self.crc_type, [self.blk_type, \
                    self.blk_num, self.control_flags, self.crc_type, \
                    self.bundle_age])

        return cbor2.dumps([self.blk_type, self.blk_num, self.control_flags, \
            self.crc_type, self.bundle_age, self.crc], \
            default=default_encoder)

    def to_json(self):
        """Encode the BundleAgeBlock block using json.

        :return: A json-encoded block
        :rtype: string
        """            
        match self.crc:
            case None:
                return json.dumps([self.blk_type, self.blk_num, \
                    self.control_flags, self.crc_type, self.bundle_age], \
                    default=custom_encoder)
            case CRCFlag.CALCULATE:
                self.crc = calc_crc(self.crc_type, [self.blk_type, \
                    self.blk_num, self.control_flags, self.crc_type, \
                    self.bundle_age])

        return json.dumps([self.blk_type, self.blk_num, self.control_flags, \
            self.crc_type, self.bundle_age, self.crc], \
            default=custom_encoder)

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Payload Block.

        :params list cand_block: A list of objects to be interpreted as a Bundle Age block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        return BundleAgeBlock(**canon_fields, bundle_age = cand_block[4])
            

class HopCountBlock(CanonicalBlock):
    """Class to represent RFC-9171 Hop Count Block."""

    def __init__(self, blk_type, blk_num, control_flags, crc_type, hop_limit, \
        hop_count, crc = None):
        """Initialze the payload block with the requested fields.

        :param dict block_fields: The payload block fields
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.hop_limit = hop_limit
        self.hop_count = hop_count

    def encode(self):
        """Encode the HopCountBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        match self.crc:
            case None:
                return cbor2.dumps([self.blk_type, self.blk_num, \
                    self.control_flags, self.crc_type, [self.hop_limit, \
                    self.hop_count]], default=default_encoder)
            case CRCFlag.CALCULATE:
                self.crc = calc_crc(self.crc_type, [self.blk_type, \
                    self.blk_num, self.control_flags, self.crc_type, \
                    [self.hop_limit, self.hop_count]])

        return cbor2.dumps([self.blk_type, self.blk_num, self.control_flags, \
            self.crc_type, [self.hop_limit, self.hop_count], self.crc], \
            default=default_encoder)

    def to_json(self):
        """Encode the HopCountBlock block using json.

        :return: A json-encoded block
        :rtype: string
        """            
        match self.crc:
            case None:
                return sjon.dumps([self.blk_type, self.blk_num, \
                    self.control_flags, self.crc_type, [self.hop_limit, \
                    self.hop_count]], default=custom_encoder)
            case CRCFlag.CALCULATE:
                self.crc = calc_crc(self.crc_type, [self.blk_type, \
                    self.blk_num, self.control_flags, self.crc_type, \
                    [self.hop_limit, self.hop_count]])

        return json.dumps([self.blk_type, self.blk_num, self.control_flags, \
            self.crc_type, [self.hop_limit, self.hop_count], self.crc], \
            default=custom_encoder)

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Hop Count Block.

        :params list cand_block: A list of objects to be interpreted as a payload block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        return HopCountBlock(**canon_fields, hop_limit = cand_block[4][0], \
            hop_count = cand_block[4][1])
    

class PayloadBlock(CanonicalBlock):
    """Class to represent RFC-9171 Payload Block."""

    def __init__(self, blk_type, blk_num, control_flags, crc_type, payload, \
        crc = None):
        """Initialze the payload block with the requested fields.

        :param dict block_fields: The payload block fields
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.payload = payload

    def encode(self):
        """Encode the Payload block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        match self.crc:
            case None:
                return cbor2.dumps([self.blk_type, self.blk_num, \
                    self.control_flags, self.crc_type, self.payload], \
                    default=default_encoder)
            case CRCFlag.CALCULATE:
                self.crc = calc_crc(self.crc_type, [self.blk_type, \
                    self.blk_num, self.control_flags, self.crc_type, \
                    self.payload])

        return cbor2.dumps([self.blk_type, self.blk_num, self.control_flags, \
            self.crc_type, self.payload, self.crc], \
            default=default_encoder)

    def to_json(self):
        """Encode the Payload block using json.

        :return: A json-encoded block
        :rtype: string
        """            
        match self.crc:
            case None:
                return json.dumps([self.blk_type, self.blk_num, \
                    self.control_flags, self.crc_type, self.payload], \
                    default=custom_encoder)
            case CRCFlag.CALCULATE:
                self.crc = calc_crc(self.crc_type, [self.blk_type, \
                    self.blk_num, self.control_flags, self.crc_type, \
                    self.payload])

        return json.dumps([self.blk_type, self.blk_num, self.control_flags, \
            self.crc_type, self.payload, self.crc], \
            default=custom_encoder)

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Payload Block.

        :params list cand_block: A list of objects to be interpreted as a payload block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        return PayloadBlock(**canon_fields, payload = cand_block[4])


class PrimaryBlock(Block):
    """RFC9171 Primary Block."""

    def __init__(self, version, control_flags, crc_type, dest_eid, src_eid, \
            rpt_eid, creation_timestamp, lifetime, crc = None):
        """Initialize the primary block with the requested fields.

        :param dict block_fields: The primary block fields
        """
        self.version = version
        self.control_flags = control_flags
        self.crc_type = crc_type
        self.dest_eid = dest_eid
        self.src_eid = src_eid
        self.rpt_eid = rpt_eid
        self.creation_timestamp = creation_timestamp
        self.lifetime = lifetime
        self.crc = crc

    def encode(self):
        """Encode the Primary block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        match self.crc:
            case None:
                return cbor2.dumps([self.version, self.control_flags, \
                    self.crc_type, \
                    self.dest_eid, self.src_eid, self.rpt_eid, \
                    self.creation_timestamp, self.lifetime], \
                    default=default_encoder)
            case CRCFlag.CALCULATE:
                self.crc = calc_crc(self.crc_type, [self.version, \
                    self.control_flags, self.crc_type, \
                    self.dest_eid, self.src_eid, self.rpt_eid, \
                    self.creation_timestamp, self.lifetime])

        return cbor2.dumps([self.version, self.control_flags, \
            self.crc_type, \
            self.dest_eid, self.src_eid, self.rpt_eid, \
            self.creation_timestamp, self.lifetime, self.crc], \
            default=default_encoder)

    def to_json(self):
        """Encode the Primary block using json.

        :return: A json-encoded block
        :rtype: string
        """            
        match self.crc:
            case None:
                return json.dumps([self.version, self.control_flags, \
                    self.crc_type, \
                    self.dest_eid, self.src_eid, self.rpt_eid, \
                    self.creation_timestamp, self.lifetime], \
                    default=custom_encoder)
            case CRCFlag.CALCULATE:
                self.crc = calc_crc(self.crc_type, [self.version, \
                    self.control_flags, self.crc_type, \
                    self.dest_eid, self.src_eid, self.rpt_eid, \
                    self.creation_timestamp, self.lifetime])

        return json.dumps([self.version, self.control_flags, \
            self.crc_type, \
            self.dest_eid, self.src_eid, self.rpt_eid, \
            self.creation_timestamp, self.lifetime, self.crc], \
            default=custom_encoder)


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

        if len(cand_block) == 9:
            return PrimaryBlock(version=cand_block[0], \
                control_flags=cand_block[1], crc_type = cand_block[2], \
                dest_eid = EID.decode(cand_block[3]), \
                src_eid = EID.decode(cand_block[4]), \
                rpt_eid = EID.decode(cand_block[5]), \
                creation_timestamp = CreationTimestamp.decode(cand_block[6]), \
                lifetime = cand_block[7], crc = cand_block[8])
        else:
             return PrimaryBlock(version=cand_block[0], \
                control_flags=cand_block[1], crc_type = cand_block[2], \
                dest_eid = EID.decode(cand_block[3]), \
                src_eid = EID.decode(cand_block[4]), \
                rpt_eid = EID.decode(cand_block[5]), \
                creation_timestamp = CreationTimestamp.decode(cand_block[6]), \
                lifetime = cand_block[7])
       

