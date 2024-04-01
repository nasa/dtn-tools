from .types import CreationTimestamp
from .types import EID
import base64


def custom_encoder(x):
    if isinstance(x, bytes):
        return {
            "type": "hexbytes",
            "value": x.hex()
#             "value": base64.b64encode(x).decode()
        }
    elif isinstance(x, EID):
        return {
            "type": "EID",
            "value": {
                "uri": x.uri,
                "ssp": x.ssp
            }
        }
    elif isinstance(x, CreationTimestamp):
        return {
            "type": "CreationTimestamp",
            "value": {
                "time": x.time,
                "sequence": x.sequence
            }
        }
    else:
        raise TypeError
        

def custom_decoder(x):
    if x.get("type") == "bytes":
        return base64.b64decode(x["value"].encode())
    elif x.get("type") == "hexbytes":
        return bytearray.fromhex(x["value"])
    elif x.get("type") == "EID":
        return EID({"uri":x["value"]["uri"], "ssp":x["value"]["ssp"]})
    elif x.get("type") == "CreationTimestamp":
        return CreationTimestamp({"time":x["value"]["time"],"sequence":x["value"]["sequence"]})
    else:
        return x