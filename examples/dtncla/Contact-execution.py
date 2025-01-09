# Cloud Instance Concurrent Contact Test
# Includes use of Data Sender and Date Receiver
# Convergence Layer: UDP

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
