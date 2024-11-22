import base64

from .types import EID, CreationTimestamp, HopCountData, CTEBData, CREBData, \
    InvalidCBOR, RawData

def custom_encoder(x):
    """JSON encode values in a non-default way."""
    if isinstance(x, bytes):
        return {
            "type": "hexbytes",
            "value": x.hex()
        }
    elif isinstance(x, EID):
        return {"type": "EID", "value": {"uri": x.uri, "ssp": x.ssp}}
    elif isinstance(x, CreationTimestamp):
        return {
            "type": "CreationTimestamp",
            "value": {"time": x.time, "sequence": x.sequence},
        }
    elif isinstance(x, HopCountData):
        return {
            "type": "HopCountData",
            "value": {"hop_limit": x.hop_limit, "hop_count": x.hop_count},
        }
    elif isinstance(x, CTEBData):
        return {
            "type": "CTEBData",
            "value": {"trans_id": x.trans_id, \
                "trans_series_id": x.trans_series_id, \
                "req_orig_eid": x.req_orig_eid},
        }
    elif isinstance(x, CREBData):
        return {
            "type": "CREBData",
            "value": {"bundle_seq_num": x.bundle_seq_num, \
                "bundle_seq_id": x.bundle_seq_id, \
                "rpt_request_flags": x.rpt_request_flags, \
                "scope_node_id": x.scope_node_id, \
                "rpt_eid": x.rpt_eid},
        }
    elif isinstance(x, InvalidCBOR):
        return {
            "type": "InvalidCBOR",
            "value": {"value": x.value, \
                "additional_info": x.additional_info},
        }
    elif isinstance(x, RawData):
        return {
            "type": "RawData",
            "value": x.value.hex(),
        }
    else:
        raise TypeError(f'Object of type {type(x)} is not JSON serializable')


def custom_decoder(x):
    """JSON decode values in a non-default way."""
    if x.get("type") == "bytes":
        return base64.b64decode(x["value"].encode())
    elif x.get("type") == "hexbytes":
        return bytes.fromhex(x["value"])
    elif x.get("type") == "EID":
        return EID({"uri": x["value"]["uri"], "ssp": x["value"]["ssp"]})
    elif x.get("type") == "CreationTimestamp":
        return CreationTimestamp(
            {"time": x["value"]["time"], "sequence": x["value"]["sequence"]}
        )
    elif x.get("type") == "HopCountData":
        return HopCountData(
            {"hop_limit": x["value"]["hop_limit"], "hop_count": x["value"]["hop_count"]}
        )
    elif x.get("type") == "CTEBData":
        return CTEBData(
            {
                "trans_id": x["value"]["trans_id"], \
                    "trans_series_id": x["value"]["trans_series_id"], \
                    "req_orig_eid": x["value"]["req_orig_eid"],
            }
        )
    elif x.get("type") == "CREBData":
        return CREBData(
            {
                "bundle_seq_num": x["value"]["bundle_seq_num"], \
                    "bundle_seq_id": x["value"]["bundle_seq_id"], \
                    "rpt_request_flags": x["value"]["rpt_request_flags"], \
                    "scope_node_id": x["value"]["scope_node_id"], \
                    "rpt_eid": x["value"]["rpt_eid"],
            }
        )
    elif x.get("type") == "InvalidCBOR":
        return InvalidCBOR(
            value = x["value"]["value"], \
                additional_info = x["value"]["additional_info"],
        )
    elif x.get("type") == "RawData":
        return RawData(
            value = bytes.fromhex(x["value"])
        )
    else:
        return x
