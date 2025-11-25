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

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from datetime import datetime

project = "dtntools"
copyright = f"{datetime.now().year}, NASA GSFC"
author = "NASA GSFC"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["autoapi.extension"]
autoapi_dirs = ["../../dtntools/"]

templates_path = ["_templates"]
exclude_patterns = []

autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


def skip_what(app, what, name, obj, skip, options):
    """Skip documenting certain features."""
    what_name = name.split(".")[-1]

    # Don't skip __init__ methods
    if what == "method" and what_name == "__init__":
        skip = False

    return skip


def setup(sphinx):
    """Connect the auto-skip-member function."""
    sphinx.connect("autoapi-skip-member", skip_what)
