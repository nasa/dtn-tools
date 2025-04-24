# DTN Tools Performance Test (250,000 bundles) - Receiving Side
# Demonstrates receiving a set of 250,000 bundles
# Convergence Layer: UDP
# This version of the script works both in OpenC3 COSMOS and from command line

# Prerequisites:
# - DTN Tools packages installed for COSMOS or command line use
# - If running in COSMOS, uncomment the "set_line_delay(0.000)" line
# - Port 4556 is available for use

import time
import traceback
import warnings

from dtntools.dtncla.udp import UdpRxSocket, UdpTxSocket

warnings.simplefilter("always")

# Setting Script Runner line delay (comment out for command line execution)
# set_line_delay(0.000)

print("Configuring the Data Receiver")
data_receiver = UdpRxSocket("0.0.0.0", 4556)

print("Connecting the Data Receiver")
data_receiver.connect()

print("Receiving bundles...")
contact_start = time.time()

try:
    bundles_received = 0
    while bundles_received < 250000:
        data_receiver.read()
        bundles_received = data_receiver.get_packets_received()

    print("Disconnecting the Data Receiver")
    data_receiver.disconnect()

except KeyboardInterrupt:
    pass

except Exception:
    print(traceback.format_exc())

finally:
    print(f"Bundles received = {data_receiver.get_packets_received()}")
