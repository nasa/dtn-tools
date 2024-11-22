import json
from abc import ABC
import cbor2
from itertools import zip_longest
import warnings
import os
import datetime

from .dtnjson import custom_encoder
from .types import TypeWarning, BlockType, BlockPCFlags, BundlePCFlags, \
    CRCType, CRCFlag, EID, CRCFlag, CreationTimestamp, HopCountData, CTEBData, \
    CREBData, calc_crc, default_encoder


class Block(ABC):
    """RFC9171 Block."""

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the block.

        :param list cand_block: A list of objects to be interpreted as a block.
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

        :param BlockType blk_type: (optional) the type of Canonical block. Can be a specific BlockType or BlockType.AUTO to set to the matching BlockType.
        :param int blk_num: (optional) block number
        :param BlockPCFlags control_flags: (optional) block processing control flags
        :param CRCType crc_type: (optional) CRC type
        :param bytes crc: (optional) crc value or CRCFlag.CALCULATE to calculate it

        .. important::
        
            CanonicalBlocks should not normally be created by the user, instead
            the sub-classes should be created.
        """
        cclass_name = self.__class__.__name__
        
        if not isinstance(blk_type, BlockType) and not isinstance(blk_type, int):
            warnmsg = f'{cclass_name} blk_type is type {type(blk_type).__name__} instead of BlockType or int'
            warnings.warn(warnmsg, TypeWarning)
        self.blk_type = blk_type
        
        if not isinstance(blk_num, int):
            warnmsg = f'{cclass_name} blk_num is type {type(blk_num).__name__} instead of int'
            warnings.warn(warnmsg, TypeWarning)
        self.blk_num = blk_num
        
        if not isinstance(control_flags, BlockPCFlags) and not isinstance(control_flags, int):
            warnmsg = f'{cclass_name} control_flags is type {type(control_flags).__name__} instead of BlockPCFlags or int'
            warnings.warn(warnmsg, TypeWarning)
        self.control_flags = control_flags
        
        if not isinstance(crc_type, CRCType) and not isinstance(crc_type, int):
            warnmsg = f'{cclass_name} crc_type is type {type(crc_type).__name__} instead of CRCType or int'
            warnings.warn(warnmsg, TypeWarning)
        self.crc_type = crc_type
        
        if not isinstance(crc, CRCFlag) and not isinstance(crc, bytes) and crc is not None:
            warnmsg = f'{cclass_name} crc is type {type(crc).__name__} instead of CRCFlag, bytes or None'
            warnings.warn(warnmsg, TypeWarning)
        self.crc = crc

    @classmethod
    def decode_common(cls, cand_block):
        """Decode the fields common to all canonical blocks.

        :param list cand_block: A list representing the candidate Canonical Block

        :return: A dictionary containing the common data for the block
        :rtype: dict

        .. important::
        
            CanonicalBlock methods should not normally be called by the user,
            instead the sub-class methods should be called.
        """
        if not isinstance(cand_block, list):
            raise ValueError("Candidate Canonical Block is not a list")
            
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
        
    def encode(self, type_spec_data=None):
        """Encode the canonical block using CBOR with the type-specific data.

        :param any type_spec_data: (optional) the type specific data

        :return: A CBOR-encoded block
        :rtype: bytearray

        .. important::
        
            CanonicalBlock methods should not normally be called by the user,
            instead the sub-class methods should be called.
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
            crc = calc_crc(self.crc_type, cfields)
        else:
            crc = self.crc
        
        tmp = \
            [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    type_spec_data,
                    crc,
            ]
        cfields = [i for i in tmp if i is not None]

        return cbor2.dumps(cfields, default=default_encoder)

        
    def to_json(self, type_spec_key, type_spec_data=None):
        """Encode the canonical block using json with the type-specific data.

        :param string type_spec_key: the key to use for the type specific data
        :param any type_spec_data: (optional) the type specific data
        
        :return: A json-encoded block
        :rtype: string

        .. important::
        
            CanonicalBlock methods should not normally be called by the user,
            instead the sub-class methods should be called.
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
            crc = calc_crc(self.crc_type, cfields)
        else:
            crc = self.crc
        
        tmp = \
            [
                self.__class__.__name__,
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                type_spec_data,
                crc,
            ]
        cfields = [i for i in tmp if i is not None]
        keys = ["_block_class", "blk_type", "blk_num", "control_flags", "crc_type", type_spec_key, "crc"]
        
        return json.dumps(dict(zip(keys, cfields)), default=custom_encoder, indent=4)


class PrevNodeBlock(CanonicalBlock):
    """Class to represent RFC-9171 Previous Node Block."""

    def __init__(self, blk_type=None, blk_num=None, control_flags=None, crc_type=None, prev_eid=None, \
        crc=None):
        """Initialize the previous node block with the requested fields.

        :param BlockType blk_type: (optional) the type of Canonical block. Can be a specific BlockType or BlockType.AUTO to set to the matching BlockType.
        :param int blk_num: (optional) block number
        :param BlockPCFlags control_flags: (optional) block processing control flags
        :param CRCType crc_type: (optional) CRC type
        :param EID prev_eid: (optional) node that forwarded this bundle to the local node
        :param bytes crc: (optional) crc value or CRCFlag.CALCULATE to calculate it

        *Usage:*

        .. code-block:: python
        
            from dtngen.blocks import PrevNodeBlock
            from dtngen.types import BlockType, BlockPCFlags, CRCType, CRCFlag, EID
            
            prevnodeblk = PrevNodeBlock(
                BlockType = BlockType.AUTO,
                blk_num = 2,
                control_flags = BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC,
                CRCType = CRCType.CRC16_X25,
                prev_eid = EID({"uri": 2, "ssp": {"node_num": 300, "service_num": 2}}),
                crc = CRCFlag.CALCULATE
            )
        """
        if blk_type == BlockType.AUTO:
            blk_type = BlockType.PREVIOUS_NODE
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)

        if not isinstance(prev_eid, EID):
            warnmsg = f'PrevNodeBlock prev_eid is type {type(prev_eid).__name__} instead of EID'
            warnings.warn(warnmsg, TypeWarning)
        self.prev_eid = prev_eid

    def get_type_spec(self):
        """Return the type-specific value.

        :return: Type-specific value
        :rtype: EID

        *Usage:*

        .. code-block:: python
        
            ts_data = prev_node_block.get_type_spec()
        """        
        return self.prev_eid

    def encode(self):
        """Encode the PrevNodeBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray

        *Usage:*
        
        .. code-block:: python
        
            cbor_encoded_pnb = prev_node_block.encode()
        """            
        return super().encode(self.get_type_spec())
        
    def to_json(self):
        """Encode the PrevNodeBlock block using json.

        :return: A json-encoded block
        :rtype: string

        *Usage:*
        
        .. code-block:: python
        
            pnb_json = prev_node_block.to_json()
        """
        return super().to_json(type_spec_key="prev_eid", type_spec_data=self.get_type_spec())
        
    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Previouse Node Block.

        :params list cand_block: A list of objects to be interpreted as a Previous Node Block.
            
        :return: A Previous Node Block
        :rtype: PrevNodeBlock

        *Usage:*
        
        The type-specific data (5th element) is doubly cbor encoded. It is passed into this method as a byte string containing cbor encoded data.

        .. code-block:: python
        
            from dtngen.blocks import PrevNodeBlock
            
            pnblock_elements = [6, 2, 1, 1, b'\\x82\\x02\\x82\\x19\\x01\\x2c\\x02', b'\\x25\\xd4']
            pnblock = PrevNodeBlock.decode(pnblock_elements)
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
        """Initialize the bundle age block with the requested fields.

        :param BlockType blk_type: (optional) the type of Canonical block. Can be a specific BlockType or BlockType.AUTO to set to the matching BlockType.
        :param int blk_num: (optional) block number
        :param BlockPCFlags control_flags: (optional) block processing control flags
        :param CRCType crc_type: (optional) CRC type
        :param int bundle_age: (optional) number of milliseconds elapsed \
