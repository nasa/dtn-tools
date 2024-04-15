import json
from abc import ABC

import cbor2

from .dtnjson import custom_encoder
from .types import EID, CRCFlag, CreationTimestamp, calc_crc, default_encoder


class Block(ABC):
    """RFC9171 Block."""

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the block.

        :param list cand_block: A list of objects to be interpreted as a \
            primary block.
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

        :param BlockType blk_type: the type of Canonical block
        :param int blk_num: block number
        :param BlockPCFlags control_flags: block processing control flags
        :param CRCType crc_type: CRC type
        :param int crc: (optional) crc value or CRCFlag.CALCULATE to \
            calculate it
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

        :param list cand_block: A list representing the candidate canonical \
            block
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
        crc=None):
        """Initialze the previous node block with the requested fields.

        :param BlockType blk_type: the type of Canonical block
        :param int blk_num: block number
        :param BlockPCFlags control_flags: block processing control flags
        :param CRCType crc_type: CRC type
        :param EID prev_eid: node that forwarded this bundle to the local node
        :param int crc: (optional) crc value or CRCFlag.CALCULATE to \
            calculate it
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.prev_eid = prev_eid

    def encode(self):
        """Encode the PrevNodeBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        if self.crc is None:
            return cbor2.dumps(
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    self.prev_eid,
                ],
                default=default_encoder,
            )
        elif self.crc == CRCFlag.CALCULATE:
            self.crc = calc_crc(
                self.crc_type,
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    self.prev_eid,
                ],
            )

        return cbor2.dumps(
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                self.prev_eid,
                self.crc,
            ],
            default=default_encoder,
        )

    def to_json(self):
        """Encode the PrevNodeBlock block using json.

        :return: A json-encoded block
        :rtype: string
        """
        if self.crc is None:
            return json.dumps(
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    self.prev_eid,
                ],
                default=custom_encoder,
            )
        elif self.crc == CRCFlag.CALCULATE:
            self.crc = calc_crc(
                self.crc_type,
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    self.prev_eid,
                ],
            )

        return json.dumps(
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                self.prev_eid,
                self.crc,
            ],
            default=custom_encoder,
        )

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Previouse Node Block.

        :params list cand_block: A list of objects to be interpreted as a \
            Previous Node block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        return PrevNodeBlock(**canon_fields, prev_eid=EID.decode(cand_block[4]))


class BundleAgeBlock(CanonicalBlock):
    """Class to represent RFC-9171 Bundle Age Block."""

    def __init__(
        self, blk_type, blk_num, control_flags, crc_type, bundle_age, crc=None
    ):
        """Initialze the bundle age block with the requested fields.

        :param BlockType blk_type: the type of Canonical block
        :param int blk_num: block number
        :param BlockPCFlags control_flags: block processing control flags
        :param CRCType crc_type: CRC type
        :param int bundle_age: number of milliseconds elapsed between time \
            bundle was created and time it was most recently forwarded
        :param int crc: (optional) crc value or CRCFlag.CALCULATE to \
            calculate it
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.bundle_age = bundle_age

    def encode(self):
        """Encode the BundleAgeBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        if self.crc is None:
            return cbor2.dumps(
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    self.bundle_age,
                ],
                default=default_encoder,
            )
        elif self.crc == CRCFlag.CALCULATE:
            self.crc = calc_crc(
                self.crc_type,
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    self.bundle_age,
                ],
            )

        return cbor2.dumps(
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                self.bundle_age,
                self.crc,
            ],
            default=default_encoder,
        )

    def to_json(self):
        """Encode the BundleAgeBlock block using json.

        :return: A json-encoded block
        :rtype: string
        """
        if self.crc is None:
            return json.dumps(
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    self.bundle_age,
                ],
                default=custom_encoder,
            )
        elif self.crc == CRCFlag.CALCULATE:
            self.crc = calc_crc(
                self.crc_type,
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    self.bundle_age,
                ],
            )

        return json.dumps(
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                self.bundle_age,
                self.crc,
            ],
            default=custom_encoder,
        )

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Bundle Age Block.

        :params list cand_block: A list of objects to be interpreted as a \
            Bundle Age block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        return BundleAgeBlock(**canon_fields, bundle_age=cand_block[4])


