# -*- coding: utf-8 -*-
"""Visual design system for the Road Network Integration Toolkit.

One source of truth for colour, type and component styling. Dialogs apply
``STYLESHEET`` once; widgets use semantic roles (``primaryButton``,
``dangerButton``, ``hint``, ``panelTitle``) instead of local style rules.
Nothing in this module touches plugin behaviour.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

TEXT = "#1F2933"            # primary text, dark charcoal
TEXT_SECONDARY = "#66727E"  # labels that support, rather than lead
TEXT_DISABLED = "#9AA4AE"

CANVAS = "#F6F7F9"          # application background
SURFACE = "#FFFFFF"         # header, footer, status panel
FIELD = "#FFFFFF"

BORDER = "#E2E6EB"          # hairlines
BORDER_STRONG = "#CDD4DC"   # input and button outlines

PRIMARY = "#0B5E8E"         # deep professional blue
PRIMARY_HOVER = "#0A517A"
PRIMARY_PRESSED = "#08425F"
ACCENT = "#1499D6"          # focus, progress, selection
ACCENT_SOFT = "#EAF5FB"
SUCCESS = "#6ABF4B"         # retained for semantic use
DANGER = "#B42318"

FONT_STACK = (
    '"Segoe UI", "SF Pro Text", "Inter", "Helvetica Neue", Arial, sans-serif'
)
MONO_STACK = '"Cascadia Mono", "Consolas", "SF Mono", "DejaVu Sans Mono", monospace'

_ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def resource_path(name: str) -> str:
    """Absolute, forward-slash path usable by ``url(...)`` in Qt style sheets."""
    return os.path.join(_ASSET_DIR, name).replace("\\", "/")


_QSS_TEMPLATE = """
QDialog#RoadNetworkIntegrationDialog, QDialog#RoadNetworkChooserDialog {
    background-color: @CANVAS@;
    color: @TEXT@;
}

QMessageBox#RoadNetworkMessageBox, QFileDialog#RoadNetworkFileDialog {
    background-color: @SURFACE@;
}

QMessageBox#RoadNetworkMessageBox QLabel, QFileDialog#RoadNetworkFileDialog QLabel {
    color: @TEXT@;
}

QWidget {
    font-family: @FONT@;
    font-size: 9pt;
    color: @TEXT@;
}

QLabel {
    background: transparent;
    color: @TEXT@;
}

QLabel:disabled {
    color: @TEXT_DISABLED@;
}

/* ---------- Application header ---------- */
QFrame#appHeader {
    background-color: @SURFACE@;
    border: 0;
    border-bottom: 1px solid @BORDER@;
}

QLabel#appTitle {
    font-size: 12pt;
    font-weight: 600;
    color: @TEXT@;
}

QLabel#appSubtitle {
    font-size: 8.5pt;
    color: @TEXT_SECONDARY@;
}

/* ---------- Scrollable page ---------- */
QScrollArea {
    border: 0;
    background: transparent;
}

QWidget#page {
    background-color: @CANVAS@;
}

/* ---------- Sections ---------- */
QGroupBox {
    background: transparent;
    border: 0;
    border-bottom: 1px solid @BORDER@;
    margin-top: 0;
    padding: 12px 0 10px 0;
    font-size: 10pt;
    font-weight: 600;
    color: @TEXT@;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 0;
    padding: 0 0 6px 0;
    background: transparent;
}

QLabel#hint {
    color: @TEXT_SECONDARY@;
    font-size: 8.5pt;
}

QLabel#previewValue {
    color: @TEXT@;
    font-family: @MONO@;
    font-size: 8.5pt;
}

/* ---------- Inputs ---------- */
QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {
    background-color: @FIELD@;
    color: @TEXT@;
    border: 1px solid @BORDER_STRONG@;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 20px;
    selection-background-color: @ACCENT@;
    selection-color: #FFFFFF;
}

QLineEdit:hover, QComboBox:hover, QDoubleSpinBox:hover, QSpinBox:hover {
    border-color: #B4BEC8;
}

QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus,
QComboBox:on {
    border-color: @ACCENT@;
}

QLineEdit:disabled, QComboBox:disabled, QDoubleSpinBox:disabled,
QSpinBox:disabled {
    background-color: #F2F4F6;
    color: @TEXT_DISABLED@;
    border-color: @BORDER@;
}

QComboBox QAbstractItemView {
    background-color: @SURFACE@;
    color: @TEXT@;
    border: 1px solid @BORDER_STRONG@;
    selection-background-color: @ACCENT_SOFT@;
    selection-color: @TEXT@;
    outline: 0;
    padding: 2px;
}

/* ---------- Buttons ---------- */
QPushButton {
    background-color: @SURFACE@;
    color: @TEXT@;
    border: 1px solid @BORDER_STRONG@;
    border-radius: 4px;
    padding: 4px 12px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #F2F5F8;
    border-color: #B4BEC8;
}

QPushButton:pressed {
    background-color: #E9EDF1;
}

QPushButton:focus {
    border-color: @ACCENT@;
}

QPushButton:disabled {
    color: @TEXT_DISABLED@;
    background-color: #F7F8FA;
    border-color: #E6E9ED;
}

QPushButton#primaryButton {
    background-color: @PRIMARY@;
    color: #FFFFFF;
    border-color: @PRIMARY@;
    font-weight: 600;
    padding: 4px 18px;
}

QPushButton#primaryButton:hover {
    background-color: @PRIMARY_HOVER@;
    border-color: @PRIMARY_HOVER@;
}

QPushButton#primaryButton:pressed {
    background-color: @PRIMARY_PRESSED@;
    border-color: @PRIMARY_PRESSED@;
}

QPushButton#primaryButton:disabled {
    background-color: #B7C8D5;
    border-color: #B7C8D5;
    color: #F4F7F9;
}

QPushButton#dangerButton {
    color: @DANGER@;
    border-color: #E3C6C2;
}

QPushButton#dangerButton:hover {
    background-color: #FCF4F3;
    border-color: #D5A8A2;
}

QPushButton#dangerButton:disabled {
    color: #BEAAA7;
    border-color: #E9DEDC;
    background-color: #FBFAFA;
}

QPushButton#ghostButton {
    background: transparent;
    border-color: transparent;
    color: @TEXT_SECONDARY@;
}

QPushButton#ghostButton:hover {
    background-color: #EEF1F4;
    color: @TEXT@;
}

QPushButton#ghostButton:pressed {
    background-color: #E5E9ED;
}

QComboBox {
    padding-right: 26px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: 0;
}

QComboBox::down-arrow {
    image: url("@CHEVRON_DOWN@");
    width: 10px;
    height: 6px;
}

QLineEdit {
    placeholder-text-color: #8B96A2;
}

QDoubleSpinBox, QSpinBox {
    padding-right: 24px;
}

QDoubleSpinBox::up-button, QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 18px;
    border-left: 1px solid @BORDER_STRONG@;
    border-bottom: 1px solid @BORDER_STRONG@;
    border-top-right-radius: 4px;
    background: transparent;
}

QDoubleSpinBox::down-button, QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 18px;
    border-left: 1px solid @BORDER_STRONG@;
    border-bottom-right-radius: 4px;
    background: transparent;
}

QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover,
QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {
    background: #F2F5F8;
}

QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {
    image: url("@CHEVRON_UP@");
    width: 8px;
    height: 5px;
}

QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {
    image: url("@CHEVRON_DOWN@");
    width: 8px;
    height: 5px;
}

/* ---------- Checkboxes and radios ---------- */
QCheckBox, QRadioButton {
    spacing: 8px;
    color: @TEXT@;
}

QCheckBox:disabled, QRadioButton:disabled {
    color: @TEXT_DISABLED@;
}

QCheckBox::indicator, QGroupBox::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid #A9B4BF;
    border-radius: 3px;
    background: @FIELD@;
}

QCheckBox::indicator:hover, QGroupBox::indicator:hover {
    border-color: @ACCENT@;
}

