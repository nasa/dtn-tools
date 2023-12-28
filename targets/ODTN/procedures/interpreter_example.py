from ODTN.lib.odtn.bundle import Bundle


def recv_candidate_bundle():
    # This is a known-valid bundle.  It is being used in place of a data-receiver call so that bundle interpreter functionality can be demonstrated.
    bplib_sample_bundle = "9f8907040182028218c801820282186401820282186401821b000000afe9537a38001a0036ee80420b19861849184900014682028218640a426747860101000154000000000000000c68656c6c6f20776f726c640a427a2fff"
    return bytes.fromhex(bplib_sample_bundle)


## Proc Start ##################################################################

# Step 1: "Receive" a Bundle from the data receiver tool
candidate_bundle = recv_candidate_bundle()

# Step 2: Attempt to cbor decode the payload using the interpreter
bundle = Bundle.decode(candidate_bundle)
if not bundle:
    raise ValueError("Bundle could not be parsed.")


# Step 3: Access fields within the bundle as required by the test
# Parsing Primary block
assert bundle.pri_block.version == 7
assert bundle.pri_block.control_flags == 4


# Parsing the payload
bplib_payload_str = bundle.canon_blocks[0].payload[8:].decode().strip()
assert bplib_payload_str == "hello world"