class HopCountBlock(CanonicalBlock):
    """Class to represent RFC-9171 Hop Count Block."""

    def __init__(
        self, blk_type, blk_num, control_flags, crc_type, hop_limit, \
            hop_count, crc=None
    ):
        """Initialize the hop count block with the requested fields.

        :param BlockType blk_type: the type of Canonical block
        :param int blk_num: block number
        :param BlockPCFlags control_flags: block processing control flags
        :param CRCType crc_type: CRC type
        :param int hop_limit: hop limit after which it should be deleted
        :param int hop_count: number of times bundle was forwarded from one \
            node to another
        :param int crc: (optional) crc value or CRCFlag.CALCULATE to \
            calculate it
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.hop_limit = hop_limit
        self.hop_count = hop_count

    def encode(self):
        """Encode the HopCountBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        if self.crc is None:
            return cbor2.dumps(
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    [self.hop_limit, self.hop_count],
                ],
                default=default_encoder,
            )
        elif self.crc == CRCFlag.CALCULATE:
            self.crc = calc_crc(
                self.crc_type,
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    [self.hop_limit, self.hop_count],
                ],
            )

        return cbor2.dumps(
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                [self.hop_limit, self.hop_count],
                self.crc,
            ],
            default=default_encoder,
        )

    def to_json(self):
        """Encode the HopCountBlock block using json.

        :return: A json-encoded block
        :rtype: string
        """
        if self.crc is None:
            return json.dumps(
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    [self.hop_limit, self.hop_count],
                ],
                default=custom_encoder,
            )
        elif self.crc == CRCFlag.CALCULATE:
            self.crc = calc_crc(
                self.crc_type,
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    [self.hop_limit, self.hop_count],
                ],
            )

        return json.dumps(
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                [self.hop_limit, self.hop_count],
                self.crc,
            ],
            default=custom_encoder,
        )

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Hop Count Block.

        :params list cand_block: A list of objects to be interpreted as a \
            payload block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        return HopCountBlock(
            **canon_fields, hop_limit=cand_block[4][0], \
                hop_count=cand_block[4][1]
        )


class PayloadBlock(CanonicalBlock):
    """Class to represent RFC-9171 Payload Block."""

    def __init__(self, blk_type, blk_num, control_flags, crc_type, payload, \
        crc=None):
        """Initialze the payload block with the requested fields.

        :param BlockType blk_type: the type of Canonical block
        :param int blk_num: block number
        :param BlockPCFlags control_flags: block processing control flags
        :param CRCType crc_type: CRC type
        :param bytes payload: the bundle payload
        :param int crc: (optional) crc value or CRCFlag.CALCULATE to \
            calculate it
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.payload = payload

    def encode(self):
        """Encode the Payload block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        if self.crc is None:
            return cbor2.dumps(
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    self.payload,
                ],
                default=default_encoder,
            )
        elif self.crc == CRCFlag.CALCULATE:
            self.crc = calc_crc(
                self.crc_type,
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    self.payload,
                ],
            )

        return cbor2.dumps(
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                self.payload,
                self.crc,
            ],
            default=default_encoder,
        )

    def to_json(self):
        """Encode the Payload block using json.

        :return: A json-encoded block
        :rtype: string
        """
        if self.crc is None:
            return json.dumps(
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    self.payload,
                ],
                default=custom_encoder,
            )
        elif self.crc == CRCFlag.CALCULATE:
            self.crc = calc_crc(
                self.crc_type,
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    self.payload,
                ],
            )

        return json.dumps(
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                self.payload,
                self.crc,
            ],
            default=custom_encoder,
        )

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Payload Block.

        :params list cand_block: A list of objects to be interpreted as a \
            payload block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        return PayloadBlock(**canon_fields, payload=cand_block[4])


