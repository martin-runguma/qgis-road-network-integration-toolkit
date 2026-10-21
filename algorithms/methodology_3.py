# -*- coding: utf-8 -*-
"""Methodology 3 — Targeted Snap, ported from the finalized legacy workflow."""

from ..core.legacy_engine import run_legacy_workflow


def run_methodology_3(priority_roads, secondary_roads, study_area, configuration, log=None):
    """Trim, build secondary square buffers, create local base vertices, and merge.

    The engine implements centroid-first, endpoint-second, and global nearest
    vertex fallback snapping. It also records the diagnostic layers used by
    the legacy Methodology 3 workflow when ``keep_intermediates`` is enabled.
    """
    return run_legacy_workflow(
        priority_roads, secondary_roads, study_area, configuration,
        method="methodology_3", log=log,
    )
