import json
from abc import ABC

import cbor2
from itertools import zip_longest

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

        :param list cand_block: A list representing the candidate Canonical \
            Block
        """
        block_fields = {}
        block_fields["blk_type"] = cand_block[0]
        block_fields["blk_num"] = cand_block[1]
        block_fields["control_flags"] = cand_block[2]
        block_fields["crc_type"] = cand_block[3]
        if len(cand_block) == 6:
            block_fields["crc"] = cand_block[5]

        return block_fields
        
    def encode(self, type_spec_data):
        """Encode the canonical block using CBOR with the type-specific data.

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
                    type_spec_data,
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
                    type_spec_data,
                ],
            )

        return cbor2.dumps(
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                type_spec_data,
                self.crc,
            ],
            default=default_encoder,
        )
        
    def to_json(self, type_spec_data):
        """Encode the canonical block using json with the type-specific data.

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
                    type_spec_data,
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
                    cbor2.dumps(type_spec_data, default=default_encoder),
                ],
            )

        return json.dumps(
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                type_spec_data,
                self.crc,
            ],
            default=custom_encoder,
        )


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

    def get_type_spec(self):
        """Return the type-specific value.

        :return: Type-specific value
        :rtype: EID
        """        
        return self.prev_eid

    def encode(self):
        """Encode the PrevNodeBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        return super().encode(cbor2.dumps(self.get_type_spec(), \
            default=default_encoder))
        
    def to_json(self):
        """Encode the PrevNodeBlock block using json.

        :return: A json-encoded block
        :rtype: string
        """
        return super().to_json(self.get_type_spec())
        
    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Previouse Node Block.

        :params list cand_block: A list of objects to be interpreted as a \
            Previous Node Block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)
        
        # Type-specific data is doubly encoded, so need to further cbor decode
        tmp = cbor2.loads(cand_block[4])

        return PrevNodeBlock(**canon_fields, prev_eid=EID.decode(tmp))


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

    def get_type_spec(self):
        """Return the type-specific value.

        :return: Type-specific value
        :rtype: unsigned int
        """        
        return self.bundle_age

    def encode(self):
        """Encode the BundleAgeBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        return super().encode(cbor2.dumps(self.get_type_spec(), \
            default=default_encoder))
        
    def to_json(self):
        """Encode the BundleAgeBlock block using json.

        :return: A json-encoded block
        :rtype: string
        """
        return super().to_json(self.get_type_spec())

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Bundle Age Block.

        :params list cand_block: A list of objects to be interpreted as a \
            Bundle Age Block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        # Type-specific data is doubly encoded, so need to further cbor decode
        tmp = cbor2.loads(cand_block[4])

        return BundleAgeBlock(**canon_fields, bundle_age=tmp)


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

    def get_type_spec(self):
        """Return the type-specific values as a list.

        :return: Type-specific values
        :rtype: list
        """        
        return [self.hop_limit, self.hop_count]

    def encode(self):
        """Encode the HopCountBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        return super().encode(cbor2.dumps(self.get_type_spec(), \
            default=default_encoder))
        
    def to_json(self):
        """Encode the HopCountBlock block using json.

        :return: A json-encoded block
        :rtype: string
        """
        return super().to_json(self.get_type_spec())

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Hop Count Block.

        :params list cand_block: A list of objects to be interpreted as a \
            Hop Count Block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        # Type-specific data is doubly encoded, so need to further cbor decode
        tmp = cbor2.loads(cand_block[4])
        
        return HopCountBlock(**canon_fields, hop_limit=tmp[0], hop_count=tmp[1])


class CustodyTransferBlock(CanonicalBlock):
    """Class to represent Custody Transfer Extension Block."""

    def __init__(
        self, blk_type, blk_num, control_flags, crc_type, trans_id, \
            trans_series_id, req_orig_eid, crc=None
    ):
        """Initialize the custody transfer extension block with the requested \
            fields.

        :param BlockType blk_type: the type of Canonical block
        :param int blk_num: block number
        :param BlockPCFlags control_flags: block processing control flags
        :param CRCType crc_type: CRC type
        :param int trans_id: identifier for the custody signal
        :param int trans_series_id: identifier for a transmission series
        :param int req_orig_eid: EID of the originator of the custody request
        :param int crc: (optional) crc value or CRCFlag.CALCULATE to \
            calculate it
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.trans_id = trans_id
        self.trans_series_id = trans_series_id
        self.req_orig_eid = req_orig_eid

    def get_type_spec(self):
        """Return the type-specific values as a list.

        :return: Type-specific values
        :rtype: list
        """        
        return [self.trans_id, self.trans_series_id, self.req_orig_eid]

    def encode(self):
        """Encode the CustodyTransferBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        return super().encode(cbor2.dumps(self.get_type_spec(), \
            default=default_encoder))
        
    def to_json(self):
        """Encode the CustodyTransferBlock block using json.

        :return: A json-encoded block
        :rtype: string
        """
        return super().to_json(self.get_type_spec())

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Custody Transfer \
            Extension Block.

        :params list cand_block: A list of objects to be interpreted as a \
            Custody Transfer Extension Block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        # Type-specific data is doubly encoded, so need to further cbor decode
        tmp = cbor2.loads(cand_block[4])
        
        return CustodyTransferBlock(
            **canon_fields, trans_id=tmp[0], \
                trans_series_id=tmp[1], \
                req_orig_eid=EID.decode(tmp[2])
        )


