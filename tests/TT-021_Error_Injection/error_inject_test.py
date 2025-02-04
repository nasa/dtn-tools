"""
error_inject_test.py
    Sends corrupted bundles to DTN Node

    Validates Requirements: DTN.TEST.0215, DTN.TEST.0220

"""
from dtntools.dtncla.udp import UdpTxSocket
from dtntools.dtngen.bundle import Bundle
from dtntools.dtncla.errors.inject import inject_errors
import os
load_utility (f"<%= target_name %>/procedures/dtngen_utils.py")

set_line_delay(0)

def binary_to_hex(filename):
    """ Reads binary file and returns hex string.

    """
    with open(filename, 'rb') as f:
        binary_data = f.read()
        hex_data = binary_data.hex()
    return hex_data


def find_mismatch(str1, str2):
    """Finds the mismatch positions between two strings.
    
    Returns:
      List of mismatch [position, str1 value, str2 value].
    """
    
    with disable_instrumentation():
        mismatch_list = []
        for i in range(min(len(str1), len(str2))):
            if str1[i] != str2[i]:
                mismatch_list.append([i, str1[i], str2[i]])
    
    return mismatch_list


# main

# Connect data sender (to HDTN Node 2 only to monitor bundle errors)
dest_ip     = "X.X.X.X"
dest_port   = 4558

data_sender = UdpTxSocket(dest_ip, dest_port)
data_sender.connect()


# Generate test bundles at /bundles/<dest_eid>

dest_eid = 103
num_bundles = 3

file_path_bundles = "/bundles/"+str(dest_eid)
os.makedirs(file_path_bundles, exist_ok=True)

payload = b'\x55'*1000 # simple pattern to see corruption
DTNGenUtils.generate_bundles(dest_eid=dest_eid, num_bundles=num_bundles, payload=payload)


# Get test bundles at /bundles/<dest_eid>
# Inject errors into bundles at different rates
# - Corrupted bundle files stored at /bundles/corrupt

file_path_corrupt = "/bundles/corrupt"
os.makedirs(file_path_corrupt, exist_ok=True)

error_rate = 0
for n in range (num_bundles):
    bundle = Bundle.from_json_file(f'{file_path_bundles}/generated_bundle_{n+1}.json')
    bundle.to_bytes_file(f'{file_path_corrupt}/original_bundle_{n+1}.bin')

    error_rate += 800 # error spacing in bits
    print(f"Bundle {n+1} - Error spacing set to {error_rate} bits")

    corrupt_bundle = inject_errors(
        data_bytes=bundle.to_bytes(),
        error_rate=error_rate,
        filename=f'{file_path_corrupt}/corrupt_bundle_{n+1}.bin',
    )

    # Send the corrupted bundles out to DTN node
    # - With HDTN we will see errors
    
    data_sender.write(corrupt_bundle)

data_sender.disconnect()


# Convert original and corrupted bundle files to hex 
# Compare and get mismatch positions and values

for n in range (num_bundles):
    hex_orig = binary_to_hex(f'{file_path_corrupt}/original_bundle_{n+1}.bin')
    hex_corr = binary_to_hex(f'{file_path_corrupt}/corrupt_bundle_{n+1}.bin')
    
    with open(f"{file_path_corrupt}/bundle_hex_diff_{n+1}.txt", 'w') as f:
        f.write ("Original bundle (hex):\n")
        f.write(hex_orig+"\n\n")
        
        f.write ("Corrupted bundle (hex):\n")
        f.write(hex_corr+"\n\n")
        
        mismatch_list = find_mismatch(hex_orig, hex_corr)
        print(f"Bundle {n+1} corruption(s): ", mismatch_list)
        
        f.write("Corruption location/values:\n" + str(mismatch_list) + "\n")
        f.close()
