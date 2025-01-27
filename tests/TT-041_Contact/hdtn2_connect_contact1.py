"""
***********************************************************************
** Sends bundles to and receives bundles from HDTN Node 2 for Contact 1
***********************************************************************
"""
load_utility(f"<%= target_name %>/procedures/build_tests/dtngen_utils.py")
from dtncla.udp import UdpRxSocket, UdpTxSocket

dest_ip = "X.X.X.X"
dest_port = 4556
local_ip = "0.0.0.0"
local_port = 4557

num_bundles = 50

print("Configuring/connecting Data Sender and Data Receiver")
data_sender = UdpTxSocket(dest_ip, dest_port)
data_receiver = UdpRxSocket(local_ip, local_port)

data_sender.connect()
data_receiver.connect()

print(f"Sending {num_bundles} bundles to HDTN Node 2 dest 102")
DTNGenUtils.send_bundles(num_bundles, 102, data_sender)

print("Receiving bundles returned from HDTN Node 2")
DTNGenUtils.receive_bundles(num_bundles, data_receiver)

print("Disconnecting Data Sender and Data Receiver")
data_receiver.disconnect()
data_sender.disconnect()
