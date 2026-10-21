
# -*- coding: utf-8 -*-
"""
Processing controller for the Road Network Integration Toolkit.

Responsibilities
----------------
1. Convert GUI settings into a validated configuration.
2. Resolve and validate the input vector layers.
3. Check geometry types, feature counts, and input CRS definitions.
4. Check output paths and write access while preserving the legacy workflow's
   overwrite-existing behaviour.
5. Provide validated inputs and configuration to the selected methodology.

The controller handles preflight validation. The shared QGIS-native engine
performs reprojection, coverage classification, geometry processing, merging,
and output export.
"""

import os
import tempfile
from dataclasses import dataclass
from typing import Optional

from qgis.core import QgsVectorLayer

from .configuration import (
    ConfigurationError,
    ProcessingConfiguration,
)

from .datasource_utils import (
    gdb_write_supported,
    geometry_description,
    geometry_matches,
)


# ----------------------------------------------------------------------
# Controller errors
# ----------------------------------------------------------------------

class ProcessingControllerError(RuntimeError):
    """Raised when input or output preparation fails."""


# ----------------------------------------------------------------------
# Prepared input container
# ----------------------------------------------------------------------

@dataclass
class PreparedInputs:
    """
    Validated input layers ready for the processing algorithm.

    These are temporary layer objects. They are not automatically added
    to the user's QGIS project.
    """

    priority_roads: QgsVectorLayer
    secondary_roads: QgsVectorLayer
    study_area: QgsVectorLayer


# ----------------------------------------------------------------------
# Processing controller
# ----------------------------------------------------------------------

