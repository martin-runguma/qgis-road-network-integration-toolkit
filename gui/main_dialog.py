# -*- coding: utf-8 -*-
"""Main guided interface for Road Network Integration Toolkit.

This stage provides file-based input selectors, a QGIS CRS selector,
methodology selection, and output-folder controls. All three methodologies use the shared legacy-compatible processing engine.

Log colours: black = normal, green = success, orange = warning, red = error.
"""

import html
import os
from contextlib import contextmanager
from datetime import datetime

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsCsException,
    QgsProject,
    QgsProviderRegistry,
    QgsSettings,
    QgsUnitTypes,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgsProjectionSelectionWidget
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor, QIcon, QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFileDialog,
    QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMenu, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from ..core.compat import (
    LINE_GEOMETRY, METERS, NULL_GEOMETRY, POINT_GEOMETRY, POLYGON_GEOMETRY,
)
from ..core.datasource_utils import (
    datasource_exists, gdb_write_supported, geometry_matches,
    geometry_description, is_file_geodatabase, load_vector_layer,
)


# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
SETTINGS_PREFIX = "RoadNetworkIntegration/"

# Log colours, chosen to stay readable on the log's white background.
LOG_COLOURS = {
    "info": "#000000",     # normal text: black
    "success": "#1E7B34",  # green
    "warning": "#C25E00",  # orange
    "error": "#C62828",    # red
}

# Words added to warning/error lines so the meaning never depends on colour alone.
LOG_TAGS = {"info": "", "success": "", "warning": "WARNING", "error": "ERROR"}

# Workflow defaults taken from the finalized road-merging scripts (metres).
ADVANCED_DEFAULTS = {
    "base_buffer": 20.0,
    "secondary_buffer": 10.0,
    "join_gap": 25.0,
    "mid_gap": 10.0,
    "centroid_max_dist": 15.0,
}
ADVANCED_LABELS = (
    ("base_buffer", "Priority road buffer distance"),
    ("secondary_buffer", "Secondary road buffer distance"),
    ("join_gap", "Maximum snapping distance"),
    ("mid_gap", "Midpoint densification interval"),
    ("centroid_max_dist", "Maximum centroid adjustment distance"),
)

DEFAULT_PATH_TOOLTIP = (
    "This field displays the datasource path. Use Browse to select a file or "
    "a specific feature layer inside a GeoPackage (.gpkg) or File Geodatabase (.gdb)."
)

INVALID_NAME_CHARS = '<>:"/\\|?*'


# ----------------------------------------------------------------------
# Small helpers (module level so they can be tested without a GUI)
# ----------------------------------------------------------------------
@contextmanager
def _busy_cursor():
    """Show a wait cursor while slow datasource work is running."""
    QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
    try:
        yield
    finally:
        QApplication.restoreOverrideCursor()


def _run_dialog(dialog):
    """Run a dialog modally on both PyQt5 (exec_) and PyQt6 (exec)."""
    runner = getattr(dialog, "exec", None) or dialog.exec_
    return runner()


_GEOMETRY_KINDS = (
    ("point", POINT_GEOMETRY),
    ("line", LINE_GEOMETRY),
    ("polygon", POLYGON_GEOMETRY),
    ("none", NULL_GEOMETRY),
)


def geometry_kind_of(wkb_type):
    """Map a WKB type to 'point', 'line', 'polygon', 'none' or 'unknown'."""
    geometry_type = QgsWkbTypes.geometryType(wkb_type)
    for kind, constant in _GEOMETRY_KINDS:
        if geometry_type == constant:
            return kind
    return "unknown"


