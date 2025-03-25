# DTN Tools Concurrent Contact Test - Master script
# Demonstrates support of concurrent contacts for a DTN implementation configured as a Relay Node
# Convergence Layer: UDP
# This script does NOT work in OpenC3 COSMOS

# Prerequisites:
# - DTN Tools packages installed for command line use
# - Called scripts are located in the same folder as this script

import subprocess
import time

print("Waiting 5 seconds")
time.sleep(5)

print("Executing contact 1 scripts")
subprocess.Popen(["python", "RX-contact_1.py"])
subprocess.Popen(["python", "TX-contact_1.py"])

print("Waiting 30 seconds")
time.sleep(30)

print("Executing contact 2 scripts")
subprocess.Popen(["python", "RX-contact_2.py"])
subprocess.Popen(["python", "TX-contact_2.py"])
