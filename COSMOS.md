## OpenC3 COSMOS
To use DTNTools with OpenC3 COSMOS, a couple of changes in the COSMOS configuration (/home/[AUID]/cosmos/compose.yaml) are needed to work with DTNTools.

For talking to external machines, add the following rows under the "restart" entry in the "openc3-cosmos-script-runner-api" section (below are the ports that we will use for interoperability testing — our HDTN configuration is set up to talk to them, but other ports can be used depending on the context):

        ports:
          - "4556:4556/udp"
          - "4557:4557/udp"
          - "4558:4558/udp"
          - "4559:4559/udp"

For allowing the COSMOS scripts to read and write bundles to disk, add the following row as the last entry under "volumes" in the "openc3-cosmos-script-runner-api" section:

        - "./bundles:/bundles"

You will need to stop and start COSMOS (using openc3.sh) for these changes to take effect.

## Install the .whl files in COSMOS

From the COSMOS Admin Console, select (under Packages) the DTNTools .whl file and click on upload.
