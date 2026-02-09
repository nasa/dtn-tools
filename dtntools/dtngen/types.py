#
# NASA Docket No. GSC-19,559-1, and identified as "Delay/Disruption Tolerant Networking 
# (DTN) Bundle Protocol (BP) v7 Core Flight System (cFS) Application Build 7.0
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this 
# file except in compliance with the License. You may obtain a copy of the License at 
#
# http://www.apache.org/licenses/LICENSE-2.0 
#
# Unless required by applicable law or agreed to in writing, software distributed under 
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF 
# ANY KIND, either express or implied. See the License for the specific language 
# governing permissions and limitations under the License. The copyright notice to be 
# included in the software is as follows: 
#
# Copyright 2025 United States Government as represented by the Administrator of the 
# National Aeronautics and Space Administration. All Rights Reserved.
#
#
import warnings
from enum import IntEnum, IntFlag
from itertools import zip_longest

import cbor2
from crccheck.crc import Crc16IbmSdlc, Crc32Iscsi

class TypeWarning(Warning):
    """Warning for an incorrect data type detected."""

    pass


class AdminRecordType(IntFlag):
    """Administrative Record Types."""

    BUNDLE_STATUS_REPORT = 1
    COMPRESSED_CUSTODY_SIGNAL = 13

class DispositionCode(IntFlag):
    """Disposition Codes for Custody Transfer"""

    CUSTODY_ACCEPTED =  1
    CUSTODY_REFUSED  = -1

class BlockPCFlags(IntFlag):
    """Block Processing Control Flags."""

    FRAG_REPLICATE = 1
    REP_UNPROC = 2
    DEL_UNPROC = 4
    DEL_BLOCK_UNPROC = 16


class BlockType(IntFlag):
    """BPv7 Block Type Flag Definitions.

    .. note::
        Only BPv7 types are defined and supported.
    """

    AUTO = -1
    BUNDLE_PAYLOAD = 1
    PREVIOUS_NODE = 6
    BUNDLE_AGE = 7
    HOP_COUNT = 10
    CUST_TRANS_EXT = 13
    COMP_RPT_EXT = 16


class BundlePCFlags(IntFlag):
    """Bundle Processing Control Flags."""

    IS_FRAGMENT = 1
    IS_ADMIN_RECORD = 2
    MUST_NOT_FRAGMENT = 4
    RQST_ACK = 32
    RPRT_STAT_TIME = 64
    RPRT_RECEP = 16384
    RPRT_FORWARDING = 65536
    RPRT_DELIVERY = 131072
    RPRT_DELETION = 262144


class StatusRRFlags(IntFlag):
    """Status Report Request Flags."""

    RECEPTION = 1
    FORWARDING = 2
    DELIVERY = 4
    DELETION = 32
    FRAGMENTATION = 64
    REASSEMBLY = 16384


class CRCType(IntFlag):
    """BPv7 Supported CRC Types."""

    NONE = 0
    CRC16_X25 = 1
    CRC32_C = 2


class CRCFlag(IntEnum):
    """Flag to indicate if CRC should be calculated."""

    CALCULATE = -1


class TimestampFlag(IntEnum):
    """Flag to indiciate if a CreationTimestamp for the primary block should be generated using current time."""

    CURR_TIME = 1


def calc_crc(crc_type, fields):
    r"""Calculate CRC given crc type and fields. The fields will be cbor encoded.

    :param CRCType crc_type: The CRC algorithm to use. Valid values are CRCType.CRC16_X25 and CRCType.CRC32_C
    :param list fields: The list of block fields to calculate the CRC on

    :return: CRC as a byte string
    :rtype: bytes

    *Usage:*

    .. code-block:: python

        from dtngen.types import CRCType, calc_crc

        crc = calc_crc(crc_type = CRCType.CRC16_X25, fields = [1, 2, b'\\x03\\x04'])
    """
    if crc_type == CRCType.CRC16_X25:
        fields.append(b"\x00\x00")
        crc = Crc16IbmSdlc.calc(cbor2.dumps(fields, default=default_encoder))
        return crc.to_bytes(2, "big")
    elif crc_type == CRCType.CRC32_C:
        fields.append(b"\x00\x00\x00\x00")
        crc = Crc32Iscsi.calc(cbor2.dumps(fields, default=default_encoder))
        return crc.to_bytes(4, "big")
    else:
        return None


