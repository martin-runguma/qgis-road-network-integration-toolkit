# -*- coding: utf-8 -*-
"""QGIS-native implementation of the finalized legacy road-merging workflow.

This module ports the Spyder/GeoPandas workflow into QGIS APIs so all processing
runs inside the QGIS Python environment. The GUI remains a thin configuration
and reporting layer. The three methodologies share the same data preparation,
priority-buffer coverage classification, and output routines.

Legacy behaviour retained
-------------------------
* Inputs are reprojected to the selected projected analysis CRS.
* The road inputs are clipped to the envelope of a 30 km buffer around the
  study-area boundary (the legacy BBOX_BUFFER_KM setting).
* Each priority road receives an individual buffer. Secondary coverage uses
  the legacy dominant-single-buffer overlap calculation, not a union-length
  calculation. The legacy classifier's exact 0.25 boundary remains unassigned.
* Methodology 1 directly merges only secondary features in missing_1..missing_4.
* Methodology 2 differences secondary missing_1..missing_4 by the dissolved
  priority buffer, creates priority-road anchors at MID_GAP_M spacing, snaps
  endpoints within JOIN_GAP_M, and writes progressive class merges.
* Methodology 3 trims the missing classes, builds square buffers from secondary
  road portions overlapping priority buffers, builds per-buffer base vertices,
  and applies centroid -> endpoint -> global-fallback snapping.

Only QGIS/PyQt APIs are required at runtime; GeoPandas, Shapely, pandas, NumPy,
matplotlib, tqdm, and the standalone Spyder environment are not required.
"""

import os
import re
import shutil
import threading
from contextlib import contextmanager
from collections import Counter, OrderedDict, defaultdict

from qgis.core import (
    Qgis,
    QgsCoordinateTransform,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsSpatialIndex,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
    QgsUnitTypes,
)

from .compat import (
    ACTION_CREATE_OR_OVERWRITE_FILE,
    ACTION_CREATE_OR_OVERWRITE_LAYER,
    LINE_GEOMETRY,
    METERS,
    WRITER_NO_ERROR,
    clean_text,
    make_field,
    runtime_summary,
)
from .datasource_utils import gdb_driver_name


# The legacy script uses a 30 km buffered-boundary envelope before overlay.
BBOX_BUFFER_M = 30000.0
MISSING_CLASSES = ("missing_1", "missing_2", "missing_3", "missing_4")
ALL_CLASS_ORDER = ("missing_1", "missing_2", "missing_3", "missing_4", "missing_a", "missing_b", "None")
COVERAGE_FIELDS = {
    "orig_length", "rem_length", "rem_pct", "missing_class", "ovl_len",
    "ovl_max", "coverage_ratio",
}
# Input attributes whose names collide with reserved columns of the output
# formats are kept under a safe name (values preserved):
#   fid / ogc_fid  - GeoPackage / OGR primary-key columns
#   objectid       - File Geodatabase primary key
#   geom / geometry - default GeoPackage geometry-column names
#   source         - the plugin's own provenance column (legacy "Src_Old")
RESERVED_FIELD_RENAMES = {
    "fid": "source_fid",
    "ogc_fid": "source_ogc_fid",
    "objectid": "source_objectid",
    "geom": "source_geom",
    "geometry": "source_geometry",
    "source": "Src_Old",
}
# Esri geometry-measure columns are reserved/auto-maintained in File
# Geodatabases and are stale once roads have been clipped or snapped, so they
# are not carried into the outputs.
STALE_GEOMETRY_FIELDS = {"shape_length", "shape_area", "shape"}


# QGIS project state must not be queried or mutated from a background task.
# The plugin captures a transform context on the GUI thread and installs it
# thread-locally while this engine runs in QgsTask. Direct/legacy callers that
# do not install a context retain the original QgsProject fallback behaviour.
_WORKER_STATE = threading.local()


@contextmanager
def worker_transform_context(context):
    """Provide a captured transform context to engine calls in a worker thread."""
    previous = getattr(_WORKER_STATE, "transform_context", None)
    _WORKER_STATE.transform_context = context
    try:
        yield
    finally:
        if previous is None:
            try:
                del _WORKER_STATE.transform_context
            except AttributeError:
                pass
        else:
            _WORKER_STATE.transform_context = previous


def _current_transform_context():
    """Return the worker's captured context or the live project context."""
    context = getattr(_WORKER_STATE, "transform_context", None)
    if context is not None:
        return context
    return QgsProject.instance().transformContext()


class OperationCancelled(RuntimeError):
    """Raised inside the engine when the user cancels the QGIS background task."""


def _check_cancel(log):
    """Abort cooperatively when the logger's owning task has been cancelled."""
    checker = getattr(log, "check_cancelled", None)
    if callable(checker):
        checker()


def _tick(log, counter, every=250):
    """Cheap periodic cancellation checkpoint for long feature loops."""
    if counter % every == 0:
        _check_cancel(log)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log(callback, message, level="info"):
    message = str(message)
    if callback is None:
        print("[Road Network Integration Toolkit] " + message)
        return
    method = getattr(callback, level, None)
    if callable(method):
        method(message)
    elif callable(callback):
        try:
            callback(message)
        except TypeError:
            print("[Road Network Integration Toolkit] " + message)
    else:
        print("[Road Network Integration Toolkit] " + message)


# ---------------------------------------------------------------------------
# Geometry and CRS helpers
# ---------------------------------------------------------------------------

def _metres_to_map_units(crs, distance_m):
    """Convert a GUI distance in metres to the units used by a projected CRS."""
    try:
        factor = QgsUnitTypes.fromUnitToUnitFactor(
            METERS, crs.mapUnits()
        )
    except Exception as exc:
        raise ValueError(
            "Could not convert metres to the selected analysis CRS units: {}".format(exc)
        ) from exc
    if not factor or factor <= 0:
        raise ValueError("The analysis CRS has unsupported distance units.")
    return float(distance_m) * float(factor)


def _map_units_to_metres(crs, distance_units):
    """Convert a geometry length in analysis-CRS units to metres."""
    try:
        factor = QgsUnitTypes.fromUnitToUnitFactor(
            crs.mapUnits(), METERS
        )
    except Exception as exc:
        raise ValueError(
            "Could not convert analysis CRS units to metres: {}".format(exc)
        ) from exc
    if not factor or factor <= 0:
        raise ValueError("The analysis CRS has unsupported distance units.")
    return float(distance_units) * float(factor)


def _memory_layer(name, geometry_type, crs, fields=()):
    authid = crs.authid()
    uri = "{}?crs={}".format(geometry_type, authid) if authid else geometry_type
    layer = QgsVectorLayer(uri, name, "memory")
    if not layer.isValid():
        raise RuntimeError("Could not create working layer '{}'.".format(name))
    # Custom/user-defined CRSs may not resolve from an authid string inside a
    # worker thread, so make sure the layer really carries the analysis CRS.
    if layer.crs() != crs:
        layer.setCrs(crs)
    if fields:
        layer.dataProvider().addAttributes([QgsField(f) for f in fields])
        layer.updateFields()
    return layer


def _transform_geometry(geometry, source_crs, target_crs, context=None):
    result = QgsGeometry(geometry)
    if result.isNull() or result.isEmpty() or source_crs == target_crs:
        return result
    context = context or _current_transform_context()
    transform = QgsCoordinateTransform(source_crs, target_crs, context)
    try:
        result.transform(transform)
    except Exception as exc:
        raise RuntimeError("Could not transform geometry from {} to {}: {}".format(
            source_crs.authid() or source_crs.description(),
            target_crs.authid() or target_crs.description(), exc
        )) from exc
    return result


def _make_valid(geometry):
    if geometry is None or geometry.isNull() or geometry.isEmpty():
        return QgsGeometry()
    result = QgsGeometry(geometry)
    try:
        if not result.isGeosValid():
            result = result.makeValid()
    except Exception:
        try:
            result = result.makeValid()
        except Exception:
            pass
    return result


def _line_parts(geometry):
    """Extract valid 2D line parts from line or geometry-collection results."""
    if geometry is None or geometry.isNull() or geometry.isEmpty():
        return []
    g = QgsGeometry(geometry)
    try:
        if QgsWkbTypes.geometryType(g.wkbType()) == LINE_GEOMETRY:
            raw = g.asMultiPolyline() if g.isMultipart() else [g.asPolyline()]
            return [[QgsPointXY(p) for p in line] for line in raw if line and len(line) >= 2]
    except Exception:
        pass
    # Difference/intersection operations can return a geometry collection.
    try:
        pieces = g.asGeometryCollection()
    except Exception:
        pieces = []
    out = []
    for piece in pieces:
        out.extend(_line_parts(piece))
    return out


def _line_geometry(geometry_or_parts, force_multi=True):
    if isinstance(geometry_or_parts, QgsGeometry):
        parts = _line_parts(geometry_or_parts)
    else:
        parts = geometry_or_parts
    parts = [part for part in parts if part and len(part) >= 2]
    if not parts:
        return QgsGeometry()
    if force_multi:
        out = QgsGeometry.fromMultiPolylineXY(parts)
    elif len(parts) == 1:
        out = QgsGeometry.fromPolylineXY(parts[0])
    else:
        out = QgsGeometry.fromMultiPolylineXY(parts)
    return out