class ProcessingController:
    """
    Coordinate configuration validation and processing preparation.

    The controller validates the GUI configuration and inputs, then passes
    prepared layers to the shared legacy-compatible processing engine.
    """

    def __init__(self, iface=None, log_callback=None):
        """
        Parameters
        ----------
        iface : QgisInterface, optional
            QGIS interface, when available.
        log_callback : callable, optional
            Function accepting a message string for GUI logging.
        """
        self.iface = iface
        self.log_callback = log_callback

        self.configuration: Optional[ProcessingConfiguration] = None
        self.prepared_inputs: Optional[PreparedInputs] = None

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        """Send a message to the GUI logger or print it to the console."""
        if self.log_callback is not None:
            try:
                self.log_callback(str(message))
                return
            except Exception:
                pass

        print("[Road Network Integration Toolkit] {}".format(message))

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def build_configuration(self, settings) -> ProcessingConfiguration:
        """Validate GUI settings and create the structured configuration."""
        try:
            configuration = ProcessingConfiguration.from_mapping(settings)
        except ConfigurationError:
            raise
        except Exception as exc:
            raise ProcessingControllerError(
                "Unable to create the processing configuration: {}".format(exc)
            ) from exc

        self.configuration = configuration

        self._log("Processing configuration validated.")
        self._log("Methodology: {}".format(configuration.method))
        self._log("Analysis CRS: {}".format(
            configuration.analysis_crs.authid()
        ))
        self._log("Output: {}".format(configuration.output_path))

        return configuration

    # ------------------------------------------------------------------
    # Input layer loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_layer(uri: str, display_name: str) -> QgsVectorLayer:
        """
        Open a vector layer directly from its stored provider URI.

        The URI may include provider-specific details, such as a selected
        feature layer within a GeoPackage or File Geodatabase.
        """
        if not isinstance(uri, str) or not uri.strip():
            raise ProcessingControllerError(
                "{} has an empty datasource URI.".format(display_name)
            )

        try:
            layer = QgsVectorLayer(
                uri.strip(),
                display_name,
                "ogr",
            )
        except Exception as exc:
            raise ProcessingControllerError(
                "Could not open {}: {}".format(display_name, exc)
            ) from exc

        if not layer.isValid():
            raise ProcessingControllerError(
                "QGIS could not open {}. Check that its datasource URI "
                "is valid and that the required file or container exists."
                .format(display_name)
            )

        return layer

    def _validate_layer(
        self,
        layer: QgsVectorLayer,
        display_name: str,
        expected_geometry: str,
        configuration: ProcessingConfiguration,
    ) -> None:
        """Validate geometry, feature availability, and CRS information."""
        if not layer.isValid():
            raise ProcessingControllerError(
                "{} is not a valid QGIS vector layer.".format(display_name)
            )

        actual_geometry = geometry_description(layer)

        if not geometry_matches(layer, expected_geometry):
            raise ProcessingControllerError(
                "{} must contain {} geometry, but its geometry type is {}."
                .format(
                    display_name,
                    expected_geometry,
                    actual_geometry,
                )
            )

        try:
            feature_count = layer.featureCount()
        except Exception as exc:
            raise ProcessingControllerError(
                "Could not read features from {}: {}".format(
                    display_name,
                    exc,
                )
            ) from exc

        if feature_count == 0:
            raise ProcessingControllerError(
                "{} contains no features.".format(display_name)
            )
        if feature_count < 0:
            # Some providers cannot report a count up front; that is not an error.
            self._log(
                "Note: {} does not report a feature count; continuing.".format(
                    display_name
                )
            )

        source_crs = layer.crs()

        if not source_crs.isValid():
            raise ProcessingControllerError(
                "{} has an undefined or invalid CRS. Define its actual "
                "source CRS before running the analysis.".format(display_name)
            )

        target_crs = configuration.analysis_crs

        self._log(
            "{}: {} features; {} geometry; source CRS {}.".format(
                display_name,
                feature_count,
                actual_geometry,
                source_crs.authid() or source_crs.description(),
            )
        )

        if source_crs != target_crs:
            self._log(
                "Note: {} uses a different CRS from the analysis CRS. "
                "Coordinate transformation will be required during "
                "processing.".format(display_name)
            )

    def prepare_inputs(
        self,
        configuration: Optional[ProcessingConfiguration] = None,
    ) -> PreparedInputs:
        """
        Load and validate all three inputs.

        No geometry edits are performed and no layers are added to the
        QGIS project by this method.
        """
        configuration = configuration or self.configuration

        if configuration is None:
            raise ProcessingControllerError(
                "No processing configuration is available. "
                "Build the configuration before preparing inputs."
            )

        self._log("Loading input layers...")

        priority_roads = self._load_layer(
            configuration.priority_uri,
            "Priority roads",
        )

        secondary_roads = self._load_layer(
            configuration.secondary_uri,
            "Secondary roads",
        )

        study_area = self._load_layer(
            configuration.boundary_uri,
            "Study area boundary",
        )

        self._validate_layer(
            priority_roads,
            "Priority roads",
            "line",
            configuration,
        )

        self._validate_layer(
            secondary_roads,
            "Secondary roads",
            "line",
            configuration,
        )

        self._validate_layer(
            study_area,
            "Study area boundary",
            "polygon",
            configuration,
        )

        prepared = PreparedInputs(
            priority_roads=priority_roads,
            secondary_roads=secondary_roads,
            study_area=study_area,
        )

        self.prepared_inputs = prepared

        self._log("All input layers passed basic validation.")

        return prepared

    # ------------------------------------------------------------------
    # Output checks
    # ------------------------------------------------------------------

    @staticmethod
    def _existing_output_components(
        output_path: str,
        output_type: str,
    ) -> list:
        """Find existing output files or folders that could be overwritten."""
        if output_type in ("gpkg", "gdb"):
            return [output_path] if os.path.exists(output_path) else []

        # Shapefile output consists of several files sharing one basename.
        base_path = os.path.splitext(output_path)[0]

        extensions = (
            ".shp",
            ".shx",
            ".dbf",
            ".prj",
            ".cpg",
            ".qix",
            ".sbn",
            ".sbx",
        )

        return [
            base_path + extension
            for extension in extensions
            if os.path.exists(base_path + extension)
        ]

    @staticmethod
    def _canonical_path(path: str) -> str:
        """Normalize a filesystem path for reliable same-file comparisons."""
        return os.path.normcase(os.path.abspath(os.path.normpath(path)))

    @staticmethod
    def _datasource_path(uri: str) -> str:
        """Strip the OGR layer selector from a file-based datasource URI."""
        return str(uri or "").strip().split("|", 1)[0].strip().strip("\"\'")

    def _check_output_does_not_replace_input(self, configuration) -> None:
        """Prevent the overwrite-compatible writer from deleting a selected input."""
        output_path = self._canonical_path(configuration.output_path)
        output_type = configuration.output_type.lower()
        output_root = os.path.splitext(output_path)[0] if output_type == "shp" else output_path

        input_names = (
            ("priority roads", configuration.priority_uri),
            ("secondary roads", configuration.secondary_uri),
            ("study-area boundary", configuration.boundary_uri),
        )
        for label, uri in input_names:
            source_path = self._datasource_path(uri)
            if not source_path:
                continue
            source_path = self._canonical_path(source_path)
            source_type = os.path.splitext(source_path)[1].lower()
            if output_type == "shp":
                source_root = os.path.splitext(source_path)[0]
                same_target = source_root == output_root and source_type == ".shp"
            else:
                same_target = source_path == output_path
            if same_target:
                raise ProcessingControllerError(
                    "The output path would overwrite the selected {} input: {}. "
                    "Choose a different output filename or folder.".format(label, source_path)
                )

    def validate_output_location(
        self,
        configuration: Optional[ProcessingConfiguration] = None,
    ) -> str:
        """
        Validate the destination directory and final output path.

        Existing outputs are allowed because the finalized legacy workflow
        overwrites them. A temporary probe file tests write access.
        """
        configuration = configuration or self.configuration

        if configuration is None:
            raise ProcessingControllerError(
                "No processing configuration is available."
            )

        output_dir = configuration.output_dir
        output_path = configuration.output_path
        self._check_output_does_not_replace_input(configuration)

        # Fail now rather than after a long run: the final export would
        # otherwise be the first place an unsupported GDB driver is noticed.
        if configuration.output_type == "gdb" and not gdb_write_supported():
            raise ProcessingControllerError(
                "This QGIS/GDAL build cannot create File Geodatabases "
                "(OpenFileGDB write support needs GDAL 3.6 or later). "
                "Choose GeoPackage output instead."
            )

        if not os.path.isdir(output_dir):
            raise ProcessingControllerError(
                "The output directory does not exist: {}".format(output_dir)
            )

        # The finalized legacy toolkit used OVERWRITE_EXISTING=True. The
        # processing engine therefore replaces an existing target only after
        # all input/configuration preflight checks have passed.

        probe_path = None

        try:
            with tempfile.NamedTemporaryFile(
                prefix=".rnit_write_test_",
                dir=output_dir,
                delete=False,
            ) as probe:
                probe_path = probe.name

        except OSError as exc:
            raise ProcessingControllerError(
                "The output directory is not writable: {}. Details: {}"
                .format(output_dir, exc)
            ) from exc

        finally:
            if probe_path and os.path.exists(probe_path):
                try:
                    os.remove(probe_path)
                except OSError as exc:
                    self._log(
                        "Warning: could not remove temporary write-test "
                        "file '{}': {}".format(probe_path, exc)
                    )

        self._log("Output directory is writable.")
        self._log("Output path is available: {}".format(output_path))

        return output_path

    # ------------------------------------------------------------------
    # Preparation entry point
    # ------------------------------------------------------------------

    def prepare(self, settings) -> PreparedInputs:
        """
        Run configuration, input, and output preflight checks before processing.
        """
        self._log("Starting processing preflight checks...")

        configuration = self.build_configuration(settings)
        prepared_inputs = self.prepare_inputs(configuration)
        self.validate_output_location(configuration)

        self._log("Preflight checks completed successfully; inputs are ready for the selected methodology.")

        return prepared_inputs