class InvalidCBOR:
    """Invalid CBOR Encoding."""

    def __init__(self, value, additional_info):
        r"""Initialize the InvalidCBOR.

        :param any value: The CBOR-encodable value
        :param int additional_info: The invalid additional info value to set. Must be 28-30 or 31. 31 is only invalid for major types 0, 1 and 6.

        *Usage:*

        .. code-block:: python

            from dtngen.types import InvalidCBOR

            invalid_cbor_eid = \\
                InvalidCBOR(
                    value=EID({"uri": 2, "ssp": {"node_num": 200, "service_num": 1}}),
                    additional_info=28
                )

            invalid_cbor_uint = InvalidCBOR(value=360000, additional_info=31)

        """
        if additional_info not in [28, 29, 30, 31]:
            err_msg = f"Attempting to create invalid CBOR encoding, but the specified additional info value {additional_info} is NOT invalid. Only values 28-31 are invalid."
            raise ValueError(err_msg)

        self.value = value
        self.additional_info = additional_info

        cbor_val = cbor2.dumps(self.value, default=default_encoder)
        major_type = (cbor_val[0] & 0b11100000) >> 5

        if additional_info == 31 and major_type not in [0, 1, 6]:
            err_msg = f"Attempting to create invalid CBOR encoding for a value of major type {major_type}, but the specified additional info value 31 is only invalid for major types 0, 1 and 6."
            raise ValueError(err_msg)

    def enc_data(self):
        """Return the data to encode.

        :return: dictionary containing the value to encode and the invalid additional info
        :rtype: dict

        *Usage:*

        .. code-block:: python

            data = myinvalidcbor.enc_data()
        """
        return {"value": self.value, "additional_info": self.additional_info}


class RawData:
    """Raw data that does not get cbor encoded."""

    def __init__(self, value):
        r"""Initialize the RawData.

        :param bytes value: The bytes data to put in the stream

        *Usage:*

        .. code-block:: python

            from dtngen.types import RawData

            # cbor int (major type 0) that, with additional info 26 (0x1a),
            # should be in 4 bytes, but only has 3
            wrong_length_cbor_int = RawData(b'\\x1a\\x01\\x02\\x03')

        """
        if not isinstance(value, bytes):
            err_msg = f"RawData value '{value}' is type {type(value)} instead of bytes."
            raise ValueError(err_msg)

        self.value = value

    def enc_data(self):
        """Return the data to encode.

        :return: the value to write to the stream
        :rtype: bytes

        *Usage:*

        .. code-block:: python

            data = rawdata.enc_data()
        """
        return self.value


