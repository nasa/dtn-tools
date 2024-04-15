from setuptools import find_packages, setup

from dtngen import __version__

# Package metadata
name = "dtngen"
version = str(__version__)
description = "Generates and interpretes DTN bundles"

# Package dependencies
dependencies = ["cbor2>=5.6.2", "crccheck>=1.3.0"]

# Development dependencies
dev_dependencies = {"dev": ["pre-commit", "sphinx-autoapi", "sphinx-rtd-theme"]}

# Package setup
setup(
    name=name,
    version=version,
    description=description,
    packages=find_packages(),
    install_requires=dependencies,
    extras_require=dev_dependencies,
)
