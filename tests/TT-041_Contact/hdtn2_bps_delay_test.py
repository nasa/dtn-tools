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
'''
****************************************************************************
** Rate Limit/Message Delay test with bundle size: 60000 bytes (480000 bits)
** - hdtn2_tx configured to communicate with HDTN Node 2
** - Run from command line on local host, not via COSMOS Script Runner
****************************************************************************
'''
from hdtn2_tx import hdtn2_tx

print("****************************************************")
print("Test 1 - Initial ... bps: 480000 delay: 0.0 sec")
print("         Expect ~480000 bps")
print("****************************************************")

hdtn2_tx(480000, 0.0)

i = input("Press Enter to continue ...")

print()
print("****************************************************")
print("Test 2 - Change rate ... bps: 960000 delay: 0.0 sec")
print("         Expect ~960000 bps")
print("****************************************************")

hdtn2_tx(960000, 0.0)

i = input("Press Enter to continue ...")

print()
print("****************************************************")
print("Test 3 - Change delay ... bps: 480000 delay: 2.0 sec")
print("         Expect ~240000 bps")
print("****************************************************")

hdtn2_tx(480000, 2.0)

i = input("Press Enter to continue ...")
