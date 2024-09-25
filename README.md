## Requirements

- Python 3.8.10 or later

You can check the version of python by entering this command at the command-line:

        python --version

## Setup

In the top level dtngen directory enter these commands to install everything needed:

        pip install -r requirements.txt
        pre-commit install

## Generating and viewing the autoapi documentation

cd into the docs directory and enter this command to build the autoapi documentation:

        make html

You will see a number of warnings, but it should complete successfully.

Once the build is complete you can view the API documentation by opening the **docs/build/html/index.html** file in a browser.

Please note that currently there is an issue in which classes/methods/etc appear both appropriately in their submodules (dtngen.blocks, dtngen.bundle, dtngen.dtnjson, dtngen.types), but also at the package level (dtngen). To avoid confusion, click on a submodule and view that submodule's APIs from there.

## Running the test script

In the top-level dtngen directory is a test script **dtngen-test.py**. Run it by entering this command in this directory:

        python dtngen-test.py 
        
This produces a lot of output and if all tests succeed it will end without an error message. You can view this script for examples of how to utilize dtngen.