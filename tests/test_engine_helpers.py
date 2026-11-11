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


    # -- skipped-event reporting ---------------------------------------------
    def test_events_are_counted_and_logged_once_per_kind(self):
        engine = self.engine
        engine._WORKER_STATE.events = {}
        engine._note_event("thing A failed")
        engine._note_event("thing A failed")
        engine._note_event("thing B failed")
        lines = []

        class Log:
            def warning(self, message):
                lines.append(message)

        engine._log_events(Log())
        self.assertEqual(len(lines), 2)
        self.assertIn("thing A failed (2 times)", lines[0])
        self.assertIn("thing B failed (1 time)", lines[1])

    def test_no_events_means_no_log_noise(self):
        self.engine._WORKER_STATE.events = {}
        lines = []

        class Log:
            def warning(self, message):
                lines.append(message)

        self.engine._log_events(Log())
        self.assertEqual(lines, [])

    # -- buffer end-cap helper -------------------------------------------------
    def test_cap_candidates_never_raise_when_enums_are_missing(self):
        self.assertIsInstance(self.engine._cap_join_candidates("Flat"), list)

    def test_cap_candidates_find_new_and_old_enum_spellings(self):
        engine = self.engine

        class NS:
            def __init__(self, **kw):
                self.__dict__.update(kw)

        new_style = NS(EndCapStyle=NS(Flat="new-flat", Square="new-square"), JoinStyle=NS(Round="new-round"))
        old_style = NS(EndCapStyle=NS(CapFlat="old-flat", CapSquare="old-square"), JoinStyle=NS(JoinRound="old-round"))
        engine.Qgis, engine.QgsGeometry = new_style, NS()
        self.assertEqual(engine._cap_join_candidates("Flat"), [("new-flat", "new-round")])
        engine.Qgis, engine.QgsGeometry = NS(), old_style
        self.assertEqual(engine._cap_join_candidates("Square"), [("old-square", "old-round")])
        engine.Qgis, engine.QgsGeometry = new_style, old_style
        self.assertEqual(len(engine._cap_join_candidates("Flat")), 2)

    def test_buffer_falls_back_loudly_not_silently(self):
        engine = self.engine
        engine._WORKER_STATE.events = {}
        calls = []

        class Geometry:
            def buffer(self, *args):
                calls.append(args)
                return "buffered"

        # With no usable cap enums on the stub, the plain buffer is used AND recorded.
        self.assertEqual(engine._buffer_with_caps(Geometry(), 10, 8, "Flat"), "buffered")
        self.assertEqual(calls[-1], (10.0, 8))
        self.assertTrue(any("round-cap" in key for key in engine._WORKER_STATE.events))

    def test_buffer_uses_first_cap_style_that_works(self):
        engine = self.engine
        engine._WORKER_STATE.events = {}
        engine._cap_join_candidates = lambda name: [("bad-cap", "j"), ("good-cap", "j")]

        class Geometry:
            def buffer(self, distance, segments, cap=None, join=None, miter=None):
                if cap == "bad-cap":
                    raise TypeError("wrong enum")
                return ("ok", cap)

        self.assertEqual(engine._buffer_with_caps(Geometry(), 5, 8, "Flat"), ("ok", "good-cap"))
        self.assertEqual(engine._WORKER_STATE.events, {})

    def test_geometry_errors_are_narrow(self):
        # A KeyError is a bug and must not be swallowed like a geometry failure.
        self.assertNotIn(KeyError, self.engine._GEOMETRY_ERRORS)
        self.assertIn(RuntimeError, self.engine._GEOMETRY_ERRORS)


class LegacyEngineTests(_EngineBase, unittest.TestCase):
    style = "legacy"


class ModernEngineTests(_EngineBase, unittest.TestCase):
    style = "modern"


if __name__ == "__main__":
    unittest.main()
