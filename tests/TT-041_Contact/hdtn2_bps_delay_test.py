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
