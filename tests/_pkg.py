# -*- coding: utf-8 -*-
"""Shared test plumbing: locate the plugin package and import it by name."""

import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.basename(ROOT)
PARENT = os.path.dirname(ROOT)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)


def import_plugin(module_path=""):
    """Import ``<plugin package>[.module_path]`` (for example ``core.compat``)."""
    name = PKG + ("." + module_path if module_path else "")
    return importlib.import_module(name)


def purge_plugin_and_qgis_modules():
    """Forget the plugin and any (stub) qgis modules so the next import is fresh."""
    for name in list(sys.modules):
        if name == PKG or name.startswith(PKG + ".") or name == "qgis" or name.startswith("qgis."):
            del sys.modules[name]
