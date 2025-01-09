# Cloud Instance Performance Test - RX Side (250,000 bundles)
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

print("Configuring the Data Receiver")
data_receiver = UdpRxSocket("0.0.0.0", 4558)

print("Connecting the Data Receiver")
data_receiver.connect()

print("Receiving bundles...")
contact_start = time.time()

try:
    bundles_received = 0
    while bundles_received < 250000:
        time.sleep(1)
        data_receiver.read_all()
        bundles_received = data_receiver.get_packets_received()
        print(bundles_received)

    print("Disconnecting the Data Receiver")
    data_receiver.disconnect()

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print(f"Bundles received = {data_receiver.get_packets_received()}")