def _line_length(geometry):
    parts = _line_parts(geometry)
    total = 0.0
    for part in parts:
        try:
            total += QgsGeometry.fromPolylineXY(part).length()
        except Exception:
            continue
    return total


def _union(geometries):
    valid = [QgsGeometry(g) for g in geometries if g is not None and not g.isNull() and not g.isEmpty()]
    if not valid:
        return QgsGeometry()
    try:
        return QgsGeometry.unaryUnion(valid)
    except Exception:
        result = QgsGeometry(valid[0])
        for geometry in valid[1:]:
            result = result.combine(geometry)
        return result


def _safe_intersection(first, second):
    try:
        result = first.intersection(second)
        if result.isNull():
            return QgsGeometry()
        return result
    except Exception:
        try:
            first_valid = _make_valid(first)
            second_valid = _make_valid(second)
            return first_valid.intersection(second_valid)
        except Exception:
            return QgsGeometry()


def _safe_difference(first, second):
    try:
        result = first.difference(second)
        if result.isNull():
            return QgsGeometry()
        return result
    except Exception:
        try:
            return _make_valid(first).difference(_make_valid(second))
        except Exception:
            return QgsGeometry()


def _copy_attrs(feature, field_count):
    return [feature[i] for i in range(min(field_count, len(feature.attributes())))]


def _add_features(layer, features):
    if features:
        ok, _ = layer.dataProvider().addFeatures(features)
        if not ok:
            raise RuntimeError("Could not add features to working layer '{}'.".format(layer.name()))
        layer.updateExtents()


