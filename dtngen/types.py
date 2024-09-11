from enum import IntEnum, IntFlag

import cbor2
from crccheck.crc import Crc16IbmSdlc, Crc32Iscsi
from itertools import zip_longest

import warnings


class AdminRecordType:
    """Administrative Record Types."""

    BUNDLE_STATUS_REPORT = 1


class AdminRecord:
    """RFC9171 Administrative Record Base Class."""

    pass


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

    BUNDLE_PAYLOAD = 1
    PREVIOUS_NODE = 6
    BUNDLE_AGE = 7
    HOP_COUNT = 10
    CUST_TRANS_EXT = 15
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


def calc_crc(crc_type, fields):
    """Calculate CRC given crc type and fields.

    :param CRCType crc_type: The CRC algorithm to use. Valid values are CRCType.CRC16_X25 and CRCType.CRC32_C
    :param bytearray fields: The bytearray of bundle fields to calculate the CRC on
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


class EID:
    """Endpoint Identifier."""

    def __init__(self, eid_fields):
        """Initialize the EID.

        :param dict eid_fields: EID fields
        """
        self.uri = None
        self.ssp = None

        if "uri" in eid_fields:
            self.uri = eid_fields["uri"]
            if (not isinstance(self.uri, int)) or self.uri < 1 or self.uri > 2:
                warnmsg = f'Unsupported EID URI type {self.uri}'
                warnings.warn(warnmsg)
        if "ssp" in eid_fields:
            self.ssp = eid_fields["ssp"]
            if isinstance(self.uri, int) and self.uri == 1 and not isinstance(self.ssp, str):
                warnmsg = f'DTN EID ssp is {self.ssp} instead of a string'
                warnings.warn(warnmsg)
            if isinstance(self.uri, int) and self.uri == 2 \
                    and ((not isinstance(self.ssp, list) or len(self.ssp != 2)) \
                        or not isinstance(self.ssp[0], int) \
                        or not instance(self.ssp[1], int)):
                warnmsg = f'IPN EID ssp is {self.ssp} instead of a list of 2 ints'
                warnings.warn(warnmsg)
                
    def enc_data(self):
        """Return the data to encode.

        :return: list of data to encode
        :rtype: list
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
        """
        if isinstance(cand_eid, list) and len(cand_eid) >= 1 \
                and cand_eid[0] < 1 and cand_eid[0] > 2:
            # Because lookslike() should be called first, we should never get
            # here. If we do it's a programatic error.
            raise ValueError(f'Unsupported EID URI Type {cand_eid[0]}')

        uri_data = None
        ssp_data = None
        
        if len(cand_eid) >= 1:
            uri_data = cand_eid[0]
            if len(cand_eid) == 2:
                if cand_eid[0] == 1:
                    ssp_data = cand_eid[1]
                else:
                    ssp_dict = {"node_num":None, "service_num":None}
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
        """
        if isinstance(cand_eid, list) and len(cand_eid) == 2 \
                and isinstance(cand_eid[0], int):
            is_dtn = cand_eid[0] == 1 and isinstance(cand_eid[1], str)
            is_ipn = cand_eid[0] == 2 \
                and isinstance(cand_eid[1], list) and len(cand_eid[1]) == 2 \
                and isinstance(cand_eid[1][0], int) \
                and isinstance(cand_eid[1][1], int)
            
            return (is_dtn or is_ipn)
        
        return False


class CreationTimestamp:
    """Creation Timestamp."""

    def __init__(self, timestamp_fields):
        """Initialize the Creation Timestamp.

        :param dict timestamp_fields: Timestamp Fields
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
        """
        data = [self.time, self.sequence]
        return [i for i in data if i is not None]

    @classmethod
    def decode(cls, cand_timestamp):
        """Attempt to parse a Creation Timestamp.

        :param list cand_timestamp: A list of fields representing a Creation Timestamp
        """
        if len(cand_timestamp) != 2:
            warnmsg = "Creation Timestamp should have exactly 2 fields."
            warnings.warn(warnmsg)
            
        type_spec_dict = {"time":None, "sequence":None}
        timestamp_d = dict(zip_longest(type_spec_dict, cand_timestamp))
        
        return CreationTimestamp(timestamp_d)
        
    @classmethod
    def lookslike(cls, cand_eid):
        """Check if candidate creation timestamp looks like an creation timestamp.

        :param list cand_eid: A list of fields representing a candidate creation timestamp.
        """
        return isinstance(cand_eid, list) and len(cand_eid) == 2 \
            and isinstance(cand_eid[0], int) and isinstance(cand_eid[1], int)


class HopCountData:
    """Hop Count Data."""

    def __init__(self, hopcount_fields):
        """Initialize the Hop Count Data.

        :param dict hopcount_fields: Hop Count Fields
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
        """
        data = [self.hop_limit, self.hop_count]
        return [i for i in data if i is not None]

    @classmethod
    def decode(cls, cand_hopcount_data):
        """Attempt to parse Hop Count data.

        :param list cand_hopcount_data: A list of fields representing Hop Count Data
        """
        if len(cand_hopcount_data) != 2:
            warnmsg = "Hop Count Data should have 2 fields."
            warnings.warn(warnmsg)
            
        type_spec_dict = {"hop_limit":None, "hop_count":None}
        hopcount_data = dict(zip_longest(type_spec_dict, cand_hopcount_data))

        return HopCountData(hopcount_data)
        
    @classmethod
    def lookslike(cls, cand_hopcount_data):
        """Check if candidate hop count data looks like Hop Count data.

        :param list cand_eid: A list of fields representing candidate hop count data.
        """
        if not isinstance(cand_hopcount_data, list):
            return False
        if not len(cand_hopcount_data) == 2:
            return False

        return isinstance(cand_hopcount_data[0], int) and \
            isinstance(cand_hopcount_data[1], int)


