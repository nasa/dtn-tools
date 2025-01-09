## Development Environment Setup
### Setup Pipenv
If your system does not have pipenv, install it using `pip`:

    pip install --user pipenv

### Add local Python binaries to PATH
If not already done, update the environmental variable PATH in `.bashrc` to include the path to dependencies:

    export PATH="$HOME/cosmos:$HOME/.local/bin:$PATH"

Then, make this change effective by re-sourcing `.bashrc`:

    source ~/.bashrc

### Create a pipenv for development and install project dependencies
It is recommended to use a virtual environment for development to avoid cluttering your machine's global Python dependencies. This only needs to be done once when the project is first cloned:

    pipenv --python 3.8
    pipenv shell
    pip install -r requirements.txt
    pre-commit install

## Development Workflow

### Enter virtual environment
Pipenv provides a shell that links to the Python virtual environment with the correct dependencies. At the beginning of a development session, this environment is loaded by running:

    pipenv shell

### Committing
The project uses pre-commit to run style enforcement and linting. When a commit is being made, the source will be auto-formatted to be compliant with PEP standards. This will result, usually, in needing to make the commit a second time. Please note that this workflow is only required if you are working on the core codebase (dtntools module). It does not apply to the `examples` or `tests` modules.

    # Before pre-commit tools run
    git add -A && git commit -m "Add a feature"

    # pre-commit automatically formats your commit and warns you of linting issues

    # After fixing linting issues:
    git add -A && git commit -m "Add a feature"

If you want to skip this step, you can bypass the pre-commit by using `--no-verify`, but please remember to run them once before merging to main:

    git add -A && git commit -m "Add a feature" --no-verify

The pre-commit tools are fairly annoying, but they ensure consistency among developers and also ensure that the Sphinx development guide has a higher chance of building without errors.

## Generating a .whl Release
To build a wheel, run the following from the top-level of the project:

    python setup.py bdist_wheel

This will produce a `.whl` file in the `dist/` folder of the repository.

## Generating and viewing the autoapi documentation

Change directory into the DTNGen docs directory and enter this command to build the autoapi documentation:

    make html

You will see a number of warnings, but it should complete successfully.

Once the build is complete, you can view the API documentation by opening the **docs/build/html/index.html** file in a browser.

Please note that currently there is an issue in which classes/methods/etc. appear both appropriately in their submodules (dtngen.blocks, dtngen.bundle, dtngen.dtnjson, dtngen.types), but also at the package level (dtngen). To avoid confusion, click on a submodule and view that submodule's APIs from there.

## Running Examples

### DTN Gen
In the `examples` folder, there is a test script `suite.py`. This can be run to verify that DTNGen is working as expected. It will be replaced in the future with pytest unit tests.

    python -m examples.dtngen.suite

This produces a lot of output, and if all tests succeed, it will end without an error message. You can view this script for examples of how to utilize DTNGen.

### DTN CLA
DTN CLA has several scripts used for self-tests. Run using the same syntax as the example below:

    python -m examples.dtncla.sender