def _write_layer(layer, path, layer_name=None, first=False, log=None):
    """Write/replace one vector layer in a GeoPackage."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = "GPKG"
    opts.layerName = layer_name or layer.name()
    opts.fileEncoding = "UTF-8"
    exists = os.path.exists(path)
    opts.actionOnExistingFile = (
        ACTION_CREATE_OR_OVERWRITE_LAYER
        if exists and not first
        else ACTION_CREATE_OR_OVERWRITE_FILE
    )
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, path, _current_transform_context(), opts
    )
    if result[0] != WRITER_NO_ERROR:
        raise RuntimeError("Could not write '{}' to '{}': {}".format(opts.layerName, path, result[1]))
    _log(log, "Saved intermediate layer '{}' → {}".format(opts.layerName, path))
    return path


def _remove_output(path, kind):
    """Remove existing output files so overwrite behaviour matches legacy config."""
    if kind == "gdb":
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.exists(path):
            os.remove(path)
        return
    if kind == "shp":
        root, _ = os.path.splitext(path)
        for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg", ".qix", ".sbn", ".sbx"):
            candidate = root + ext
            if os.path.exists(candidate):
                try:
                    os.remove(candidate)
                except OSError:
                    pass
        return
    for candidate in (path, path + "-wal", path + "-shm", path + "-journal"):
        if os.path.exists(candidate):
            try:
                os.remove(candidate)
            except OSError:
                pass


def _write_final(layer, configuration, log=None):
    path = configuration.output_path
    kind = configuration.output_type.lower()
    layer_name = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    # GUI callers may still use the engine synchronously. In a QgsTask, do not
    # query/mutate QgsProject from the worker: matching loaded layers are
    # released by the dialog on the main thread before the task starts.
    if getattr(_WORKER_STATE, "transform_context", None) is None:
        target_path = os.path.normcase(os.path.abspath(os.path.normpath(path)))
        for project_layer in list(QgsProject.instance().mapLayers().values()):
            try:
                source_path = project_layer.source().split("|", 1)[0]
                source_path = os.path.normcase(os.path.abspath(os.path.normpath(source_path)))
                if source_path == target_path:
                    QgsProject.instance().removeMapLayer(project_layer.id())
                    _log(log, "Released previously loaded output layer '{}' before overwriting.".format(
                        project_layer.name()))
            except Exception:
                continue
    else:
        _log(log, "Output layer handles were checked on the GUI thread before background processing.")
    if kind == "gpkg":
        driver = "GPKG"
    elif kind == "shp":
        driver = "ESRI Shapefile"
    elif kind == "gdb":
        driver = gdb_driver_name()
        if driver is None:
            # Fail before anything is deleted: this GDAL build cannot create
            # File Geodatabases (OpenFileGDB gained write support in GDAL 3.6).
            raise RuntimeError(
                "This QGIS/GDAL build cannot create File Geodatabases. "
                "Choose GeoPackage output instead."
            )
    else:
        raise ValueError("Unsupported output type: {}".format(kind))
    _remove_output(path, kind)

    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = driver
    opts.layerName = layer_name
    opts.fileEncoding = "UTF-8"
    opts.actionOnExistingFile = ACTION_CREATE_OR_OVERWRITE_FILE
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, path, _current_transform_context(), opts
    )
    if result[0] != WRITER_NO_ERROR:
        raise RuntimeError("Final export to '{}' failed: {}".format(path, result[1]))

    if kind == "gpkg":
        uri = "{}|layername={}".format(path, layer_name)
    elif kind == "gdb":
        uri = "{}|layername={}".format(path, layer_name)
    else:
        uri = path
    output_layer = QgsVectorLayer(uri, layer_name, "ogr")
    if not output_layer.isValid():
        raise RuntimeError("The file was written, but QGIS could not reopen it: {}".format(uri))
    _log(log, "Final harmonized network written to {}".format(path), "success")
    return path, output_layer


def _dataset_label(uri, fallback):
    """Infer the OSM/MS label used in legacy output provenance from a datasource.

    Only the file name, the selected layer name and the *immediate* parent folder
    are inspected. Earlier versions searched the whole path, so any input stored
    under a folder such as ``.../OSM_project/...`` or ``C:/Users/ms/...`` was
    labelled OSM/MS regardless of what it contained.
    """
    raw = str(uri or "")
    path_part = raw.split("|", 1)[0].strip().strip("\"\'").replace("\\", "/")
    layer_match = re.search(r"layername=([^|]+)", raw, re.IGNORECASE)
    layer_name = layer_match.group(1) if layer_match else ""
    stem = os.path.splitext(os.path.basename(path_part.rstrip("/")))[0]
    parent = os.path.basename(os.path.dirname(path_part.rstrip("/")))
    text = " ".join((stem, layer_name, parent)).lower()
    tokens = set(re.split(r"[^a-z0-9]+", text))
    if "microsoft" in text or "ms" in tokens:
        return "MS"
    if "openstreetmap" in text or "osm" in text:
        return "OSM"
    # Preserve a useful source label if users are working with other data.
    words = re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_").upper()
    if words and words not in ("ROADS", "ROAD", "ROAD_NETWORK", "PRIORITY_ROADS", "SECONDARY_ROADS"):
        return words[:32]
    return fallback


def _unique_renamed_field(fields, wanted):
    names = {f.name().casefold() for f in fields}
    if wanted.casefold() not in names:
        return wanted
    suffix = 1
    while "{}_{}".format(wanted, suffix).casefold() in names:
        suffix += 1
    return "{}_{}".format(wanted, suffix)


def _input_schema(layer):
    """Copy input fields, rename old source, and discard stale coverage fields."""
    fields = []
    source_index_by_output = {}
    for idx, field in enumerate(layer.fields()):
        key = field.name().casefold()
        if key in COVERAGE_FIELDS or key in STALE_GEOMETRY_FIELDS:
            continue
        copied = QgsField(field)
        # GeoPackage reserves the column name ``fid`` for its unique feature
        # primary key. Some OSM/MS sources expose their own source identifier
        # as an ordinary attribute also named ``fid``. Keeping that name when
        # combining two sources (or splitting one road into several line parts)
        # makes the writer attempt to insert duplicate primary keys. Rename the
        # source attribute during preparation, preserving its values while
        # letting the destination GeoPackage generate fresh unique feature IDs.
        if key in RESERVED_FIELD_RENAMES:
            copied.setName(_unique_renamed_field(fields, RESERVED_FIELD_RENAMES[key]))
        # QGIS layers from unusual formats can include duplicate aliases. Do not
        # create a second indistinguishable output field.
        if copied.name().casefold() in {f.name().casefold() for f in fields}:
            copied.setName(_unique_renamed_field(fields, copied.name()))
        fields.append(copied)
        source_index_by_output[copied.name().casefold()] = idx
    return fields, source_index_by_output


def _prepare_line_layer(source, target_crs, clip_geometry, name, log=None):
    """Reproject, crop to the legacy buffered-boundary envelope, and clean roads."""
    fields, origin_indices = _input_schema(source)
    out = _memory_layer(name, "MultiLineString", target_crs, fields)
    features = []
    skipped = 0
    processed = source.featureCount()
    context = _current_transform_context()
    for position, feature in enumerate(source.getFeatures(), start=1):
        _tick(log, position, 250)
        geometry = _transform_geometry(feature.geometry(), source.crs(), target_crs, context)
        geometry = _make_valid(geometry)
        parts = _line_parts(geometry)
        if not parts:
            skipped += 1
            continue
        geometry = _line_geometry(parts)
        if clip_geometry is not None and not clip_geometry.isNull() and not clip_geometry.isEmpty():
            try:
                if not clip_geometry.contains(geometry):
                    if not clip_geometry.intersects(geometry):
                        skipped += 1
                        continue
                    geometry = _safe_intersection(geometry, clip_geometry)
                    parts = _line_parts(geometry)
                    if not parts:
                        skipped += 1
                        continue
                    geometry = _line_geometry(parts)
            except Exception:
                geometry = _safe_intersection(geometry, clip_geometry)
                parts = _line_parts(geometry)
                if not parts:
                    skipped += 1
                    continue
                geometry = _line_geometry(parts)
        if geometry.isNull() or geometry.isEmpty() or _line_length(geometry) <= 0:
            skipped += 1
            continue
        nf = QgsFeature(out.fields())
        nf.setGeometry(geometry)
        values = []
        for field in out.fields():
            origin_idx = origin_indices.get(field.name().casefold())
            values.append(feature[origin_idx] if origin_idx is not None else None)
        nf.setAttributes(values)
        features.append(nf)
    _add_features(out, features)
    _log(log, "{}: kept {:,} of {:,} road features after reprojection/cleaning{}.".format(
        name, len(features), processed,
        "; skipped {:,} empty, invalid, non-line, or out-of-area features".format(skipped) if skipped else ""
    ))
    return out


def _prepare_area(study_area, target_crs, log=None):
    geoms = []
    context = _current_transform_context()
    for feature in study_area.getFeatures():
        g = _transform_geometry(feature.geometry(), study_area.crs(), target_crs, context)
        g = _make_valid(g)
        if not g.isNull() and not g.isEmpty():
            geoms.append(g)
    union = _union(geoms)
    if union.isNull() or union.isEmpty():
        raise ValueError("The study-area layer has no usable polygon geometry.")
    # The legacy script buffered the boundary by 30 km and clipped road layers
    # to that buffered geometry's envelope to reduce edge effects.
    expanded = union.buffer(_metres_to_map_units(target_crs, BBOX_BUFFER_M), 8)
    clip_geometry = QgsGeometry.fromRect(expanded.boundingBox())
    _log(log, "Study area prepared; roads will be clipped to the boundary's {:.0f} km buffered envelope.".format(BBOX_BUFFER_M / 1000.0))
    return union, clip_geometry


# ---------------------------------------------------------------------------
# Buffer generation and legacy coverage classification
# ---------------------------------------------------------------------------

def _flat_buffer(geometry, distance, segments=8):
    """Buffer a line with flat ends, matching Shapely ``cap_style=2``.

    The legacy preparation used flat-ended priority-road buffers. QGIS uses
    explicit cap/join enums for this overload, so support both current and
    older enum locations before falling back to the provider default.
    """
    attempts = []
    try:
        attempts.append((Qgis.EndCapStyle.Flat, Qgis.JoinStyle.Round))
    except Exception:
        pass
    try:
        attempts.append((QgsGeometry.EndCapStyle.Flat, QgsGeometry.JoinStyle.Round))
    except Exception:
        pass
    try:
        attempts.append((QgsGeometry.CapFlat, QgsGeometry.JoinStyle.Round))
    except Exception:
        pass
    for cap, join in attempts:
        try:
            return geometry.buffer(float(distance), int(segments), cap, join, 2.0)
        except Exception:
            continue
    return geometry.buffer(float(distance), int(segments))


def _create_priority_buffers(priority_roads, distance, log=None):
    crs = priority_roads.crs()
    layer = _memory_layer(
        "Priority_Buffer_Individual", "MultiPolygon", crs,
        [make_field("source_fid", "longlong"), make_field("buffer_m", "double")]
    )
    features = []
    for position, road in enumerate(priority_roads.getFeatures(), start=1):
        _tick(log, position, 500)
        g = road.geometry()
        if g.isNull() or g.isEmpty() or _line_length(g) <= 0:
            continue
        try:
            buffer = _flat_buffer(g, _metres_to_map_units(crs, float(distance)), segments=8)
        except Exception:
            continue
        if buffer.isNull() or buffer.isEmpty():
            continue
        if not buffer.isMultipart():
            buffer.convertToMultiType()
        nf = QgsFeature(layer.fields())
        nf.setGeometry(buffer)
        nf.setAttributes([int(road.id()), float(distance)])
        features.append(nf)
    _add_features(layer, features)
    if not features:
        raise ValueError("No priority-road buffers could be created. Check the input geometries and buffer distance.")

    # Use provider-assigned IDs in the spatial index; this works even if the
    # memory provider normalizes feature IDs during insertion.
    index = QgsSpatialIndex()
    buffers_by_id = {}
    for feature in layer.getFeatures():
        index.addFeature(feature)
        buffers_by_id[feature.id()] = QgsGeometry(feature.geometry())
    dissolved = _union(list(buffers_by_id.values()))
    dissolved_layer = _memory_layer(
        "Priority_Buffer_Dissolved", "MultiPolygon", crs,
        [make_field("buffer_count", "longlong"), make_field("buffer_m", "double")]
    )
    if not dissolved.isNull() and not dissolved.isEmpty():
        if not dissolved.isMultipart():
            dissolved.convertToMultiType()
        df = QgsFeature(dissolved_layer.fields())
        df.setGeometry(dissolved)
        df.setAttributes([len(buffers_by_id), float(distance)])
        _add_features(dissolved_layer, [df])
    _log(log, "Created {:,} individual priority-road buffers ({} m); dissolved mask prepared.".format(
        len(buffers_by_id), float(distance)))
    return layer, buffers_by_id, index, dissolved, dissolved_layer


def _legacy_classify(rem_ratio, cv_max=0.75, tolerance=0.99):
    """Exact classification conditions in the finalized legacy coverage module."""
    if rem_ratio <= (1.0 - tolerance):
        return "missing_a"
    if rem_ratio < (1.0 - cv_max):
        return "missing_b"
    if rem_ratio == 1.0:
        return "missing_1"
    if rem_ratio > 0.75:
        return "missing_2"
    if 0.50 < rem_ratio <= 0.75:
        return "missing_3"
    if 0.25 < rem_ratio <= 0.50:
        return "missing_4"
    # Exact 0.25 returns no class in the legacy implementation. This is kept
    # intentionally rather than silently changing classification boundaries.
    return None


def _coverage_values(road_geometry, buffers_by_id, buffer_index, length_to_m=1.0):
    original_length = _line_length(road_geometry)
    if road_geometry.isNull() or road_geometry.isEmpty() or original_length <= 0:
        return 0.0, 0.0, 1.0, None, "missing_1"

    candidate_ids = buffer_index.intersects(road_geometry.boundingBox())
    hits = []
    for buffer_id in candidate_ids:
        buffer = buffers_by_id.get(buffer_id)
        if buffer is None:
            continue
        try:
            if buffer.intersects(road_geometry):
                hits.append((buffer_id, buffer))
        except Exception:
            continue
    if not hits:
        return original_length * length_to_m, original_length * length_to_m, 1.0, None, "missing_1"

    # The legacy evaluator treated a road as fully covered when one individual
    # priority buffer covers it (not merely when the union covers it).
    for _, buffer in hits:
        covered = False
        try:
            covers_method = getattr(buffer, "covers", None)
            covered = bool(buffer.contains(road_geometry)) or bool(
                callable(covers_method) and covers_method(road_geometry)
            )
            # On QGIS builds without QgsGeometry.covers(), intersection-length
            # equality supplies a safe equivalent for line coverage, including
            # the rare case where the road lies on the buffer boundary.
            if not covered:
                overlap_geom = buffer.intersection(road_geometry)
                covered = (
                    not overlap_geom.isNull()
                    and abs(_line_length(overlap_geom) - original_length)
                    <= max(1e-8, original_length * 1e-10)
                )
        except Exception:
            covered = False
        if covered:
            return original_length * length_to_m, 0.0, 0.0, None, "missing_a"

    overlaps = []
    for _, buffer in hits:
        try:
            intersection = road_geometry.intersection(buffer)
            if not intersection.isNull() and not intersection.isEmpty():
                overlaps.append(float(intersection.length()))
        except Exception:
            continue
    max_overlap = max(overlaps) if overlaps else 0.0
    remaining_length = max(original_length - max_overlap, 0.0)
    remaining_ratio = remaining_length / original_length if original_length > 0 else 1.0
    overlap_text = str([round(value * length_to_m, 3) for value in overlaps])
    return (original_length * length_to_m, remaining_length * length_to_m, remaining_ratio,
            (overlap_text, max_overlap * length_to_m), _legacy_classify(remaining_ratio))


def _classified_secondary(secondary_roads, buffers_by_id, buffer_index, log=None):
    source_fields = list(secondary_roads.fields())
    names = {field.name().casefold() for field in source_fields}
    additions = [
        ("orig_length", "double", 0),
        ("rem_length", "double", 0),
        ("rem_pct", "double", 0),
        ("Missing_Class", "string", 32),
        ("ovl_len", "string", 0),
        ("ovl_max", "double", 0),
        ("coverage_ratio", "double", 0),
    ]
    for name, typ, length in additions:
        if name.casefold() not in names:
            source_fields.append(make_field(name, typ, length=length))
            names.add(name.casefold())
    out = _memory_layer(
        "Secondary_Coverage_Classified", "MultiLineString", secondary_roads.crs(), source_fields
    )
    result_features = []
    counts = Counter()
    total = secondary_roads.featureCount()
    length_to_m = QgsUnitTypes.fromUnitToUnitFactor(
        secondary_roads.crs().mapUnits(), METERS
    )
    for count, road in enumerate(secondary_roads.getFeatures(), start=1):
        geometry = road.geometry()
        orig_len, rem_len, ratio, overlap, cls = _coverage_values(
            geometry, buffers_by_id, buffer_index, length_to_m=length_to_m
        )
        ovl_text, max_overlap = (overlap if overlap is not None else (None, None))
        nf = QgsFeature(out.fields())
        nf.setGeometry(QgsGeometry(geometry))
        values = list(road.attributes())
        values.extend([
            orig_len, rem_len, ratio, cls, ovl_text, max_overlap,
            round(ratio, 3) if ratio is not None else None,
        ])
        # All stale coverage fields were removed during input preparation, so
        # the new values append in this exact order.
        nf.setAttributes(values)
        result_features.append(nf)
        counts[cls if cls is not None else "None"] += 1
        _tick(log, count, 200)
        if count % 5000 == 0:
            _log(log, "Coverage classification: {:,}/{:,} secondary roads processed.".format(count, total))
    _add_features(out, result_features)
    _log(log, "Coverage classification complete: {:,} roads.".format(total), "success")
    for cls in ALL_CLASS_ORDER:
        if counts.get(cls, 0):
            _log(log, "  {}: {:,}".format(cls, counts[cls]))
    return out


def _feature_value(feature, layer, field_name):
    index = next((i for i, field in enumerate(layer.fields()) if field.name().casefold() == field_name.casefold()), -1)
    if index < 0:
        return None
    try:
        return feature[index]
    except Exception:
        return None


def _clone_with_field(layer, name, field_name, field_type, default_value=None, field_len=0):
    """Clone a line layer and add one field if absent; values initially null."""
    fields = list(layer.fields())
    lookup = {f.name().casefold() for f in fields}
    if field_name.casefold() not in lookup:
        fields.append(make_field(field_name, field_type, length=field_len))
    out = _memory_layer(name, "MultiLineString", layer.crs(), fields)
    src_lookup = {f.name().casefold(): i for i, f in enumerate(layer.fields())}
    out_lookup = {f.name().casefold(): i for i, f in enumerate(out.fields())}
    feats = []
    for f in layer.getFeatures():
        nf = QgsFeature(out.fields())
        nf.setGeometry(QgsGeometry(f.geometry()))
        vals = [None] * len(out.fields())
        for key, src_idx in src_lookup.items():
            vals[out_lookup[key]] = f[src_idx]
        if field_name.casefold() not in src_lookup and default_value is not None:
            vals[out_lookup[field_name.casefold()]] = default_value
        nf.setAttributes(vals)
        feats.append(nf)
    _add_features(out, feats)
    return out


def _add_source_field(layer, label, include_coverage=True):
    fields = list(layer.fields())
    lower = {f.name().casefold() for f in fields}
    if include_coverage and "coverage_ratio" not in lower:
        fields.append(make_field("coverage_ratio", "double"))
        lower.add("coverage_ratio")
    if include_coverage and "missing_class" not in lower:
        fields.append(make_field("Missing_Class", "string", length=32))
        lower.add("missing_class")
    if "source" not in lower:
        fields.append(make_field("source", "string", length=64))
    out = _memory_layer(layer.name() + "_Tagged", "MultiLineString", layer.crs(), fields)
    old_lookup = {f.name().casefold(): i for i, f in enumerate(layer.fields())}
    out_lookup = {f.name().casefold(): i for i, f in enumerate(out.fields())}
    feats = []
    for f in layer.getFeatures():
        nf = QgsFeature(out.fields())
        nf.setGeometry(QgsGeometry(f.geometry()))
        vals = [None] * len(out.fields())
        for key, i in old_lookup.items():
            vals[out_lookup[key]] = f[i]
        vals[out_lookup["source"]] = label
        nf.setAttributes(vals)
        feats.append(nf)
    _add_features(out, feats)
    return out


# ---------------------------------------------------------------------------
# Output merge utilities
# ---------------------------------------------------------------------------

def _combine_layers(layers, crs, name, fields_override=None):
    """Combine road layers into a MultiLineString layer with unioned fields."""
    fields = []
    field_index = {}
    for layer in layers:
        if layer is None:
            continue
        for field in layer.fields():
            key = field.name().casefold()
            if key not in field_index:
                field_index[key] = len(fields)
                fields.append(QgsField(field))
    if fields_override is not None:
        fields = [QgsField(f) for f in fields_override]
        field_index = {f.name().casefold(): i for i, f in enumerate(fields)}
    out = _memory_layer(name, "MultiLineString", crs, fields)
    feats = []
    for layer in layers:
        if layer is None:
            continue
        lookup = {f.name().casefold(): i for i, f in enumerate(layer.fields())}
        for f in layer.getFeatures():
            g = QgsGeometry(f.geometry())
            parts = _line_parts(g)
            if not parts:
                continue
            nf = QgsFeature(out.fields())
            nf.setGeometry(_line_geometry(parts))
            vals = [None] * len(out.fields())
            for key, src_index in lookup.items():
                if key in field_index:
                    vals[field_index[key]] = f[src_index]
            nf.setAttributes(vals)
            feats.append(nf)
    _add_features(out, feats)
    return out


def _methodology_1(base_roads, classified_secondary, base_label, secondary_label, log=None):
    """Legacy direct merge: attributes simplified; geometry is not modified."""
    fields = [
        make_field("coverage_ratio", "double"),
        make_field("Missing_Class", "string", length=32),
        make_field("source", "string", length=64),
    ]
    base_out = _memory_layer("Base_Roads_M1", "MultiLineString", base_roads.crs(), fields)
    sec_out = _memory_layer("Missing_Secondary_M1", "MultiLineString", classified_secondary.crs(), fields)
    base_feats = []
    for f in base_roads.getFeatures():
        parts = _line_parts(f.geometry())
        if not parts:
            continue
        nf = QgsFeature(base_out.fields())
        nf.setGeometry(_line_geometry(parts))
        nf.setAttributes([None, None, base_label])
        base_feats.append(nf)
    _add_features(base_out, base_feats)

    class_index = next(i for i, field in enumerate(classified_secondary.fields()) if field.name().casefold() == "missing_class")
    ratio_index = next(i for i, field in enumerate(classified_secondary.fields()) if field.name().casefold() == "coverage_ratio")
    sec_feats = []
    for f in classified_secondary.getFeatures():
        cls = clean_text(f[class_index])
        if cls not in MISSING_CLASSES:
            continue
        parts = _line_parts(f.geometry())
        if not parts:
            continue
        nf = QgsFeature(sec_out.fields())
        nf.setGeometry(_line_geometry(parts))
        nf.setAttributes([f[ratio_index], cls, secondary_label])
        sec_feats.append(nf)
    _add_features(sec_out, sec_feats)
    merged = _combine_layers([base_out, sec_out], base_roads.crs(), "Merged_Road_Network_M1", fields_override=fields)
    _log(log, "Methodology 1: retained {:,} priority roads and added {:,} secondary roads in missing_1..missing_4.".format(
        base_out.featureCount(), sec_out.featureCount()), "success")
    return merged


def _spatial_index_for_points(point_geometries, target_crs):
    layer = _memory_layer("Point_Index", "Point", target_crs, [make_field("anchor_id", "longlong")])
    features = []
    for anchor_id, geom in enumerate(point_geometries):
        nf = QgsFeature(layer.fields())
        nf.setGeometry(QgsGeometry(geom))
        nf.setAttributes([anchor_id])
        features.append(nf)
    _add_features(layer, features)
    index = QgsSpatialIndex()
    geoms = {}
    for f in layer.getFeatures():
        index.addFeature(f)
        geoms[f.id()] = QgsGeometry(f.geometry())
    return index, geoms


def _nearest_point(point, index, point_geometries):
    try:
        nearest_ids = index.nearestNeighbor(QgsPointXY(point), 1)
    except Exception:
        nearest_ids = []
    if not nearest_ids:
        return None
    return point_geometries.get(nearest_ids[0])


def _densified_base_anchors(base_roads, interval, log=None, display_interval=None):
    """Reproduce the legacy endpoint/midpoint anchor construction."""
    anchors = []
    for position, feature in enumerate(base_roads.getFeatures(), start=1):
        _tick(log, position, 250)
        for part in _line_parts(feature.geometry()):
            line = QgsGeometry.fromPolylineXY(part)
            length = line.length()
            if length <= 0:
                continue
            if length <= interval:
                candidates = [QgsGeometry.fromPointXY(point) for point in part]
            else:
                distances = [0.0]
                distance = float(interval)
                while distance < length:
                    distances.append(distance)
                    distance += float(interval)
                # Shapely's normalized/interpolate pattern in the legacy code
                # includes the endpoint even when the interval does not land
                # exactly on the end. Add the true endpoint directly instead
                # of asking QgsGeometry.interpolate() for a distance beyond
                # the line's length (which may return a null geometry).
                distances.append(length)
                candidates = [line.interpolate(d) for d in distances]
            for point in candidates:
                if point is not None and not point.isNull() and not point.isEmpty():
                    anchors.append(QgsGeometry(point))
    # Dedup exact duplicate locations to reduce spatial-index overhead; every
    # legacy anchor has the same snapping effect when coordinates are identical.
    unique = OrderedDict()
    for geometry in anchors:
        point = geometry.asPoint()
        key = (round(point.x(), 8), round(point.y(), 8))
        if key not in unique:
            unique[key] = geometry
    anchors = list(unique.values())
    displayed_interval = interval if display_interval is None else display_interval
    _log(log, "Generated {:,} priority-road snap anchors at {:.2f} m spacing.".format(len(anchors), displayed_interval))
    return anchors


def _point_layer(name, crs, point_records, fields):
    layer = _memory_layer(name, "Point", crs, fields)
    features = []
    for geom, attrs in point_records:
        if geom is None or geom.isNull() or geom.isEmpty():
            continue
        nf = QgsFeature(layer.fields())
        nf.setGeometry(QgsGeometry(geom))
        nf.setAttributes(attrs)
        features.append(nf)
    _add_features(layer, features)
    return layer


def _trimmed_class_layer(classified_secondary, dissolved_mask, target_class=None, name="Trimmed_Secondary", log=None):
    fields = list(classified_secondary.fields())
    out = _memory_layer(name, "MultiLineString", classified_secondary.crs(), fields)
    class_idx = next((i for i, f in enumerate(classified_secondary.fields()) if f.name().casefold() == "missing_class"), -1)
    feats = []
    for position, f in enumerate(classified_secondary.getFeatures(), start=1):
        _tick(log, position, 250)
        cls = clean_text(f[class_idx]) if class_idx >= 0 else ""
        if target_class is not None and cls != target_class:
            continue
        if target_class is None and cls not in MISSING_CLASSES:
            continue
        g = _safe_difference(f.geometry(), dissolved_mask)
        parts = _line_parts(g)
        if not parts:
            continue
        nf = QgsFeature(out.fields())
        nf.setGeometry(_line_geometry(parts))
        nf.setAttributes(f.attributes())
        feats.append(nf)
    _add_features(out, feats)
    return out


def _with_snapped_field(layer, name="Snapped_Secondary"):
    return _clone_with_field(layer, name, "Snapped", "int")


def _snap_parts_to_anchors(geometry, anchor_index, anchor_geoms, max_distance):
    """Snap the first/last coordinate of every line part to nearest anchor."""
    parts = _line_parts(geometry)
    out_parts = []
    did_snap = False
    snap_events = 0
    for part in parts:
        coords = [QgsPointXY(p) for p in part]
        for endpoint_index in (0, len(coords) - 1):
            current = QgsGeometry.fromPointXY(coords[endpoint_index])
            nearest = _nearest_point(coords[endpoint_index], anchor_index, anchor_geoms)
            if nearest is None:
                continue
            if current.distance(nearest) <= max_distance:
                anchor_point = nearest.asPoint()
                coords[endpoint_index] = QgsPointXY(anchor_point)
                did_snap = True
                snap_events += 1
        out_parts.append(coords)
    return _line_geometry(out_parts), did_snap, snap_events


def _methodology_2(base_roads, classified_secondary, dissolved_mask, configuration, prefix, base_label, secondary_label, log=None):
    """Legacy Methodology 2: buffer difference + dense-anchor endpoint snapping."""
    _log(log, "Starting Methodology 2 — Clip + Snap Integration.", "info")
    target_crs = configuration.analysis_crs
    trimmed_by_class = OrderedDict()
    all_trimmed = []
    for cls in MISSING_CLASSES:
        class_layer = _trimmed_class_layer(
            classified_secondary, dissolved_mask, target_class=cls,
            name="Secondary_{}".format(cls), log=log
        )
        trimmed_by_class[cls] = class_layer
        all_trimmed.append(class_layer)
        _log(log, "{}: {:,} feature(s) remain after priority-buffer trimming.".format(cls, class_layer.featureCount()))

    anchors = _densified_base_anchors(
        base_roads, _metres_to_map_units(target_crs, configuration.mid_gap_m),
        log, display_interval=configuration.mid_gap_m
    )
    join_gap_units = _metres_to_map_units(target_crs, configuration.join_gap_m)
    anchor_index, anchor_geoms = _spatial_index_for_points(anchors, target_crs) if anchors else (QgsSpatialIndex(), {})
    anchor_layer = _point_layer(
        "Base_Vertices_Snap", target_crs,
        [(g, [i]) for i, g in enumerate(anchors)],
        [make_field("anchor_id", "longlong")],
    )

    snapped_by_class = OrderedDict()
    snap_stats = {}
    total_snapped = 0
    total_events = 0
    for cls, layer in trimmed_by_class.items():
        out = _with_snapped_field(layer, "Secondary_{}_Snapped".format(cls))
        snapped_idx = next(i for i, f in enumerate(out.fields()) if f.name().casefold() == "snapped")
        feats = []
        snapped_count = 0
        events_count = 0
        for position, f in enumerate(out.getFeatures(), start=1):
            _tick(log, position, 250)
            geometry = f.geometry()
            snapped_geometry, did_snap, events = _snap_parts_to_anchors(
                geometry, anchor_index, anchor_geoms, join_gap_units
            ) if anchors else (QgsGeometry(geometry), False, 0)
            if not snapped_geometry.isNull() and not snapped_geometry.isEmpty():
                nf = QgsFeature(out.fields())
                nf.setGeometry(snapped_geometry)
                attrs = list(f.attributes())
                attrs[snapped_idx] = 1 if did_snap else 0
                nf.setAttributes(attrs)
                feats.append(nf)
                snapped_count += int(did_snap)
                events_count += events
        # Rebuild rather than editing the same layer so the geometry/attribute
        # output is deterministic and safe to write using both QGIS 3.x APIs.
        clean = _memory_layer(out.name() + "_Final", "MultiLineString", target_crs, list(out.fields()))
        _add_features(clean, feats)
        snapped_by_class[cls] = clean
        snap_stats[cls] = snapped_count
        total_snapped += snapped_count
        total_events += events_count
        _log(log, "{}: {:,} retained, {:,} feature(s) snapped ({} endpoint events).".format(
            cls, clean.featureCount(), snapped_count, events_count))

    # The legacy script generated progressive versions of the merged network.
    progressive = OrderedDict()
    for upto, key in enumerate(MISSING_CLASSES, start=1):
        secondary_layers = [snapped_by_class[cls] for cls in MISSING_CLASSES[:upto]]
        progressive_name = "Merged_Base_{}".format("".join(str(i) for i in range(1, upto + 1)))
        progressive[key] = _combine_layers([base_roads] + secondary_layers, target_crs, progressive_name)

    final = progressive[MISSING_CLASSES[-1]]
    total_segments = sum(layer.featureCount() for layer in snapped_by_class.values())
    ratio = (100.0 * total_snapped / total_segments) if total_segments else 0.0
    _log(log, "Methodology 2 snapping summary: {}. Snapped {:,}/{:,} features ({:.2f}%).".format(
        dict(snap_stats), total_snapped, total_segments, ratio), "success")

    if configuration.keep_intermediates:
        gpkg = os.path.join(configuration.output_dir, "Intermediate_Files", "{}_M2_Output.gpkg".format(prefix))
        os.makedirs(os.path.dirname(gpkg), exist_ok=True)
        _remove_output(gpkg, "gpkg")
        first = True
        for name, layer in [
            ("Base_Vertices_Snap", anchor_layer),
            ("Secondary_Missing1_Snapped", snapped_by_class["missing_1"]),
            ("Secondary_Missing2_Snapped", snapped_by_class["missing_2"]),
            ("Secondary_Missing3_Snapped", snapped_by_class["missing_3"]),
            ("Secondary_Missing4_Snapped", snapped_by_class["missing_4"]),
            ("Merged_Base_Missing1", progressive["missing_1"]),
            ("Merged_Base_Missing12", progressive["missing_2"]),
            ("Merged_Base_Missing123", progressive["missing_3"]),
            ("Merged_Base_Missing1234", progressive["missing_4"]),
        ]:
            if layer.featureCount() == 0:
                _log(log, "Skipped empty intermediate layer '{}' (legacy equivalent would omit it).".format(name), "warning")
                continue
            _write_layer(layer, gpkg, name, first=first, log=log)
            first = False
    return final, {"gpkg": os.path.join(configuration.output_dir, "Intermediate_Files", "{}_M2_Output.gpkg".format(prefix)) if configuration.keep_intermediates else None,
                   "snap_stats": snap_stats, "total_snapped": total_snapped,
                   "total_endpoint_events": total_events, "snap_ratio": ratio}


# ---------------------------------------------------------------------------
# Methodology 3: square-buffer / local-vertex snapping
# ---------------------------------------------------------------------------

def _square_buffer(geometry, distance):
    """Use flat/square end caps, as Shapely buffer(cap_style=3) does."""
    # QGIS changed enum locations across 3.x releases; try the current API,
    # then the legacy QgsGeometry enum, then fall back to a standard buffer.
    attempts = []
    try:
        attempts.append((Qgis.EndCapStyle.Square, Qgis.JoinStyle.Round))
    except Exception:
        pass
    try:
        attempts.append((QgsGeometry.EndCapStyle.Square, QgsGeometry.JoinStyle.Round))
    except Exception:
        pass
    try:
        attempts.append((QgsGeometry.CapSquare, QgsGeometry.JoinStyle.Round))
    except Exception:
        pass
    for cap, join in attempts:
        try:
            return geometry.buffer(float(distance), 8, cap, join, 2.0)
        except Exception:
            continue
    return geometry.buffer(float(distance), 8)


def _explode_line_layer(layer, name):
    """Explode multipart line features into one line feature per part.

    Methodology 3's legacy workflow explicitly explodes the trimmed secondary
    network before snapping, so per-part snapping flags and feature counts are
    retained here as well.
    """
    out = _memory_layer(name, "MultiLineString", layer.crs(), list(layer.fields()))
    features = []
    for source_feature in layer.getFeatures():
        for part in _line_parts(source_feature.geometry()):
            if len(part) < 2:
                continue
            feature = QgsFeature(out.fields())
            feature.setGeometry(_line_geometry([part]))
            feature.setAttributes(source_feature.attributes())
            features.append(feature)
    _add_features(out, features)
    return out


def _vertices_for_buffered_base(base_roads, secondary_buffers, target_crs, log=None):
    """Clip priority roads to secondary buffers using a spatial index."""
    vertex_records = []
    fragment_records = []
    parent_id = 0
    road_index = QgsSpatialIndex()
    for road_feature in base_roads.getFeatures():
        road_index.addFeature(road_feature)

    for position, buffer_feature in enumerate(secondary_buffers.getFeatures(), start=1):
        _tick(log, position, 100)
        buffer_id = int(buffer_feature["buffer_id"])
        polygon = buffer_feature.geometry()
        candidate_ids = road_index.intersects(polygon.boundingBox())
        for road_id in candidate_ids:
            road = base_roads.getFeature(road_id)
            if not road.isValid():
                continue
            geometry = road.geometry()
            try:
                if not geometry.intersects(polygon):
                    continue
            except Exception:
                continue
            clipped = _safe_intersection(geometry, polygon)
            parts = _line_parts(clipped)
            if not parts:
                continue
            clipped_line = _line_geometry(parts)
            fragment_records.append((clipped_line, buffer_id, parent_id))
            for part in parts:
                line = QgsGeometry.fromPolylineXY(part)
                if len(part) < 2 or line.length() <= 0:
                    continue
                points = [
                    (QgsGeometry.fromPointXY(part[0]), "start"),
                    (QgsGeometry.fromPointXY(part[-1]), "end"),
                    (line.interpolate(line.length() * 0.5), "centroid"),
                ]
                for point, vertex_type in points:
                    if point is not None and not point.isNull() and not point.isEmpty():
                        vertex_records.append((point, buffer_id, vertex_type, parent_id))
            parent_id += 1
    _log(log, "Methodology 3: clipped priority roads into {:,} secondary-buffer fragments; built {:,} local snap vertices.".format(
        len(fragment_records), len(vertex_records)))
    return fragment_records, vertex_records


def _nearest_vertex_record(point_geometry, records, vertex_types=None):
    # For global fallback searches, use QGIS' nearest-neighbour spatial index.
    # Local per-buffer subsets stay as short lists so they can be filtered by
    # vertex type before choosing the nearest target.
    if isinstance(records, tuple) and len(records) == 2 and isinstance(records[0], QgsSpatialIndex):
        index, record_by_fid = records
        try:
            point = point_geometry.asPoint()
            nearest_ids = index.nearestNeighbor(QgsPointXY(point), 1)
        except Exception:
            nearest_ids = []
        if not nearest_ids:
            return None, None
        record = record_by_fid.get(nearest_ids[0])
        if record is None:
            return None, None
        try:
            return record, point_geometry.distance(record[0])
        except Exception:
            return record, None

    candidates = records
    if vertex_types is not None:
        candidates = [record for record in records if record[2] in vertex_types]
    if not candidates:
        return None, None
    point = point_geometry.asPoint()
    best = None
    best_distance = float("inf")
    for record in candidates:
        p = record[0].asPoint()
        distance = ((point.x() - p.x()) ** 2 + (point.y() - p.y()) ** 2) ** 0.5
        if distance < best_distance:
            best = record
            best_distance = distance
    return best, best_distance


def _snap_m3_line_part(part, same_buffer_vertices, global_vertices, max_distance):
    coords = [QgsPointXY(point) for point in part]
    if len(coords) < 2:
        return coords, False, 0
    start_point = QgsGeometry.fromPointXY(coords[0])
    end_point = QgsGeometry.fromPointXY(coords[-1])
    line_geometry = QgsGeometry.fromPolylineXY(coords)
    midpoint = line_geometry.centroid()
    snapped = False
    events = 0

    # 1. Base-road midpoint targets are preferred within the associated buffer.
    if same_buffer_vertices:
        centroid_record, centroid_dist = _nearest_vertex_record(
            midpoint, same_buffer_vertices, {"centroid"}
        )
        if centroid_record is not None and centroid_dist <= max_distance:
            target_point = centroid_record[0].asPoint()
            d_start = start_point.distance(centroid_record[0])
            d_end = end_point.distance(centroid_record[0])
            if d_start < d_end:
                coords[0] = QgsPointXY(target_point)
            else:
                coords[-1] = QgsPointXY(target_point)
            snapped = True
            events += 1

    # 2. If midpoint snapping did not occur, test local start/end vertices.
    if not snapped and same_buffer_vertices:
        local_endpoints = [
            record for record in same_buffer_vertices
            if record[2] in ("start", "end")
        ]
        nearest_start, start_dist = _nearest_vertex_record(start_point, local_endpoints)
        if nearest_start is not None and start_dist <= max_distance:
            coords[0] = QgsPointXY(nearest_start[0].asPoint())
            snapped = True
            events += 1
        nearest_end, end_dist = _nearest_vertex_record(end_point, local_endpoints)
        if nearest_end is not None and end_dist <= max_distance:
            coords[-1] = QgsPointXY(nearest_end[0].asPoint())
            snapped = True
            events += 1

    # 3. If neither local rule snapped anything, try global nearest vertices.
    if not snapped and global_vertices:
        nearest_start, start_dist = _nearest_vertex_record(start_point, global_vertices)
        if nearest_start is not None and start_dist <= max_distance:
            coords[0] = QgsPointXY(nearest_start[0].asPoint())
            snapped = True
            events += 1
        nearest_end, end_dist = _nearest_vertex_record(end_point, global_vertices)
        if nearest_end is not None and end_dist <= max_distance:
            coords[-1] = QgsPointXY(nearest_end[0].asPoint())
            snapped = True
            events += 1
    return coords, snapped, events


def _methodology_3(base_roads, classified_secondary, dissolved_mask, configuration, prefix, log=None):
    """Legacy Methodology 3: trim -> secondary square buffers -> targeted snap -> merge."""
    _log(log, "Starting Methodology 3 — Buffer → Snap → Merge.", "info")
    target_crs = configuration.analysis_crs
    trimmed_all = _trimmed_class_layer(
        classified_secondary, dissolved_mask, target_class=None,
        name="Secondary_Trimmed_All", log=log
    )
    trimmed = _explode_line_layer(trimmed_all, "Secondary_Trimmed_Exploded")
    _log(log, "Trimmed missing_1..missing_4 secondary roads: {:,} feature(s), {:,} line part(s).".format(
        trimmed_all.featureCount(), trimmed.featureCount()))

    # Legacy step: clip missing roads to the dissolved priority-buffer mask,
    # then make square buffers around those overlap pieces.
    overlap_fields = list(classified_secondary.fields())
    overlap = _memory_layer(
        "Secondary_Overlap_Inside_Priority_Buffer", "MultiLineString",
        target_crs, overlap_fields
    )
    overlap_feats = []
    class_idx = next(
        i for i, f in enumerate(classified_secondary.fields())
        if f.name().casefold() == "missing_class"
    )
    for position, f in enumerate(classified_secondary.getFeatures(), start=1):
        _tick(log, position, 250)
        if clean_text(f[class_idx]) not in MISSING_CLASSES:
            continue
        intersection = _safe_intersection(f.geometry(), dissolved_mask)
        parts = _line_parts(intersection)
        if not parts:
            continue
        nf = QgsFeature(overlap.fields())
        nf.setGeometry(_line_geometry(parts))
        nf.setAttributes(f.attributes())
        overlap_feats.append(nf)
    _add_features(overlap, overlap_feats)

    # Keep the source attributes on the generated square-buffer layer. The
    # legacy workflow buffered a copy of the overlapping secondary rows and
    # added only a buffer_id field. If the input already has a buffer_id field,
    # rename that old value to avoid a duplicate field name.
    buffer_source_fields = []
    existing_names = set()
    for source_field in overlap.fields():
        copied_field = QgsField(source_field)
        if copied_field.name().casefold() == "buffer_id":
            copied_field.setName(_unique_renamed_field(buffer_source_fields, "buffer_id_src"))
        if copied_field.name().casefold() in existing_names:
            copied_field.setName(_unique_renamed_field(buffer_source_fields, copied_field.name()))
        existing_names.add(copied_field.name().casefold())
        buffer_source_fields.append(copied_field)
    buffer_id_field_name = _unique_renamed_field(buffer_source_fields, "buffer_id")
    buffer_layer = _memory_layer(
        "Secondary_Buffers_Overlap", "MultiPolygon", target_crs,
        buffer_source_fields + [make_field(buffer_id_field_name, "longlong")]
    )
    buffer_features = []
    for buffer_id, f in enumerate(overlap.getFeatures(), start=1):
        _tick(log, buffer_id, 250)
        square = _square_buffer(
            f.geometry(), _metres_to_map_units(target_crs, configuration.secondary_buffer_m)
        )
        if square.isNull() or square.isEmpty():
            continue
        if not square.isMultipart():
            square.convertToMultiType()
        nf = QgsFeature(buffer_layer.fields())
        nf.setGeometry(square)
        nf.setAttributes(list(f.attributes()) + [buffer_id])
        buffer_features.append(nf)
    _add_features(buffer_layer, buffer_features)

    # Endpoint QA layers. Legacy used a spatial join with the secondary square
    # buffers; a point may be recorded against more than one buffer.
    sec_vertex_records = []
    vertex_id = 0
    for f in trimmed.getFeatures():
        for part in _line_parts(f.geometry()):
            if len(part) < 2:
                continue
            sec_vertex_records.extend([
                (QgsGeometry.fromPointXY(part[0]), [vertex_id, int(f.id()), "start"]),
                (QgsGeometry.fromPointXY(part[-1]), [vertex_id + 1, int(f.id()), "end"]),
            ])
            vertex_id += 2
    secondary_vertices = _point_layer(
        "Secondary_Vertices_All", target_crs, sec_vertex_records,
        [make_field("vertex_id", "longlong"),
         make_field("parent_id", "longlong"),
         make_field("vertex_type", "string", length=16)]
    )
    sec_vertices_inside = []
    buffers_by_id = {}
    buffers_by_fid = {}
    buffer_id_by_fid = {}
    buffer_index = QgsSpatialIndex()
    for buf in buffer_layer.getFeatures():
        buffer_index.addFeature(buf)
        geom_copy = QgsGeometry(buf.geometry())
        attr_buffer_id = int(buf["buffer_id"])
        buffers_by_id[attr_buffer_id] = geom_copy
        buffers_by_fid[buf.id()] = geom_copy
        buffer_id_by_fid[buf.id()] = attr_buffer_id
    for position, (geom, attrs) in enumerate(sec_vertex_records, start=1):
        _tick(log, position, 500)
        for buffer_fid in buffer_index.intersects(geom.boundingBox()):
            # Map index/provider IDs back to buffer IDs using the geometry and
            # ID caches built above (no per-candidate feature fetch).
            buffer_geometry = buffers_by_fid.get(buffer_fid)
            if buffer_geometry is None:
                continue
            try:
                if buffer_geometry.contains(geom):
                    sec_vertices_inside.append((geom, attrs + [buffer_id_by_fid[buffer_fid]]))
            except Exception:
                continue
    secondary_vertices_in_buffer = _point_layer(
        "Secondary_Vertices_InBuffer", target_crs, sec_vertices_inside,
        [make_field("vertex_id", "longlong"),
         make_field("parent_id", "longlong"),
         make_field("vertex_type", "string", length=16),
         make_field("buffer_id", "longlong")]
    )

    base_fragments, vertex_records = _vertices_for_buffered_base(
        base_roads, buffer_layer, target_crs, log
    )
    base_vertex_layer = _point_layer(
        "Base_Vertices", target_crs,
        [(record[0], [record[1], record[2], record[3]]) for record in vertex_records],
        [make_field("buffer_id", "longlong"),
         make_field("vertex_type", "string", length=16),
         make_field("parent_id", "longlong")]
    )
    vertices_by_buffer = defaultdict(list)
    for record in vertex_records:
        vertices_by_buffer[record[1]].append(record)
    # Use a spatial index for the global fallback path (critical for city-scale
    # datasets with hundreds of thousands of base vertices).
    global_vertex_index = QgsSpatialIndex()
    global_record_by_fid = {}
    for vertex_feature in base_vertex_layer.getFeatures():
        global_vertex_index.addFeature(vertex_feature)
        global_record_by_fid[vertex_feature.id()] = (
            QgsGeometry(vertex_feature.geometry()),
            int(vertex_feature["buffer_id"]),
            str(vertex_feature["vertex_type"]),
            int(vertex_feature["parent_id"]),
        )
    global_vertices = (global_vertex_index, global_record_by_fid)

    # The stand-alone legacy script did not assign buffer_id back to trimmed
    # secondary roads, which made its local-priority snapping stage unreachable.
    # Re-associate each trimmed road with intersecting square buffers to restore
    # the documented centroid -> endpoint -> global-fallback procedure.
    snapped_fields = list(trimmed.fields())
    if not any(f.name().casefold() == "snapped" for f in snapped_fields):
        snapped_fields.append(make_field("Snapped", "int"))
    snapped_layer = _memory_layer(
        "Secondary_Snapped_Final", "MultiLineString", target_crs, snapped_fields
    )
    snapped_idx = next(i for i, f in enumerate(snapped_layer.fields()) if f.name().casefold() == "snapped")
    class_idx_trim = next(i for i, f in enumerate(trimmed.fields()) if f.name().casefold() == "missing_class")
    snap_features = []
    snapped_stats = Counter()
    snap_events = 0
    join_gap_units = _metres_to_map_units(target_crs, configuration.join_gap_m)
    for position, f in enumerate(trimmed.getFeatures(), start=1):
        _tick(log, position, 100)
        cls = clean_text(f[class_idx_trim])
        geom = f.geometry()
        parts = _line_parts(geom)
        if not parts:
            continue
        did_any = False
        out_parts = []
        events_for_feature = 0
        if cls == "missing_1":
            out_parts = parts
        else:
            candidate_buffers = []
            for buffer_fid in buffer_index.intersects(geom.boundingBox()):
                buffer_geometry = buffers_by_fid.get(buffer_fid)
                if buffer_geometry is None:
                    continue
                try:
                    if buffer_geometry.intersects(geom):
                        # The distance between intersecting geometries is zero
                        # for every match. Compare their centroids instead so
                        # a road intersecting several square buffers is linked
                        # to the spatially closest local buffer, not merely the
                        # one that received the lowest generated ID.
                        buffer_centroid = buffer_geometry.centroid()
                        line_centroid = geom.centroid()
                        centroid_distance = buffer_centroid.distance(line_centroid)
                        candidate_buffers.append((centroid_distance, buffer_id_by_fid[buffer_fid]))
                except Exception:
                    continue
            associated = min(candidate_buffers)[1] if candidate_buffers else None
            local_records = vertices_by_buffer.get(associated, []) if associated is not None else []
            for part in parts:
                new_part, did_snap, events = _snap_m3_line_part(
                    part, local_records, global_vertices, join_gap_units
                )
                out_parts.append(new_part)
                did_any = did_any or did_snap
                events_for_feature += events
        new_geom = _line_geometry(out_parts)
        if new_geom.isNull() or new_geom.isEmpty():
            continue
        nf = QgsFeature(snapped_layer.fields())
        nf.setGeometry(new_geom)
        values = list(f.attributes()) + [None] * (len(snapped_layer.fields()) - len(f.attributes()))
        values[snapped_idx] = 1 if did_any else 0
        nf.setAttributes(values)
        snap_features.append(nf)
        if did_any:
            snapped_stats[cls] += 1
        snap_events += events_for_feature
    _add_features(snapped_layer, snap_features)
    _log(log, "Methodology 3 snapping: {:,}/{:,} secondary features snapped; {:,} endpoint events.".format(
        sum(snapped_stats.values()), snapped_layer.featureCount(), snap_events), "success")

    # The legacy final merge places secondary features before the priority roads.
    final = _combine_layers(
        [snapped_layer, base_roads], target_crs, "Merged_Base_Secondary_Final"
    )
    _log(log, "Methodology 3 completed: {:,} secondary + {:,} priority = {:,} merged features.".format(
        snapped_layer.featureCount(), base_roads.featureCount(), final.featureCount()), "success")

    if configuration.keep_intermediates:
        gpkg = os.path.join(
            configuration.output_dir, "Intermediate_Files", "{}_M3_Output.gpkg".format(prefix)
        )
        os.makedirs(os.path.dirname(gpkg), exist_ok=True)
        _remove_output(gpkg, "gpkg")
        first = True
        for name, layer in [
            ("Secondary_Trimmed_All", trimmed_all),
            ("Secondary_Buffers_Overlap", buffer_layer),
            ("Secondary_Vertices_All", secondary_vertices),
            ("Secondary_Vertices_InBuffer", secondary_vertices_in_buffer),
            ("Base_Vertices", base_vertex_layer),
            ("Secondary_Snapped_Final", snapped_layer),
            ("Merged_Base_Secondary_Final", final),
        ]:
            if layer.featureCount() == 0:
                _log(log, "Skipped empty intermediate layer '{}' (no features to inspect).".format(name), "warning")
                continue
            _write_layer(layer, gpkg, name, first=first, log=log)
            first = False
    return final, {
        "gpkg": os.path.join(configuration.output_dir, "Intermediate_Files", "{}_M3_Output.gpkg".format(prefix)) if configuration.keep_intermediates else None,
        "secondary_snapped_count": snapped_layer.featureCount(),
        "snap_stats": dict(snapped_stats), "total_endpoint_events": snap_events,
        "secondary_buffers": buffer_layer.featureCount(),
    }


# ---------------------------------------------------------------------------
# Legacy coverage and length summaries
# ---------------------------------------------------------------------------

def _log_legacy_summary(base_roads, classified_secondary, base_label, secondary_label, log=None):
    """Write the descriptive and missing-road length statistics from the legacy main script."""
    ratio_idx = next(i for i, field in enumerate(classified_secondary.fields())
                     if field.name().casefold() == "rem_pct")
    class_idx = next(i for i, field in enumerate(classified_secondary.fields())
                     if field.name().casefold() == "missing_class")
    target_crs = classified_secondary.crs()
    length_to_m = QgsUnitTypes.fromUnitToUnitFactor(
        target_crs.mapUnits(), METERS
    )

    ratios = []
    classes = Counter()
    class_lengths_km = Counter()
    secondary_length_m = 0.0
    for feature in classified_secondary.getFeatures():
        cls = clean_text(feature[class_idx]) or "None"
        classes[cls] += 1
        geometry = feature.geometry()
        length_m = _line_length(geometry) * length_to_m
        secondary_length_m += length_m
        class_lengths_km[cls] += length_m / 1000.0
        try:
            value = float(feature[ratio_idx])
            if value == value and abs(value) != float("inf"):
                ratios.append(value)
        except (TypeError, ValueError):
            pass

    base_length_m = sum(_line_length(f.geometry()) for f in base_roads.getFeatures()) * length_to_m
    total_secondary_km = secondary_length_m / 1000.0
    total_base_km = base_length_m / 1000.0

    _log(log, "Coverage statistics for {} relative to {}:".format(secondary_label, base_label))
    if ratios:
        ordered = sorted(ratios)
        n = len(ordered)
        mean_value = sum(ordered) / n
        median_value = (ordered[n // 2] if n % 2 else
                        (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0)
        variance = (sum((value - mean_value) ** 2 for value in ordered) / (n - 1)) if n > 1 else None
        frequencies = Counter(ordered)
        highest_frequency = max(frequencies.values())
        # pandas.Series.mode() returns sorted tied modes; use the first of those.
        mode_value = min(value for value, count in frequencies.items() if count == highest_frequency)
        std_value = variance ** 0.5 if variance is not None else None
        _log(log, "  Remaining-length ratio (0–1): min={:.4f}; max={:.4f}; mean={:.4f}; std={}; median={:.4f}; mode={:.4f}".format(
            ordered[0], ordered[-1], mean_value,
            "{:.4f}".format(std_value) if std_value is not None else "n/a",
            median_value, mode_value,
        ))
    else:
        _log(log, "  No valid remaining-length ratios were available.", "warning")

    class_order = ("missing_1", "missing_2", "missing_3", "missing_4", "missing_a", "missing_b", "None")
    feature_count = max(1, classified_secondary.featureCount())
    _log(log, "  Coverage-class summary (all classified secondary features):")
    for cls in class_order:
        count = classes.get(cls, 0)
        _log(log, "    {}: {:,} feature(s) ({:.2f}%)".format(cls, count, 100.0 * count / feature_count))

    missing_total_km = sum(class_lengths_km.get(cls, 0.0) for cls in MISSING_CLASSES)
    _log(log, "Road lengths (clipped/reprojected inputs): priority={:.3f} km; secondary={:.3f} km.".format(
        total_base_km, total_secondary_km))
    for cls in class_order:
        cls_km = class_lengths_km.get(cls, 0.0)
        if total_base_km > 0:
            ratio_base = 100.0 * cls_km / total_base_km
        else:
            ratio_base = 0.0
        _log(log, "  {}: {:.3f} km; {:.2f}% of priority-road length.".format(cls, cls_km, ratio_base))
    _log(log, "  Missing classes 1–4 total: {:.3f} km; {:.2f}% of priority length; {:.2f}% of secondary length.".format(
        missing_total_km,
        100.0 * missing_total_km / total_base_km if total_base_km > 0 else 0.0,
        100.0 * missing_total_km / total_secondary_km if total_secondary_km > 0 else 0.0,
    ))
    return {
        "coverage_ratio_statistics": {
            "min": min(ratios) if ratios else None,
            "max": max(ratios) if ratios else None,
            "mean": sum(ratios) / len(ratios) if ratios else None,
            "median": median_value if ratios else None,
            "mode": mode_value if ratios else None,
            "std": std_value if ratios else None,
        },
        "coverage_class_counts": dict(classes),
        "priority_length_km": total_base_km,
        "secondary_length_km": total_secondary_km,
        "missing_length_km_by_class": dict(class_lengths_km),
        "missing_total_km": missing_total_km,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def _output_prefix(configuration):
    stem = os.path.splitext(os.path.basename(configuration.output_filename))[0]
    suffix = "_Road_Network_Harmonized"
    if stem.endswith(suffix):
        stem = stem[:-len(suffix)]
    return stem or "Road_Network"


def run_legacy_workflow(priority_roads, secondary_roads, study_area, configuration, method, log=None):
    """Execute the complete legacy preparation/classification/integration flow."""
    if method not in ("methodology_1", "methodology_2", "methodology_3"):
        raise ValueError("Unsupported methodology: {}".format(method))
    target_crs = configuration.analysis_crs
    if not target_crs.isValid() or target_crs.isGeographic():
        raise ValueError("A valid projected analysis CRS is required for metre-based operations.")
    if min(configuration.base_buffer_m, configuration.secondary_buffer_m,
           configuration.join_gap_m, configuration.mid_gap_m,
           configuration.centroid_max_dist_m) <= 0:
        raise ValueError("All buffer and snapping distances must be greater than zero.")

    prefix = _output_prefix(configuration)
    base_label = _dataset_label(configuration.priority_uri, "BASE")
    secondary_label = _dataset_label(configuration.secondary_uri, "SECONDARY")
    _log(log, "=" * 58)
    _log(log, "Road Network Integration Toolkit — legacy workflow port")
    _log(log, "Runtime: {}".format(runtime_summary()))
    _log(log, "Priority dataset: {} | Secondary dataset: {}".format(base_label, secondary_label))
    _log(log, "Methodology: {} | Analysis CRS: {}".format(method.replace("methodology_", "Methodology "), target_crs.authid() or target_crs.description()))
    _log(log, "Output prefix: {}".format(prefix))
    _log(log, "Distance controls are interpreted as metres and converted to the selected CRS units ({}).".format(
        QgsUnitTypes.toString(target_crs.mapUnits())
    ))

    _, clip_geometry = _prepare_area(study_area, target_crs, log)
    _check_cancel(log)
    base_roads = _prepare_line_layer(priority_roads, target_crs, clip_geometry, "Priority_Roads_Prepared", log)
    _check_cancel(log)
    secondary_roads_prepared = _prepare_line_layer(secondary_roads, target_crs, clip_geometry, "Secondary_Roads_Prepared", log)
    _check_cancel(log)
    if base_roads.featureCount() == 0:
        raise ValueError("No priority-road features remain after preparation and clipping.")
    if secondary_roads_prepared.featureCount() == 0:
        raise ValueError("No secondary-road features remain after preparation and clipping.")

    buffer_layer, buffers_by_id, buffer_index, dissolved_mask, dissolved_layer = _create_priority_buffers(
        base_roads, configuration.base_buffer_m, log
    )
    _check_cancel(log)
    classified_secondary = _classified_secondary(secondary_roads_prepared, buffers_by_id, buffer_index, log)
    _check_cancel(log)
    summary_diagnostics = _log_legacy_summary(
        base_roads, classified_secondary, base_label, secondary_label, log
    )

    if configuration.keep_intermediates:
        intermediate_dir = os.path.join(configuration.output_dir, "Intermediate_Files")
        os.makedirs(intermediate_dir, exist_ok=True)
        buffers_path = os.path.join(intermediate_dir, "{}_{}_Road_Buffers.gpkg".format(prefix, base_label))
        _remove_output(buffers_path, "gpkg")
        _write_layer(buffer_layer, buffers_path, "{}_Buffer_Individual".format(base_label), first=True, log=log)
        _write_layer(dissolved_layer, buffers_path, "{}_Buffer_Dissolved".format(base_label), log=log)
        classified_path = os.path.join(configuration.output_dir, "{}_{}_Coverage_Classified.gpkg".format(prefix, secondary_label))
        _remove_output(classified_path, "gpkg")
        _write_layer(classified_secondary, classified_path, "{}_Classified".format(secondary_label), first=True, log=log)

    if method == "methodology_1":
        final = _methodology_1(base_roads, classified_secondary, base_label, secondary_label, log)
        diagnostics = {"methodology": 1}
        if configuration.keep_intermediates:
            diagnostic_path = os.path.join(configuration.output_dir, "Intermediate_Files", "{}_Merged_{}_{}_Method1.gpkg".format(prefix, base_label, secondary_label))
            _remove_output(diagnostic_path, "gpkg")
            _write_layer(final, diagnostic_path, "Merged_Roads_Method1", first=True, log=log)
    elif method == "methodology_2":
        final, diagnostics = _methodology_2(
            base_roads, classified_secondary, dissolved_mask, configuration,
            prefix, base_label, secondary_label, log
        )
    else:
        final, diagnostics = _methodology_3(
            base_roads, classified_secondary, dissolved_mask, configuration, prefix, log
        )

    if final is None or final.featureCount() == 0:
        raise RuntimeError("The selected methodology did not produce a non-empty merged road network.")

    _check_cancel(log)
    output_path, output_layer = _write_final(final, configuration, log)
    result = {
        "output_path": output_path,
        "output_layer": output_layer,
        "output_feature_count": output_layer.featureCount(),
        "methodology": method,
        "priority_label": base_label,
        "secondary_label": secondary_label,
        "classified_feature_count": classified_secondary.featureCount(),
    }
    result.update(summary_diagnostics)
    result.update(diagnostics)
    _log(log, "Finished {}: {:,} features in the final network.".format(
        method.replace("methodology_", "Methodology "), result["output_feature_count"]), "success")
    return result