class EID:
    """Endpoint Identifier."""

    def __init__(self, eid_fields):
        """Initialize the EID.

        :param dict eid_fields: EID fields

        *Usage:*

        URI type 1 (dtn URI scheme):

        .. code-block:: python

            from dtngen.types import EID

            myeid = EID(
                {
                    uri: 1,
                    ssp: "dtn:none"
                }
            )

        URI type 2 (ipn URI scheme):

        .. code-block:: python

            myeid = EID(
                {
                    uri: 2,
                    ssp: {"node_num": 200, "service_num": 1}
                }
            )
        """
        self.uri = None
        self.ssp = None

        if "uri" in eid_fields:
            self.uri = eid_fields["uri"]
            if (not isinstance(self.uri, int)) or self.uri < 1 or self.uri > 2:
                warnmsg = f"Unsupported EID URI type {self.uri}"
                warnings.warn(warnmsg)
        if "ssp" in eid_fields:
            self.ssp = eid_fields["ssp"]
            if (
                isinstance(self.uri, int)
                and self.uri == 1
                and not isinstance(self.ssp, str)
            ):
                warnmsg = f"DTN EID ssp is {self.ssp} instead of a string"
                warnings.warn(warnmsg, TypeWarning)
            if (
                isinstance(self.uri, int)
                and self.uri == 2
                and (
                    not isinstance(self.ssp, dict)
                    or len(self.ssp) != 2
                    or "node_num" not in self.ssp
                    or "service_num" not in self.ssp
                    or not isinstance(self.ssp["node_num"], int)
                    or not isinstance(self.ssp["service_num"], int)
                )
            ):
                warnmsg = f"IPN EID ssp is {self.ssp} instead of a dict with 'node_num' and 'service_num' elements that are ints"
                warnings.warn(warnmsg, TypeWarning)

    def enc_data(self):
        """Return the data to encode.

        :return: list of data to encode
        :rtype: list

        *Usage:*

        .. code-block:: python

            data = myeid.enc_data()
        """
        if (not isinstance(self.uri, int)) or self.uri <= 1 or self.uri > 2:
            # If it is DTN type or is an invalid type, pass through the data
            # as is
            return [i for i in [self.uri, self.ssp] if i is not None]

        # It is ipn type
        node_num = None
        service_num = None

        if "node_num" in self.ssp:
            node_num = self.ssp["node_num"]
        if "service_num" in self.ssp:
            service_num = self.ssp["service_num"]

        ssp_data = [i for i in [node_num, service_num] if i is not None]
        return [j for j in [self.uri, ssp_data] if j is not None]

    @classmethod
    def decode(cls, cand_eid):
        """Attempt to parse an EID.

        :param list cand_eid: A list of fields representing a candidate EID.
        :return: The decoded EID
        :rtype: EID

        *Usage:*

        .. code-block:: python

            from dtngen.types import EID

            eid_elements = [2, [200, 1]]
            myeid = EID.decode(eid_elements)
        """
        if (
            isinstance(cand_eid, list)
            and len(cand_eid) >= 1
            and (cand_eid[0] < 1 or cand_eid[0] > 2)
        ):
            # Because lookslike() should be called first, we should never get
            # here. If we do it's a programatic error.
            raise ValueError(f"Unsupported EID URI Type {cand_eid[0]}")

        uri_data = None
        ssp_data = None

        if len(cand_eid) >= 1:
            uri_data = cand_eid[0]
            if len(cand_eid) == 2:
                if cand_eid[0] == 1:
                    ssp_data = cand_eid[1]
                else:
                    ssp_dict = {"node_num": None, "service_num": None}
                    ssp_data = dict(zip_longest(ssp_dict, cand_eid[1]))

        eid_d = {
            "uri": uri_data,
            "ssp": ssp_data,
        }
        return EID(eid_d)

    @classmethod
    def lookslike(cls, cand_eid):
        """Check if candidate EID looks like an EID.

        :param list cand_eid: A list of fields representing a candidate EID.
        :return: True if the fields look like an EID, otherwise False
        :rtype: bool

        *Usage:*

        .. code-block:: python

            from dtngen.types import EID

            if EID.lookslike(list_of_candidate_fields):
                print ("It looks like an EID")
        """
        if (
            isinstance(cand_eid, list)
            and len(cand_eid) == 2
            and isinstance(cand_eid[0], int)
        ):
            is_dtn = cand_eid[0] == 1 and isinstance(cand_eid[1], str)
            is_ipn = (
                cand_eid[0] == 2
                and isinstance(cand_eid[1], list)
                and len(cand_eid[1]) == 2
                and isinstance(cand_eid[1][0], int)
                and isinstance(cand_eid[1][1], int)
            )

            return is_dtn or is_ipn

        return False


class CreationTimestamp:
    """Creation Timestamp."""

    def __init__(self, timestamp_fields):
        """Initialize the Creation Timestamp.

        :param dict timestamp_fields: Timestamp Fields

        *Usage:*

        .. code-block:: python

            from dtngen.types import CreationTimestamp

            mytimestamp = CreationTimestamp({"time": 755533838904, "sequence": 0})
        """
        self.time = None
        self.sequence = None

        if "time" in timestamp_fields:
            self.time = timestamp_fields["time"]
        if "sequence" in timestamp_fields:
            self.sequence = timestamp_fields["sequence"]

    def enc_data(self):
        """Return the data to encode.

        :return: list of data to encode
        :rtype: list

        *Usage:*

        .. code-block:: python

            data = mytimestamp.enc_data()
        """
        data = [self.time, self.sequence]
        return [i for i in data if i is not None]

    @classmethod
    def decode(cls, cand_timestamp):
        """Attempt to parse a Creation Timestamp.

        :param list cand_timestamp: A list of fields representing a Creation Timestamp
        :return: The decoded creation timestamp
        :rtype: CreationTimestamp

        *Usage:*

        .. code-block:: python

            from dtngen.types import CreationTimestamp


            cts_elements = [755533838904, 0]
            mytimestamp = CreationTimestamp.decode(cts_elements)
        """
        if len(cand_timestamp) != 2:
            # Because lookslike() should be called first, we should never get
            # here. If we do it's a programatic error.
            raise ValueError(
                f"Creation Timestamp has {len(cand_timestamp)} elements but should have 2."
            )

        type_spec_dict = {"time": None, "sequence": None}
        timestamp_d = dict(zip_longest(type_spec_dict, cand_timestamp))

        return CreationTimestamp(timestamp_d)

    @classmethod
    def lookslike(cls, cand_eid):
        """Check if candidate creation timestamp looks like an creation timestamp.

        :param list cand_eid: A list of fields representing a candidate creation timestamp.
        :return: True if the fields look like a CreationTimestamp, otherwise False
        :rtype: bool

        *Usage:*

        .. code-block:: python

            from dtngen.types import CreationTimestamp

            if CreationTimestamp.lookslike(list_of_candidate_fields):
                print ("It looks like a CreationTimestamp")
        """
        return (
            isinstance(cand_eid, list)
            and len(cand_eid) == 2
            and isinstance(cand_eid[0], int)
            and isinstance(cand_eid[1], int)
        )


