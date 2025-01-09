from setuptools import find_packages, setup

from __version__ import __version__

# Package metadata
name = "dtntools"
version = str(__version__)
description = "GSFC DTN Test Tools Suite"

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