class PrimaryBlock(Block):
    """RFC9171 Primary Block."""

    def __init__(
        self,
        version,
        control_flags,
        crc_type,
        dest_eid,
        src_eid,
        rpt_eid,
        creation_timestamp,
        lifetime,
        crc=None,
    ):
        """Initialize the primary block with the requested fields.

        :param int version: version of the Bundle Protocol that constructed \
            this block
        :param BundlePCFlags control_flags: bundle processing control flags
        :param CRCType crc_type: CRC type
        :param EID dest_eid: bundle endpoint that is the bundle's destination
        :param EID src_eid: bundle node at which the bundle was initially \
            transmitted, or null endpoint if anomymous
        :param EID rpt_eid: bundle endpoint to which status reports pertaining \
            to the forwarding and delivery of this bundle are to be transmitted
        :param CreationTimestamp creation_timestamp: creation timestamp
        :para int lifetime: number of milliseconds past the creation time at \
            which the bundle's payload will no longer be useful
        :param int crc: (optional) crc value or CRCFlag.CALCULATE to \
            calculate it
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
        if self.crc is None:
            return cbor2.dumps(
                [
                    self.version,
                    self.control_flags,
                    self.crc_type,
                    self.dest_eid,
                    self.src_eid,
                    self.rpt_eid,
                    self.creation_timestamp,
                    self.lifetime,
                ],
                default=default_encoder,
            )
        elif self.crc == CRCFlag.CALCULATE:
            self.crc = calc_crc(
                self.crc_type,
                [
                    self.version,
                    self.control_flags,
                    self.crc_type,
                    self.dest_eid,
                    self.src_eid,
                    self.rpt_eid,
                    self.creation_timestamp,
                    self.lifetime,
                ],
            )

        return cbor2.dumps(
            [
                self.version,
                self.control_flags,
                self.crc_type,
                self.dest_eid,
                self.src_eid,
                self.rpt_eid,
                self.creation_timestamp,
                self.lifetime,
                self.crc,
            ],
            default=default_encoder,
        )

    def to_json(self):
        """Encode the Primary block using json.

        :return: A json-encoded block
        :rtype: string
        """
        if self.crc is None:
            return json.dumps(
                [
                    self.version,
                    self.control_flags,
                    self.crc_type,
                    self.dest_eid,
                    self.src_eid,
                    self.rpt_eid,
                    self.creation_timestamp,
                    self.lifetime,
                ],
                default=custom_encoder,
            )
        elif self.crc == CRCFlag.CALCULATE:
            self.crc = calc_crc(
                self.crc_type,
                [
                    self.version,
                    self.control_flags,
                    self.crc_type,
                    self.dest_eid,
                    self.src_eid,
                    self.rpt_eid,
                    self.creation_timestamp,
                    self.lifetime,
                ],
            )

        return json.dumps(
            [
                self.version,
                self.control_flags,
                self.crc_type,
                self.dest_eid,
                self.src_eid,
                self.rpt_eid,
                self.creation_timestamp,
                self.lifetime,
                self.crc,
            ],
            default=custom_encoder,
        )

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Primary Block.

        :params list cand_block: A list of objects to be interpreted as a \
            primary block.
        """
        # TODO: Length checks

        # Version
        if cand_block[0] != 7:
            raise ValueError(
                f"Primary block: Expected BP Version 7, got {cand_block[0]}"
            )

        if len(cand_block) == 9:
            return PrimaryBlock(
                version=cand_block[0],
                control_flags=cand_block[1],
                crc_type=cand_block[2],
                dest_eid=EID.decode(cand_block[3]),
                src_eid=EID.decode(cand_block[4]),
                rpt_eid=EID.decode(cand_block[5]),
                creation_timestamp=CreationTimestamp.decode(cand_block[6]),
                lifetime=cand_block[7],
                crc=cand_block[8],
            )
        else:
            return PrimaryBlock(
                version=cand_block[0],
                control_flags=cand_block[1],
                crc_type=cand_block[2],
                dest_eid=EID.decode(cand_block[3]),
                src_eid=EID.decode(cand_block[4]),
                rpt_eid=EID.decode(cand_block[5]),
                creation_timestamp=CreationTimestamp.decode(cand_block[6]),
                lifetime=cand_block[7],
            )