class HopCountData:
    """Hop Count Data."""

    def __init__(self, hopcount_fields):
        """Initialize the Hop Count Data.

        :param dict hopcount_fields: Hop Count Fields

        *Usage:*

        .. code-block:: python

            from dtngen.types import HopCountData

            myhopdata = HopCountData({"hop_limit": 15, "hop_count": 3})
        """
        self.hop_limit = None
        self.hop_count = None

        if "hop_limit" in hopcount_fields:
            self.hop_limit = hopcount_fields["hop_limit"]
        if "hop_count" in hopcount_fields:
            self.hop_count = hopcount_fields["hop_count"]

    def enc_data(self):
        """Return the data to encode.

        :return: list of data to encode
        :rtype: list

        *Usage:*

        .. code-block:: python

            data = myhopdata.enc_data()
        """
        data = [self.hop_limit, self.hop_count]
        return [i for i in data if i is not None]

    @classmethod
    def decode(cls, cand_hopcount_data):
        """Attempt to parse Hop Count data.

        :param list cand_hopcount_data: A list of fields representing Hop Count Data
        :return: The decoded hop count data
        :rtype: HopCountData

        *Usage:*

        .. code-block:: python

            from dtngen.types import HopCountData

            hc_elements = [15, 3]
            myhopdata = HopCountData.decode(hc_elements)
        """
        if len(cand_hopcount_data) != 2:
            # Because lookslike() should be called first, we should never get
            # here. If we do it's a programatic error.
            raise ValueError(
                f"Hop Count Data has {len(cand_hopcount_data)} elements but should have 2."
            )

        type_spec_dict = {"hop_limit": None, "hop_count": None}
        hopcount_data = dict(zip_longest(type_spec_dict, cand_hopcount_data))

        return HopCountData(hopcount_data)

    @classmethod
    def lookslike(cls, cand_hopcount_data):
        """Check if candidate hop count data looks like Hop Count data.

        :param list cand_eid: A list of fields representing candidate hop count data.
        :return: True if the fields look like HopCountData, otherwise False
        :rtype: bool

        *Usage:*

        .. code-block:: python

            from dtngen.types import HopCountData

            if HopCountData.lookslike(list_of_candidate_fields):
                print ("It looks like HopCountData")
        """
        if not isinstance(cand_hopcount_data, list):
            return False
        if not len(cand_hopcount_data) == 2:
            return False

        return isinstance(cand_hopcount_data[0], int) and isinstance(
            cand_hopcount_data[1], int
        )


