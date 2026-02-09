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
