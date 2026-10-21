# -*- coding: utf-8 -*-
"""The compat layer must resolve correctly on both legacy (3.28) and modern (4.x) APIs."""

import unittest

import qgis_stubs
from _pkg import import_plugin


class _Base:
    style = None

    def setUp(self):
        self.stub = qgis_stubs.install(self.style)
        self.compat = import_plugin("core.compat")

    def test_geometry_constants_resolve(self):
        c = self.compat
        self.assertEqual(
            (c.POINT_GEOMETRY, c.LINE_GEOMETRY, c.POLYGON_GEOMETRY, c.NULL_GEOMETRY),
            ("pt", "line", "poly", "null"),
        )

    def test_units_writer_and_message_enums(self):
        c = self.compat
        self.assertEqual(c.METERS, "metres")
        self.assertEqual(c.WRITER_NO_ERROR, 0)
        self.assertEqual(c.ACTION_CREATE_OR_OVERWRITE_FILE, 1)
        self.assertEqual(c.ACTION_CREATE_OR_OVERWRITE_LAYER, 2)
        self.assertEqual(c.MSG_CRITICAL, "critical")

    def test_make_field_all_kinds(self):
        for kind, length in (("int", 0), ("longlong", 0), ("double", 0), ("string", 32)):
            field = self.compat.make_field("f_" + kind, kind, length=length)
            self.assertEqual(field.name(), "f_" + kind)
            self.assertEqual(field.length(), length)

    def test_make_field_rejects_unknown_kind(self):
        with self.assertRaises(ValueError):
            self.compat.make_field("x", "blob")

    def test_make_field_type_is_cached_after_first_success(self):
        self.compat.make_field("a", "string")
        self.assertIn("string", self.compat._field_type_cache)

    def test_qaction_resolved_from_either_module(self):
        self.assertIs(self.compat.QAction, self.stub.QAction)

    def test_is_null_and_clean_text(self):
        c = self.compat
        from qgis.core import NULL
        self.assertTrue(c.is_null(None))
        self.assertTrue(c.is_null(NULL))
        self.assertFalse(c.is_null("missing_1"))
        self.assertFalse(c.is_null(0))
        self.assertEqual(c.clean_text(NULL), "")
        self.assertEqual(c.clean_text(None), "")
        self.assertEqual(c.clean_text("missing_2"), "missing_2")

    def test_runtime_summary_mentions_qgis_and_qt(self):
        text = self.compat.runtime_summary()
        self.assertIn("QGIS", text)
        self.assertIn("Qt", text)


class LegacyApiTests(_Base, unittest.TestCase):
    style = "legacy"

    def test_field_falls_back_to_qvariant(self):
        # QGIS 3.28 rejects QMetaType constants, so QVariant must have been used.
        field = self.compat.make_field("a", "int")
        self.assertEqual(type(field.type()).__name__, "VariantEnum")


class ModernApiTests(_Base, unittest.TestCase):
    style = "modern"

    def test_field_uses_qmetatype(self):
        field = self.compat.make_field("a", "string")
        self.assertEqual(type(field.type()).__name__, "MetaEnum")
        self.assertEqual(field.type().name, "QString")


if __name__ == "__main__":
    unittest.main()
