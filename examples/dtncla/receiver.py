import time

from dtntools.dtncla.udp import UdpRxSocket
from dtntools.dtngen.bundle import Bundle

LOCAL_IP = "127.0.0.1"
LOCAL_PORT = 13708
# LOCAL_IP = "10.1.1.230"
# LOCAL_PORT = 13708

data_receiver = UdpRxSocket(LOCAL_IP, LOCAL_PORT)
data_receiver.connect()

packets = []

print("Listening for packets.")
try:
    last_cnt = data_receiver.get_packets_received()
    print("Start sender within 10 seconds...")
    time.sleep(10)

    print(
        "Receiver will stop once packets stop being received for 5 seconds. Press ctrl-c to stop early."
    )
    while last_cnt != data_receiver.get_packets_received():
        last_cnt = data_receiver.get_packets_received()
        print(last_cnt)
        packets = packets + data_receiver.read_all()
        time.sleep(5)

except KeyboardInterrupt:
    pass

finally:
    # Get any straggler packets
    packets = packets + data_receiver.read_all()

    print(f"\npackets received = {data_receiver.get_packets_received()}")
    print(f"packets count = {len(packets)}")
    data_receiver.disconnect()
    if len(packets) > 0:
        bundle = Bundle.from_bytes(packets[len(packets) - 1])
        print(f"bundle = {bundle}")
