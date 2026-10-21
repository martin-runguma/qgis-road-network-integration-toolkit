# -*- coding: utf-8 -*-
"""Methodology 2 — Clip + Snap, ported from the finalized legacy workflow."""

from ..core.legacy_engine import run_legacy_workflow


def run_methodology_2(priority_roads, secondary_roads, study_area, configuration, log=None):
    """Trim secondary missing roads by the priority buffer and snap endpoints.

    The engine preserves the legacy progressive products (base + missing 1,
    then classes 1–2, 1–3, and 1–4) when intermediate outputs are enabled.
    The selected final result is the cumulative network with classes 1–4.
    """
    return run_legacy_workflow(
        priority_roads, secondary_roads, study_area, configuration,
        method="methodology_2", log=log,
    )
