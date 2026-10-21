
# -*- coding: utf-8 -*-
"""
Processing configuration for the Road Network Integration Toolkit.

This module converts the dictionary returned by
RoadNetworkIntegrationDialog.collect_settings() into a consistent
configuration object for the processing engine.

Responsibilities
----------------
1. Check that required configuration keys are present.
2. Validate distance parameters and output settings.
3. Preserve the QgsCoordinateReferenceSystem object supplied by the GUI.
4. Provide a predictable interface for the processing controller.

This module does not load layers, modify geometries, or run algorithms.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from qgis.core import QgsCoordinateReferenceSystem


# ----------------------------------------------------------------------
# Supported processing options
# ----------------------------------------------------------------------

SUPPORTED_METHODS = {
    "methodology_1",
    "methodology_2",
    "methodology_3",
}

SUPPORTED_OUTPUT_TYPES = {
    "gpkg",
    "shp",
    "gdb",
}

# These values must match the GUI's established workflow defaults.
DEFAULT_DISTANCES = {
    "base_buffer_m": 20.0,
    "secondary_buffer_m": 10.0,
    "join_gap_m": 25.0,
    "mid_gap_m": 10.0,
    "centroid_max_dist_m": 15.0,
}

REQUIRED_KEYS = (
    "priority_uri",
    "secondary_uri",
    "boundary_uri",
    "method",
    "analysis_crs",
    "output_dir",
    "output_filename",
    "output_type",
)


# ----------------------------------------------------------------------
# Configuration errors
# ----------------------------------------------------------------------

class ConfigurationError(ValueError):
    """Raised when processing configuration is missing or invalid."""


# ----------------------------------------------------------------------
# Structured configuration
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ProcessingConfiguration:
    """
    Immutable configuration passed from the GUI to the processing engine.

    Distances are expressed in metres. The analysis CRS remains a QGIS
    CRS object so it can be used directly by QGIS processing code.
    """

    priority_uri: str
    secondary_uri: str
    boundary_uri: str

    method: str
    analysis_crs: QgsCoordinateReferenceSystem

    base_buffer_m: float
    secondary_buffer_m: float
    join_gap_m: float
    mid_gap_m: float
    centroid_max_dist_m: float

    output_dir: str
    output_filename: str
    output_type: str

    add_outputs_to_project: bool = True
    keep_intermediates: bool = True

    @property
    def output_path(self) -> str:
        """Return the full path planned for the final output."""
        return str(Path(self.output_dir) / self.output_filename)

    @classmethod
    def from_mapping(
        cls,
        settings: Mapping[str, Any],
    ) -> "ProcessingConfiguration":
        """
        Build a configuration from the GUI's collect_settings() dictionary.

        Raises
        ------
        ConfigurationError
            If required settings are missing or their values are invalid.
        """
        if not isinstance(settings, Mapping):
            raise ConfigurationError(
                "Processing settings must be supplied as a mapping/dictionary."
            )

        # Check structure before reading individual values.
        missing = [
            key for key in REQUIRED_KEYS
            if key not in settings
        ]
        if missing:
            raise ConfigurationError(
                "Missing required configuration key(s): {}.".format(
                    ", ".join(missing)
                )
            )

        # Normalize required text values.
        text_keys = (
            "priority_uri",
            "secondary_uri",
            "boundary_uri",
            "method",
            "output_dir",
            "output_filename",
            "output_type",
        )

        values = {}
        for key in text_keys:
            value = settings[key]
            if not isinstance(value, str) or not value.strip():
                raise ConfigurationError(
                    "'{}' must be a non-empty string.".format(key)
                )
            values[key] = value.strip()

        # Ensure that the selected methodology is implemented.
        if values["method"] not in SUPPORTED_METHODS:
            raise ConfigurationError(
                "Unsupported or unavailable methodology: '{}'. "
                "Currently supported: {}.".format(
                    values["method"],
                    ", ".join(sorted(SUPPORTED_METHODS)),
                )
            )

        # Validate the output format.
        if values["output_type"] not in SUPPORTED_OUTPUT_TYPES:
            raise ConfigurationError(
                "Unsupported output type '{}'. Choose one of: {}.".format(
                    values["output_type"],
                    ", ".join(sorted(SUPPORTED_OUTPUT_TYPES)),
                )
            )

        # The GUI supplies an actual QGIS CRS object.
        analysis_crs = settings["analysis_crs"]
        if not isinstance(analysis_crs, QgsCoordinateReferenceSystem):
            raise ConfigurationError(
                "'analysis_crs' must be a QgsCoordinateReferenceSystem object."
            )

        if not analysis_crs.isValid():
            raise ConfigurationError(
                "The analysis CRS is invalid."
            )

        if analysis_crs.isGeographic():
            raise ConfigurationError(
                "The analysis CRS must be projected for distance-based processing."
            )

        # Convert distances to floats and ensure they are positive and finite.
        distances = {}
        for key, default_value in DEFAULT_DISTANCES.items():
            raw_value = settings.get(key, default_value)

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                raise ConfigurationError(
                    "'{}' must be a valid numeric distance.".format(key)
                )

            if not (0.0 < value < float("inf")):
                raise ConfigurationError(
                    "'{}' must be finite and greater than zero.".format(key)
                )

            distances[key] = value

        # Basic output-path checks. Existence and write permissions are
        # checked by the controller immediately before processing.
        output_dir = Path(values["output_dir"])
        if not output_dir.is_dir():
            raise ConfigurationError(
                "The output directory does not exist: {}".format(output_dir)
            )

        output_filename = values["output_filename"]
        if Path(output_filename).name != output_filename:
            raise ConfigurationError(
                "The output filename must not contain directory components."
            )

        expected_extensions = {
            "gpkg": ".gpkg",
            "shp": ".shp",
            "gdb": ".gdb",
        }
        expected_extension = expected_extensions[values["output_type"]]

        if Path(output_filename).suffix.lower() != expected_extension:
            raise ConfigurationError(
                "The output filename extension must be '{}' for output type '{}'.".format(
                    expected_extension,
                    values["output_type"],
                )
            )

        # Ensure output options are actual Boolean values.
        add_outputs = settings.get("add_outputs_to_project", True)
        keep_intermediates = settings.get("keep_intermediates", True)

        if not isinstance(add_outputs, bool):
            raise ConfigurationError(
                "'add_outputs_to_project' must be True or False."
            )

        if not isinstance(keep_intermediates, bool):
            raise ConfigurationError(
                "'keep_intermediates' must be True or False."
            )

        return cls(
            priority_uri=values["priority_uri"],
            secondary_uri=values["secondary_uri"],
            boundary_uri=values["boundary_uri"],
            method=values["method"],
            analysis_crs=analysis_crs,
            output_dir=str(output_dir),
            output_filename=output_filename,
            output_type=values["output_type"],
            add_outputs_to_project=add_outputs,
            keep_intermediates=keep_intermediates,
            **distances
        )
