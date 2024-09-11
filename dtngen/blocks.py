import json
from abc import ABC
import cbor2
from itertools import zip_longest
import warnings
import os
import datetime

from .dtnjson import custom_encoder
from .types import EID, CRCFlag, CreationTimestamp, HopCountData, CTEBData, \
    CREBData, calc_crc, default_encoder


class Block(ABC):
    """RFC9171 Block."""

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the block.

        :param list cand_block: A list of objects to be interpreted as a \
            block.
        """
        # I initially tried @abstractmethod, but Python doesn't seem to enforce abstract
        # class methods until an object is instantiated. We have to throw this exception to guarantee all
        # classes dervived from block have a decode method.
        raise NotImplementedError(
            "Forgot to implement decode() in the derived class of Block"
        )


class CanonicalBlock(Block):
    """RFC9171 Extension Block Base Class."""
    
    def __init__(self, blk_type=None, blk_num=None, control_flags=None, crc_type=None, crc=None):
        """Initialize the extension block with the requested fields.

        :param BlockType blk_type: (optional) the type of Canonical block
        :param int blk_num: (optional) block number
        :param BlockPCFlags control_flags: (optional) block processing control \
            flags
        :param CRCType crc_type: (optional) CRC type
        :param bytes crc: (optional) crc value or types.CRCFlag.CALCULATE to \
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
        blen = len(cand_block)
        
        if blen > 6:
            warnmsg = "Canoncial block length greater than 6 elements. Truncating to 6 elements"
            warnings.warn(warnmsg)
            cand_block = cand_block[0:6]
        
        block_fields = {}
        if blen >= 1:
            block_fields["blk_type"] = cand_block[0]
        if blen >= 2:
            block_fields["blk_num"] = cand_block[1]
        if blen >= 3:
            block_fields["control_flags"] = cand_block[2]
        if blen >= 4:
            block_fields["crc_type"] = cand_block[3]
        if blen == 6:
            block_fields["crc"] = cand_block[5]

        return block_fields
        
    def encode(self, type_spec_data):
        """Encode the canonical block using CBOR with the type-specific data.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        if type_spec_data is not None:
            if not isinstance(type_spec_data, bytes):
                type_spec_data = cbor2.dumps(type_spec_data, \
                default=default_encoder)
        
        if self.crc is CRCFlag.CALCULATE and self.crc_type is not None \
            and self.crc_type >= 1 and self.crc_type <= 2:
            tmp = \
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    type_spec_data,
                ]
            cfields = [i for i in tmp if i is not None]
            self.crc = calc_crc(self.crc_type, cfields)
        
        tmp = \
            [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    type_spec_data,
                    self.crc,
            ]
        cfields = [i for i in tmp if i is not None]

        return cbor2.dumps(cfields, default=default_encoder)

        
    def to_json(self, type_spec_data=None):
        """Encode the canonical block using json with the type-specific data.

        :return: A json-encoded block
        :rtype: string
        """
        enc_type_spec_data = type_spec_data
        if type_spec_data is not None:
            if not isinstance(type_spec_data, bytes):
                enc_type_spec_data = cbor2.dumps(type_spec_data, \
                    default=default_encoder)
            
        if self.crc is CRCFlag.CALCULATE and self.crc_type is not None \
            and self.crc_type >= 1 and self.crc_type <= 2:
            tmp = \
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    enc_type_spec_data,
                ]
            cfields = [i for i in tmp if i is not None]
            self.crc = calc_crc(self.crc_type, cfields)
        
        tmp = \
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                type_spec_data,
                self.crc,
            ]
        cfields = [i for i in tmp if i is not None]

        return json.dumps(cfields, default=custom_encoder, indent=4)


class PrevNodeBlock(CanonicalBlock):
    """Class to represent RFC-9171 Previous Node Block."""

    def __init__(self, blk_type=None, blk_num=None, control_flags=None, crc_type=None, prev_eid=None, \
        crc=None):
        """Initialze the previous node block with the requested fields.

        :param BlockType blk_type: (optional) the type of Canonical block
        :param int blk_num: (optional) block number
        :param BlockPCFlags control_flags: (optional) block processing control \
            flags
        :param CRCType crc_type: (optional) CRC type
        :param EID prev_eid: (optional) node that forwarded this bundle to the \
            local node
        :param bytes crc: (optional) crc value or types.CRCFlag.CALCULATE to \
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
        return super().encode(self.get_type_spec())
        
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
            
        :return: A Previous Node Block
        :rtype: PrevNodeBlock
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)
        
        # Type-specific data is doubly encoded, so need to further cbor decode
        tmp = None
        if len(cand_block) >= 5:
            try:
                tmp = cbor2.loads(cand_block[4])
            except (TypeError, cbor2.CBORDecodeValueError, \
                    cbor2.CBORDecodeError, cbor2.CBORDecodeEOF):
                pass

            # If it was not doubly CBOR encoded, pass through original value
            if not cbor2.dumps(tmp) == cand_block[4]:
                tmp = cand_block[4]
            elif EID.lookslike(tmp):
                tmp = EID.decode(tmp)

        return PrevNodeBlock(**canon_fields, prev_eid=tmp)


