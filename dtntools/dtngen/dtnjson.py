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
import base64

from .types import (
    EID,
    CreationTimestamp,
    CREBData,
    CTEBData,
    HopCountData,
    InvalidCBOR,
    RawData,
)


def custom_encoder(x):
    """JSON encode values in a non-default way."""
    if isinstance(x, bytes):
        return {"type": "hexbytes", "value": x.hex()}
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
            "value": {
                "trans_id": x.trans_id,
                "trans_series_id": x.trans_series_id,
                "req_orig_eid": x.req_orig_eid,
            },
        }
    elif isinstance(x, CREBData):
        return {
            "type": "CREBData",
            "value": {
                "bundle_seq_num": x.bundle_seq_num,
                "bundle_seq_id": x.bundle_seq_id,
                "rpt_request_flags": x.rpt_request_flags,
                "scope_node_id": x.scope_node_id,
                "rpt_eid": x.rpt_eid,
            },
        }
    elif isinstance(x, InvalidCBOR):
        return {
            "type": "InvalidCBOR",
            "value": {"value": x.value, "additional_info": x.additional_info},
        }
    elif isinstance(x, RawData):
        return {
            "type": "RawData",
            "value": x.value.hex(),
        }
    else:
        raise TypeError(f"Object of type {type(x)} is not JSON serializable")


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
                "trans_id": x["value"]["trans_id"],
                "trans_series_id": x["value"]["trans_series_id"],
                "req_orig_eid": x["value"]["req_orig_eid"],
            }
        )
    elif x.get("type") == "CREBData":
        return CREBData(
            {
                "bundle_seq_num": x["value"]["bundle_seq_num"],
                "bundle_seq_id": x["value"]["bundle_seq_id"],
                "rpt_request_flags": x["value"]["rpt_request_flags"],
                "scope_node_id": x["value"]["scope_node_id"],
                "rpt_eid": x["value"]["rpt_eid"],
            }
        )
    elif x.get("type") == "InvalidCBOR":
        return InvalidCBOR(
            value=x["value"]["value"],
            additional_info=x["value"]["additional_info"],
        )
    elif x.get("type") == "RawData":
        return RawData(value=bytes.fromhex(x["value"]))
    else:
        return x
