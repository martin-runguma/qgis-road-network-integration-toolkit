# -*- coding: utf-8 -*-
"""Minimal fake ``qgis`` modules for testing outside QGIS.

Two API "styles" are emulated so the compatibility layer can be checked against
both ends of the supported range without a QGIS installation:

``legacy``  QGIS 3.28 / PyQt5 - flat enums (``QgsWkbTypes.LineGeometry``),
            ``QgsField`` only accepts ``QVariant`` type constants,
            ``QAction`` lives in ``QtWidgets``.
``modern``  QGIS 4 / PyQt6   - only scoped enums (``Qgis.GeometryType.Line``),
            ``QgsField`` only accepts ``QMetaType.Type`` constants,
            ``QVariant`` has no ``Int``/``String`` members,
            ``QAction`` lives in ``QtGui``.

Anything not modelled explicitly resolves to a harmless dummy class, which is
enough to import the plugin's modules and exercise their pure-Python helpers.
This is a smoke test, not a substitute for running the plugin in real QGIS.
"""

import sys
import types

from _pkg import purge_plugin_and_qgis_modules


class _Enum(int):
    def __new__(cls, value, name):
        obj = int.__new__(cls, value)
        obj.name = name
        return obj

    def __repr__(self):
        return "<{} {}>".format(type(self).__name__, self.name)


class VariantEnum(_Enum):
    """Stands in for QVariant.Type members (QGIS 3.x field types)."""


class MetaEnum(_Enum):
    """Stands in for QMetaType.Type members (QGIS 4 field types)."""


class Dummy:
    """Accepts any constructor arguments; used for every unmodelled class."""

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return lambda *a, **k: None


def _dummy_class(name):
    return type(name, (Dummy,), {})


class _AutoModule(types.ModuleType):
    """Module whose unknown attributes are generated dummy classes."""

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        value = _dummy_class(name)
        setattr(self, name, value)
        return value


class _Namespace:
    """Simple attribute bag used as an enum scope."""

    def __init__(self, **members):
        self.__dict__.update(members)


class FakeQgsNull:
    pass


def install(style):
    """Install fake qgis modules for ``style`` ('legacy' or 'modern')."""
    assert style in ("legacy", "modern")
    purge_plugin_and_qgis_modules()

    qgis = _AutoModule("qgis")
    core = _AutoModule("qgis.core")
    gui = _AutoModule("qgis.gui")
    pyqt = _AutoModule("qgis.PyQt")
    qtcore = _AutoModule("qgis.PyQt.QtCore")
    class _Qt5Gui(_AutoModule):
        """Qt5's QtGui has no QAction: importing it must raise ImportError."""

        def __getattr__(self, name):
            if name == "QAction":
                raise AttributeError(name)
            return _AutoModule.__getattr__(self, name)

    qtgui = (_Qt5Gui if style == "legacy" else _AutoModule)("qgis.PyQt.QtGui")
    qtwidgets = _AutoModule("qgis.PyQt.QtWidgets")
    qgis.core, qgis.gui, qgis.PyQt = core, gui, pyqt
    pyqt.QtCore, pyqt.QtGui, pyqt.QtWidgets = qtcore, qtgui, qtwidgets

    # --- Qt ---------------------------------------------------------------
    qtcore.pyqtSignal = lambda *a, **k: None
    qtcore.QT_VERSION_STR = "5.15.3" if style == "legacy" else "6.8.0"
    qtcore.PYQT_VERSION_STR = "5.15.9" if style == "legacy" else "6.8.0"

    meta_members = {
        "Int": MetaEnum(2, "Int"),
        "LongLong": MetaEnum(4, "LongLong"),
        "Double": MetaEnum(6, "Double"),
        "QString": MetaEnum(10, "QString"),
    }
    meta = type("QMetaType", (), {})
    meta.Type = _Namespace(**meta_members)
    for key, value in meta_members.items():
        setattr(meta, key, value)
    qtcore.QMetaType = meta

    variant = type("QVariant", (), {})
    if style == "legacy":
        for key, number in (("Int", 2), ("LongLong", 4), ("Double", 6), ("String", 10)):
            setattr(variant, key, VariantEnum(number, key))
    qtcore.QVariant = variant

    class QAction(Dummy):
        pass

    if style == "legacy":
        qtwidgets.QAction = QAction
    else:
        qtgui.QAction = QAction

    # --- qgis.core ---------------------------------------------------------
    core.NULL = FakeQgsNull()

    accepted = VariantEnum if style == "legacy" else MetaEnum

    class QgsField:
        def __init__(self, name="", type=None, typeName="", len=0, prec=0, comment="", subType=None):
            if isinstance(name, QgsField):  # copy constructor
                self._name, self._type, self._len = name._name, name._type, name._len
                return
            if not isinstance(type, accepted):
                raise TypeError("QgsField: argument 2 has unexpected type {!r}".format(type))
            self._name, self._type, self._len = name, type, len

        def name(self):
            return self._name

        def setName(self, value):
            self._name = value

        def type(self):
            return self._type

        def length(self):
            return self._len

    core.QgsField = QgsField

    geometry_members = {"Point": "pt", "Line": "line", "Polygon": "poly", "Null": "null"}
    qgis_cls = type("Qgis", (), {"version": staticmethod(lambda: "9.9.9-stub")})
    wkb = type("QgsWkbTypes", (), {"geometryType": staticmethod(lambda wkb: wkb)})
    units = type("QgsUnitTypes", (), {})
    writer = type("QgsVectorFileWriter", (), {})
    if style == "legacy":
        for key, value in geometry_members.items():
            setattr(wkb, key + "Geometry", value)
        units.DistanceMeters = "metres"
        qgis_cls.Critical = "critical"
        writer.NoError = 0
        writer.CreateOrOverwriteFile = 1
        writer.CreateOrOverwriteLayer = 2
        writer.WriterError = type("WriterError", (), {})          # enum type without members
        writer.ActionOnExistingFile = type("ActionOnExistingFile", (), {})
    else:
        qgis_cls.GeometryType = _Namespace(**geometry_members)
        qgis_cls.DistanceUnit = _Namespace(Meters="metres")
        qgis_cls.MessageLevel = _Namespace(Critical="critical")
        writer.WriterError = _Namespace(NoError=0)
        writer.ActionOnExistingFile = _Namespace(CreateOrOverwriteFile=1, CreateOrOverwriteLayer=2)
    core.Qgis, core.QgsWkbTypes, core.QgsUnitTypes, core.QgsVectorFileWriter = qgis_cls, wkb, units, writer

    for module in (qgis, core, gui, pyqt, qtcore, qtgui, qtwidgets):
        sys.modules[module.__name__] = module
    return types.SimpleNamespace(QgsField=QgsField, geometry_members=geometry_members,
                                 QAction=QAction, style=style)
