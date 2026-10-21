# -*- coding: utf-8 -*-
"""QGIS 3.28 -> 4.x (PyQt5 -> PyQt6) compatibility helpers.

QGIS 4 is built on Qt 6, which removed several things this plugin used to
rely on:

* flat enum access such as ``QgsWkbTypes.LineGeometry`` or
  ``QgsVectorFileWriter.NoError`` (only scoped access such as
  ``Qgis.GeometryType.Line`` still works),
* ``QVariant.Int`` / ``QVariant.String`` as ``QgsField`` type arguments
  (``QMetaType.Type.Int`` / ``QMetaType.Type.QString`` are used instead),
* ``QAction`` living in ``QtWidgets`` (it moved to ``QtGui``).

QGIS 3.28, on the other hand, only understands the *old* spellings for most of
these, and the scoped ``Qgis.*`` enums only appeared gradually from 3.30.
Every version-sensitive lookup therefore lives in this module: it tries the
modern spelling first and falls back to the legacy one. The rest of the plugin
imports these names and never touches a version-specific API directly.
"""

from qgis.PyQt.QtCore import QMetaType
from qgis.core import (
    NULL,
    Qgis,
    QgsField,
    QgsUnitTypes,
    QgsVectorFileWriter,
    QgsWkbTypes,
)

try:  # QVariant still exists on Qt 6, but without the old Type constants.
    from qgis.PyQt.QtCore import QVariant
except ImportError:  # pragma: no cover - defensive
    QVariant = None

try:  # Qt 6 / QGIS 4: QAction moved to QtGui.
    from qgis.PyQt.QtGui import QAction
except ImportError:  # Qt 5 / QGIS 3.x
    from qgis.PyQt.QtWidgets import QAction


# ---------------------------------------------------------------------------
# Generic scoped-enum lookup
# ---------------------------------------------------------------------------

def scoped_enum(owner, enum_name, member):
    """Return ``owner.enum_name.member`` (modern) or ``owner.member`` (legacy)."""
    enum_type = getattr(owner, enum_name, None)
    if enum_type is not None:
        value = getattr(enum_type, member, None)
        if value is not None:
            return value
    value = getattr(owner, member, None)
    if value is None:
        raise AttributeError(
            "This QGIS version exposes neither {0}.{1}.{2} nor {0}.{2}.".format(
                getattr(owner, "__name__", owner), enum_name, member
            )
        )
    return value


# ---------------------------------------------------------------------------
# Geometry types
# ---------------------------------------------------------------------------

def _geometry_constant(modern_name, legacy_name):
    """``Qgis.GeometryType.X`` on QGIS >= 3.30, ``QgsWkbTypes.XGeometry`` before."""
    modern_enum = getattr(Qgis, "GeometryType", None)
    if modern_enum is not None:
        value = getattr(modern_enum, modern_name, None)
        if value is not None:
            return value
    return getattr(QgsWkbTypes, legacy_name)


POINT_GEOMETRY = _geometry_constant("Point", "PointGeometry")
LINE_GEOMETRY = _geometry_constant("Line", "LineGeometry")
POLYGON_GEOMETRY = _geometry_constant("Polygon", "PolygonGeometry")
NULL_GEOMETRY = _geometry_constant("Null", "NullGeometry")


# ---------------------------------------------------------------------------
# Distance units
# ---------------------------------------------------------------------------

def _meters_unit():
    unit_enum = getattr(Qgis, "DistanceUnit", None)
    if unit_enum is not None:
        value = getattr(unit_enum, "Meters", None)
        if value is not None:
            return value
    return QgsUnitTypes.DistanceMeters


METERS = _meters_unit()


# ---------------------------------------------------------------------------
# QgsVectorFileWriter enums
# ---------------------------------------------------------------------------

