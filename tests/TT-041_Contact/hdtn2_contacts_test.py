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
"""
***********************************************************************
** DTNGen Contact Handling Test
**
** Spawns three scripts to send bundles to and receive bundles from
** HDTN Node 2 concurrently for three contacts
**
** Note:
**   500 bundles of size 1000 bytes for each <dest> generated and stored
**   in /bundles/<dest>, where <dest>=102,103,104, prior to the test.
**   Data sender scripts retrieve appropriate bundles and send them to
**   respective destinations.
***********************************************************************
"""
id1 = script_run(f"<%= target_name %>/procedures/hdtn2_connect_contact1.py")
id2 = script_run(f"<%= target_name %>/procedures/hdtn2_connect_contact2.py")
id3 = script_run(f"<%= target_name %>/procedures/hdtn2_connect_contact3.py")

print(id1, id2, id3)