between time bundle was created and time it was most recently forwarded
        :param bytes crc: (optional) crc value or CRCFlag.CALCULATE to \
calculate it

        *Usage:*

        .. code-block:: python
        
            from dtngen.blocks import BundleAgeBlock
            from dtngen.types import BlockType, BlockPCFlags, CRCType, CRCFlag
            
            bundle_age_block = BundleAgeBlock(
                blk_type=BlockType.AUTO,
                blk_num=2,
                control_flags=BlockPCFlags.FRAG_REPLICATE | BlockPCFlags.DEL_UNPROC,
                crc_type=CRCType.CRC16_X25,
                bundle_age=108000,
                crc=CRCFlag.CALCULATE,
            )
        """
        if blk_type == BlockType.AUTO:
            blk_type = BlockType.BUNDLE_AGE
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)

        if not isinstance(bundle_age, int):
            warnmsg = f'BundleAgeBlock bundle_age is type {type(bundle_age).__name__} instead of int'
            warnings.warn(warnmsg, TypeWarning)
        self.bundle_age = bundle_age

    def get_type_spec(self):
        """Return the type-specific value.

        :return: Type-specific value
        :rtype: unsigned int

        *Usage:*

        .. code-block:: python
        
            ts_data = bundle_age_block.get_type_spec()
        """        
        return self.bundle_age

    def encode(self):
        """Encode the BundleAgeBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray

        *Usage:*
        
        .. code-block:: python
        
            cbor_encoded_bab = bundle_age_block.encode()
        """
        return super().encode(self.get_type_spec())
        
    def to_json(self):
        """Encode the BundleAgeBlock block using json.

        :return: A json-encoded block
        :rtype: string

        *Usage:*
        
        .. code-block:: python
        
            bab_json = bundle_age_block.to_json()
        """
        return super().to_json(type_spec_key="bundle_age", type_spec_data=self.get_type_spec())

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Bundle Age Block.

        :params list cand_block: A list of objects to be interpreted as a Bundle Age Block.
            
        :return: A Bundle Age Block
        :rtype: BundleAgeBlock

        *Usage:*
        
        The type-specific data (5th element) is doubly cbor encoded. It is passed into this method as a byte string containing cbor encoded data.

        .. code-block:: python
        
            from dtngen.blocks import BundleAgeBlock
            
            bablock_elements = [7, 2, 5, 1, b'\\x1a\\x00\\x01\\xa5\\xe0', b'\\x3a\\xed']
            pnblock = BundleAgeBlock.decode(bablock_elements)
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

        :param BlockType blk_type: (optional) the type of Canonical block. Can be a specific BlockType or BlockType.AUTO to set to the matching BlockType.
        :param int blk_num: (optional) block number
        :param BlockPCFlags (optional) control_flags: block processing control flags
        :param CRCType crc_type: (optional) CRC type
        :param HopCountData hop_data: (optional) hop_limit after which it \
should be deleted and hop_count number of times bundle was forward from one \
node to another
        :param bytes crc: (optional) crc value or CRCFlag.CALCULATE to calculate it

        *Usage:*

        .. code-block:: python
        
            from dtngen.blocks import HopCountBlock
            from dtngen.types import BlockType, BlockPCFlags, CRCType, CRCFlag, HopCountData
            
            hop_count_block = HopCountBlock(
                blk_type=BlockType.AUTO,
                blk_num=3,
                control_flags=BlockPCFlags.FRAG_REPLICATE,
                crc_type=CRCType.CRC16_X25,
                hop_data=HopCountData({"hop_limit": 15, "hop_count": 3}),
                crc=CRCFlag.CALCULATE,
            )
        """
        if blk_type == BlockType.AUTO:
            blk_type = BlockType.HOP_COUNT
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)

        if not isinstance(hop_data, HopCountData):
            warnmsg = f'HopCountBlock hop_data is type {type(hop_data).__name__} instead of HopCountData'
            warnings.warn(warnmsg, TypeWarning)
        self.hop_data = hop_data

    def get_type_spec(self):
        """Return the type-specific values as a list.

        :return: Type-specific values
        :rtype: list

        *Usage:*

        .. code-block:: python
        
            ts_data = hop_count_block.get_type_spec()
        """
        return self.hop_data

    def encode(self):
        """Encode the HopCountBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray

        *Usage:*
        
        .. code-block:: python
        
            cbor_encoded_hcb = hop_count_block.encode()
        """
        return super().encode(self.get_type_spec())
        
    def to_json(self):
        """Encode the HopCountBlock block using json.

        :return: A json-encoded block
        :rtype: string

        *Usage:*
        
        .. code-block:: python
        
            hcb_json = hop_count_block.to_json()
        """
        return super().to_json(type_spec_key="hop_data", type_spec_data=self.get_type_spec())

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Hop Count Block.

        :params list cand_block: A list of objects to be interpreted as a Hop Count Block.
            
        :return: A Hop Count Block
        :rtype: HopCountBlock

        *Usage:*
        
        The type-specific data (5th element) is doubly cbor encoded. It is passed into this method as a byte string containing cbor encoded data.

        .. code-block:: python
        
            from dtngen.blocks import HopCountBlock
            
            hcblock_elements = [10, 3, 1, 1, b'\\x82\\x0f\\x03', b'\\xf8\\x13']
            hcblock = HopCountBlock.decode(hcblock_elements)
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
        """Initialize the custody transfer extension block with the requested fields.

        :param BlockType blk_type: (optional) the type of Canonical block. Can be a specific BlockType or BlockType.AUTO to set to the matching BlockType.
        :param int blk_num: (optional) block number
        :param BlockPCFlags (optional) control_flags: block processing control flags
        :param CRCType crc_type: (optional) CRC type
        :param CTEBData cteb_data: (optional) trans_id identifier for the \
custody signal, trans_series_id intentifier for a transmission series \
reg_orig_eid EID of the originator of the custody request
        :param bytes crc: (optional) crc value or CRCFlag.CALCULATE to calculate it

        *Usage:*

        .. code-block:: python
        
            from dtngen.blocks import CustodyTransferBlock
            from dtngen.types import BlockType, BlockPCFlags, CRCType, CRCFlag, CTEBData
            
            cte_block = CustodyTransferBlock(
                blk_type=BlockType.AUTO,
                blk_num=4,
                control_flags=BlockPCFlags.REP_UNPROC,
                crc_type=CRCType.CRC16_X25,
                cteb_data=CTEBData(
                    {"trans_id": 10,
                    "trans_series_id": 2,
                    "req_orig_eid": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}})}
                ),
                crc=CRCFlag.CALCULATE,
            )
        """
        if blk_type == BlockType.AUTO:
            blk_type = BlockType.CUST_TRANS_EXT
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)

        if not isinstance(cteb_data, CTEBData):
            warnmsg = f'CustodyTransferBlock cteb_data is type {type(cteb_data).__name__} instead of CTEBData'
            warnings.warn(warnmsg, TypeWarning)
        self.cteb_data = cteb_data

    def get_type_spec(self):
        """Return the type-specific values as a list.

        :return: Type-specific values
        :rtype: list

        *Usage:*

        .. code-block:: python
        
            ts_data = custody_transfer_block.get_type_spec()
        """        
        return self.cteb_data

    def encode(self):
        """Encode the CustodyTransferBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray

        *Usage:*
        
        .. code-block:: python
        
            cbor_encoded_ctb = custody_transfer_block.encode()
        """
        return super().encode(self.get_type_spec())
        
    def to_json(self):
        """Encode the CustodyTransferBlock block using json.

        :return: A json-encoded block
        :rtype: string

        *Usage:*
        
        .. code-block:: python
        
            ctb_json = custody_transfer_block.to_json()
        """
        return super().to_json(type_spec_key="cteb_data", type_spec_data=self.get_type_spec())

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Custody Transfer Extension Block.

        :params list cand_block: A list of objects to be interpreted as a Custody Transfer Extension Block.
            
        :return: A Custody Transfer Extension Block
        :rtype: CustodyTransferBlock

        *Usage:*
        
        The type-specific data (5th element) is doubly cbor encoded. It is passed into this method as a byte string containing cbor encoded data.

        .. code-block:: python
        
            from dtngen.blocks import CustodyTransferBlock
            
            ctblock_elements = [15, 4, 2, 1, b'\\x83\\x0a\\x02\\x82\\x02\\x82\\x19\\x01\\x2f\\x01', b'\\x25\\xc7']
            ctblock = CustodyTransferBlock.decode(ctblock_elements)
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
        """Initialize the compressed reporting extension block with the requested fields.
        
        For the block-type-specific fields, if one is provided, all prior ones
        must also be provided. For example, if rpt_request_flags is provided,
        then both bundle_seq_id and bundle_seq_num must be provided as well.

        :param BlockType blk_type: (optional) the type of Canonical block. Can be a specific BlockType or BlockType.AUTO to set to the matching BlockType.
        :param int blk_num: (optional) block number
        :param BlockPCFlags control_flags: (optional) block processing control flags
        :param CRCType crc_type: (optional) CRC type
        :param CREBData creb_data: (optional) The CREB type-specific data
        :param bytes crc: (optional) crc value or CRCFlag.CALCULATE to calculate it

        *Usage:*

        .. code-block:: python
        
            from dtngen.blocks import CompressedReportingBlock
            from dtngen.types import BlockType, BlockPCFlags, CRCType, CRCFlag, CREBData, EID
            
            cre_block = CompressedReportingBlock(
                blk_type=BlockType.AUTO,
                blk_num=5,
                control_flags=0,
                crc_type=CRCType.CRC16_X25,
                creb_data=CREBData(
                    {"bundle_seq_num": 1,
                    "bundle_seq_id": 4,
                    "rpt_request_flags": 0,
                    "scope_node_id": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}}),
                    "rpt_eid": EID({"uri": 2, "ssp": {"node_num": 305, "service_num": 2}})}
                ),
                crc=CRCFlag.CALCULATE,
            )
        """
        if blk_type == BlockType.AUTO:
            blk_type = BlockType.COMP_RPT_EXT
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)

        if not isinstance(creb_data, CREBData):
            warnmsg = f'CompressedReportingBlock creb_data is type {type(creb_data).__name__} instead of CREBData'
            warnings.warn(warnmsg, TypeWarning)
        self.creb_data = creb_data

    def get_type_spec(self):
        """Return the type-specific values as a list.

        :return: Type-specific values
        :rtype: list

        *Usage:*

        .. code-block:: python
        
            ts_data = compressed_reporting_block.get_type_spec()
        """
        return self.creb_data
        
    def encode(self):
        """Encode the CompressedReportingBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray

        *Usage:*
        
        .. code-block:: python
        
            cbor_encoded_crb = compressed_reporting_block.encode()
        """
        return super().encode(self.get_type_spec())
        
    def to_json(self):
        """Encode the CompressedReportingBlock block using json.

        :return: A json-encoded block
        :rtype: string

        *Usage:*
        
        .. code-block:: python
        
            cbor_encoded_crb = compressed_reporting_block.to_json()
        """
        return super().to_json(type_spec_key="creb_data", type_spec_data=self.get_type_spec())

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Compressed Reporting Extension Block.

        :params list cand_block: A list of objects to be interpreted as a Compressed Reporting Extension Block.
            
        :return: A Compressed Reporting Extension Block
        :rtype: CompressedReportingBlock

        *Usage:*
        
        The type-specific data (5th element) is doubly cbor encoded. It is passed into this method as a byte string containing cbor encoded data.

        .. code-block:: python
        
            from dtngen.blocks import CompressedReportingBlock
            
            crblock_elements = [16, 5, 0, 1, b'\\x85\\x01\\x04\\x00\\x82\\x02\\x82\\x19\\x01\\x2f\\x01\\x82\\x02\\x82\\x19\\x01\\x31\\x02', b'\\x66\\xce']
            ctblock = CompressedReportingBlock.decode(crblock_elements)
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
        """Initialize the payload block with the requested fields.

        :param BlockType blk_type: (optional) the type of Canonical block. Can be a specific BlockType or BlockType.AUTO to set to the matching BlockType.
        :param int blk_num: (optional) block number
        :param BlockPCFlags control_flags: (optional) block processing control flags
        :param CRCType crc_type: (optional) CRC type
        :param bytes payload: (optional) the bundle payload
        :param bytes crc: (optional) crc value or CRCFlag.CALCULATE to calculate it

        *Usage:*

        .. code-block:: python
        
            from dtngen.blocks import PayloadBlock
            from dtngen.types import BlockType, BlockPCFlags, CRCType, CRCFlag
            
            payload_block = PayloadBlock(
                blk_type=BlockType.AUTO,
                blk_num=1,
                control_flags=0,
                crc_type=CRCType.CRC16_X25,
                payload=b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x0chello world\\n',
                crc=CRCFlag.CALCULATE,
            )
        """
        if blk_type == BlockType.AUTO:
            blk_type = BlockType.BUNDLE_PAYLOAD
        super().__init__(blk_type, blk_num, control_flags, crc_type, crc)

        if not isinstance(payload, bytes):
            warnmsg = f'PayloadBlock payload is type {type(payload).__name__} instead of bytes'
            warnings.warn(warnmsg, TypeWarning)
        self.payload = payload  # payload is NOT doubly cbor encoded

        if self.blk_num != 1:
            warnmsg = f'PayloadBlock blk_num is {self.blk_num} but should be 1'
            warnings.warn(warnmsg)

    def get_type_spec(self):
        """Return the payload

        :return: Payload
        :rtype: CBOR bytestring

        *Usage:*

        .. code-block:: python
        
            ts_data = payload_block.get_type_spec()
        """                    
        return self.payload

    def encode(self):
        """Encode the PayloadBlock block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray

        *Usage:*
        
        .. code-block:: python
        
            cbor_encoded_pb = payload_block.encode()
        """
        # The payload is NOT doubly cbor encoded
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
            crc = calc_crc(self.crc_type, cfields)
        else:
            crc = self.crc
        
        tmp = \
            [
                    self.blk_type,
                    self.blk_num,
                    self.control_flags,
                    self.crc_type,
                    type_spec_data,
                    crc,
            ]
        cfields = [i for i in tmp if i is not None]

        return cbor2.dumps(cfields, default=default_encoder)

    def to_json(self):
        """Encode the Payload block using json.

        :return: A json-encoded block
        :rtype: string

        *Usage:*
        
        .. code-block:: python
        
            pb_json = payload_block.to_json()
        """
        # The payload is NOT doubly cbor encoded
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
            crc = calc_crc(self.crc_type, cfields)
        else:
            crc = self.crc
            
        tmp = \
            [
                self.__class__.__name__,
                self.blk_type,
                self.blk_num,
                self.control_flags,
                self.crc_type,
                type_spec_data,
                crc,
            ]
        cfields = [i for i in tmp if i is not None]
        keys = ["_block_class", "blk_type", "blk_num", "control_flags", "crc_type", "payload", "crc"]
        
        return json.dumps(dict(zip(keys, cfields)), default=custom_encoder, indent=4)

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Payload Block.

        :params list cand_block: A list of objects to be interpreted as a \
            Payload Block.
            
        :return: A Payload Block
        :rtype: PayloadBlock

        *Usage:*
        
        Unlike other canonical blocks, the type-specific data (5th element) of the PayloadBlock is NOT doubly cbor encoded. The byte string is the payload.

        .. code-block:: python
        
            from dtngen.blocks import PayloadBlock
            
            pblock_elements = [1, 1, 0, 1, b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x0chello world\\n', b'\\x7a\\x2f']
            ctblock = PayloadBlock.decode(pblock_elements)
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
        """Initialize the payload block with the requested fields.

        :param BlockType blk_type: (optional) the type of Canonical block. Can be a specific BlockType or BlockType.AUTO to set to the matching BlockType.
        :param int blk_num: (optional) block number
        :param BlockPCFlags control_flags: (optional) block processing control flags
        :param CRCType crc_type: (optional) CRC type
        :param dict payload: (optional) {"size": <payload size>} "size" key with payload size in bytes to generate
        :param bytes crc: (optional) crc value or CRCFlag.CALCULATE to calculate it

        *Usage:*
        
        .. code-block:: python
        
            from dtngen.blocks import PayloadBlockSettings

            # PayloadBlockSettings is like PayloadBlock except the payload has
            # the size (in bytes) of random payload to generate instead of a
            # specific payload
            payloadblk_settings = PayloadBlockSettings(
                blk_type=BlockType.AUTO,
                blk_num=1,
                control_flags=0,
                crc_type=CRCType.CRC16_X25,
                payload={"size": 1024},
                crc=CRCFlag.CALCULATE,
            )
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
        """Generate a payload block with the settings in this PayloadBundleSettings. bundle_num is ignored.
        
        :param int bundle_num: the number of the bundle being generated (0 to ...). In this case this value is ignored.

        :return: The generated Payload block
        :rtype: PayloadBlock

        *Usage:*

        .. code-block:: python
        
            generated_payload_block = payload_block_settings.generate(0)
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

        :param int version: (optional) version of the Bundle Protocol that constructed this block
        :param BundlePCFlags control_flags: (optional) bundle processing control flags
        :param CRCType crc_type: (optional) CRC type
        :param EID dest_eid: (optional) bundle endpoint that is the bundle's destination
        :param EID src_eid: (optional) bundle node at which the bundle was \
initially transmitted, or null endpoint if anomymous
        :param EID rpt_eid: (optional) bundle endpoint to which status reports \
pertaining to the forwarding and delivery of this bundle are to be transmitted
        :param CreationTimestamp creation_timestamp: (optional) creation timestamp
        :param int lifetime: (optional) number of milliseconds past the \
creation time at which the bundle's payload will no longer be useful
        :param bytes crc: (optional) crc value or CRCFlag.CALCULATE to calculate it

        *Usage:*

        .. code-block:: python
        
            from dtngen.blocks import PrimaryBlock
            from dtngen.types import BundlePCFlags, CRCType, CRCFlag, EID, CreationTimestamp
            
            primary_block = PrimaryBlock(
                version=7,
                control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
                crc_type=CRCType.CRC16_X25,
                dest_eid=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
                src_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
                rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
                creation_timestamp=CreationTimestamp({"time": 755533838904, "sequence": 0}),
                lifetime=3600000,
                crc=CRCFlag.CALCULATE,
            )
        """
        if not isinstance(version, int):
            warnmsg = f'PrimaryBlock version is type {type(version).__name__} instead of int'
            warnings.warn(warnmsg, TypeWarning)
        self.version = version

        if not isinstance(control_flags, BundlePCFlags) and not isinstance(control_flags, int):
            warnmsg = f'PrimaryBlock control_flags is type {type(control_flags).__name__} instead of BundlePCFlags or int'
            warnings.warn(warnmsg, TypeWarning)
        self.control_flags = control_flags

        if not isinstance(crc_type, CRCType) and not isinstance(crc_type, int):
            warnmsg = f'PrimaryBlock crc_type is type {type(crc_type).__name__} instead of CRCType or int'
            warnings.warn(warnmsg, TypeWarning)
        self.crc_type = crc_type

        if not isinstance(dest_eid, EID):
            warnmsg = f'PrimaryBlock dest_eid is type {type(dest_eid).__name__} instead of EID'
            warnings.warn(warnmsg, TypeWarning)
        self.dest_eid = dest_eid

        if not isinstance(src_eid, EID):
            warnmsg = f'PrimaryBlock src_eid is type {type(src_eid).__name__} instead of EID'
            warnings.warn(warnmsg, TypeWarning)
        self.src_eid = src_eid

        if not isinstance(rpt_eid, EID):
            warnmsg = f'PrimaryBlock rpt_eid is type {type(rpt_eid).__name__} instead of EID'
            warnings.warn(warnmsg, TypeWarning)
        self.rpt_eid = rpt_eid

        if not isinstance(creation_timestamp, CreationTimestamp):
            warnmsg = f'PrimaryBlock creation_timestamp is type {type(creation_timestamp).__name__} instead of CreationTimestamp'
            warnings.warn(warnmsg, TypeWarning)
        self.creation_timestamp = creation_timestamp

        if not isinstance(lifetime, int):
            warnmsg = f'PrimaryBlock lifetime is type {type(lifetime).__name__} instead of int'
            warnings.warn(warnmsg, TypeWarning)
        self.lifetime = lifetime
        
        if not isinstance(crc, CRCFlag) and not isinstance(crc, bytes) and crc is not None:
            warnmsg = f'PrimaryBlock crc is type {type(crc).__name__} instead of CRCFlag, bytes or None'
            warnings.warn(warnmsg, TypeWarning)
        self.crc = crc

    def encode(self):
        """Encode the Primary block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytearray

        *Usage:*
        
        .. code-block:: python
        
            cbor_encoded_prb = primary_block.encode()
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
            crc = calc_crc(self.crc_type, fields)
        else:
            crc = self.crc
        
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
                crc,
            ]
        fields = [i for i in tmp if i is not None]

        return cbor2.dumps(fields, default=default_encoder)
        

    def to_json(self):
        """Encode the Primary block using json.

        :return: A json-encoded block
        :rtype: string

        *Usage:*
        
        .. code-block:: python
        
            prb_json = primary_block.to_json()
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
            crc = calc_crc(self.crc_type, fields)
        else:
            crc = self.crc
        
        tmp = \
            [
                self.__class__.__name__,
                self.version,
                self.control_flags,
                self.crc_type,
                self.dest_eid,
                self.src_eid,
                self.rpt_eid,
                self.creation_timestamp,
                self.lifetime,
                crc,
            ]
        fields = [i for i in tmp if i is not None]
        keys = ["_block_class", "version", "control_flags", "crc_type", "dest_eid", "src_eid", "rpt_eid", "creation_timestamp", "lifetime", "crc"]
        
        return json.dumps(dict(zip(keys, fields)), default=custom_encoder, indent=4)
        

    @classmethod
    def decode(cls, cand_block):
        """Attempt to decode the candidate block as a BPv7 Primary Block.

        :params list cand_block: A list of objects to be interpreted as a Primary Block.
            
        :return: A Primary Block
        :rtype: PrimaryBlock

        *Usage:*

        .. code-block:: python
        
            from dtngen.blocks import PrimaryBlock
            
            prblock_elements = [7, 4, 1, [2, [200, 1]], [2, [100, 1]], [2, [100, 1]], [755533838904, 0], 3600000, b'\\x0b\\x19']
            prblock = PrimaryBlock.decode(prblock_elements)
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

        :param int version: (optional) version of the Bundle Protocol that constructed this block
        :param BundlePCFlags control_flags: (optional) bundle processing control flags
        :param CRCType crc_type: (optional) CRC type
        :param EID dest_eid: (optional) bundle endpoint that is the bundle's destination
        :param EID src_eid: (optional) bundle node at which the bundle was \
