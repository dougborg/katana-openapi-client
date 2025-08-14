"""
Configuration file for the Sphinx documentation builder.

This file contains the configuration for generating API documentation from
the katana-openapi-client codebase.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# -- Project information -----------------------------------------------------
project = "katana-openapi-client"
copyright = "2025, Doug Borg"
author = "Doug Borg"

# Get version from package
try:
    from katana_public_api_client import __version__

    version = __version__
    release = __version__
except ImportError:
    version = "0.1.0"
    release = "0.1.0"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "autoapi.extension",
    "myst_parser",
]

# AutoAPI configuration
autoapi_dirs = ["../katana_public_api_client"]
autoapi_type = "python"
autoapi_template_dir = "_templates"
autoapi_generate_api_docs = True
autoapi_add_toctree_entry = True
autoapi_member_order = "groupwise"
# Use "init" to only document __init__ method docstrings, avoiding
# duplication between class docstring attributes and type annotations
autoapi_python_class_content = "init"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]
autoapi_keep_files = False

# Exclude only tests and cache files from AutoAPI, include generated client
autoapi_ignore = [
    "**/test*",
    "**/conftest.py",
    "**/__pycache__/**/*",
    "**/.*",
    # Ignore specific problematic modules that cause KeyError
    "**/generated/**",
]

# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
html_theme_options = {
    "canonical_url": "",
    "analytics_id": "",
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    "style_nav_header_background": "white",
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "relations.html",
        "searchbox.html",
        "donate.html",
    ]
}

# -- Options for intersphinx extension ---------------------------------------
# Disabled due to network access limitations in build environment
# intersphinx_mapping = {
#     "python": ("https://docs.python.org/3/", None),
#     "httpx": ("https://www.python-httpx.org/", None),
#     "attrs": ("https://www.attrs.org/en/stable/", None),
# }

# -- Options for autodoc extension ------------------------------------------

# This value selects what content will be inserted into the main body of an autoclass directive.
autoclass_content = "both"

# This value is a list of autodoc directive flags that should be automatically applied to all autodoc directives.
autodoc_default_flags = [
    "members",
    "undoc-members",
    "show-inheritance",
]

# This value controls the behavior of sphinx.ext.autodoc-skip-member event.
autodoc_member_order = "groupwise"

# Controls whether functions documented by autodoc show their return type annotations.
autodoc_typehints = "description"

# -- Source file parsers -----------------------------------------------------

# MyST parser configuration
myst_enable_extensions = [
    "deflist",
    "tasklist",
    "colon_fence",
    "smartquotes",
    "replacements",
    "strikethrough",
    "fieldlist",
]

# MyST heading anchors
myst_heading_anchors = 3

# Source file suffixes
source_suffix = {
    ".rst": None,
    ".md": None,
}

# -- Custom configuration ---------------------------------------------------

# Master document (entry point)
master_doc = "index"

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# -- Build environment ------------------------------------------------------

# Set environment variables for documentation builds
os.environ["SPHINX_BUILD"] = "1"
