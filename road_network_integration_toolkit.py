# -*- coding: utf-8 -*-
"""QGIS plugin lifecycle, menu action, and main-dialog management."""

import os
import traceback

from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsMessageLog

# QAction moved from QtWidgets (Qt5) to QtGui (Qt6); compat resolves it for both.
from .core.compat import MSG_CRITICAL, QAction


class RoadNetworkIntegrationToolkit:
    """Register the plugin action and manage its non-modal main dialog."""

    PLUGIN_NAME = "Road Network Integration Toolkit"
    MENU_NAME = "&Road Network Integration Toolkit"
    ACTION_OBJECT_NAME = "roadNetworkIntegrationToolkitAction"

    def __init__(self, iface):
        """Store the QGIS interface and initialize lifecycle references."""
        self.iface = iface
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.action = None
        self.dialog = None

    def initGui(self):
        """Add one action to the QGIS Plugins menu and toolbar."""
        # Guard against duplicate menu/toolbar actions if initGui is invoked again.
        if self.action is not None:
            return

        icon_path = os.path.join(self.plugin_dir, "icon.png")
        self.action = QAction(
            QIcon(icon_path), self.PLUGIN_NAME, self.iface.mainWindow()
        )
        self.action.setObjectName(self.ACTION_OBJECT_NAME)
        self.action.setStatusTip("Open the Road Network Integration Toolkit")
        self.action.setWhatsThis(
            "Select priority and secondary road networks, choose an analysis CRS, "
            "and validate the inputs for road-network integration."
        )
        self.action.triggered.connect(self.run)

        self.iface.addPluginToMenu(self.MENU_NAME, self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        """Remove QGIS actions and close any open plugin dialog."""
        # Prevent unload before touching the action/dialog while the worker is active.
        if self.dialog is not None and getattr(self.dialog, "_is_processing", False):
            self.iface.messageBar().pushWarning(
                self.PLUGIN_NAME,
                "Processing is still running. Let it finish before unloading the plugin."
            )
            return

        if self.action is not None:
            self.iface.removePluginMenu(self.MENU_NAME, self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None

        if self.dialog is not None:
            try:
                self.dialog.close()
                self.dialog.deleteLater()
            except RuntimeError:
                # The Qt object may already have been destroyed by QGIS.
                pass
            finally:
                self.dialog = None

    def _dialog_destroyed(self, *_args):
        """Drop the reference when the user closes the window, so reopening resets it."""
        self.dialog = None

    def run(self):
        """Show the non-modal dialog, creating a fresh instance after each close."""
        if self.dialog is None:
            try:
                # Imported here, not at module level, so a GUI import problem
                # is reported to the user instead of breaking plugin loading.
                from .gui.main_dialog import RoadNetworkIntegrationDialog
                self.dialog = RoadNetworkIntegrationDialog(self.iface)
            except Exception as exc:
                self.dialog = None
                QgsMessageLog.logMessage(traceback.format_exc(), self.PLUGIN_NAME, MSG_CRITICAL)
                self.iface.messageBar().pushCritical(
                    self.PLUGIN_NAME,
                    "The toolkit window could not be opened: {}. "
                    "See View > Panels > Log Messages for details.".format(exc),
                )
                return
            self.dialog.destroyed.connect(self._dialog_destroyed)

        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