class CompressedReportingBlock(CanonicalBlock):
    """Class to represent Compressed Reporting Extension Block."""

    def __init__(
        self, blk_type, blk_num, control_flags, crc_type, bundle_seq_num, \
            bundle_seq_id=None, rpt_request_flags=None, scope_node_id=None, \
            rpt_eid=None, crc=None
    ):
        """Initialize the compress reporting extension block with the \
            requested fields. For the block-type-specific fields, if one is \
            provided, all prior ones must also be provided. For example, if \
            rpt_request_flags is provided, then both bundle_seq_id and \
            bundle_seq_num must be provided as well.

        :param BlockType blk_type: the type of Canonical block
        :param int blk_num: block number
        :param BlockPCFlags control_flags: block processing control flags
        :param CRCType crc_type: CRC type
        :param int bundle_seq_num: bundle sequence number
        :param int bundle_seq_id: bundle sequence identifier
        :param int rpt_request_flags: status report request flags
        :param int scope_node_id: EID of the node that created the CREB
        :param int rpt_eid: EID of the node to send the reports to
        :param int crc: (optional) crc value or CRCFlag.CALCULATE to \
            calculate it
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.bundle_seq_num = bundle_seq_num
        self.bundle_seq_id = bundle_seq_id
        self.rpt_request_flags = rpt_request_flags
        self.scope_node_id = scope_node_id
        self.rpt_eid = rpt_eid
        
        if (bundle_seq_id is not None and bundle_seq_num is None) \
            or (rpt_request_flags is not None and any(arg is None for arg in (bundle_seq_num, bundle_seq_id))) \
            or (scope_node_id is not None and any(arg is None for arg in (bundle_seq_num, bundle_seq_id, rpt_request_flags))) \
            or (rpt_eid is not None and any(arg is None for arg in (bundle_seq_num, bundle_seq_id, rpt_request_flags, scope_node_id))):
                raise ValueError(
                    "Compressed Reporting Extension Block: One or more of bundle_seq_id, rpt_request_flags, scope_node_id or rpt_eid was provided without one or more of the prior arguments provided"
                )

    def get_type_spec(self):
        """Return the type-specific values as a list.

        :return: Type-specific values
        :rtype: list
        """
        type_spec_vals = []
        if self.bundle_seq_num is not None:
            type_spec_vals.append(self.bundle_seq_num)
        if self.bundle_seq_id is not None:
            type_spec_vals.append(self.bundle_seq_id)
        if self.rpt_request_flags is not None:
            type_spec_vals.append(self.rpt_request_flags)
        if self.scope_node_id is not None:
            type_spec_vals.append(self.scope_node_id)
        if self.rpt_eid is not None:
            type_spec_vals.append(self.rpt_eid)
        
        return type_spec_vals
        
    def encode(self):
        """Encode the CompressedReportingBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        return super().encode(cbor2.dumps(self.get_type_spec(), \
            default=default_encoder))
        
    def to_json(self):
        """Encode the CompressedReportingBlock block using json.

        :return: A json-encoded block
        :rtype: string
        """
        return super().to_json(self.get_type_spec())

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Compressed \
            Reporting Extension Block.

        :params list cand_block: A list of objects to be interpreted as a \
            Compressed Reporting Extension Block.
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        # Type-specific data is doubly encoded, so need to further cbor decode
        tmp = cbor2.loads(cand_block[4])
        
        type_spec_dict = {"bundle_seq_num":None, "bundle_seq_id":None, \
            "rpt_request_flags":None, "scope_node_id":None, "rpt_eid":None}
        type_spec_args = dict(zip_longest(type_spec_dict, tmp))
        
        if type_spec_args["scope_node_id"] is not None:
            type_spec_args["scope_node_id"] = EID.decode(type_spec_args["scope_node_id"])
        if type_spec_args["rpt_eid"] is not None:
            type_spec_args["rpt_eid"] = EID.decode(type_spec_args["rpt_eid"])
        
        return CompressedReportingBlock(**canon_fields, **type_spec_args)


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
        self.type_spec_data = payload   # payload is NOT doubly cbor encoded

    def get_type_spec(self):
        """Return the payload

        :return: Payload
        :rtype: CBOR bytestring
        """                    
        return self.payload

    def encode(self):
        """Encode the PayloadBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        return super().encode(self.get_type_spec())

    def to_json(self):
        """Encode the Payload block using json.

        :return: A json-encoded block
        :rtype: string
        """
        type_spec = self.get_type_spec()
        if self.crc is None:
            return json.dumps(
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    type_spec,
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
                    type_spec,
                ],
            )

        return json.dumps(
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                type_spec,
                self.crc,
            ],
            default=custom_encoder,
        )

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Payload Block.

        :params list cand_block: A list of objects to be interpreted as a \
            Payload Block.
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
            Primary Block.
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
