from abc import ABC
from enum import IntEnum


class AdminRecordType:
    """Administrative Record Types."""

    BUNDLE_STATUS_REPORT = 1


class AdminRecord:
    """RFC9171 Administrative Record Base Class."""

    pass


class BlockPCFlags(IntEnum):
    """Block Processing Control Flags."""

    FRAG_REPLICATE = 0
    REP_UNPROC = 1
    DEL_UNPROC = 2
    DEL_BLOCK_UNPROC = 4


class BlockType:
    """BPv7 Block Type Flag Definitions.

    .. note::
        Only BPv7 types are defined and supported.
    """

    BUNDLE_PAYLOAD = 1
    PREVIOUS_NODE = 6
    BUNDLE_AGE = 7
    HOP_COUNT = 10


class BundlePCFlags(IntEnum):
    """Bundle Processing Control Flag."""

    FRAGMENT = 0
    ADMIN_RECORD = 1
    BUNDLE_NO_FRAG = 2
    ACK_REQ = 5
    REPORT_STATUS_TIME = 6
    REPORT_BUNDLE_RCV = 14
    REPORT_BUNDLE_FWD = 16
    REPORT_BUNDLE_DLV = 17
    REPORTBUNDLE_DEL = 18


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


class CRCType(IntEnum):
    """BPv7 Supported CRC Types."""

    NONE = 0
    CRC16_X25 = 1
    CRC32_C = 2


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