class CTEBData:
    """Custody Transfer Extension Block Data."""

    def __init__(self, cteb_fields):
        """Initialize the CTEB Data.

        :param dict cteb_fields: CTEB Data Fields

        *Usage:*

        .. code-block:: python

            from dtngen.types import CTEBData, EID

            myctebdata = CTEBData(
                {
                    "bundle_seq_num": 10,
                    "bundle_seq_id": 2,
                    "block_src_admin_eid": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}})}
                )
        """
        self.bundle_seq_num = None
        self.bundle_seq_id = None
        self.block_src_admin_eid = None

        if "bundle_seq_num" in cteb_fields:
            self.bundle_seq_num = cteb_fields["bundle_seq_num"]
        if "bundle_seq_id" in cteb_fields:
            self.bundle_seq_id = cteb_fields["bundle_seq_id"]
        if "block_src_admin_eid" in cteb_fields:
            self.block_src_admin_eid = cteb_fields["block_src_admin_eid"]

    def enc_data(self):
        """Return the data to encode.

        :return: list of data to encode
        :rtype: list

        *Usage:*

        .. code-block:: python

            data = myctebdata.enc_data()
        """
        data = [self.bundle_seq_num, self.bundle_seq_id, self.block_src_admin_eid]
        return [i for i in data if i is not None]

    @classmethod
    def decode(cls, cand_cteb_data):
        """Attempt to parse CTEB data.

        :param list cand_cteb_data: A list of fields representing CTEB Data
        :return: The decoded CTEB data
        :rtype: CTEBData

        *Usage:*

        .. code-block:: python

            from dtngen.types import CTEBData

            ctebd_elements = [10, 2, [2, [303, 1]]]
            myctebdata = CTEBData.decode(ctebd_elements)
        """
        if len(cand_cteb_data) != 3:
            # Because lookslike() should be called first, we should never get
            # here. If we do it's a programatic error.
            raise ValueError(
                f"CTEB Data has {len(cand_cteb_data)} elements but should have 3."
            )

        type_spec_dict = {
            "bundle_seq_num": None,
            "bundle_seq_id": None,
            "block_src_admin_eid": None,
        }
        cteb_data = dict(zip_longest(type_spec_dict, cand_cteb_data))

        if "block_src_admin_eid" in cteb_data and cteb_data["block_src_admin_eid"] is not None:
            cteb_data["block_src_admin_eid"] = EID.decode(cteb_data["block_src_admin_eid"])

        return CTEBData(cteb_data)

    @classmethod
    def lookslike(cls, cand_cteb_data):
        """Check if candidate hop count data looks like Hop Count data.

        :param list cand_eid: A list of fields representing candidate CTEB data.
        :return: True if the fields look like CTEBData, otherwise False
        :rtype: bool

        *Usage:*

        .. code-block:: python

            from dtngen.types import CTEBData

            if CTEBData.lookslike(list_of_candidate_fields):
                print ("It looks like CTEBData")
        """
        if not isinstance(cand_cteb_data, list):
            return False
        if not len(cand_cteb_data) == 3:
            return False

        return (
            isinstance(cand_cteb_data[0], int)
            and isinstance(cand_cteb_data[1], int)
            and EID.lookslike(cand_cteb_data[2])
        )


