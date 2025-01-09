# Cloud Instance Performance Test - RX Side
# Includes use of Data Receiver
# Convergence Layer: UDP

# Prerequisites:
# - DTN Gen / DTN CLA packages installed

import time
import traceback
import warnings

from dtntools.dtncla.udp import UdpRxSocket, UdpTxSocket

warnings.simplefilter("always")

# Setting Script Runner line delay (comment out for command line execution)
# set_line_delay(0.000)

print("Contact #2: Configuring the Data Receiver")
data_receiver = UdpRxSocket("0.0.0.0", 4557)

print("Contact #2: Connecting the Data Receiver")
data_receiver.connect()

print("Contact #2: Receiving bundles...")
contact_start = time.time()

try:
    while time.time() < contact_start + 150:
        print(f"Contact #2: {data_receiver.get_packets_received()}")
        data_receiver.read_all()
        time.sleep(10)

    print("Contact #2: Disconnecting the Data Receiver")
    data_receiver.disconnect()

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print(f"Contact #2: Bundles received = {data_receiver.get_packets_received()}")