initially transmitted, or null endpoint if anomymous
        :param EID rpt_eid: (optional) bundle endpoint to which status reports \
pertaining to the forwarding and delivery of this bundle are to be transmitted
        :param dict creation_timestamp: (optional) creation timestamp generation settings\n
            {\n
                "time": "current" or {"start": <start_time>, "increment": <ms between bundles>},\n
                "sequence": {"start": <start value>} or {"fixed": <fixed value>}\n
            }
        :param int lifetime: (optional) number of milliseconds past the \
creation time at which the bundle's payload will no longer be useful
        :param bytes crc: (optional) crc value or CRCFlag.CALCULATE to calculate it

        *Usage:*
        
        PrimaryBlockSettings with creation_timestamp \"time\" set to a specific
        value and an increment value and \"sequence\" set to an incrementing
        value:
        
        .. code-block:: python
        
            from dtngen.blocks import PrimaryBlockSettings

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

        PrimaryBlockSettings with creation_timestamp \"time\" set to current DTN
        time and \"sequence\" set to a fixed value:
        
        .. code-block:: python
        
            from dtngen.blocks import PrimaryBlockSettings

            primaryblk_settings = PrimaryBlockSettings(
                ...
                creation_timestamp={
                    "time": "current", 
                    "sequence": {"fixed": 5} 
                },
                ...
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
        """Generate a Primary Block with the settings in this PayloadBundleSettings and the given bundle number.
        
        :param int bundle_num: the number of the bundle being generated (0 to ...)

        :return: The generated Primary block
        :rtype: PrimaryBlock

        *Usage:*

        .. code-block:: python
        
            generated_primary_block = primary_block_settings.generate(3)
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
    """Unknown Block. Used to handle blocks of an unknown type."""

    def __init__(
        self,
        elements=None,
    ):
        """Initialize the unknown block with the requested fields.

        :param list elements: list of all of the elements of the block
        
        *Usage:*
        
        .. code-block:: python
        
            from dtngen.blocks import UnknownBlock
            
            unknown_block = UnknownBlock(
                elements=
                [
                    73,
                    73,
                    0,
                    1,
                    b'\\x82\\x02\\x82\\x18\\x64\\x0a',
                    b'\\x67\\x47'
                ]
            )
        """
        self.elements = elements

    def encode(self):
        """Encode the Unknown block using CBOR.

        :return: A CBOR-encoded block
        :rtype: bytes

        *Usage:*
        
        .. code-block:: python
        
            cbor_encoded_unknown = unknown_block.encode()
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

        *Usage:*
        
        .. code-block:: python
        
            unknown_json = unknown_block.to_json()
        """
        if isinstance(self.elements, list):
            fields = [self.__class__.__name__] + [i for i in self.elements if i is not None]
        else:
            fields = [self.__class__.__name__, self.elements]

        keys = ["_block_class"] + [f'Element {i}' for i in range(1, len(fields)+1)]
        
        return json.dumps(dict(zip(keys, fields)), default=custom_encoder, indent=4)
        

    @classmethod
    def decode(cls, cand_block):
        """Decode the candidate block as an Unknown Block.

        :params list cand_block: A list of objects to be interpreted as a Unknown Block.

        *Usage:*

        .. code-block:: python
        
            from dtngen.blocks import UnknownBlock
            
            ublock_elements = [73, 73, 0, 1, b'\\x82\\x02\\x82\\x18\\x64\\x0a', b'\\x67\\x47'] 
            ublock = UnknownBlock.decode(ublock_elements)
        """
        return UnknownBlock(elements=cand_block)            
