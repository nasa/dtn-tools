from enum import IntEnum, IntFlag

from cbor2 import dumps
from crccheck.crc import Crc16IbmSdlc, Crc32Iscsi


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


class CreationTimestamp:
    """Creation Timestamp."""

    def __init__(self, timestamp_fields):
        """Initialize the Creation Timestamp.

        :param dict timestamp_fields: Timestamp Fields
        """
        self.time = timestamp_fields["time"]
        self.sequence = timestamp_fields["sequence"]

    @classmethod
    def decode(cls, cand_timestamp):
        """Attempt to parse a Creation Timestamp.

        :param list cand_timestamp: A list of fields representing a Creation Timestamp
        """
        if len(cand_timestamp) != 2:
            raise ValueError("Creation Timestamp should have exactly 2 fields.")
        timestamp_d = {"time": cand_timestamp[0], "sequence": cand_timestamp[1]}
        return CreationTimestamp(timestamp_d)


class CRCType(IntFlag):
    """BPv7 Supported CRC Types."""

    NONE = 0
    CRC16_X25 = 1
    CRC32_C = 2


class CRCFlag(IntEnum):
    """Flag to indicate if CRC should be calculated."""

    CALCULATE = 0


def calc_crc(crc_type, fields):
    """Calculate CRC given crc type and fields.

    :param CRCType crc_type: The CRC algorithm to use. Valid values are CRCType.CRC16_X25 and CRCType.CRC32_C
    :param bytearray fields: The bytearray of bundle fields to calculate the CRC on
    """
    if crc_type == CRCType.CRC16_X25:
        fields.append(b"\x00\x00")
        crc = Crc16IbmSdlc.calc(dumps(fields, default=default_encoder))
        return crc.to_bytes(2, "big")
    elif crc_type == CRCType.CRC32_C:
        fields.append(b"\x00\x00\x00\x00")
        crc = Crc32Iscsi.calc(dumps(fields, default=default_encoder))
        return crc.to_bytes(4, "big")
    else:
        return None


class EID:
    """Endpoint Identifier."""

    def __init__(self, eid_fields):
        """Initialize the EID.

        :param dict eid_fields: EID fields
        """
        self.uri = eid_fields["uri"]
        self.ssp = eid_fields["ssp"]

    @classmethod
    def decode(cls, cand_eid):
        """Attempt to parse an EID.

        :param list cand_eid: A list of fields representing a candidate EID.
        """
        if cand_eid[0] != 2:
            raise ValueError(f"Unsupported URI Type {cand_eid[0]}")
        eid_d = {
            "uri": cand_eid[0],
            "ssp": {"node_num": cand_eid[1][0], "service_num": cand_eid[1][1]},
        }
        return EID(eid_d)


def default_encoder(encoder, value):
    """cbor2 custom field encoder."""
    if isinstance(value, EID):
        encoder.encode([value.uri, [value.ssp["node_num"], value.ssp["service_num"]]])
    elif isinstance(value, CreationTimestamp):
        encoder.encode([value.time, value.sequence])
    else:
        raise TypeError