class BundleAgeBlock(CanonicalBlock):
    """Class to represent RFC-9171 Bundle Age Block."""

    def __init__(
        self, blk_type=None, blk_num=None, control_flags=None, crc_type=None, bundle_age=None, crc=None
    ):
        """Initialze the bundle age block with the requested fields.

        :param BlockType blk_type: (optional) the type of Canonical block
        :param int blk_num: (optional) block number
        :param BlockPCFlags control_flags: (optional) block processing control \
            flags
        :param CRCType crc_type: (optional) CRC type
        :param int bundle_age: (optional) number of milliseconds elapsed \
            between time bundle was created and time it was most recently \
            forwarded
        :param bytes crc: (optional) crc value or types.CRCFlag.CALCULATE to \
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
        return super().encode(self.get_type_spec())
        
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
            
        :return: A Bundle Age Block
        :rtype: BundleAgeBlock
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        # Type-specific data is doubly encoded, so need to further cbor decode
        tmp = None
        if len(cand_block) >= 5:
            try:
                tmp = cbor2.loads(cand_block[4])
            except (TypeError, cbor2.CBORDecodeValueError, \
                    cbor2.CBORDecodeError, cbor2.CBORDecodeEOF):
                pass

            # If it was not doubly CBOR encoded, pass through original value
            if not cbor2.dumps(tmp) == cand_block[4]:
                tmp = cand_block[4]

        return BundleAgeBlock(**canon_fields, bundle_age=tmp)


class HopCountBlock(CanonicalBlock):
    """Class to represent RFC-9171 Hop Count Block."""

    def __init__(
        self, blk_type=None, blk_num=None, control_flags=None, crc_type=None, hop_data=None, \
        crc=None
    ):
        """Initialize the hop count block with the requested fields.

        :param BlockType blk_type: (optional) the type of Canonical block
        :param int blk_num: (optional) block number
        :param BlockPCFlags (optional) control_flags: block processing control flags
        :param CRCType crc_type: (optional) CRC type
        :param HopCountData hop_data: (optional) hop_limit after which it \
            should be deleted and hop_count number of times bundle was forward \
            from one node to another
        :param bytes crc: (optional) crc value or types.CRCFlag.CALCULATE to calculate it
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.hop_data = hop_data

    def get_type_spec(self):
        """Return the type-specific values as a list.

        :return: Type-specific values
        :rtype: list
        """
        return self.hop_data

    def encode(self):
        """Encode the HopCountBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        return super().encode(self.get_type_spec())
        
    def to_json(self):
        """Encode the HopCountBlock block using json.

        :return: A json-encoded block
        :rtype: string
        """
        return super().to_json(self.get_type_spec())

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Hop Count Block.

        :params list cand_block: A list of objects to be interpreted as a Hop \
            Count Block.
            
        :return: A Hop Count Block
        :rtype: HopCountBlock
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        # Type-specific data is doubly encoded, so need to further cbor decode
        tmp = None
        if len(cand_block) >= 5:
            try:
                tmp = cbor2.loads(cand_block[4])
            except (TypeError, cbor2.CBORDecodeValueError, \
                    cbor2.CBORDecodeError, cbor2.CBORDecodeEOF):
                pass

            # If it was not doubly CBOR encoded, pass through original value
            if not cbor2.dumps(tmp) == cand_block[4]:
                tmp = cand_block[4]
            elif HopCountData.lookslike(tmp):
                tmp = HopCountData.decode(tmp)

        return HopCountBlock(**canon_fields, hop_data=tmp)


class CustodyTransferBlock(CanonicalBlock):
    """Class to represent Custody Transfer Extension Block."""
    def __init__(
        self, blk_type=None, blk_num=None, control_flags=None, crc_type=None, \
            cteb_data=None, crc=None
    ):
        """Initialize the custody transfer extension block with the requested \
            fields.

        :param BlockType blk_type: (optional) the type of Canonical block
        :param int blk_num: (optional) block number
        :param BlockPCFlags (optional) control_flags: block processing control \
            flags
        :param CRCType crc_type: (optional) CRC type
        :param CTEBData cteb_data: (optional) trans_id identifier for the \
            custody signal, trans_series_id intentifier for a transmission \
            series reg_orig_eid EID of the originator of the custody request
        :param bytes crc: (optional) crc value or types.CRCFlag.CALCULATE to \
            calculate it
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.cteb_data = cteb_data

    def get_type_spec(self):
        """Return the type-specific values as a list.

        :return: Type-specific values
        :rtype: list
        """        
        return self.cteb_data

    def encode(self):
        """Encode the CustodyTransferBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        return super().encode(self.get_type_spec())
        
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
            
        :return: A Custody Transfer Extension Block
        :rtype: CustodyTransferBlock
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        # Type-specific data is doubly encoded, so need to further cbor decode
        tmp = None
        if len(cand_block) >= 5:
            try:
                tmp = cbor2.loads(cand_block[4])
            except (TypeError, cbor2.CBORDecodeValueError, \
                    cbor2.CBORDecodeError, cbor2.CBORDecodeEOF):
                pass

            # If it was not doubly CBOR encoded, pass through original value
            if not cbor2.dumps(tmp) == cand_block[4]:
                tmp = cand_block[4]
            elif CTEBData.lookslike(tmp):
                tmp = CTEBData.decode(tmp)

        return CustodyTransferBlock(**canon_fields, cteb_data=tmp)


class CompressedReportingBlock(CanonicalBlock):
    """Class to represent Compressed Reporting Extension Block."""

    def __init__(
        self, blk_type=None, blk_num=None, control_flags=None, crc_type=None, \
            creb_data=None, crc=None
    ):
        """Initialize the compressed reporting extension block with the \
            requested fields. For the block-type-specific fields, if one is \
            provided, all prior ones must also be provided. For example, if \
            rpt_request_flags is provided, then both bundle_seq_id and \
            bundle_seq_num must be provided as well.

        :param BlockType blk_type: (optional) the type of Canonical block
        :param int blk_num: (optional) block number
        :param BlockPCFlags control_flags: (optional) block processing control \
            flags
        :param CRCType crc_type: (optional) CRC type
        :param CREBData creb_data: (optional) The CREB type-specific data
        :param bytes crc: (optional) crc value or types.CRCFlag.CALCULATE to \
            calculate it
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.creb_data = creb_data

    def get_type_spec(self):
        """Return the type-specific values as a list.

        :return: Type-specific values
        :rtype: list
        """
        return self.creb_data
        
    def encode(self):
        """Encode the CompressedReportingBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray
        """
        return super().encode(self.get_type_spec())
        
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
            
        :return: A Compressed Reporting Extension Block
        :rtype: CompressedReportingBlock
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)

        # Type-specific data is doubly encoded, so need to further cbor decode
        tmp = None
        if len(cand_block) >= 5:
            try:
                tmp = cbor2.loads(cand_block[4])
            except (TypeError, cbor2.CBORDecodeValueError, \
                    cbor2.CBORDecodeError, cbor2.CBORDecodeEOF):
                pass

            # If it was not doubly CBOR encoded, pass through original value
            if not cbor2.dumps(tmp) == cand_block[4]:
                tmp = cand_block[4]
            elif CREBData.lookslike(tmp):
                tmp = CREBData.decode(tmp)
        
        return CompressedReportingBlock(**canon_fields, creb_data=tmp)