class CTEBData:
    """Custody Transfer Extension Block Data."""

    def __init__(self, cteb_fields):
        """Initialize the CTEB Data.

        :param dict cteb_fields: CTEB Data Fields
        """
        self.trans_id = None
        self.trans_series_id = None
        self.req_orig_eid = None
        
        if "trans_id" in cteb_fields:
            self.trans_id = cteb_fields["trans_id"]
        if "trans_series_id" in cteb_fields:
            self.trans_series_id = cteb_fields["trans_series_id"]
        if "req_orig_eid" in cteb_fields:
            self.req_orig_eid = cteb_fields["req_orig_eid"]
                
    def enc_data(self):
        """Return the data to encode.

        :return: list of data to encode
        :rtype: list
        """
        data = [self.trans_id, self.trans_series_id, self.req_orig_eid]
        return [i for i in data if i is not None]

    @classmethod
    def decode(cls, cand_cteb_data):
        """Attempt to parse CTEB data.

        :param list cand_hopcount_data: A list of fields representing CTEB Data
        """
        if len(cand_cteb_data) != 3:
            warnmsg = "CTEB Data should have 3 fields."
            warnings.warn(warnmsg)
            
        type_spec_dict = {"trans_id":None, "trans_series_id":None, \
            "req_orig_eid":None}
        cteb_data = dict(zip_longest(type_spec_dict, cand_cteb_data))

        if "req_orig_eid" in cteb_data and cteb_data["req_orig_eid"] is not None:
            cteb_data["req_orig_eid"] = EID.decode(cteb_data["req_orig_eid"])

        return CTEBData(cteb_data)
        
    @classmethod
    def lookslike(cls, cand_cteb_data):
        """Check if candidate hop count data looks like Hop Count data.

        :param list cand_eid: A list of fields representing candidate hop count data.
        """
        if not isinstance(cand_cteb_data, list):
            return False
        if not len(cand_cteb_data) == 3:
            return False
            
        return isinstance(cand_cteb_data[0], int) and \
            isinstance(cand_cteb_data[1], int) \
            and EID.lookslike(cand_cteb_data[2])


class CREBData:
    """Compressed Reporting Extension Block Data."""

    def __init__(self, creb_fields):
        """Initialize the CREB Data.

        :param dict creb_fields: CREB Data Fields
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

        if (self.bundle_seq_id is not None and self.bundle_seq_num is None) \
            or (self.rpt_request_flags is not None and any(arg is None for arg in (self.bundle_seq_num, self.bundle_seq_id))) \
            or (self.scope_node_id is not None and any(arg is None for arg in (self.bundle_seq_num, self.bundle_seq_id, self.rpt_request_flags))) \
            or (self.rpt_eid is not None and any(arg is None for arg in (self.bundle_seq_num, self.bundle_seq_id, self.rpt_request_flags, self.scope_node_id))):
                warnmsg = "Compressed Reporting Extension Block: One or more of bundle_seq_id, rpt_request_flags, scope_node_id or rpt_eid was provided without one or more of the prior arguments provided"
                warnings.warn(warnmsg)
                
    def enc_data(self):
        """Return the data to encode.

        :return: list of data to encode
        :rtype: list
        """
        data = [self.bundle_seq_num, self.bundle_seq_id, \
            self.rpt_request_flags, self.scope_node_id, self.rpt_eid]
        return [i for i in data if i is not None]
        

    @classmethod
    def decode(cls, cand_creb_data):
        """Attempt to parse CTEB data.

        :param list cand_hopcount_data: A list of fields representing CTEB Data
        """
        if len(cand_creb_data) < 1 or len(cand_creb_data) > 5:
            warnmsg = "CREB Data should have 1 to 5 elements."
            warnings.warn(warnmsg)
            
        type_spec_dict = {"bundle_seq_num":None, "bundle_seq_id":None, \
            "rpt_request_flags":None, "scope_node_id":None, "rpt_eid":None}
        creb_data = dict(zip_longest(type_spec_dict, cand_creb_data))

        if "scope_node_id" in creb_data and creb_data["scope_node_id"] is not None:
            creb_data["scope_node_id"] = EID.decode(creb_data["scope_node_id"])
        if "rpt_eid" in creb_data and creb_data["rpt_eid"] is not None:
            creb_data["rpt_eid"] = EID.decode(creb_data["rpt_eid"])

        return CREBData(creb_data)
        
    @classmethod
    def lookslike(cls, cand_creb_data):
        """Check if candidate hop count data looks like Hop Count data.

        :param list cand_creb_data: A list of fields representing candidate hop count data.
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


def default_encoder(encoder, value):
    """cbor2 custom field encoder."""
    class_list = \
        ['EID', 'CreationTimestamp', 'HopCountData', 'CTEBData', 'CREBData']
    class_name = type(value).__name__
    
    if class_name in class_list:
        encoder.encode(value.enc_data())
    else:
        raise TypeError