class CREBData:
    """Compressed Reporting Extension Block Data."""

    def __init__(self, creb_fields):
        """Initialize the CREB Data.

        :param dict creb_fields: CREB Data Fields

        *Usage:*

        CREBData contains 1 to 5 elements. In a valid case, if an element is provided, all prior elements must also be provided.

        All elements provided:

        .. code-block:: python

            from dtngen.types import CTEBData, EID

            myrtebdata = CREBData
            (
                {
                    "bundle_seq_num": 1,
                    "bundle_seq_id": 4,
                    "rpt_request_flags": 0,
                    "scope_node_id": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 1}}),
                    "rpt_eid": EID({"uri": 2, "ssp": {"node_num": 305, "service_num": 2}})
                }
            )

        Only the first two elements provided:

        .. code-block:: python

            myrtebdata = CREBData
            (
                {
                    "bundle_seq_num": 2,
                    "bundle_seq_id": 6
                }
            )
        """
        self.bundle_seq_num = None
        self.bundle_seq_id = None
        self.rpt_request_flags = None
        self.scope_node_id = None
        self.rpt_eid = None

        if "bundle_seq_num" in creb_fields:
            self.bundle_seq_num = creb_fields["bundle_seq_num"]
        if "bundle_seq_id" in creb_fields:
            self.bundle_seq_id = creb_fields["bundle_seq_id"]
        if "rpt_request_flags" in creb_fields:
            self.rpt_request_flags = creb_fields["rpt_request_flags"]
        if "scope_node_id" in creb_fields:
            self.scope_node_id = creb_fields["scope_node_id"]
        if "rpt_eid" in creb_fields:
            self.rpt_eid = creb_fields["rpt_eid"]

        if (
            (self.bundle_seq_id is not None and self.bundle_seq_num is None)
            or (
                self.rpt_request_flags is not None
                and any(
                    arg is None for arg in (self.bundle_seq_num, self.bundle_seq_id)
                )
            )
            or (
                self.scope_node_id is not None
                and any(
                    arg is None
                    for arg in (
                        self.bundle_seq_num,
                        self.bundle_seq_id,
                        self.rpt_request_flags,
                    )
                )
            )
            or (
                self.rpt_eid is not None
                and any(
                    arg is None
                    for arg in (
                        self.bundle_seq_num,
                        self.bundle_seq_id,
                        self.rpt_request_flags,
                        self.scope_node_id,
                    )
                )
            )
        ):
            warnmsg = "Compressed Reporting Extension Block: One or more of bundle_seq_id, rpt_request_flags, scope_node_id or rpt_eid was provided without one or more of the prior arguments provided"
            warnings.warn(warnmsg)

    def enc_data(self):
        """Return the data to encode.

        :return: list of data to encode
        :rtype: list

        *Usage:*

        .. code-block:: python

            data = mycrebdata.enc_data()
        """
        data = [
            self.bundle_seq_num,
            self.bundle_seq_id,
            self.rpt_request_flags,
            self.scope_node_id,
            self.rpt_eid,
        ]
        return [i for i in data if i is not None]

    @classmethod
    def decode(cls, cand_creb_data):
        """Attempt to parse CTEB data.

        :param list cand_hopcount_data: A list of fields representing CTEB Data
        :return: The decoded CREB data
        :rtype: CREBData

        *Usage:*

        .. code-block:: python

            from dtngen.types import CREBData

            crebd_elements = [1, 4, 0, [2, [303, 1]], [2, [305, 2]]]
            mycrebdata = CREBData.decode(crebd_elements)
        """
        if len(cand_creb_data) < 1 or len(cand_creb_data) > 5:
            # Because lookslike() should be called first, we should never get
            # here. If we do it's a programatic error.
            raise ValueError(
                f"CREB Data has {len(cand_creb_data)} elements but should have 1 to 5."
            )

        type_spec_dict = {
            "bundle_seq_num": None,
            "bundle_seq_id": None,
            "rpt_request_flags": None,
            "scope_node_id": None,
            "rpt_eid": None,
        }
        creb_data = dict(zip_longest(type_spec_dict, cand_creb_data))

        if "scope_node_id" in creb_data and creb_data["scope_node_id"] is not None:
            creb_data["scope_node_id"] = EID.decode(creb_data["scope_node_id"])
        if "rpt_eid" in creb_data and creb_data["rpt_eid"] is not None:
            creb_data["rpt_eid"] = EID.decode(creb_data["rpt_eid"])

        return CREBData(creb_data)

    @classmethod
    def lookslike(cls, cand_creb_data):
        """Check if candidate hop count data looks like Hop Count data.

        :param list cand_creb_data: A list of fields representing candidate CREB data.
        :return: True if the fields look like CREBData, otherwise False
        :rtype: bool

        *Usage:*

        .. code-block:: python

            from dtngen.types import CREBData

            if CREBData.lookslike(list_of_candidate_fields):
                print ("It looks like CREBData")
        """
        if not isinstance(cand_creb_data, list):
            return False

        clen = len(cand_creb_data)
        if not (clen >= 1 and clen <= 5):
            return False
        if not isinstance(cand_creb_data[0], int):
            return False
        if clen >= 2 and not isinstance(cand_creb_data[1], int):
            return False
        if clen >= 3 and not isinstance(cand_creb_data[2], int):
            return False
        if clen >= 4 and not EID.lookslike(cand_creb_data[3]):
            return False
        if clen == 5 and not EID.lookslike(cand_creb_data[4]):
            return False
        return True

