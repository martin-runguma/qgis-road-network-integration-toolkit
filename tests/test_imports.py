# -*- coding: utf-8 -*-
"""Every plugin module must import cleanly on both emulated QGIS API styles."""

import unittest

import qgis_stubs
from _pkg import import_plugin

MODULES = (
    "core.compat", "core.configuration", "core.datasource_utils", "core.legacy_engine",
    "core.controller", "core.background_task", "algorithms.methodology_1",
    "algorithms.methodology_2", "algorithms.methodology_3", "gui.main_dialog",
    "road_network_integration_toolkit",
)


class ImportSmokeTests(unittest.TestCase):
    def _check(self, style):
        qgis_stubs.install(style)
        for name in MODULES:
            with self.subTest(style=style, module=name):
                import_plugin(name)

    def test_legacy(self):
        self._check("legacy")

    def test_modern(self):
        self._check("modern")

    def test_dialog_geometry_kind_mapping(self):
        for style in ("legacy", "modern"):
            qgis_stubs.install(style)
            dialog = import_plugin("gui.main_dialog")
            with self.subTest(style=style):
                self.assertEqual(dialog.geometry_kind_of("line"), "line")
                self.assertEqual(dialog.geometry_kind_of("poly"), "polygon")
                self.assertEqual(dialog.geometry_kind_of("pt"), "point")
                self.assertEqual(dialog.geometry_kind_of("null"), "none")
                self.assertEqual(dialog.geometry_kind_of("???"), "unknown")

    def test_dialog_pure_helpers(self):
        qgis_stubs.install("modern")
        dialog = import_plugin("gui.main_dialog")
        self.assertEqual(dialog.utm_epsg_for(36.8, -1.3), (32737, 37, "S"))
        self.assertEqual(dialog.utm_epsg_for(-0.1, 51.5), (32630, 30, "N"))
        self.assertEqual(dialog.invalid_name_chars("a:b?c"), [":", "?"])


if __name__ == "__main__":
    unittest.main()
