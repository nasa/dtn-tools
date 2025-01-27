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