class BundleSequenceCollection:
    """Bundle Sequence Collection"""

    def __init__(self, bundle_seq_id=None, dest_eid=None, first_seq_num=None, 
                                        bundle_seq_range=None, block_src_admin_eid=None):
        """Initialize the bundle sequence collection

        :param dict bundle_seq_collection: Bundle Sequence Collection

        *Usage:*

        A bundle sequence range has either 3 or 4 items. The first field can be either
        a bundle_seq_id (integer) or a dest_eid (EID). The second field is the first_seq_num,
        an integer. The third field is the bundle_seq_range, which is either an integer
        representing a single range, or an array of odd-numbered length, alternately
        representing the ranges included or excluded. The fourth field, the block_src_admin_eid,
        is optional and must always be excluded from CCSs.

        One set of elements provided, for a typical CCS:

        .. code-block:: python

            from dtngen.types import BundleSequenceCollection

            myseqcollection = BundleSequenceCollection(
                {
                    "bundle_seq_id": 1,
                    "first_seq_num": 12,
                    "bundle_seq_range": [2, 4, 5]
                )

        Another set of elements provided:

        .. code-block:: python

            from dtngen.types import BundleSequenceCollection

            myseqcollection = BundleSequenceCollection(
                {
                    "dest_eid": EID({"uri": 2, "ssp": {"node_num": 306, "service_num": 1}})}
                    "first_seq_num": 12,
                    "bundle_seq_range": 1,
                    "block_src_admin_eid": EID({"uri": 2, "ssp": {"node_num": 303, "service_num": 0}})}
                )        
        """
        self.bundle_seq_id = bundle_seq_id
        self.dest_eid = dest_eid
        self.first_seq_num = first_seq_num
        self.bundle_seq_range = bundle_seq_range
        self.block_src_admin_eid = block_src_admin_eid

        if self.first_seq_num is None or self.bundle_seq_range is None:
            warnmsg = "Bundle Sequence Collection: Missing a field"
            warnings.warn(warnmsg)
        elif self.bundle_seq_id is not None and self.dest_eid is not None:
            warnmsg = "Bundle Sequence Collection: Cannot have both a bundle_seq_id and a dest_eid"
            warnings.warn(warnmsg)
        elif isinstance(self.bundle_seq_range, list) and len(self.bundle_seq_range) % 2 != 1:
            warnmsg = "Bundle Sequence Collection: bundle_seq_range must be an odd-numbered list"
            warnings.warn(warnmsg)            

    def enc_data(self):
        """Return the data to encode.

        :return: list of data to encode
        :rtype: list

        *Usage:*

        .. code-block:: python

            data = myctebdata.enc_data()
        """
        data = [self.bundle_seq_id, self.dest_eid, self.first_seq_num, self.bundle_seq_range, self.block_src_admin_eid]
        return [i for i in data if i is not None]

    @classmethod
    def decode(cls, cand_bundle_seq_collection):
        """Attempt to parse CTEB data.

        :param list cand_bundle_seq_collection: A list of fields representing a bundle sequence collection
        :return: The decoded data
        :rtype: BundleSequenceCollection

        *Usage:*

        .. code-block:: python

            from dtngen.types import BundleSequenceCollection

            ctebd_elements = [10, 2, [2, [303, 1]]]
            myctebdata = CTEBData.decode(ctebd_elements)
        """
        if len(cand_bundle_seq_collection) != 3 and len(cand_bundle_seq_collection) != 4:
            # Because lookslike() should be called first, we should never get
            # here. If we do it's a programatic error.
            raise ValueError(
                f"Bundle Sequence Collection has {len(cand_bundle_seq_collection)} elements but should have 3 or 4."
            )
        
        bsc_data = {
            "bundle_seq_id": None,
            "dest_eid": None,
            "first_seq_num": None,
            "bundle_seq_range": None,
            "block_src_admin_eid": None,
        }

        if EID.lookslike(cand_bundle_seq_collection[0]):
            bsc_data["dest_eid"] = EID.decode(cand_bundle_seq_collection[0])
        else:
            bsc_data["bundle_seq_id"] = cand_bundle_seq_collection[0]
        
        bsc_data["first_seq_num"] = cand_bundle_seq_collection[1]

        if isinstance(cand_bundle_seq_collection[2], list):
            bsc_data["bundle_seq_range"] = cand_bundle_seq_collection[2]

        if len(cand_bundle_seq_collection) == 4 and EID.lookslike(cand_bundle_seq_collection[3]):
            bsc_data["block_src_admin_eid"] = EID.decode(cand_bundle_seq_collection[3])

        return BundleSequenceCollection(bsc_data["bundle_seq_id"], 
                                        bsc_data["dest_eid"],
                                        bsc_data["first_seq_num"],
                                        bsc_data["bundle_seq_range"],
                                        bsc_data["block_src_admin_eid"])

    @classmethod
    def lookslike(cls, cand_bundle_seq_collection):
        """Check if a candidate bundle sequence collection looks like a bundle sequence collection

        :param list cand_bundle_seq_collection: A list of fields representing a candidate BSC
        :return: True if the fields look like BundleSequenceCollection, otherwise False
        :rtype: bool

        *Usage:*

        .. code-block:: python

            from dtngen.types import BundleSequenceCollection

            if BundleSequenceCollection.lookslike(list_of_candidate_fields):
                print ("It looks like BundleSequenceCollection")
        """
        if not isinstance(cand_bundle_seq_collection, list):
            return False
        if not len(cand_bundle_seq_collection) == 3 or len(cand_bundle_seq_collection) == 4:
            return False

        return (
            (isinstance(cand_bundle_seq_collection[0], int) or EID.lookslike(cand_bundle_seq_collection[0]))
            and isinstance(cand_bundle_seq_collection[1], int)
            and (isinstance(cand_bundle_seq_collection[2], int) or 
                 (isinstance(cand_bundle_seq_collection[2], list) and len(cand_bundle_seq_collection[2]) % 2 == 1))
            and (len(cand_bundle_seq_collection) == 3 or EID.lookslike(cand_bundle_seq_collection[3]))
        )

