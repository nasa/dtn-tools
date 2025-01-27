#!/bin/sh

# path variables
config_files=$HDTN_SOURCE_ROOT/config_files
hdtn_config=$config_files/hdtn/hdtn_udp_max_contacts.json

cd $HDTN_SOURCE_ROOT


# HDTN one process
./build/module/hdtn_one_process/hdtn-one-process --hdtn-config-file=$hdtn_config --contact-plan-file=contactPlanMaxContacts.json &
oneprocess_PID=$!
sleep 10
