# -*- coding: utf-8 -*-
"""Pure-Python helpers of the engine, exercised on both emulated API styles."""

import unittest

import qgis_stubs
from _pkg import import_plugin


class _Layer:
    def __init__(self, field_objects):
        self._fields = field_objects

    def fields(self):
        return list(self._fields)


class _EngineBase:
    style = None

    def setUp(self):
        self.stub = qgis_stubs.install(self.style)
        self.engine = import_plugin("core.legacy_engine")

    def _fields(self, *names):
        return [self.engine.make_field(n, "string") for n in names]

    # -- dataset labels ------------------------------------------------------
    def test_label_from_file_name(self):
        label = self.engine._dataset_label
        self.assertEqual(label("C:/data/ms_roads.gpkg", "X"), "MS")
        self.assertEqual(label("C:/data/Microsoft_Roads.shp", "X"), "MS")
        self.assertEqual(label("C:/data/osm_roads.gpkg", "X"), "OSM")
        self.assertEqual(label("C:/data/roads.gpkg|layername=OpenStreetMap_lines", "X"), "OSM")

    def test_label_from_layer_name_inside_container(self):
        self.assertEqual(self.engine._dataset_label("C:/d/Kenya.gdb|layername=ms_roads", "X"), "MS")

    def test_label_ignores_unrelated_ancestor_folders(self):
        label = self.engine._dataset_label
        # Regression: these used to be labelled OSM / MS because of the folder path.
        self.assertEqual(label("C:/Projects/OSM_Toolkit/outputs/city_roads.gpkg", "BASE"), "CITY_ROADS")
        self.assertEqual(label("C:/Users/ms/Documents/a/b/nairobi.shp", "BASE"), "NAIROBI")

    def test_label_uses_immediate_parent_folder(self):
        label = self.engine._dataset_label
        self.assertEqual(label("D:/data/MS/roads.shp", "BASE"), "MS")
        self.assertEqual(label("D:/data/OSM/roads.shp", "BASE"), "OSM")

    def test_label_fallback(self):
        self.assertEqual(self.engine._dataset_label("", "BASE"), "BASE")
        self.assertEqual(self.engine._dataset_label("C:/x/roads.shp", "SECONDARY"), "SECONDARY")

    # -- input schema ----------------------------------------------------------
    def test_schema_renames_reserved_names_and_keeps_values_mapping(self):
        layer = _Layer(self._fields("fid", "OBJECTID", "ogc_fid", "name", "source", "geom"))
        fields, index_by_output = self.engine._input_schema(layer)
        names = [f.name() for f in fields]
        self.assertEqual(names, ["source_fid", "source_objectid", "source_ogc_fid", "name", "Src_Old", "source_geom"])
        # each output field still points at its original column
        self.assertEqual(index_by_output["source_fid"], 0)
        self.assertEqual(index_by_output["src_old"], 4)

    def test_schema_drops_stale_geometry_measures_and_coverage_fields(self):
        layer = _Layer(self._fields("Shape_Length", "Shape_Area", "name", "Missing_Class", "coverage_ratio"))
        names = [f.name() for f in self.engine._input_schema(layer)[0]]
        self.assertEqual(names, ["name"])

    def test_schema_handles_existing_source_fid(self):
        layer = _Layer(self._fields("fid", "source_fid"))
        names = [f.name() for f in self.engine._input_schema(layer)[0]]
        self.assertEqual(len(names), len(set(n.casefold() for n in names)))
        self.assertIn("source_fid", names)

    # -- cancellation ----------------------------------------------------------
    def test_cancel_checkpoint(self):
        calls = []

        class Log:
            def check_cancelled(self):
                calls.append(1)
                raise self_engine.OperationCancelled("stop")

        self_engine = self.engine
        self.engine._tick(Log(), 1, every=250)      # not on a checkpoint
        self.assertEqual(calls, [])
        with self.assertRaises(self.engine.OperationCancelled):
            self.engine._tick(Log(), 250, every=250)
        self.engine._check_cancel(None)             # loggers without the hook are fine
        self.engine._check_cancel(lambda m: None)


class LegacyEngineTests(_EngineBase, unittest.TestCase):
    style = "legacy"


class ModernEngineTests(_EngineBase, unittest.TestCase):
    style = "modern"


if __name__ == "__main__":
    unittest.main()