WRITER_NO_ERROR = scoped_enum(QgsVectorFileWriter, "WriterError", "NoError")
ACTION_CREATE_OR_OVERWRITE_FILE = scoped_enum(
    QgsVectorFileWriter, "ActionOnExistingFile", "CreateOrOverwriteFile"
)
ACTION_CREATE_OR_OVERWRITE_LAYER = scoped_enum(
    QgsVectorFileWriter, "ActionOnExistingFile", "CreateOrOverwriteLayer"
)


# ---------------------------------------------------------------------------
# Message-log levels
# ---------------------------------------------------------------------------

MSG_CRITICAL = scoped_enum(Qgis, "MessageLevel", "Critical")


# ---------------------------------------------------------------------------
# Attribute field construction
# ---------------------------------------------------------------------------

# kind -> (QMetaType.Type member, QVariant member)
_FIELD_TYPE_NAMES = {
    "int": ("Int", "Int"),
    "longlong": ("LongLong", "LongLong"),
    "double": ("Double", "Double"),
    "string": ("QString", "String"),
}
_field_type_cache = {}


def _lookup_type(owner, scope_name, member):
    if owner is None:
        return None
    for container in (getattr(owner, scope_name, None), owner):
        if container is None:
            continue
        value = getattr(container, member, None)
        if value is not None:
            return value
    return None


def _field_type_candidates(kind):
    try:
        meta_name, variant_name = _FIELD_TYPE_NAMES[kind]
    except KeyError:
        raise ValueError("Unknown field kind '{}'.".format(kind))
    # QMetaType first: it is the only option on QGIS 4 and avoids deprecation
    # warnings on 3.38+. QGIS 3.28 rejects it with a TypeError, and the QVariant
    # spelling is then used instead.
    candidates = [
        _lookup_type(QMetaType, "Type", meta_name),
        _lookup_type(QVariant, "Type", variant_name),
    ]
    return [candidate for candidate in candidates if candidate is not None]


def make_field(name, kind, length=0, precision=0):
    """Create a ``QgsField`` on any supported QGIS version.

    ``kind`` is one of ``"int"``, ``"longlong"``, ``"double"`` or ``"string"``.
    """
    options = {}
    if length:
        options["len"] = length
    if precision:
        options["prec"] = precision

    cached = _field_type_cache.get(kind)
    candidates = [cached] if cached is not None else _field_type_candidates(kind)
    last_error = None
    for field_type in candidates:
        try:
            field = QgsField(name, field_type, **options)
        except TypeError as exc:
            last_error = exc
            continue
        _field_type_cache[kind] = field_type
        return field
    raise TypeError(
        "Could not create a '{}' attribute field on this QGIS version: {}".format(
            kind, last_error or "no usable field type constant was found"
        )
    )


# ---------------------------------------------------------------------------
# NULL handling
# ---------------------------------------------------------------------------

def is_null(value):
    """True for Python ``None`` and for QGIS NULL attribute values."""
    if value is None or value is NULL:
        return True
    if QVariant is not None and isinstance(value, QVariant):
        try:
            return bool(value.isNull())
        except Exception:
            return False
    try:
        if type(value) is type(NULL):
            return bool(value == NULL)
    except Exception:
        pass
    return False


def clean_text(value):
    """Attribute value as text; NULL/None become an empty string."""
    return "" if is_null(value) else str(value)


# ---------------------------------------------------------------------------
# Runtime information (useful in logs and bug reports)
# ---------------------------------------------------------------------------

def runtime_summary():
    """One-line description of the QGIS / Qt / PyQt versions in use."""
    try:
        qgis_version = Qgis.version()
    except Exception:
        qgis_version = getattr(Qgis, "QGIS_VERSION", "unknown")
    try:
        from qgis.PyQt.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
        qt = "Qt {} / PyQt {}".format(QT_VERSION_STR, PYQT_VERSION_STR)
    except Exception:
        qt = "Qt version unknown"
    return "QGIS {} | {}".format(qgis_version, qt)