class PayloadBlock(CanonicalBlock):
    """Class to represent RFC-9171 Payload Block."""

    def __init__(self, blk_type=None, blk_num=None, control_flags=None, crc_type=None, payload=None, \
        crc=None):
        """Initialze the payload block with the requested fields.

        :param BlockType blk_type: (optional) the type of Canonical block
        :param int blk_num: (optional) block number
        :param BlockPCFlags control_flags: (optional) block processing control \
            flags
        :param CRCType crc_type: (optional) CRC type
        :param bytes payload: (optional) the bundle payload
        :param bytes crc: (optional) crc value or types.CRCFlag.CALCULATE to \
            calculate it
        """
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)
        self.payload = payload  # payload is NOT doubly cbor encoded

        if self.blk_num != 1:
            warnmsg = f'Payload block number is {self.blk_num} but should be 1'
            warnings.warn(warnmsg)

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
        type_spec_data = self.get_type_spec()
        
        if self.crc is CRCFlag.CALCULATE and self.crc_type is not None \
            and self.crc_type >= 1 and self.crc_type <= 2:
            tmp = \
                [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    type_spec_data,
                ]
            cfields = [i for i in tmp if i is not None]
            self.crc = calc_crc(self.crc_type, cfields)
            
        tmp = \
            [
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                type_spec_data,
                self.crc,
            ]
        cfields = [i for i in tmp if i is not None]

        return json.dumps(cfields, default=custom_encoder, indent=4)

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
                    type_spec_data,
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

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Payload Block.

        :params list cand_block: A list of objects to be interpreted as a \
            Payload Block.
            
        :return: A Payload Block
        :rtype: PayloadBlock
        """
        canon_fields = CanonicalBlock.decode_common(cand_block)
        
        # payload is NOT doubly cbor encoded
        tmp = None
        if len(cand_block) >= 5:
            tmp = cand_block[4]
            
        return PayloadBlock(**canon_fields, payload=tmp)


class PayloadBlockSettings:
    """Class to represent settings for RFC-9171 Payload Block generation."""

    MAX_PAYLOAD_SIZE = 10*1024*1024     # Maximum payload currently is 10 MB

    def __init__(self, blk_type=None, blk_num=None, control_flags=None, 
        crc_type=None, payload=None, crc=None):
        """Initialze the payload block with the requested fields.

        :param BlockType blk_type: (optional) the type of Canonical block
        :param int blk_num: (optional) block number
        :param BlockPCFlags control_flags: (optional) block processing control \
            flags
        :param CRCType crc_type: (optional) CRC type
        :param dict payload: (optional) {"size": <payload size>} "size" key \
            with payload size in bytes to generate
        :param bytes crc: (optional) crc value or types.CRCFlag.CALCULATE to \
            calculate it
        """
        self.blk_type = blk_type
        self.blk_num = blk_num
        self.control_flags = control_flags
        self.crc_type = crc_type
        self.crc = crc
        
        if isinstance(payload, dict) and "size" in payload \
                and isinstance(payload["size"], int):
            self.payload_size = payload["size"]
            
            if self.payload_size > PayloadBlockSettings.MAX_PAYLOAD_SIZE:
                warnmsg = f'Specified payload size {self.payload_size} is \
larger than the MAX_PAYLOAD_SIZE of {PayloadBlockSettings.MAX_PAYLOAD_SIZE}'
                warnings.warn(warnmsg)
        else:
            raise ValueError("payload settings not provided or does not \
contain \"size\" key with int value")

    def generate(self, bundle_num):
        """Generate a payload block with the settings in this \
            PayloadBundleSettings. bundle_num is ignored.
        
        :param int bundle_num: the number of the bundle being generated \
            (0 to ...)

        :return: The generated Payload block
        :rtype: PayloadBlock
        """
        # generate a random byte string payload of the specified size in bytes
        generated_payload = os.urandom(self.payload_size)

        return PayloadBlock(blk_type=self.blk_type, blk_num=self.blk_num,
            control_flags=self.control_flags, crc_type=self.crc_type, 
            payload=generated_payload, crc=self.crc)


class PrimaryBlock(Block):
    """RFC9171 Primary Block."""

    def __init__(
        self,
        version=None,
        control_flags=None,
        crc_type=None,
        dest_eid=None,
        src_eid=None,
        rpt_eid=None,
        creation_timestamp=None,
        lifetime=None,
        crc=None,
    ):
        """Initialize the primary block with the requested fields.

        :param int version: (optional) version of the Bundle Protocol that \
            constructed this block
        :param BundlePCFlags control_flags: (optional) bundle processing \
            control flags
        :param CRCType crc_type: (optional) CRC type
        :param EID dest_eid: (optional) bundle endpoint that is the bundle's \
            destination
        :param EID src_eid: (optional) bundle node at which the bundle was \
            initially transmitted, or null endpoint if anomymous
        :param EID rpt_eid: (optional) bundle endpoint to which status reports \
            pertaining to the forwarding and delivery of this bundle are to be \
            transmitted
        :param CreationTimestamp creation_timestamp: (optional) creation \
            timestamp
        :param int lifetime: (optional) number of milliseconds past the \
            creation time at which the bundle's payload will no longer be useful
        :param bytes crc: (optional) crc value or types.CRCFlag.CALCULATE to \
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
        if self.crc is CRCFlag.CALCULATE and self.crc_type is not None \
            and self.crc_type >= 1 and self.crc_type <= 2:
            tmp = \
                [
                    self.version,
                    self.control_flags,
                    self.crc_type,
                    self.dest_eid,
                    self.src_eid,
                    self.rpt_eid,
                    self.creation_timestamp,
                    self.lifetime,
                ]
            fields = [i for i in tmp if i is not None]
            self.crc = calc_crc(self.crc_type, fields)
        
        tmp = \
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
            ]
        fields = [i for i in tmp if i is not None]

        return cbor2.dumps(fields, default=default_encoder)
        

    def to_json(self):
        """Encode the Primary block using json.

        :return: A json-encoded block
        :rtype: string
        """
        if self.crc is CRCFlag.CALCULATE and self.crc_type is not None \
            and self.crc_type >= 1 and self.crc_type <= 2:
            tmp = \
                [
                    self.version,
                    self.control_flags,
                    self.crc_type,
                    self.dest_eid,
                    self.src_eid,
                    self.rpt_eid,
                    self.creation_timestamp,
                    self.lifetime,
                ]
            fields = [i for i in tmp if i is not None]
            self.crc = calc_crc(self.crc_type, fields)
        
        tmp = \
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
            ]
        fields = [i for i in tmp if i is not None]

        return json.dumps(fields, default=custom_encoder, indent=4)
        

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Primary Block.

        :params list cand_block: A list of objects to be interpreted as a \
            Primary Block.
            
        :return: A Primary Block
        :rtype: PrimaryBlock
        """
        blen = len(cand_block)
        
        if blen > 9:
            warnmsg = "Primary block length greater than 9 elements. Truncating to 9 elements"
            warnings.warn(warnmsg)
            cand_block = cand_block[0:9]
        
        if blen >= 4 and EID.lookslike(cand_block[3]):
            cand_block[3] = EID.decode(cand_block[3])
        if blen >= 5 and EID.lookslike(cand_block[4]):
            cand_block[4] = EID.decode(cand_block[4])
        if blen >= 6 and EID.lookslike(cand_block[5]):
            cand_block[5] = EID.decode(cand_block[5])
        if blen >= 7 and CreationTimestamp.lookslike(cand_block[6]):
            cand_block[6] = CreationTimestamp.decode(cand_block[6])

        return PrimaryBlock(*cand_block)            


class PrimaryBlockSettings:
    """Settings to generate RFC9171 Primary Blocks."""

    def __init__(self,
        version=None,
        control_flags=None,
        crc_type=None,
        dest_eid=None,
        src_eid=None,
        rpt_eid=None,
        creation_timestamp=None,
        lifetime=None,
        crc=None,
    ):
        """Initialize the primary block with the requested fields.

        :param int version: (optional) version of the Bundle Protocol that \
            constructed this block
        :param BundlePCFlags control_flags: (optional) bundle processing \
            control flags
        :param CRCType crc_type: (optional) CRC type
        :param EID dest_eid: (optional) bundle endpoint that is the bundle's \
            destination
        :param EID src_eid: (optional) bundle node at which the bundle was \
            initially transmitted, or null endpoint if anomymous
        :param EID rpt_eid: (optional) bundle endpoint to which status reports \
            pertaining to the forwarding and delivery of this bundle are to be \
            transmitted
        :param dict creation_timestamp: (optional) creation timestamp \
                generation settings\n
            {\n
                "time": "current" or {"start": <start_time>, "increment": \
                    <ms between bundles>},\n
                "sequence": {"start": <start value>} or {"fixed": <fixed value>}\n
            }
        :param int lifetime: (optional) number of milliseconds past the \
            creation time at which the bundle's payload will no longer be useful
        :param bytes crc: (optional) crc value or types.CRCFlag.CALCULATE to \
            calculate it
        """
        self.version = version
        self.control_flags = control_flags
        self.crc_type = crc_type
        self.dest_eid = dest_eid
        self.src_eid = src_eid
        self.rpt_eid = rpt_eid
        self.lifetime = lifetime
        self.crc = crc
        
        self.cts_time_current = False
        self.cts_time_start = None
        self.cts_time_increment = None
        
        self.cts_seq_fixed = False
        self.cts_seq_start = None
        
        if creation_timestamp and isinstance(creation_timestamp, dict):
            if isinstance(creation_timestamp["time"], str) \
                    and creation_timestamp["time"].lower() == "current":
                self.cts_time_current = True
            
            if not self.cts_time_current \
                    and isinstance(creation_timestamp["time"], dict):
                if "start" in creation_timestamp["time"] \
                        and isinstance(creation_timestamp["time"]["start"], int):
                    self.cts_time_start = creation_timestamp["time"]["start"]
                if "increment" in creation_timestamp["time"] \
                        and isinstance(creation_timestamp["time"]["increment"], int):
                    self.cts_time_increment = creation_timestamp["time"]["increment"]

            if "sequence" in creation_timestamp \
                    and isinstance(creation_timestamp["sequence"], dict):
                if "fixed" in creation_timestamp["sequence"]:
                    self.cts_seq_fixed = True
                    if isinstance(creation_timestamp["sequence"]["fixed"], int):
                        self.cts_seq_start = \
                            creation_timestamp["sequence"]["fixed"]
                elif "start" in creation_timestamp["sequence"] \
                        and isinstance(creation_timestamp["sequence"]["start"], int):
                    self.cts_seq_start = creation_timestamp["sequence"]["start"]

        else:
            raise ValueError("creation_timestamp not provided or not a dict with settings")

        if not self.cts_time_current:
            if not (self.cts_time_start and self.cts_time_increment):
                raise ValueError("creation_timestamp \"time\" is not \"current\" \
and \"start\" and/or \"increment\" not provided or are not ints")
                    
        if self.cts_seq_fixed:
            if self.cts_seq_start is None:
                raise ValueError("creation_timestamp \"sequence\" type is \
fixed, but \"fixed\" value is not an int")
        else:
            if self.cts_seq_start is None:
                raise ValueError("creation_timestamp \"sequence\" \"start\" \
value is not an int")

    def generate(self, bundle_num):
        """Generate a Primary Block with the settings in this \
            PayloadBundleSettings and the given bundle number.
        
        :param int bundle_num: the number of the bundle being generated \
            (0 to ...)

        :return: The generated Primary block
        :rtype: PrimaryBlock
        """

        if self.cts_time_current:
            # The difference in milliseconds between the UTC epoch and the
            # dtn epoch is 946684800000
            generated_time = int(datetime.datetime.now().timestamp() * 1000) \
                - 946684800000
        else:
            generated_time = self.cts_time_start \
                + self.cts_time_increment*bundle_num
                
        generated_seq = self.cts_seq_start \
            + (0 if self.cts_seq_fixed else bundle_num)
            
        return PrimaryBlock(
            version=self.version,
            control_flags=self.control_flags,
            crc_type=self.crc_type,
            dest_eid=self.dest_eid,
            src_eid=self.src_eid,
            rpt_eid=self.rpt_eid,
            creation_timestamp=CreationTimestamp({"time": generated_time, \
                "sequence": generated_seq}),
            lifetime=self.lifetime,
            crc=self.crc,
        )


class UnknownBlock(Block):
    """Unknown Block."""

    def __init__(
        self,
        elements=None,
    ):
        """Initialize the unknown block with the requested fields.

        :param list elements: list of all of the elements of the block
        """
        self.elements = elements

    def encode(self):
        """Encode the Unknown block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytes
        """
        if isinstance(self.elements, list):
            fields = [i for i in self.elements if i is not None]
        else:
            fields = self.elements

        return cbor2.dumps(fields, default=default_encoder)
        

    def to_json(self):
        """Encode the Unknown block using json.

        :return: A json-encoded block
        :rtype: string
        """
        if isinstance(self.elements, list):
            fields = [i for i in self.elements if i is not None]
        else:
            fields = self.elements

        return json.dumps(fields, default=custom_encoder, indent=4)
        

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as an Unknown Block.

        :params list cand_block: A list of objects to be interpreted as a \
            Unknown Block.
        """
        return UnknownBlock(elements=cand_block)            
