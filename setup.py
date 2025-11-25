#
# NASA Docket No. GSC-19,559-1, and identified as "Delay/Disruption Tolerant Networking 
# (DTN) Bundle Protocol (BP) v7 Core Flight System (cFS) Application Build 7.0
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this 
# file except in compliance with the License. You may obtain a copy of the License at 
#
# http://www.apache.org/licenses/LICENSE-2.0 
#
# Unless required by applicable law or agreed to in writing, software distributed under 
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF 
# ANY KIND, either express or implied. See the License for the specific language 
# governing permissions and limitations under the License. The copyright notice to be 
# included in the software is as follows: 
#
# Copyright 2025 United States Government as represented by the Administrator of the 
# National Aeronautics and Space Administration. All Rights Reserved.
#
#
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
