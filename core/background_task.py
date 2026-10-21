# -*- coding: utf-8 -*-
"""Background runner for Road Network Integration Toolkit.

All heavyweight preparation, overlay, snapping, and export work is delegated to
QGIS' task manager. GUI widgets and QgsProject mutation remain on the main thread.
"""

import gc

from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsTask

from .legacy_engine import OperationCancelled


class _TaskLogger:
    """Bridge the engine's level-aware logger to queued Qt signals."""

    def __init__(self, task):
        self.task = task

    def __call__(self, message):
        self._emit(message, "info")

    def info(self, message):
        self._emit(message, "info")

    def success(self, message):
        self._emit(message, "success")

    def warning(self, message):
        self._emit(message, "warning")

    def error(self, message):
        self._emit(message, "error")

    def check_cancelled(self):
        """Called by the engine at checkpoints; aborts the run if the task was cancelled."""
        if self.task.isCanceled():
            raise OperationCancelled("Processing was cancelled.")

    def _emit(self, message, level):
        message = str(message)
        self.task.log_message.emit(message, level)
        progress = self.task.progress_for_message(message)
        if progress is not None:
            self.task._progress_value = max(self.task._progress_value, progress)
            self.task.setProgress(float(self.task._progress_value))
            self.task.progress_message.emit(self.task._progress_value, message)
        else:
            self.task.progress_message.emit(self.task._progress_value, message)


class RoadIntegrationTask(QgsTask):
    """Execute one road-integration run in a QGIS-managed background task."""

    log_message = pyqtSignal(str, str)
    progress_message = pyqtSignal(int, str)
    completed = pyqtSignal(bool, str, object)

    def __init__(self, settings, transform_context):
        super().__init__("Road Network Integration Toolkit")
        self.settings = dict(settings)
        self.transform_context = transform_context
        self.error_message = ""
        self.was_cancelled = False
        self.result_payload = None
        self._progress_value = 1
        self.logger = _TaskLogger(self)

    @staticmethod
    def progress_for_message(message):
        """Map engine milestones to a monotonic, approximate user-facing progress."""
        text = str(message).lower()
        milestones = (
            ("starting processing preflight checks", 3),
            ("processing configuration validated", 5),
            ("loading input layers", 7),
            ("all input layers passed basic validation", 12),
            ("preflight checks completed successfully", 15),
            ("study area prepared", 19),
            ("priority_roads_prepared", 23),
            ("secondary_roads_prepared", 27),
            ("priority-road buffers", 34),
            ("coverage classification complete", 45),
            ("coverage statistics", 47),
            ("starting methodology 1", 53),
            ("starting methodology 2", 53),
            ("starting methodology 3", 53),
            ("remain after priority-buffer trimming", 61),
            ("snap anchors", 68),
            ("snapping summary", 82),
            ("methodology 3 snapping", 82),
            ("methodology 3: clipped priority roads", 61),
            ("trimmed missing_1", 61),
            ("methodology 1: retained", 84),
            ("methodology 3 completed", 87),
            ("finished methodology", 96),
            ("final harmonized network written", 97),
        )
        for marker, value in milestones:
            if marker in text:
                return value
        if "finished methodology" in text or text.startswith("finished method"):
            return 98
        if text.startswith("finished methodology") or text.startswith("finished ") and "features in the final network" in text:
            return 99
        return None

    def run(self):
        """Worker-thread entry point. Do not access dialogs or mutate QgsProject here."""
        controller = None
        prepared = None
        result = None
        output_layer = None
        try:
            from . import legacy_engine
            from .controller import ProcessingController

            method = self.settings.get("method")
            if method == "methodology_1":
                from ..algorithms.methodology_1 import run_methodology_1 as run_algorithm
                method_label = "Methodology 1 — Direct Merge"
            elif method == "methodology_2":
                from ..algorithms.methodology_2 import run_methodology_2 as run_algorithm
                method_label = "Methodology 2 — Clip + Snap"
            elif method == "methodology_3":
                from ..algorithms.methodology_3 import run_methodology_3 as run_algorithm
                method_label = "Methodology 3 — Targeted Snap"
            else:
                raise ValueError("Choose one of the three implemented methodologies.")

            self.log_message.emit("Starting background processing…", "info")
            with legacy_engine.worker_transform_context(self.transform_context):
                controller = ProcessingController(log_callback=self.logger)
                prepared = controller.prepare(self.settings)
                configuration = controller.configuration
                self.logger.info("Executing {}…".format(method_label))
                result = run_algorithm(
                    priority_roads=prepared.priority_roads,
                    secondary_roads=prepared.secondary_roads,
                    study_area=prepared.study_area,
                    configuration=configuration,
                    log=self.logger,
                )

                # Only small, serializable result data crosses back to the GUI.
                # The engine's reopened result layer belongs to the worker and
                # must not be transferred to the main thread.
                output_layer = result.pop("output_layer", None)
                self.result_payload = {
                    "output_path": str(result.get("output_path", configuration.output_path)),
                    "output_feature_count": int(result.get("output_feature_count", 0)),
                    "methodology": str(method),
                    "add_outputs_to_project": bool(configuration.add_outputs_to_project),
                    "output_type": str(configuration.output_type),
                    "output_filename": str(configuration.output_filename),
                }
                self.setProgress(99.0)
                self.log_message.emit("Background processing completed; returning results to QGIS…", "success")
            return True
        except OperationCancelled:
            self.was_cancelled = True
            self.error_message = "Processing was cancelled."
            self.log_message.emit(
                "Processing was cancelled. Any intermediate files already written were left in place; "
                "the final output was not replaced.", "warning")
            return False
        except Exception as exc:
            self.error_message = "{}: {}".format(type(exc).__name__, exc)
            self.log_message.emit("Integration failed: {}".format(self.error_message), "error")
            return False
        finally:
            # Ensure provider-backed layers created in the worker are released
            # there, before GUI completion handlers try to reopen the output.
            output_layer = None
            if controller is not None:
                try:
                    controller.prepared_inputs = None
                except Exception:
                    pass
            prepared = None
            controller = None
            result = None
            gc.collect()

    def finished(self, result):
        """QGIS calls this on the main thread after run() finishes."""
        success = bool(result and self.result_payload)
        payload = dict(self.result_payload or {})
        # A task cancelled from QGIS' task manager before it started never runs
        # run(), so check isCanceled() as well as the flag set by run().
        if not success and (self.was_cancelled or self.isCanceled()):
            payload["cancelled"] = True
            self.error_message = self.error_message or "Processing was cancelled."
        self.completed.emit(success, self.error_message, payload)