QCheckBox::indicator:checked, QGroupBox::indicator:checked {
    background: @PRIMARY@;
    border-color: @PRIMARY@;
    image: url("@CHECK@");
}

QCheckBox::indicator:disabled, QGroupBox::indicator:disabled {
    background: #F2F4F6;
    border-color: @BORDER@;
}

QCheckBox::indicator:checked:disabled, QGroupBox::indicator:checked:disabled {
    background: #B7C8D5;
    border-color: #B7C8D5;
}

/* ---------- Progress ---------- */
QProgressBar {
    background-color: #E7ECF1;
    border: 0;
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
}

QProgressBar::chunk {
    background-color: @ACCENT@;
    border-radius: 3px;
}

/* ---------- Status panel and log ---------- */
QFrame#statusPanel {
    background-color: @SURFACE@;
    border: 0;
    border-top: 1px solid @BORDER@;
}

QLabel#panelTitle {
    font-size: 9.5pt;
    font-weight: 600;
    color: @TEXT@;
}

QLabel#statusText {
    color: @TEXT@;
}

QLabel#percentText {
    color: @TEXT_SECONDARY@;
    font-family: @MONO@;
    font-size: 8.5pt;
}

QPlainTextEdit {
    background-color: #FBFCFD;
    color: #2B3440;
    border: 1px solid @BORDER@;
    border-radius: 4px;
    padding: 6px;
    font-family: @MONO@;
    font-size: 8.5pt;
    selection-background-color: @ACCENT@;
    selection-color: #FFFFFF;
}

/* ---------- Footer ---------- */
QFrame#footer {
    background-color: @SURFACE@;
    border: 0;
    border-top: 1px solid @BORDER@;
}

/* ---------- Menus ---------- */
QMenu {
    background-color: @SURFACE@;
    border: 1px solid @BORDER_STRONG@;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
    color: @TEXT@;
}

QMenu::item:selected {
    background-color: @ACCENT_SOFT@;
    color: @TEXT@;
}

QMenu::separator {
    height: 1px;
    background: @BORDER@;
    margin: 4px 8px;
}

/* ---------- Scroll bars ---------- */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #C7D0D9;
    min-height: 30px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #AAB6C0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #C7D0D9;
    min-width: 30px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #AAB6C0;
}

QScrollBar::add-line, QScrollBar::sub-line {
    width: 0;
    height: 0;
}

QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
}

/* ---------- Tooltips ---------- */
QToolTip {
    background-color: #1F2933;
    color: #FFFFFF;
    border: 1px solid #1F2933;
    padding: 4px 6px;
}
"""


def build_stylesheet() -> str:
    """Return the complete style sheet with palette and fonts substituted."""
    tokens = {
        "@TEXT@": TEXT,
        "@TEXT_SECONDARY@": TEXT_SECONDARY,
        "@TEXT_DISABLED@": TEXT_DISABLED,
        "@CANVAS@": CANVAS,
        "@SURFACE@": SURFACE,
        "@FIELD@": FIELD,
        "@BORDER@": BORDER,
        "@BORDER_STRONG@": BORDER_STRONG,
        "@PRIMARY@": PRIMARY,
        "@PRIMARY_HOVER@": PRIMARY_HOVER,
        "@PRIMARY_PRESSED@": PRIMARY_PRESSED,
        "@ACCENT@": ACCENT,
        "@ACCENT_SOFT@": ACCENT_SOFT,
        "@DANGER@": DANGER,
        "@FONT@": FONT_STACK,
        "@MONO@": MONO_STACK,
        "@CHECK@": resource_path("check.svg"),
        "@CHEVRON_DOWN@": resource_path("chevron-down.svg"),
        "@CHEVRON_UP@": resource_path("chevron-up.svg"),
    }
    qss = _QSS_TEMPLATE
    for token, value in tokens.items():
        qss = qss.replace(token, value)
    return qss


STYLESHEET = build_stylesheet()


def apply_theme(widget) -> None:
    """Apply the design system to one dialog and its child widgets."""
    widget.setStyleSheet(STYLESHEET)
