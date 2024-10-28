## Requirements

- Python 3.8.10 or later

You can check the version of python by entering this command at the command-line:

        python --version

## Generic Setup

If not already done, update the environmental varaiable PATH in .bashrc to include the path to dependencies:

        export PATH="$HOME/cosmos:$HOME/.local/bin:$PATH"

Note that you need to fully log out of this instance in FastX and log back in before the change takes effect.

In the top level dtngen directory enter these commands to install everything needed:

        pip install -r requirements.txt
        pre-commit install

## Generating and viewing the autoapi documentation

cd into the DTNGen docs directory and enter this command to build the autoapi documentation:

        make html

You will see a number of warnings, but it should complete successfully.  Repeat for DTNCLA.

Once the build is complete you can view the API documentation by opening the **docs/build/html/index.html** file in a browser.

Please note that currently there is an issue in which classes/methods/etc appear both appropriately in their submodules (dtngen.blocks, dtngen.bundle, dtngen.dtnjson, dtngen.types), but also at the package level (dtngen). To avoid confusion, click on a submodule and view that submodule's APIs from there.

## OpenC3 COSMOS-specific Setup

A couple of changes in the COSMOS configuration (/home/[AUID]/cosmos/compose.yaml) are needed to work with DTNGen and DTNCLA.

For talking to external machines, add the following rows under the "restart" entry in the "openc3-cosmos-script-runner-api" section (below are the ports that we will use for interoperability testing - our HDTN configuration is set up to talk to them - but other ports can be used depending on context):

        ports:
          - "4556:4556/udp"
          - "4557:4557/udp"
          - "4558:4558/udp"
          - "4559:4559/udp"

For allowing the COSMOS scripts to read and write bundles to disk, add the following row as the last entry under "volumes" in the "openc3-cosmos-script-runner-api" section:

        - "./bundles:/bundles"

You may need to stop and start COSMOS (using openc3.sh) for these changes to take effect.

## Building the .whl package files

In the top level dtngen directory enter this command to build the DTNGen python .whl package file (it is created in the dist subdirectory):

        python setup.py bdist_wheel

Repeat for DTNCLA.

## Install the .whl files in COSMOS

From the COSMOS Admin Console select (under Packages) the DTNGen .whl file and click on upload.  Repeat for DTNCLA.

## Install the .whl files for commmand-line python usage

In a terminal, cd to the dtngen dist subdirectory and enter this command (substitute with the current .whl filename):

        pip install dtngen-0.6.0-py3-none-any.whl
    
Repeat for DTNCLA

## Running the test script

In the top-level dtngen directory is a test script **dtngen-test.py**. Run it by entering this command in this directory:

        python dtngen-test.py 
        
This produces a lot of output and if all tests succeed it will end without an error message. You can view this script for examples of how to utilize dtngen.