class CCSData:
    """Compressed Custody Signal Data"""

    def __init__(self, ccs_data):
        """Initialize the CCS

        :param dict ccs_data: Compressed Custody Signal Data

        *Usage:*

        The contents of a CCS are a dictionary of nonzero disposition code keys
        mapping to bundle sequence collections.

        .. code-block:: python

            from dtngen.types import BundleSequenceCollection, CCSData

            myccsdata = CCSData(
                {
                    1: BundleSequenceCollection({"bundle_seq_id": 1, 
                                                 "first_seq_num": 12,
                                                 "bundle_seq_range": [2, 4, 5]}),
                    -1: BundleSequenceCollection({"bundle_seq_id": 1, 
                                                 "first_seq_num": 32,
                                                 "bundle_seq_range": [2, 4, 5]}),
                }
            )
        """

        if ccs_data is None or not isinstance(ccs_data, dict):
            warnmsg = "CCS data: field error"
            warnings.warn(warnmsg)

        for key in ccs_data:
            if not isinstance(key, int) or key == 0 or not isinstance(ccs_data[key], BundleSequenceCollection):
                warnmsg = "CCS data: field error"
                warnings.warn(warnmsg)                

        self.ccsdata = ccs_data          

    def enc_data(self):
        """Return the data to encode.

        :return: dictionary of data to encode
        :rtype: dict

        *Usage:*

        .. code-block:: python

            data = myccsdata.enc_data()
        """
        return self.ccsdata

    @classmethod
    def decode(cls, cand_ccs_data):
        """Attempt to parse CTEB data.

        :param list cand_ccs_data: A list of fields representing CCS data
        :return: The decoded data
        :rtype: CCSData

        *Usage:*

        .. code-block:: python

            from dtngen.types import CCSData, BundleSequenceCollection

            ccs_elements = {
                                1: [10, 2, [2, [303, 1]]],
                                -1: [10, 2, [2, [303, 1]]]
                            }
            ccs_elements = CCSData.decode(ccs_elements)
        """

        if not isinstance(cand_ccs_data, dict) or len(cand_ccs_data) == 0:
            # Because lookslike() should be called first, we should never get
            # here. If we do it's a programatic error.
            raise ValueError(
                f"CCS Data has is not a valid type."
            )
        
        ccs_data = {}

        for key in cand_ccs_data:
            ccs_data[key] = BundleSequenceCollection.decode(cand_ccs_data[key])

        return CCSData(ccs_data)

    @classmethod
    def lookslike(cls, cand_ccs_data):
        """Check if a candidate CCS datalooks like CCS data

        :param list cand_ccs_data: A list of fields representing a candidate CCS data
        :return: True if the fields look like CCSData, otherwise False
        :rtype: bool

        *Usage:*

        .. code-block:: python

            from dtngen.types import CCSData

            if CCSData.lookslike(list_of_candidate_fields):
                print ("It looks like CCSData")
        """
        if not isinstance(cand_ccs_data, dict) or len(cand_ccs_data) == 0:
            return False

        for key in cand_ccs_data:
            if not isinstance(key, int) or key == 0 or not BundleSequenceCollection.lookslike(cand_ccs_data[key]):
                return False
        
        return True

def default_encoder(encoder, value):
    """cbor2 custom field encoder. Encodes a value of one of the defined dtngen.types data types as cbor."""
    class_list = ["EID", "CreationTimestamp", "HopCountData", "CTEBData", "CREBData", "CCSData", "BundleSequenceCollection", "CCSData"]
    class_name = type(value).__name__

    if class_name in class_list:
        encoder.encode(value.enc_data())
    elif class_name == "InvalidCBOR":
        # Encode the value as normal
        cbor_val = bytearray(
            cbor2.dumps(value.enc_data()["value"], default=default_encoder)
        )

        # Replace the additional info of the first byte with the invalid
        # additional info
        cbor_val[0] &= 0b11100000
        cbor_val[0] |= value.enc_data()["additional_info"]

        # Write the modified encoding to the stream
        encoder.write(bytes(cbor_val))
    elif class_name == "RawData":
        # write the value (bytes) as-is to the stream
        encoder.write(value.enc_data())
    else:
        raise cbor2.CBOREncodeTypeError(f"cannot serialize type {type(value)}")

