# -*- coding: utf-8 -*-
"""Methodology 1 — Direct Merge, using the legacy shared processing engine."""

from ..core.legacy_engine import run_legacy_workflow


def run_methodology_1(priority_roads, secondary_roads, study_area, configuration, log=None):
    """Classify secondary roads and directly merge legacy missing classes 1–4.

    Input geometries are reprojected and clipped to the legacy buffered-boundary
    envelope during preparation. The final merge itself does not trim or snap
    road geometry and contains the priority network plus secondary features in
    ``missing_1`` through ``missing_4``.
    """
    return run_legacy_workflow(
        priority_roads, secondary_roads, study_area, configuration,
        method="methodology_1", log=log,
    )
