# Cloud Instance Performance Test - RX Side
# Includes use of Data Receiver
# Convergence Layer: UDP

# Prerequisites:
# - DTN CLA packages installed

import time
import traceback
import warnings

from dtntools.dtncla.udp import UdpRxSocket, UdpTxSocket

warnings.simplefilter("always")

# Setting Script Runner line delay (comment out for command line execution)
# set_line_delay(0.000)

print("Contact #1: Configuring the Data Receiver")
data_receiver = UdpRxSocket("0.0.0.0", 4558)

print("Contact #1: Connecting the Data Receiver")
data_receiver.connect()

print("Contact #1: Receiving bundles...")
contact_start = time.time()

try:
    while time.time() < contact_start + 180:
        print(f"Contact #1: {data_receiver.get_packets_received()}")
        data_receiver.read_all()
        time.sleep(10)

    print("Contact #1: Disconnecting the Data Receiver")
    data_receiver.disconnect()

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print(f"Contact #1: Bundles received = {data_receiver.get_packets_received()}")
