# -*- coding: utf-8 -*-
"""Utilities for discovering and loading vector datasources in QGIS.

Supported containers include single-layer vector files, GeoPackages, and
File Geodatabases. A datasource path and its selected feature-layer URI are
kept separately so the GUI can display a simple path while loading the exact
feature layer selected by the user.
"""

import os
from dataclasses import dataclass
from typing import List, Optional

from qgis.core import QgsProviderRegistry, QgsVectorLayer, QgsWkbTypes

from .compat import (
    LINE_GEOMETRY, NULL_GEOMETRY, POINT_GEOMETRY, POLYGON_GEOMETRY,
)


@dataclass
class VectorLayerChoice:
    """A readable vector feature layer discovered inside a datasource."""

    name: str
    uri: str
    provider: str
    feature_count: int
    geometry_type: int
    crs_authid: str


def is_file_geodatabase(path: str) -> bool:
    """Return True when *path* points to a directory-based .gdb datasource."""
    return bool(path) and os.path.isdir(path) and path.lower().endswith(".gdb")


def datasource_exists(path: str) -> bool:
    """Check the datasource path independently of any provider sublayer URI."""
    return bool(path) and os.path.exists(path)


def _details_to_choice(detail, fallback_path: str) -> Optional[VectorLayerChoice]:
    """Open one QGIS-discovered sublayer and convert it to a safe choice."""
    try:
        uri = detail.uri()
        name = detail.name() or os.path.basename(fallback_path)
        provider = detail.providerKey() or "ogr"
        layer = QgsVectorLayer(uri, name, provider)
        if not layer.isValid():
            return None
        return VectorLayerChoice(
            name=layer.name() or name,
            uri=uri,
            provider=provider,
            feature_count=layer.featureCount(),
            geometry_type=QgsWkbTypes.geometryType(layer.wkbType()),
            crs_authid=layer.crs().authid() if layer.crs().isValid() else "",
        )
    except Exception:
        return None


def discover_vector_layers(path: str) -> List[VectorLayerChoice]:
    """Return readable vector feature layers in a file or container.

    QgsProviderRegistry/OGR performs the layer discovery; this function does
    not inspect GeoPackage or File Geodatabase internals itself. If the
    provider reports no sublayers, a direct vector-layer open is attempted.
    """
    if not datasource_exists(path):
        return []

    choices: List[VectorLayerChoice] = []
    try:
        details = QgsProviderRegistry.instance().querySublayers(path)
    except Exception:
        details = []

    for detail in details:
        choice = _details_to_choice(detail, path)
        if choice is not None:
            # Avoid duplicate entries sometimes reported by provider discovery.
            if not any(existing.uri == choice.uri for existing in choices):
                choices.append(choice)

    if not choices:
        try:
            layer = QgsVectorLayer(path, os.path.basename(path.rstrip("/\\")), "ogr")
            if layer.isValid():
                choices.append(
                    VectorLayerChoice(
                        name=layer.name(),
                        uri=path,
                        provider="ogr",
                        feature_count=layer.featureCount(),
                        geometry_type=QgsWkbTypes.geometryType(layer.wkbType()),
                        crs_authid=layer.crs().authid() if layer.crs().isValid() else "",
                    )
                )
        except Exception:
            pass

    return choices


def load_vector_layer(path: str, layer_uri: str = "", display_name: str = "Input layer") -> Optional[QgsVectorLayer]:
    """Load the selected feature layer, returning None when QGIS cannot open it."""
    if not datasource_exists(path):
        return None
    uri = layer_uri.strip() if layer_uri else path
    try:
        layer = QgsVectorLayer(uri, display_name, "ogr")
        return layer if layer.isValid() else None
    except Exception:
        return None


def geometry_matches(layer: QgsVectorLayer, expected: str) -> bool:
    """Check whether a vector layer has line or polygon geometry."""
    if layer is None or not layer.isValid():
        return False
    actual = QgsWkbTypes.geometryType(layer.wkbType())
    expected = (expected or "").strip().lower()
    if expected in ("line", "lines", "line geometry"):
        return actual == LINE_GEOMETRY
    if expected in ("polygon", "polygons", "polygon geometry"):
        return actual == POLYGON_GEOMETRY
    return True


def geometry_description(layer: QgsVectorLayer) -> str:
    """Return a readable geometry description for validation messages."""
    if layer is None or not layer.isValid():
        return "invalid layer"
    geometry_type = QgsWkbTypes.geometryType(layer.wkbType())
    if geometry_type == POINT_GEOMETRY:
        return "point"
    if geometry_type == LINE_GEOMETRY:
        return "line"
    if geometry_type == POLYGON_GEOMETRY:
        return "polygon"
    if geometry_type == NULL_GEOMETRY:
        return "no geometry"
    return "unknown geometry"


# ----------------------------------------------------------------------
# File Geodatabase write support
# ----------------------------------------------------------------------

def gdb_driver_name() -> Optional[str]:
    """Name of a GDAL driver that can *create* File Geodatabases, or None.

    OpenFileGDB gained write support in GDAL 3.6; older GDAL builds only offer
    creation through the proprietary Esri FileGDB driver, when it is installed.
    """
    try:
        from osgeo import ogr
    except ImportError:
        return None
    for driver_name in ("OpenFileGDB", "FileGDB"):
        driver = ogr.GetDriverByName(driver_name)
        if driver is not None and driver.TestCapability(ogr.ODrCCreateDataSource):
            return driver_name
    return None


def gdb_write_supported() -> bool:
    """True if this QGIS/GDAL build can create File Geodatabases."""
    return gdb_driver_name() is not None