def utm_epsg_for(lon, lat):
    """Return (EPSG code, zone, hemisphere letter) of the UTM zone for lon/lat."""
    lon = ((lon + 180.0) % 360.0) - 180.0
    zone = min(60, max(1, int((lon + 180.0) // 6) + 1))
    north = lat >= 0.0
    return (32600 if north else 32700) + zone, zone, ("N" if north else "S")


def invalid_name_chars(name):
    """Return the characters in `name` that cannot be used in a file name."""
    return sorted({c for c in name if c in INVALID_NAME_CHARS or ord(c) < 32})


def format_log_html(message, level="info", bold=False, stamp=None):
    """Return one colour-coded, HTML-escaped log line."""
    colour = LOG_COLOURS.get(level, LOG_COLOURS["info"])
    tag = LOG_TAGS.get(level, "")
    stamp = stamp or datetime.now().strftime("%H:%M:%S")
    text = "[{}] ".format(stamp)
    if tag:
        text += "{}: ".format(tag)
    text += str(message)
    escaped = html.escape(text).replace("\n", "<br>").replace("  ", "&nbsp;&nbsp;")
    if bold:
        escaped = "<b>{}</b>".format(escaped)
    return '<span style="color:{};">{}</span>'.format(colour, escaped)


class LayerChooserDialog(QDialog):
    """Themed layer picker: choose one feature layer from a drop-down.

    Replaces QInputDialog so the chooser matches the main toolkit window.
    """

    def __init__(self, parent, prompt, labels):
        super().__init__(parent)
        self.setObjectName("RoadNetworkChooserDialog")
        self.setWindowTitle("Choose feature layer")
        self.setModal(True)
        self.setMinimumWidth(660)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        heading = QLabel("Choose feature layer")
        heading.setObjectName("pluginTitle")
        subtitle = QLabel(prompt)
        subtitle.setObjectName("pluginSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        card = QGroupBox("Available feature layers")
        card_layout = QVBoxLayout(card)
        self.combo = QComboBox()
        self.combo.addItems(labels)
        self.combo.setMaxVisibleItems(12)
        self.combo.setMinimumContentsLength(48)
        self.combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        # Let the drop-down list be as wide as its longest entry.
        self.combo.view().setMinimumWidth(self.combo.view().sizeHintForColumn(0) + 24)
        self.detail = QLabel()
        self.detail.setObjectName("helpText")
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.combo.currentIndexChanged.connect(self._update_detail)
        card_layout.addWidget(self.combo)
        card_layout.addWidget(self.detail)
        layout.addWidget(card)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel_button = QPushButton("Cancel")
        select_button = QPushButton("Select layer")
        select_button.setObjectName("primaryButton")
        select_button.setDefault(True)
        cancel_button.clicked.connect(self.reject)
        select_button.clicked.connect(self.accept)
        buttons.addWidget(cancel_button)
        buttons.addWidget(select_button)
        layout.addLayout(buttons)

        self._update_detail()

    def _update_detail(self, *_args):
        """Show the full text of the highlighted layer (long names are elided in the box)."""
        self.detail.setText("Selected: {}".format(self.combo.currentText()))

    def selected_index(self):
        """Index of the chosen layer in the list of labels given to the dialog."""
        return self.combo.currentIndex()


class RoadNetworkIntegrationDialog(QDialog):
    """Main plugin window for selecting and validating input data."""

    INPUT_FILTER = (
        "Supported vector data (*.shp *.gpkg *.geojson *.json *.gml *.kml *.tab *.mif *.dxf);;"
        "All files (*.*)"
    )
    OUTPUT_SUFFIX = "_Road_Network_Harmonized"

    # True  = operating-system file dialogs (fast, familiar, but they cannot be themed).
    # False = Qt file dialogs styled like the rest of the toolkit.
    NATIVE_FILE_DIALOGS = True

    LABEL_PRIORITY = "Priority roads"
    LABEL_SECONDARY = "Secondary roads"
    LABEL_BOUNDARY = "Study-area boundary"

    def __init__(self, iface, parent=None):
        super().__init__(parent or iface.mainWindow())
        self.iface = iface
        self._crs_user_set = False  # becomes True once the user picks a CRS themselves
        self._active_task = None
        self._is_processing = False
        self._run_log_path = ""
        self._run_log_error = ""
        plugin_dir = os.path.dirname(os.path.dirname(__file__))
        self.setObjectName("RoadNetworkIntegrationDialog")
        self.setWindowTitle("Road Network Integration Toolkit")
        self.setWindowIcon(QIcon(os.path.join(plugin_dir, "icon.png")))
        self.setModal(False)
        # Request a native minimise button beside the standard close button.
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinimizeButtonHint)
        # Closing destroys this instance; reopening the plugin creates a clean dialog.
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.resize(900, 850)
        self.setMinimumSize(820, 740)
        self._build_ui()
        self._load_settings()
        self._update_output_preview()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        """Build a scrollable, OSM-Toolkit-inspired interface."""
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("contentWidget")
        root = QVBoxLayout(content)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        root.addLayout(self._build_header())
        root.addWidget(self._build_input_group())
        root.addWidget(self._build_settings_group())
        root.addWidget(self._build_advanced_group())
        root.addWidget(self._build_output_group())
        root.addWidget(self._build_log_group())

        scroll.setWidget(content)
        outer_layout.addWidget(scroll, 1)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        outer_layout.addWidget(line)
        outer_layout.addLayout(self._build_buttons())

        self._apply_stylesheet()

    def _build_header(self):
        """Title and subtitle using the OSM Data Toolkit blue/green palette."""
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title = QLabel("Road Network Integration Toolkit")
        title.setObjectName("pluginTitle")
        subtitle = QLabel("Integrate complementary road networks using a guided workflow")
        subtitle.setObjectName("pluginSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col, 1)
        return header

    def _build_input_group(self):
        """1. Input data: each row has a path field and matching browse controls."""
        input_group = QGroupBox("1. Input data")
        input_layout = QFormLayout(input_group)
        input_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        input_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        input_layout.setHorizontalSpacing(12)
        input_layout.setVerticalSpacing(9)

        self.priority_path = self._make_path_row(
            "Select the priority road dataset", self.LABEL_PRIORITY, "line"
        )
        self.secondary_path = self._make_path_row(
            "Select the secondary road dataset", self.LABEL_SECONDARY, "line"
        )
        self.boundary_path = self._make_path_row(
            "Select the study-area boundary", self.LABEL_BOUNDARY, "polygon"
        )
        input_layout.addRow("Priority road network (Path):", self.priority_path[0])
        input_layout.addRow("Secondary road network (Path):", self.secondary_path[0])
        input_layout.addRow("Study area boundary (Polygon):", self.boundary_path[0])

        supported_note = QLabel(
            "Use Browse to choose a vector file or a layer inside a GeoPackage (.gpkg) or "
            "File Geodatabase (.gdb). Only layers with the expected geometry type (lines for "
            "roads, polygons for the boundary) are offered."
        )
        supported_note.setWordWrap(True)
        input_layout.addRow(supported_note)
        return input_group

    def _build_settings_group(self):
        """2. Integration settings: methodology and analysis CRS."""
        settings_group = QGroupBox("2. Integration settings")
        settings_form = QFormLayout(settings_group)
        settings_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        settings_form.setVerticalSpacing(9)

        self.method_combo = QComboBox()
        self.method_model = QStandardItemModel(self.method_combo)
        method1 = QStandardItem("Methodology 1 — Direct Merge")
        method1.setData("methodology_1", Qt.ItemDataRole.UserRole)
        self.method_model.appendRow(method1)
        for label, key in (
            ("Methodology 2 — Clip + Snap", "methodology_2"),
            ("Methodology 3 — Targeted Snap", "methodology_3"),
        ):
            item = QStandardItem(label)
            item.setData(key, Qt.ItemDataRole.UserRole)
            self.method_model.appendRow(item)
        self.method_combo.setModel(self.method_model)
        self.method_combo.setCurrentIndex(max(0, self.method_combo.findData("methodology_3")))
        self.method_combo.setToolTip(
            "Methodology 1 directly merges secondary roads classified as missing_1 to missing_4. "
            "Methodology 2 trims secondary roads by priority-road buffers and snaps their endpoints. "
            "Methodology 3 uses secondary square buffers and targeted centroid/endpoint snapping."
        )
        settings_form.addRow("Merging methodology:", self.method_combo)

        # CRS selector plus a shortcut that suggests the UTM zone of the study area.
        crs_row = QHBoxLayout()
        self.crs_widget = QgsProjectionSelectionWidget()
        project_crs = QgsProject.instance().crs()
        if project_crs.isValid():
            self.crs_widget.setCrs(project_crs)
        self.crs_widget.setToolTip(
            "Choose the projected coordinate reference system used for distance and snapping operations. "
            "Select a suitable local projected CRS for your study area."
        )
        self.crs_widget.crsChanged.connect(self._on_crs_changed)
        self.suggest_crs_button = QPushButton("Suggest from study area")
        self.suggest_crs_button.setToolTip(
            "Select the UTM zone that contains the centre of the study-area boundary."
        )
        self.suggest_crs_button.clicked.connect(self._on_suggest_crs_clicked)
        crs_row.addWidget(self.crs_widget, 1)
        crs_row.addWidget(self.suggest_crs_button)
        settings_form.addRow("Analysis CRS / projection:", crs_row)

        crs_note = QLabel(
            "Choose this the same way you select a CRS in QGIS export or reprojection tools. "
            "A projected CRS with metre units is required for distance-based processing. "
            "When you pick a study-area boundary, a suitable UTM zone is suggested automatically "
            "unless you have already chosen a CRS yourself."
        )
        crs_note.setWordWrap(True)
        settings_form.addRow(crs_note)
        return settings_group

    def _build_advanced_group(self):
        """Advanced settings: defaults are shown but disabled until the group is ticked."""
        self.advanced_group = QGroupBox("Advanced settings — check to edit")
        self.advanced_group.setCheckable(True)
        self.advanced_group.setChecked(False)

        advanced_form = QFormLayout(self.advanced_group)
        advanced_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        advanced_form.setVerticalSpacing(8)

        def make_distance_control(default_value, tooltip):
            """Create a distance input with metre units and a default value."""
            control = QDoubleSpinBox()
            control.setRange(0.01, 100000.0)
            control.setDecimals(2)
            control.setSingleStep(1.0)
            control.setSuffix(" m")
            control.setValue(default_value)
            control.setToolTip(tooltip)
            return control

        self.base_buffer_spin = make_distance_control(
            ADVANCED_DEFAULTS["base_buffer"], "Buffer distance for the priority road network."
        )
        self.secondary_buffer_spin = make_distance_control(
            ADVANCED_DEFAULTS["secondary_buffer"], "Buffer distance for the secondary road network."
        )
        self.join_gap_spin = make_distance_control(
            ADVANCED_DEFAULTS["join_gap"], "Maximum snapping distance between road features."
        )
        self.mid_gap_spin = make_distance_control(
            ADVANCED_DEFAULTS["mid_gap"], "Midpoint densification interval."
        )
        self.centroid_max_dist_spin = make_distance_control(
            ADVANCED_DEFAULTS["centroid_max_dist"], "Maximum centroid-to-vertex adjustment distance."
        )
        self._advanced_spins = {
            "base_buffer": self.base_buffer_spin,
            "secondary_buffer": self.secondary_buffer_spin,
            "join_gap": self.join_gap_spin,
            "mid_gap": self.mid_gap_spin,
            "centroid_max_dist": self.centroid_max_dist_spin,
        }
        for key, label in ADVANCED_LABELS:
            advanced_form.addRow(label + ":", self._advanced_spins[key])

        advanced_note = QLabel(
            "The displayed values are the workflow defaults, in metres. "
            "Tick Advanced settings to edit them; unticking restores the defaults. "
            "These values are passed to the legacy-compatible processing engine for buffer, trimming, and snapping operations."
        )
        advanced_note.setWordWrap(True)
        advanced_note.setObjectName("helpText")
        advanced_form.addRow(advanced_note)

        self.advanced_group.toggled.connect(self._on_advanced_toggled)
        return self.advanced_group

    def _build_output_group(self):
        """3. Output settings: the folder is both working folder and destination."""
        output_group = QGroupBox("3. Output settings")
        output_layout = QFormLayout(output_group)
        output_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        output_layout.setVerticalSpacing(9)

        output_row = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select the mandatory output / working folder...")
        self.output_path.setClearButtonEnabled(True)
        self.output_path.setToolTip(
            "Required. This folder will be used as both the working "
            "directory and the output destination."
        )
        self.output_path.textChanged.connect(self._update_output_preview)
        self.browse_output_button = QPushButton("Browse...")
        self.browse_output_button.clicked.connect(self._browse_output_folder)
        output_row.addWidget(self.output_path, 1)
        output_row.addWidget(self.browse_output_button)
        output_layout.addRow("Output / working folder:", output_row)

        self.output_name = QLineEdit()
        self.output_name.setPlaceholderText("Enter a project or city code, e.g. KE_Nairobi")
        self.output_name.setToolTip(
            "Enter the prefix only. The toolkit adds "
            "'{}' automatically.".format(self.OUTPUT_SUFFIX)
        )
        self.output_name.textChanged.connect(self._update_output_preview)
        output_layout.addRow("Output name / prefix:", self.output_name)

        self.output_type_combo = QComboBox()
        self.output_type_combo.addItem("GeoPackage (.gpkg)", "gpkg")
        self.output_type_combo.addItem("Shapefile (.shp)", "shp")
        self.output_type_combo.addItem("File Geodatabase (.gdb)", "gdb")
        self.output_type_combo.setToolTip(
            "Choose the format for the final harmonized road-network output."
        )
        self.output_type_combo.currentIndexChanged.connect(self._update_output_preview)
        output_layout.addRow("Output data type:", self.output_type_combo)

        self.output_preview = QLabel("Enter an output name to preview the final filename.")
        self.output_preview.setWordWrap(True)
        self.output_preview.setObjectName("helpText")
        self.output_preview.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        output_layout.addRow("Output preview:", self.output_preview)

        self.add_outputs_checkbox = QCheckBox(
            "Automatically add successful outputs to the QGIS project"
        )
        self.add_outputs_checkbox.setChecked(False)
        output_layout.addRow("", self.add_outputs_checkbox)

        self.keep_intermediates_checkbox = QCheckBox("Keep intermediate diagnostic layers")
        self.keep_intermediates_checkbox.setChecked(False)
        output_layout.addRow("", self.keep_intermediates_checkbox)
        return output_group

    def _build_log_group(self):
        """Processing status, progress bar, and colour-coded process log."""
        log_group = QGroupBox("Processing progress and log")
        log_layout = QVBoxLayout(log_group)
        self.processing_status_label = QLabel("Ready. Select your inputs and run a methodology.")
        self.processing_status_label.setObjectName("helpText")
        self.processing_status_label.setWordWrap(True)
        log_layout.addWidget(self.processing_status_label)

        self.processing_progress = QProgressBar()
        self.processing_progress.setRange(0, 100)
        self.processing_progress.setValue(0)
        self.processing_progress.setTextVisible(True)
        self.processing_progress.setFormat("%p%")
        self.processing_progress.setMinimumHeight(18)
        log_layout.addWidget(self.processing_progress)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Validation and processing messages will appear here.")
        self.log_output.setMaximumBlockCount(3000)
        self.log_output.setMinimumHeight(125)
        log_layout.addWidget(self.log_output)

        legend = QLabel(
            '<span style="color:{info};">Black: normal</span> &nbsp;|&nbsp; '
            '<span style="color:{success};">Green: success</span> &nbsp;|&nbsp; '
            '<span style="color:{warning};">Orange: warning</span> &nbsp;|&nbsp; '
            '<span style="color:{error};">Red: error</span>'.format(**LOG_COLOURS)
        )
        legend.setObjectName("helpText")
        self.clear_log_button = QPushButton("Clear log")
        self.clear_log_button.clicked.connect(self.log_output.clear)
        legend_row = QHBoxLayout()
        legend_row.addWidget(legend, 1)
        legend_row.addWidget(self.clear_log_button)
        log_layout.addLayout(legend_row)
        return log_group

    def _build_buttons(self):
        """Validate / Run / Close buttons."""
        buttons = QHBoxLayout()
        self.validate_button = QPushButton("Validate Inputs")
        self.run_button = QPushButton("Run Integration")
        self.run_button.setObjectName("primaryButton")
        self.run_button.setEnabled(True)
        self.cancel_button = QPushButton("Cancel Run")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setToolTip(
            "Stop the running integration. Processing stops at the next safe checkpoint, "
            "and the final output is not replaced."
        )
        self.close_button = QPushButton("Close")
        self.cancel_button.clicked.connect(self._cancel_run)
        self.validate_button.clicked.connect(self.validate_inputs)
        self.run_button.clicked.connect(self.run_integration)
        self.close_button.clicked.connect(self.close)
        self.run_button.setToolTip(
            "Run the selected integration methodology. Inputs and output settings will be checked before processing."
        )
        buttons.addWidget(self.validate_button)
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.close_button)
        return buttons

    def _apply_stylesheet(self):
        """Light theme. Text colours are set explicitly so dark QGIS themes stay readable."""
        self.setStyleSheet("""
            QDialog#RoadNetworkIntegrationDialog, QDialog#RoadNetworkChooserDialog,
            QMessageBox#RoadNetworkMessageBox, QFileDialog#RoadNetworkFileDialog { background: #F7F9FB; }
            QMessageBox#RoadNetworkMessageBox QLabel, QFileDialog#RoadNetworkFileDialog QLabel {
                color: #1B2A33; font-weight: 400;
            }
            QMessageBox#RoadNetworkMessageBox QPushButton:default {
                color: #FFFFFF; background: #1499D6; border-color: #0B5E8E; font-weight: 600;
            }
            QMessageBox#RoadNetworkMessageBox QPushButton:default:hover { background: #0B5E8E; }
            QFileDialog#RoadNetworkFileDialog QAbstractItemView {
                background: #FFFFFF; color: #1B2A33; border: 1px solid #C9D5DE;
                selection-background-color: #1499D6; selection-color: #FFFFFF;
            }
            QWidget#contentWidget { background: #F7F9FB; }
            QGroupBox {
                font-weight: 600; color: #17313F;
                border: 1px solid #C9D5DE; border-radius: 6px;
                margin-top: 10px; padding: 10px 8px 8px 8px;
                background: #FFFFFF;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QGroupBox QLabel, QGroupBox QCheckBox { color: #1B2A33; font-weight: 400; }
            QLabel#pluginTitle { font-size: 18px; font-weight: 700; color: #0B5E8E; }
            QLabel#pluginSubtitle { color: #606A73; padding-bottom: 3px; }
            QGroupBox QLabel#helpText { color: #596A75; font-weight: 400; }
            QLineEdit, QComboBox, QDoubleSpinBox {
                min-height: 25px; padding: 3px 6px; color: #1B2A33;
                border: 1px solid #B8C7D1; border-radius: 4px; background: #FFFFFF;
            }
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus { border: 1px solid #1499D6; }
            QComboBox { combobox-popup: 0; }
            QComboBox QAbstractItemView {
                background: #FFFFFF; color: #1B2A33; border: 1px solid #B8C7D1; outline: 0;
                selection-background-color: #1499D6; selection-color: #FFFFFF;
            }
            QDoubleSpinBox:disabled { color: #7A868E; background: #F0F3F5; }
            QPushButton {
                padding: 6px 12px; min-height: 23px; color: #1B2A33;
                border: 1px solid #B8C7D1; border-radius: 4px; background: #F2F6F8;
            }
            QPushButton:hover { border-color: #1499D6; background: #EAF6FC; }
            QPushButton:disabled { color: #8A9298; background: #E9ECEF; }
            QPushButton#primaryButton { color: #FFFFFF; background: #1499D6; border-color: #0B5E8E; font-weight: 600; }
            QPushButton#primaryButton:hover { background: #0B5E8E; }
            QPushButton#primaryButton:disabled { color: #DDE7EE; background: #8FB9D1; border-color: #8FB9D1; }
            QPlainTextEdit { border: 1px solid #C9D5DE; border-radius: 4px; background: #FFFFFF; color: #000000; }
            QProgressBar { border: 1px solid #B8C7D1; border-radius: 4px; text-align: center; background: #FFFFFF; color: #17313F; }
            QProgressBar::chunk { background: #1499D6; border-radius: 3px; }
            QCheckBox { spacing: 7px; }
        """)

    # ------------------------------------------------------------------
    # Path rows and browsing
    # ------------------------------------------------------------------
    def _make_path_row(self, placeholder, label, geometry_kind):
        """Create one path field with a Browse menu (vector file or File Geodatabase)."""
        row_widget = QWidget()
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(5)
        path_edit = QLineEdit()
        path_edit.setPlaceholderText(placeholder)
        path_edit.setClearButtonEnabled(True)
        path_edit.setToolTip(DEFAULT_PATH_TOOLTIP)
        # The provider URI is stored separately from the friendly text shown to users.
        path_edit.setProperty("source_uri", "")
        path_edit.setProperty("source_path", "")
        path_edit.setProperty("source_layer_name", "")
        path_edit.setProperty("geometry_kind", geometry_kind)
        path_edit.textEdited.connect(lambda _text, edit=path_edit: self._clear_selected_source(edit))

        # Attaching the menu to the button makes it open right under Browse.
        browse_button = QPushButton("Browse…")
        browse_button.setToolTip(
            "Browse for a vector file or a feature layer inside a GeoPackage/File Geodatabase"
        )
        menu = QMenu(browse_button)
        file_action = menu.addAction("Vector file or GeoPackage…")
        gdb_action = menu.addAction("File Geodatabase (.gdb)…")
        file_action.triggered.connect(
            lambda _checked=False, edit=path_edit, title=label: self._browse_vector_file(edit, title)
        )
        gdb_action.triggered.connect(
            lambda _checked=False, edit=path_edit, title=label: self._browse_geodatabase(edit, title)
        )
        browse_button.setMenu(menu)

        row.addWidget(path_edit, 1)
        row.addWidget(browse_button)
        return row_widget, path_edit, geometry_kind

    def _clear_selected_source(self, line_edit):
        """Discard the previously selected provider URI when the user edits the field."""
        line_edit.setProperty("source_uri", "")
        line_edit.setProperty("source_path", "")
        line_edit.setProperty("source_layer_name", "")
        line_edit.setToolTip(DEFAULT_PATH_TOOLTIP)

    def _start_directory(self, line_edit):
        """Choose where a browse dialog should open."""
        start = (
            line_edit.property("source_path")
            or line_edit.text().strip()
            or self._setting("last_input_dir", "")
            or os.path.expanduser("~")
        )
        if os.path.isfile(start):
            start = os.path.dirname(start)
        elif os.path.isdir(start) and is_file_geodatabase(start):
            start = os.path.dirname(start)
        if not os.path.isdir(start):
            start = self._setting("last_input_dir", "") or os.path.expanduser("~")
        return start

    def _remember_input_dir(self, path):
        """Remember the folder of the last chosen input for the next browse."""
        folder = path.rstrip("/\\")
        folder = os.path.dirname(folder) if os.path.exists(folder) else folder
        if os.path.isdir(folder):
            self._store_setting("last_input_dir", folder)

    # ------------------------------------------------------------------
    # Themed popups and file dialogs
    # ------------------------------------------------------------------
    def _show_message(self, kind, title, text):
        """Show a message box that matches the toolkit theme. kind: warning/information/critical."""
        icons = {
            "warning": QMessageBox.Icon.Warning,
            "information": QMessageBox.Icon.Information,
            "critical": QMessageBox.Icon.Critical,
        }
        box = QMessageBox(self)
        box.setObjectName("RoadNetworkMessageBox")
        box.setIcon(icons.get(kind, QMessageBox.Icon.Information))
        box.setWindowTitle(title)
        box.setTextFormat(Qt.TextFormat.PlainText)  # paths and messages are shown literally
        box.setText(text)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setDefaultButton(QMessageBox.StandardButton.Ok)
        _run_dialog(box)

    def _themed_file_dialog(self, title, start):
        """A Qt (non-native) file dialog styled like the rest of the toolkit."""
        dialog = QFileDialog(self, title, start)
        dialog.setObjectName("RoadNetworkFileDialog")
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        return dialog

    def _pick_open_file(self, title, start):
        """Choose one vector file. Returns the path, or '' if cancelled."""
        if self.NATIVE_FILE_DIALOGS:
            path, _ = QFileDialog.getOpenFileName(self, title, start, self.INPUT_FILTER)
            return path
        dialog = self._themed_file_dialog(title, start)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter(self.INPUT_FILTER)
        if _run_dialog(dialog) and dialog.selectedFiles():
            return dialog.selectedFiles()[0]
        return ""

    def _pick_folder(self, title, start):
        """Choose a folder. Returns the path, or '' if cancelled."""
        if self.NATIVE_FILE_DIALOGS:
            return QFileDialog.getExistingDirectory(self, title, start)
        dialog = self._themed_file_dialog(title, start)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if _run_dialog(dialog) and dialog.selectedFiles():
            return dialog.selectedFiles()[0]
        return ""

    def _browse_vector_file(self, line_edit, title):
        """Pick a vector file or GeoPackage."""
        path = self._pick_open_file(
            "Select {} vector dataset".format(title), self._start_directory(line_edit)
        )
        if path:
            self._remember_input_dir(path)
            self._select_layer_from_container(line_edit, path, title)

    def _browse_geodatabase(self, line_edit, title):
        """Pick a File Geodatabase. A .gdb is a directory, so use a directory dialog."""
        dialog = self._themed_file_dialog(
            "Select {} File Geodatabase".format(title), self._start_directory(line_edit)
        )
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if not _run_dialog(dialog):
            return
        folders = dialog.selectedFiles()
        if not folders:
            return
        folder = folders[0]
        if not is_file_geodatabase(folder):
            self._show_message(
                "warning", "File Geodatabase", "Please select the .gdb directory itself."
            )
            return
        self._remember_input_dir(folder)
        self._select_layer_from_container(line_edit, folder, title)

    # ------------------------------------------------------------------
    # Layer discovery and selection
    # ------------------------------------------------------------------
    def _discover_candidates(self, path, expected_kind):
        """Find feature layers in a datasource without opening each of them.

        Returns (candidates, skipped). Layers whose geometry type differs from
        `expected_kind` ('line' / 'polygon') are skipped, so users are never offered
        points, tables or the wrong geometry. Feature counts and geometry types come
        from QGIS's sublayer discovery; a layer is only opened if its type is unknown.
        """
        candidates = []
        skipped = []
        seen_uris = set()

        self._log("Discovering feature layers: {}".format(path))
        try:
            details = QgsProviderRegistry.instance().querySublayers(path)
        except Exception as exc:  # providers can raise several exception types
            details = []
            self._log("Sublayer discovery failed: {}".format(exc), "error")
        else:
            self._log("QGIS discovered {} sublayer candidate(s).".format(len(details)))

        for detail in details:
            try:
                uri = detail.uri()
                name = detail.name() or "Unnamed layer"
                provider = detail.providerKey() or "ogr"
                if not uri or uri in seen_uris:
                    continue
                seen_uris.add(uri)

                if provider != "ogr":
                    skipped.append((name, "not a vector layer"))
                    continue

                wkb_type = detail.wkbType()
                count = detail.featureCount()
                kind = geometry_kind_of(wkb_type)

                if kind == "unknown":
                    # Geometry type not reported by discovery: open the layer to find out.
                    layer = QgsVectorLayer(uri, name, provider)
                    if not layer.isValid():
                        skipped.append((name, "could not be opened"))
                        self._log("Skipped invalid layer: {}".format(name), "warning")
                        continue
                    wkb_type = layer.wkbType()
                    count = layer.featureCount()
                    kind = geometry_kind_of(wkb_type)

                if kind == "none":
                    skipped.append((name, "table without geometry"))
                elif kind == "unknown":
                    skipped.append((name, "unknown geometry type"))
                elif expected_kind and kind != expected_kind:
                    skipped.append((name, "{} layer".format(kind)))
                else:
                    candidates.append({
                        "name": name,
                        "uri": uri,
                        "provider": provider,
                        "kind": kind,
                        "wkb": wkb_type,
                        "count": count,
                    })
            except Exception as exc:  # keep going: one bad sublayer must not stop discovery
                self._log("Could not inspect a discovered sublayer: {}".format(exc), "warning")

        # Ordinary single-layer files: open the datasource itself if discovery found nothing.
        if not candidates and not skipped and not (
            os.path.isdir(path) and is_file_geodatabase(path)
        ):
            layer = QgsVectorLayer(path, os.path.basename(path), "ogr")
            if layer.isValid():
                kind = geometry_kind_of(layer.wkbType())
                if not expected_kind or kind == expected_kind:
                    candidates.append({
                        "name": layer.name(),
                        "uri": path,
                        "provider": "ogr",
                        "kind": kind,
                        "wkb": layer.wkbType(),
                        "count": layer.featureCount(),
                    })
                else:
                    skipped.append((layer.name(), "{} layer".format(kind)))

        for name, reason in skipped:
            self._log("Skipped '{}': {}.".format(name, reason))
        return candidates, skipped

    @staticmethod
    def _summarise_skipped(skipped, limit=6):
        """Short human-readable list of skipped layers for messages."""
        if not skipped:
            return ""
        parts = ["{} ({})".format(name, reason) for name, reason in skipped[:limit]]
        if len(skipped) > limit:
            parts.append("and {} more".format(len(skipped) - limit))
        return "Skipped: " + "; ".join(parts) + "."

    def _select_layer_from_container(self, line_edit, path, title):
        """Use QGIS sublayer discovery to select a feature layer."""
        expected_kind = line_edit.property("geometry_kind") or ""
        with _busy_cursor():
            candidates, skipped = self._discover_candidates(path, expected_kind)

        if not candidates:
            self._log(
                "No readable {} feature layers found: {}".format(expected_kind or "vector", path),
                "error",
            )
            self._show_message(
                "warning",
                "No feature layers found",
                "QGIS did not find a readable {} feature layer in:\n\n{}\n\n{}\n\n"
                "Check the log for discovery details.".format(
                    expected_kind or "vector", path, self._summarise_skipped(skipped)
                ).replace("\n\n\n\n", "\n\n"),
            )
            return

        # Always let the user choose a layer inside GDB/GPKG containers.
        extension = os.path.splitext(path.rstrip("/\\"))[1].lower()
        is_gdb = os.path.isdir(path) and is_file_geodatabase(path)
        is_gpkg = extension == ".gpkg"

        if is_gdb or is_gpkg or len(candidates) > 1:
            labels = []
            for item in candidates:
                count = item["count"]
                count_text = "{:,} feature(s)".format(count) if count >= 0 else "feature count unavailable"
                labels.append("{} | {} | {}".format(
                    item["name"], count_text, QgsWkbTypes.displayString(item["wkb"])
                ))

            chooser = LayerChooserDialog(
                self, "Select the feature layer for {}:".format(title.lower()), labels
            )
            if not _run_dialog(chooser):
                return
            selected = candidates[chooser.selected_index()]
        else:
            selected = candidates[0]

        layer = self._apply_selection(line_edit, path, selected)
        if layer is None:
            self._show_message(
                "warning",
                "Layer could not be opened",
                "QGIS could not open the layer '{}'. See the log for details.".format(selected["name"]),
            )
            return

        self._log(
            "Selected {} layer '{}' ({} feature(s)).".format(
                title, selected["name"], layer.featureCount()
            ),
            "success",
        )
        if line_edit is self.boundary_path[1]:
            self._suggest_analysis_crs(layer)

    def _apply_selection(self, line_edit, path, selected):
        """Store a chosen layer on the path field. Returns the opened layer, or None."""
        layer = QgsVectorLayer(selected["uri"], selected["name"], selected["provider"])
        if not layer.isValid():
            self._log("Could not open layer '{}'.".format(selected["name"]), "error")
            return None

        # Preserve the actual layer URI for later loading and validation.
        line_edit.setProperty("source_uri", selected["uri"])
        line_edit.setProperty("source_path", path)
        line_edit.setProperty("source_layer_name", selected["name"])
        line_edit.setText(path)
        line_edit.setToolTip(
            "Selected feature layer: {}\n"
            "Datasource: {}\n"
            "Features: {}\n"
            "Geometry: {}\n"
            "CRS: {}".format(
                selected["name"],
                path,
                layer.featureCount(),
                QgsWkbTypes.displayString(layer.wkbType()),
                layer.crs().authid() or "Not defined",
            )
        )
        return layer

    def _resolve_typed_source(self, line_edit, label, expected_kind, errors):
        """Resolve a path typed or pasted by hand, as Browse would, without popups.

        Returns True when exactly one suitable layer was found and selected.
        """
        path = line_edit.text().strip()
        candidates, skipped = self._discover_candidates(path, expected_kind)
        if not candidates:
            errors.append(
                "No readable {} layer found for {} in: {} {}".format(
                    expected_kind, label.lower(), path, self._summarise_skipped(skipped)
                ).strip()
            )
            return False
        if len(candidates) > 1:
            errors.append(
                "The datasource for {} contains {} {} layers. Use Browse to choose the one to use.".format(
                    label.lower(), len(candidates), expected_kind
                )
            )
            return False
        if self._apply_selection(line_edit, path, candidates[0]) is None:
            errors.append("QGIS could not open the layer found for {}.".format(label.lower()))
            return False
        self._log("Resolved {} to layer '{}'.".format(label.lower(), candidates[0]["name"]))
        return True

    # ------------------------------------------------------------------
    # Analysis CRS helpers
    # ------------------------------------------------------------------
    def _on_crs_changed(self, *_args):
        """Remember that the user chose a CRS, so it is not overwritten automatically."""
        self._crs_user_set = True

    def _on_suggest_crs_clicked(self, *_args):
        """Suggest the UTM zone of the boundary on request."""
        edit = self.boundary_path[1]
        if not edit.text().strip():
            self._log("Select the study-area boundary first, then suggest a CRS.", "warning")
            return
        with _busy_cursor():
            if not (edit.property("source_uri") or "") and not self._resolve_typed_source(
                edit, self.LABEL_BOUNDARY, "polygon", []
            ):
                layer = None
            else:
                layer = self._load_vector(edit, self.LABEL_BOUNDARY)
        if layer is None:
            self._log("The study-area boundary could not be opened, so no CRS was suggested.", "error")
            return
        self._suggest_analysis_crs(layer, force=True)

    def _suggest_analysis_crs(self, layer, force=False):
        """Set the analysis CRS to the UTM zone at the centre of `layer`."""
        if self._crs_user_set and not force:
            return
        extent = layer.extent()
        if extent.isNull() or extent.isEmpty() or not layer.crs().isValid():
            return
        try:
            transform = QgsCoordinateTransform(
                layer.crs(),
                QgsCoordinateReferenceSystem("EPSG:4326"),
                QgsProject.instance().transformContext(),
            )
            centre = transform.transform(extent.center())
        except QgsCsException as exc:
            self._log("Could not suggest a UTM zone: {}".format(exc), "warning")
            return
        epsg, zone, hemisphere = utm_epsg_for(centre.x(), centre.y())
        crs = QgsCoordinateReferenceSystem("EPSG:{}".format(epsg))
        if not crs.isValid():
            return
        # Programmatic change: block the signal so it is not counted as a user choice.
        self.crs_widget.blockSignals(True)
        self.crs_widget.setCrs(crs)
        self.crs_widget.blockSignals(False)
        self._log(
            "Analysis CRS set to EPSG:{} (UTM zone {}{}) from the study area. "
            "Change it if you prefer a different local projection.".format(epsg, zone, hemisphere)
        )

    # ------------------------------------------------------------------
    # Advanced settings
    # ------------------------------------------------------------------
    def _on_advanced_toggled(self, checked):
        """Unticking the group restores the defaults so the displayed values are the ones used."""
        if not checked:
            for key, spin in self._advanced_spins.items():
                spin.setValue(ADVANCED_DEFAULTS[key])

    def _advanced_values(self):
        """Current advanced distances in metres."""
        return {key: spin.value() for key, spin in self._advanced_spins.items()}

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------
    def _output_extension(self):
        """Return the extension for the selected output data type."""
        extensions = {"gpkg": ".gpkg", "shp": ".shp", "gdb": ".gdb"}
        return extensions.get(self.output_type_combo.currentData(), ".gpkg")

    def _output_filename(self):
        """Build the final output name from the user-entered prefix."""
        prefix = self.output_name.text().strip()
        if not prefix:
            return ""
        return prefix + self.OUTPUT_SUFFIX + self._output_extension()

    def _update_output_preview(self, *_args):
        """Update the preview when the folder, prefix or format changes."""
        filename = self._output_filename()
        folder = self.output_path.text().strip()
        if not filename:
            self.output_preview.setText(
                "Enter an output name (e.g. KE_Nairobi) to preview the final filename."
            )
        elif folder:
            self.output_preview.setText(os.path.join(folder, filename))
        else:
            self.output_preview.setText(filename)

    def _browse_output_folder(self):
        """Select the destination folder for the outputs."""
        start = self.output_path.text().strip() or self._setting("output_dir", "") or os.path.expanduser("~")
        if not os.path.isdir(start):
            start = os.path.expanduser("~")
        folder = self._pick_folder("Select output folder", start)
        if folder:
            self.output_path.setText(folder)

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------
    @staticmethod
    def _setting(key, default):
        return QgsSettings().value(SETTINGS_PREFIX + key, default, type=type(default))

    @staticmethod
    def _store_setting(key, value):
        QgsSettings().setValue(SETTINGS_PREFIX + key, value)

    def _load_settings(self):
        """Start every dialog instance with a clean form and safe output options."""
        # The last output folder remains the starting location of Browse, but it is
        # not automatically populated: each run must explicitly choose its target.
        self.output_path.clear()
        index = self.output_type_combo.findData("gpkg")
        if index >= 0:
            self.output_type_combo.setCurrentIndex(index)
        self.method_combo.setCurrentIndex(max(0, self.method_combo.findData("methodology_3")))
        self.add_outputs_checkbox.setChecked(False)
        self.keep_intermediates_checkbox.setChecked(False)
        self.processing_progress.setValue(0)
        self.processing_status_label.setText("Ready. Select your inputs and run a methodology.")

    def _save_settings(self):
        """Remember only the last folder as a Browse starting point, not run state."""
        output_dir = self.output_path.text().strip()
        if output_dir and os.path.isdir(output_dir):
            self._store_setting("output_dir", output_dir)

    def done(self, result):
        """Save settings on close; keep the dialog alive while a task is active."""
        if self._is_processing:
            self._log("Processing is still running. Minimize the window and let the task finish before closing.", "warning")
            return
        self._save_settings()
        super().done(result)

    def closeEvent(self, event):
        """Do not destroy the dialog while its background task is using the plugin."""
        if self._is_processing:
            self._log("Close was prevented because processing is active. You can minimize this window while QGIS remains responsive.", "warning")
            self.processing_status_label.setText("Processing is active — minimize this window if you want it out of the way.")
            event.ignore()
            return
        self._save_settings()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Loading sources
    # ------------------------------------------------------------------
    def _load_vector(self, line_edit, display_name):
        """Load the exact feature layer selected in the Browse dialog."""
        path = line_edit.property("source_path") or line_edit.text().strip()
        uri = line_edit.property("source_uri") or ""
        return load_vector_layer(path, uri, display_name)

    @staticmethod
    def _source_exists(line_edit):
        """Check the original datasource path, not its layer-specific URI."""
        path = line_edit.property("source_path") or line_edit.text().strip()
        return datasource_exists(path)

    def _input_specs(self):
        return [
            (self.LABEL_PRIORITY, self.priority_path[1], "line"),
            (self.LABEL_SECONDARY, self.secondary_path[1], "line"),
            (self.LABEL_BOUNDARY, self.boundary_path[1], "polygon"),
        ]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _extents_overlap(layer, boundary_layer):
        """True/False if the layer's extent overlaps the boundary's; None if it cannot be compared."""
        if layer.extent().isNull() or boundary_layer.extent().isNull():
            return None
        try:
            transform = QgsCoordinateTransform(
                layer.crs(), boundary_layer.crs(), QgsProject.instance().transformContext()
            )
            extent = transform.transformBoundingBox(layer.extent())
        except QgsCsException:
            return None
        return extent.intersects(boundary_layer.extent())

    def _check_sources(self, errors, warnings):
        """Validate the three input datasets. Returns {label: (layer, feature_count)}."""
        loaded = {}
        sources = []
        for label, edit, expected_kind in self._input_specs():
            text = edit.text().strip()
            if not text:
                errors.append("Browse to a dataset for {}.".format(label.lower()))
                continue
            path = edit.property("source_path") or text
            if not self._source_exists(edit):
                errors.append("The source for {} does not exist: {}".format(label.lower(), path))
                continue
            # A hand-typed path has no layer URI yet: resolve it the way Browse would.
            if not edit.property("source_uri") and not self._resolve_typed_source(
                edit, label, expected_kind, errors
            ):
                continue
            layer = self._load_vector(edit, label)
            if layer is None:
                errors.append(
                    "QGIS could not open the selected feature layer for {}. Use Browse to choose "
                    "a supported datasource and, where needed, its specific feature layer.".format(label.lower())
                )
                continue

            count = layer.featureCount()
            loaded[label] = (layer, count)
            sources.append(edit.property("source_uri") or text)
            if count == 0:
                errors.append("{} contains no features.".format(label))
            elif count < 0:
                warnings.append("{}: this datasource does not report a feature count.".format(label))
            if not layer.crs().isValid():
                errors.append("{} has no valid coordinate reference system.".format(label))
            if not geometry_matches(layer, expected_kind):
                errors.append(
                    "{} must be a {} geometry layer; the selected layer is {}.".format(
                        label, expected_kind, geometry_description(layer)
                    )
                )

        if len(sources) != len(set(sources)):
            errors.append("Priority roads, secondary roads, and study area must use different feature layers.")

        crs_names = {
            label: (layer.crs().authid() or layer.crs().description())
            for label, (layer, _count) in loaded.items() if layer.crs().isValid()
        }
        if len(set(crs_names.values())) > 1:
            warnings.append(
                "The inputs use different CRSs ({}). They are reprojected to the analysis CRS, "
                "so confirm that each layer's CRS is defined correctly.".format(
                    ", ".join("{}: {}".format(k, v) for k, v in crs_names.items())
                )
            )

        boundary = loaded.get(self.LABEL_BOUNDARY)
        if boundary is not None:
            for label in (self.LABEL_PRIORITY, self.LABEL_SECONDARY):
                if label not in loaded:
                    continue
                overlap = self._extents_overlap(loaded[label][0], boundary[0])
                if overlap is False:
                    warnings.append(
                        "{} does not overlap the study-area boundary. Check that both layers' "
                        "CRSs are correct.".format(label)
                    )
                elif overlap is None:
                    warnings.append(
                        "Could not compare the extent of {} with the study-area boundary.".format(label.lower())
                    )
        return loaded

    def _check_analysis_crs(self, errors, warnings):
        """Validate the analysis CRS. Returns it."""
        analysis_crs = self.crs_widget.crs()
        if not analysis_crs.isValid():
            errors.append("Select a valid analysis CRS / projection.")
        elif analysis_crs.isGeographic():
            errors.append(
                "The analysis CRS is geographic. Select a suitable projected CRS for distance-based processing."
            )
        else:
            if analysis_crs.mapUnits() != METERS:
                warnings.append(
                    "The analysis CRS uses {} rather than metres; the distances below are in metres.".format(
                        QgsUnitTypes.toString(analysis_crs.mapUnits())
                    )
                )
            if analysis_crs.authid() == "EPSG:3857":
                warnings.append(
                    "EPSG:3857 (Web Mercator) distorts distances more the further you are from the "
                    "equator. A local UTM zone is more accurate for buffers and snapping."
                )
        return analysis_crs

    def _check_advanced_values(self, errors, warnings):
        """Sanity-check the distance settings."""
        values = self._advanced_values()
        for key, label in ADVANCED_LABELS:
            if values[key] <= 0:
                errors.append("{} must be greater than 0 m.".format(label))
        if values["join_gap"] < values["base_buffer"]:
            warnings.append(
                "The maximum snapping distance ({:g} m) is smaller than the priority buffer ({:g} m). "
                "Trimmed road ends sit about one buffer width from the priority roads, so few "
                "ends will be able to snap.".format(values["join_gap"], values["base_buffer"])
            )
        if 0 < values["mid_gap"] < 1.0:
            warnings.append(
                "A midpoint densification interval below 1 m creates very many vertices and will be slow."
            )

    def _check_output(self, errors, warnings):
        """Validate the output folder, name and format. Returns the target path or ''."""
        output_dir = self.output_path.text().strip()
        if not output_dir:
            errors.append("Choose an output folder.")
        elif not os.path.isdir(output_dir):
            errors.append("The selected output folder does not exist.")
        elif not os.access(output_dir, os.W_OK):
            errors.append("The selected output folder is not writable.")

        output_name = self.output_name.text().strip()
        if not output_name:
            errors.append("Enter an output name / prefix (for example, KE_Nairobi).")
        else:
            bad_chars = invalid_name_chars(output_name)
            if bad_chars:
                errors.append(
                    "The output name contains characters that are not valid in a file name: {}".format(
                        " ".join(bad_chars)
                    )
                )

        output_type = self.output_type_combo.currentData()
        if output_type == "shp":
            warnings.append(
                "Shapefile output truncates field names to 10 characters and stores one layer per "
                "file. GeoPackage is recommended."
            )
        elif output_type == "gdb" and not gdb_write_supported():
            errors.append(
                "This QGIS installation's GDAL cannot create File Geodatabases "
                "(OpenFileGDB write support needs GDAL 3.6 or later). Choose GeoPackage instead."
            )

        target = ""
        if output_dir and output_name and not invalid_name_chars(output_name):
            target = os.path.join(output_dir, self._output_filename())
            if os.path.exists(target):
                warnings.append("The output already exists and may be overwritten: {}".format(target))
        return target

    def validate_inputs(self):
        """Validate selected datasets, geometry types, CRS, settings and output choices."""
        errors = []
        warnings = []
        with _busy_cursor():
            loaded = self._check_sources(errors, warnings)
            analysis_crs = self._check_analysis_crs(errors, warnings)
            self._check_advanced_values(errors, warnings)
            target = self._check_output(errors, warnings)

        if errors:
            self._log(
                "Input validation FAILED: {} problem(s).".format(len(errors)), "error", bold=True
            )
            for error in errors:
                self._log(error, "error")
            for warning in warnings:
                self._log(warning, "warning")
            self._show_message(
                "warning",
                "Input validation",
                "Please correct the following issues:\n\n" + "\n".join(errors)
                + ("\n\n({} warning(s) are listed in the log.)".format(len(warnings)) if warnings else ""),
            )
            return False

        self._log("Input validation PASSED.", "success", bold=True)
        for label, (layer, count) in loaded.items():
            self._log("{}: {}; source CRS: {}".format(
                label,
                "{:,} feature(s)".format(count) if count >= 0 else "feature count unavailable",
                layer.crs().authid() or layer.crs().description(),
            ))
        self._log("Analysis CRS: {}".format(analysis_crs.authid() or analysis_crs.description()))
        self._log("Output: {}".format(target))
        for warning in warnings:
            self._log(warning, "warning")

        self._show_message(
            "information",
            "Input validation",
            "The selected inputs passed the current basic checks"
            + (" with {} warning(s) (see the log).".format(len(warnings)) if warnings else ".")
            + "\n\nYou can now run the selected integration methodology.",
        )
        self._save_settings()
        return True

    def _quick_run_check(self):
        """Check required form values without loading/iterating large GIS layers on the UI thread."""
        errors = []
        warnings = []
        input_sources = []
        for label, edit, expected_kind in self._input_specs():
            text = edit.text().strip()
            if not text:
                errors.append("Browse to a dataset for {}.".format(label.lower()))
                continue
            if not self._source_exists(edit):
                path = edit.property("source_path") or text
                errors.append("The source for {} does not exist: {}".format(label.lower(), path))
                continue
            if not edit.property("source_uri"):
                # A typed path may need its internal GeoPackage/GDB layer resolved.
                if not self._resolve_typed_source(edit, label, expected_kind, errors):
                    continue
            uri = str(edit.property("source_uri") or "").strip()
            if not uri:
                errors.append("Could not resolve the selected feature layer for {}. Use Browse to select it.".format(label.lower()))
                continue
            input_sources.append(uri)

        if len(input_sources) != len(set(input_sources)):
            errors.append("Priority roads, secondary roads, and study area must use different feature layers.")

        analysis_crs = self._check_analysis_crs(errors, warnings)
        self._check_advanced_values(errors, warnings)
        target = self._check_output(errors, warnings)
        return errors, warnings, analysis_crs, target

    def run_integration(self):
        """Start the selected methodology as a QGIS background task."""
        if self._is_processing:
            self._log("A processing task is already running.", "warning")
            return False

        selected_method = self.method_combo.currentData()
        if selected_method not in ("methodology_1", "methodology_2", "methodology_3"):
            self._log("The selected methodology is not available.", "error")
            self._show_message("warning", "Methodology unavailable",
                               "Choose one of the implemented integration methodologies.")
            return False

        errors, warnings, analysis_crs, target = self._quick_run_check()
        if errors:
            self._log("Pre-run checks FAILED: {} issue(s).".format(len(errors)), "error", bold=True)
            for error in errors:
                self._log(error, "error")
            for warning in warnings:
                self._log(warning, "warning")
            self._show_message("warning", "Check processing settings",
                               "Please correct the following issues before processing:\n\n" + "\n".join(errors))
            return False

        settings = self.collect_settings()
        if not settings.get("priority_uri") or not settings.get("secondary_uri") or not settings.get("boundary_uri"):
            self._log("One or more input feature-layer URIs could not be resolved.", "error")
            self._show_message("warning", "Input selection",
                               "Use Browse to select the exact feature layer for each input.")
            return False

        # Release an already-loaded copy of this exact output on the GUI thread.
        # This avoids Windows file locks while the worker replaces the dataset.
        self._release_project_output_layer(target, settings.get("output_type"))
        self._save_settings()
        self._start_run_log(settings, selected_method, analysis_crs)

        self._is_processing = True
        self.run_button.setEnabled(False)
        self.validate_button.setEnabled(False)
        self.close_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.processing_progress.setValue(1)
        self.processing_status_label.setText("Scheduling background processing…")

        method_labels = {
            "methodology_1": "Methodology 1 — Direct Merge",
            "methodology_2": "Methodology 2 — Clip + Snap",
            "methodology_3": "Methodology 3 — Targeted Snap",
        }
        self._log("Starting {} in the QGIS background task manager…".format(method_labels[selected_method]), "info", bold=True)
        for warning in warnings:
            self._log(warning, "warning")

        try:
            from qgis.core import QgsApplication
            from ..core.background_task import RoadIntegrationTask

            # Capture this on the main thread. The engine uses this copy inside its worker.
            transform_context = QgsProject.instance().transformContext()
            task = RoadIntegrationTask(settings, transform_context)
            task.log_message.connect(self._on_worker_log)
            task.progress_message.connect(self._on_worker_progress)
            task.completed.connect(self._on_task_completed)
            self._active_task = task
            accepted = QgsApplication.taskManager().addTask(task)
            if accepted is False:
                raise RuntimeError("QGIS did not accept the background processing task.")
            return True
        except Exception as exc:
            self._is_processing = False
            self._active_task = None
            self.run_button.setEnabled(True)
            self.validate_button.setEnabled(True)
            self.close_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self._log("Could not start the background task: {}".format(exc), "error", bold=True)
            self._show_message("critical", "Could not start processing",
                               "The background task could not be started.\n\n{}\n\nProcessing log: {}".format(
                                   exc, self._run_log_path or "Could not create log file"))
            return False

    def _cancel_run(self):
        """Ask the running background task to stop at its next checkpoint."""
        task = self._active_task
        if task is None or not self._is_processing:
            return
        self.cancel_button.setEnabled(False)
        self.processing_status_label.setText("Cancelling… waiting for the next safe checkpoint.")
        self._log("Cancellation requested; stopping at the next safe checkpoint…", "warning")
        task.cancel()

    def _release_project_output_layer(self, output_path, output_type):
        """Remove a matching loaded output before worker-thread overwrite starts."""
        from qgis.core import QgsProject
        if not output_path:
            return
        target = os.path.normcase(os.path.abspath(os.path.normpath(output_path)))
        if str(output_type).lower() == "shp":
            target = os.path.splitext(target)[0]
        for layer in list(QgsProject.instance().mapLayers().values()):
            try:
                source = layer.source().split("|", 1)[0]
                source = os.path.normcase(os.path.abspath(os.path.normpath(source)))
                if str(output_type).lower() == "shp":
                    source = os.path.splitext(source)[0]
                if source == target:
                    QgsProject.instance().removeMapLayer(layer.id())
                    self._log("Released previously loaded output layer '{}' before overwriting.".format(layer.name()), "info")
            except Exception:
                continue

    def _start_run_log(self, settings, method, analysis_crs):
        """Create/append a plain-text processing log in the selected output folder."""
        output_dir = settings.get("output_dir", "")
        base = os.path.splitext(os.path.basename(settings.get("output_filename", "road_network")))[0]
        self._run_log_path = os.path.join(output_dir, base + "_processing.log") if output_dir else ""
        self._run_log_error = ""
        if not self._run_log_path:
            self._run_log_error = "No output folder was available for the log file."
            return
        try:
            os.makedirs(output_dir, exist_ok=True)
            with open(self._run_log_path, "a", encoding="utf-8") as stream:
                stream.write("\n" + "=" * 88 + "\n")
                stream.write("Run started: {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                stream.write("Methodology: {}\n".format(method))
                stream.write("Analysis CRS: {}\n".format(analysis_crs.authid() or analysis_crs.description()))
                stream.write("Priority input: {}\n".format(settings.get("priority_uri", "")))
                stream.write("Secondary input: {}\n".format(settings.get("secondary_uri", "")))
                stream.write("Study-area input: {}\n".format(settings.get("boundary_uri", "")))
                stream.write("Output: {}\n".format(os.path.join(output_dir, settings.get("output_filename", ""))))
                stream.write("Intermediate diagnostics enabled: {}\n".format(bool(settings.get("keep_intermediates"))))
                stream.write("Add output to QGIS project: {}\n\n".format(bool(settings.get("add_outputs_to_project"))))
        except Exception as exc:
            self._run_log_error = str(exc)
            self._run_log_path = ""
            self._log("Could not create the processing log file: {}".format(exc), "warning")

    def _append_run_log(self, message, level):
        """Persist each message as it arrives so the run log survives interruptions."""
        if not self._run_log_path:
            return
        try:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tag = level.upper() if level in ("warning", "error") else level.upper() if level == "success" else "INFO"
            with open(self._run_log_path, "a", encoding="utf-8") as stream:
                stream.write("[{}] [{}] {}\n".format(stamp, tag, str(message)))
        except Exception as exc:
            self._run_log_error = str(exc)
            self._run_log_path = ""

    def _on_worker_log(self, message, level="info"):
        """Receive queued worker messages safely on the GUI thread."""
        self._log(message, level)

    def _on_worker_progress(self, value, message):
        """Update progress UI from worker-sent, queued signals."""
        self.processing_progress.setValue(max(self.processing_progress.value(), int(value)))
        self.processing_status_label.setText(str(message))

    def _load_final_output_on_gui_thread(self, payload):
        """Reopen a completed output on the main thread, only when requested."""
        output_path = payload.get("output_path", "")
        output_type = str(payload.get("output_type", "gpkg")).lower()
        if output_type in ("gpkg", "gdb"):
            layer_name = os.path.splitext(os.path.basename(output_path))[0]
            uri = "{}|layername={}".format(output_path, layer_name)
        else:
            uri = output_path
            layer_name = os.path.basename(output_path)
        layer = QgsVectorLayer(uri, layer_name, "ogr")
        if not layer.isValid():
            raise RuntimeError("The output was written but could not be loaded into QGIS: {}".format(uri))
        QgsProject.instance().addMapLayer(layer)
        self._log("Added merged output to the current QGIS project.", "success")

    def _on_task_completed(self, success, error_message, payload):
        """Finish the UI updates after the background task returns to the main thread."""
        self._is_processing = False
        self._active_task = None
        self.run_button.setEnabled(True)
        self.validate_button.setEnabled(True)
        self.close_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        payload = payload or {}
        method = payload.get("methodology", self.method_combo.currentData())
        method_labels = {
            "methodology_1": "Methodology 1 — Direct Merge",
            "methodology_2": "Methodology 2 — Clip + Snap",
            "methodology_3": "Methodology 3 — Targeted Snap",
        }
        method_label = method_labels.get(method, "Road-network integration")

        if success:
            try:
                if payload.get("add_outputs_to_project"):
                    self._load_final_output_on_gui_thread(payload)
                self.processing_progress.setValue(100)
                self.processing_status_label.setText("Completed successfully.")
                self._log("{} finished successfully.".format(method_label), "success", bold=True)
                if self._run_log_path:
                    self._log("Processing log saved to: {}".format(self._run_log_path), "success")
                popup = (
                    "{} completed successfully.\n\nOutput: {}\nFeatures written: {:,}".format(
                        method_label, payload.get("output_path", ""),
                        int(payload.get("output_feature_count", 0))
                    )
                    + "\n\nProcessing log: {}".format(self._run_log_path or "Unavailable")
                )
                self._show_message("information", "Integration complete", popup)
            except Exception as exc:
                self.processing_status_label.setText("Output was written, but final QGIS reporting had a problem.")
                self._log("Output was written, but GUI completion handling failed: {}".format(exc), "error", bold=True)
                self._show_message("critical", "Integration finished with a warning",
                                   "Output: {}\n\n{}\n\nProcessing log: {}".format(
                                       payload.get("output_path", ""), exc, self._run_log_path or "Unavailable"))
        elif payload.get("cancelled"):
            self.processing_progress.setValue(0)
            self.processing_status_label.setText("Processing was cancelled.")
            self._log("{} was cancelled.".format(method_label), "warning", bold=True)
            if self._run_log_path:
                self._log("Run log: {}".format(self._run_log_path), "info")
            self._show_message("information", "Integration cancelled",
                               "{} was cancelled before the final output was written.\n\n"
                               "Processing log: {}".format(method_label, self._run_log_path or "Unavailable"))
        else:
            self.processing_status_label.setText("Processing failed. See the log for details.")
            self._log("{} failed.".format(method_label), "error", bold=True)
            if self._run_log_path:
                self._log("Failure details have been recorded in: {}".format(self._run_log_path), "warning")
            self._show_message("critical", "Integration failed",
                               "{} could not complete.\n\n{}\n\nProcessing log: {}".format(
                                   method_label, error_message or "No additional error details were reported.",
                                   self._run_log_path or "Unavailable"))

    def collect_settings(self):
        """Return every GUI selection in one dictionary, for the processing engine to use."""
        advanced = self._advanced_values()
        return {
            "priority_uri": self.priority_path[1].property("source_uri") or "",
            "secondary_uri": self.secondary_path[1].property("source_uri") or "",
            "boundary_uri": self.boundary_path[1].property("source_uri") or "",
            "method": self.method_combo.currentData(),
            "analysis_crs": self.crs_widget.crs(),
            "base_buffer_m": advanced["base_buffer"],
            "secondary_buffer_m": advanced["secondary_buffer"],
            "join_gap_m": advanced["join_gap"],
            "mid_gap_m": advanced["mid_gap"],
            "centroid_max_dist_m": advanced["centroid_max_dist"],
            "output_dir": self.output_path.text().strip(),
            "output_filename": self._output_filename(),
            "output_type": self.output_type_combo.currentData(),
            "add_outputs_to_project": self.add_outputs_checkbox.isChecked(),
            "keep_intermediates": self.keep_intermediates_checkbox.isChecked(),
        }

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def _log(self, message, level="info", bold=False):
        """Append a timestamped, colour-coded message and persist active-run logs."""
        self.log_output.appendHtml(format_log_html(message, level, bold))
        self._append_run_log(message, level)