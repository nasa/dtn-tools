#!/bin/bash
set -e
OPENC3=/opt/OpenC3_cosmos-project/openc3.sh

if [[ -z $1 ]]; then
    echo "Please supply a version number"
    exit -1
fi

$OPENC3 cli rake build VERSION=$1
