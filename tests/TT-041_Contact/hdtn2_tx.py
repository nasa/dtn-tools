def hdtn2_tx(bpslim=25000000, delay=0.0):
    '''
    *********************************************************************
    ** Sends bundles to HDTN Node 2 at specified rate/inter message delay
    *********************************************************************
    '''
    import codecs
    import time
    import traceback
    import warnings

    from dtncla.udp import UdpTxSocket
    from dtngen.blocks import (
        BundleAgeBlock,
        CanonicalBlock,
        CompressedReportingBlock,
        CustodyTransferBlock,
        HopCountBlock,
        PayloadBlock,
        PayloadBlockSettings,
        PrevNodeBlock,
        PrimaryBlock,
        PrimaryBlockSettings,
        UnknownBlock,
    )
    from dtngen.bundle import Bundle
    from dtngen.types import (
        EID,
        BlockPCFlags,
        BlockType,
        BundlePCFlags,
        CRCFlag,
        CRCType,
        CreationTimestamp,
        CREBData,
        CTEBData,
        HopCountData,
        StatusRRFlags,
        TypeWarning,
    )

    warnings.simplefilter("always")

    # Setting Script Runner line delay (comment out for command line execution)
    # set_line_delay(0.000)

    print("Defining new primary and payload blocks")
    primary_block_settings = PrimaryBlockSettings(
        version=7,
        control_flags=BundlePCFlags.MUST_NOT_FRAGMENT,
        crc_type=CRCType.CRC16_X25,
        dest_eid=EID({"uri": 2, "ssp": {"node_num": 103, "service_num": 1}}),
        src_eid=EID({"uri": 2, "ssp": {"node_num": 101, "service_num": 1}}),
        rpt_eid=EID({"uri": 2, "ssp": {"node_num": 100, "service_num": 1}}),
        creation_timestamp={
            "time": {"start": 755533838904, "increment": 256},
            "sequence": {"start": 0},
        },
        lifetime=3600000,
        crc=CRCFlag.CALCULATE,
    )

    payload_block_settings = PayloadBlockSettings(
        blk_type=BlockType.AUTO,
        blk_num=1,
        control_flags=0,
        crc_type=CRCType.CRC16_X25,
        payload={"size": 60000},
        crc=CRCFlag.CALCULATE,
    )

    print("Creating the new set of bundles")
    generated_bundles = Bundle.generate(
        num_bundles=50,
        pri_settings=primary_block_settings,
        canon_settings=[payload_block_settings],
    )

    print("Converting bundles (size: 60000) to bytes ...")
    bundle_data = [x.to_bytes() for x in generated_bundles]

    print(f"Configuring the Data Sender for bps limit: {bpslim} delay: {delay} sec")
    # Node1  10.2.23.114
    # Node2  10.2.17.211
    # Node3  10.2.22.185
    data_sender = UdpTxSocket(
        "X.X.X.X", 4558, bps_limit=bpslim, inter_msg_delay=delay
    )

    try:
        print("Connecting the Data Sender")
        data_sender.connect()

        loops = 0
        start_time = time.time()

        print("Sending bundles....")
        # print(f'... Start Time = {start_time}')
        while loops < 2:
            loops = loops + 1

            for x in bundle_data:
                data_sender.write(x)

            print(f"... Current bps: {int(data_sender.get_bps()):d}")

        end_time = time.time()
        # print(f'... End Time = {end_time}')

        tx_time = int(end_time - start_time + 0.5)

        time.sleep(5)

        print(f"... {data_sender.get_packets_sent()} packets sent in {tx_time} sec")

    except KeyboardInterrupt:
        pass

    except Exception:
        print(traceback.format_exc())

    finally:
        print("Disconnecting the Data Sender")
        data_sender.disconnect()


# main
# hdtn2_tx(10000, 2.0)
