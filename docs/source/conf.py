# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from datetime import datetime

project = "dtngen"
copyright = f"{datetime.now().year}, NASA GSFC"
author = "NASA GSFC"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["autoapi.extension"]
autoapi_dirs = ["../../dtngen"]

templates_path = ["_templates"]
exclude_patterns = []

autoapi_options = [ 'members', 'undoc-members', 'private-members', 'show-inheritance-diagram', 'show-module-summary', 'imported-members', ]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


def skip_what(app, what, name, obj, skip, options):
    """Skip documenting certain features."""
    # Usually, starting with _ indicates a desire for private implementation
    # This isn't perfect, but it's close enough
    what_name = name.split(".")[-1]
    
    if what == "data":
        if what_name.startswith("_"):
            skip = True

    if what == "function" or what == "method":
        if what_name.startswith("__") and what_name.endswith("__"):
            skip = False
        # Attempt at a "private" function
        elif what_name.startswith("_"):
            skip = True
    
    return skip


def setup(sphinx):
    """Connect the auto-skip-member function."""
    sphinx.connect("autoapi-skip-member", skip_what)
