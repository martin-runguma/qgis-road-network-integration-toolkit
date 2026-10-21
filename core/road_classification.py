"""
Road Network Integration Toolkit
================================

Module: road_classification.py

Purpose
-------
Classify secondary roads according to the proportion of their length that
remains uncovered by priority-road buffers.

This module is independent of QGIS, GeoPandas, Shapely, NumPy, and other
GIS libraries. It can be imported and tested using standard Python.

Classification Logic
--------------------
The remaining ratio is calculated as:

    rem_ratio = remaining (uncovered) road length / original road length

Interpretation:

    0.00 = no road length remains uncovered
    0.25 = 25% of the road length remains uncovered
    1.00 = the entire road length remains uncovered

The classification retains the existing class codes, default thresholds,
and the exact boundary behavior of the finalized legacy script.

    rem_ratio == 0.25 is left unclassified.

Class Codes
-----------
missing_a : Effectively fully covered
missing_b : More than 75% covered (strictly below a remaining ratio of 0.25)
missing_1 : Completely uncovered
missing_2 : More than 75% remains uncovered
missing_3 : More than 50%, up to and including 75%, remains uncovered
missing_4 : More than 25%, up to and including 50%, remains uncovered

Important
---------
The finalized legacy coverage module does not classify exactly 0.25 into any
class. That boundary behaviour is retained so results align with the source
workflow; downstream integrations that only select missing_1..missing_4 omit
features at precisely that ratio.
"""

import math
from numbers import Real
from typing import Optional


# =============================================================================
# DEFAULT PARAMETERS
# =============================================================================

DEFAULT_CV_MAX = 0.75
DEFAULT_TOLERANCE = 0.99


# =============================================================================
# CLASSIFICATION CODES
# =============================================================================

# Do not rename these values without reviewing downstream processing scripts.
CLASS_FULLY_COVERED = "missing_a"
CLASS_MOSTLY_COVERED = "missing_b"
CLASS_COMPLETELY_UNCOVERED = "missing_1"
CLASS_MOSTLY_UNCOVERED = "missing_2"
CLASS_HALF_TO_THREE_QUARTERS_UNCOVERED = "missing_3"
CLASS_QUARTER_TO_HALF_UNCOVERED = "missing_4"


# =============================================================================
# INPUT VALIDATION
# =============================================================================

def _validate_number(name: str, value: Real) -> float:
    """
    Validate a numeric argument and return it as a finite float.

    Booleans are explicitly rejected because bool is a subclass of int
    in Python.

    Parameters
    ----------
    name : str
        Name of the argument, used in error messages.

    value : Real
        Numeric value to validate.

    Returns
    -------
    float
        Validated numeric value.

    Raises
    ------
    TypeError
        If the value is not a real number or is a boolean.

    ValueError
        If the value is NaN or infinite.
    """
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number.")

    value = float(value)

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")

    return value


# =============================================================================
# ROAD CLASSIFICATION
# =============================================================================

def refined_classify_value(
    rem_ratio: float,
    cv_max: float = DEFAULT_CV_MAX,
    tolerance: float = DEFAULT_TOLERANCE,
) -> Optional[str]:
    """
    Classify a road using its remaining (uncovered) length ratio.

    Parameters
    ----------
    rem_ratio : float
        Remaining/uncovered road length divided by original road length.
        Must be between 0 and 1, inclusive.

    cv_max : float, default 0.75
        Coverage threshold used by the missing_b rule. The condition is
        rem_ratio < (1 - cv_max). With the default cv_max=0.75, exactly
        0.25 is not assigned to missing_b and falls through to None.

    tolerance : float, default 0.99
        Full-coverage tolerance. The missing_a condition is evaluated using
        rem_ratio <= (1 - tolerance).

    Returns
    -------
    str or None
        A classification code, or None if no classification condition
        matches. With the default parameters, exactly 0.25 returns None.

    Default classification rules
    ----------------------------
    rem_ratio <= 0.01
        missing_a: effectively fully covered

    0.01 < rem_ratio < 0.25
        missing_b: more than 75% covered

    rem_ratio == 1.0
        missing_1: completely uncovered

    0.75 < rem_ratio < 1.0
        missing_2: more than 75% remains uncovered

    0.50 < rem_ratio <= 0.75
        missing_3: more than 50%, up to 75%, remains uncovered

    0.25 < rem_ratio <= 0.50
        missing_4: more than 25%, up to 50%, remains uncovered

    Raises
    ------
    TypeError
        If an argument is not a real number or is a boolean.

    ValueError
        If an argument is non-finite or outside its permitted range.
    """

    # -------------------------------------------------------------------------
    # Validate inputs before classification.
    # -------------------------------------------------------------------------
    rem_ratio = _validate_number("rem_ratio", rem_ratio)
    cv_max = _validate_number("cv_max", cv_max)
    tolerance = _validate_number("tolerance", tolerance)

    if not 0.0 <= rem_ratio <= 1.0:
        raise ValueError("rem_ratio must be between 0 and 1 inclusive.")

    if not 0.0 <= cv_max <= 1.0:
        raise ValueError("cv_max must be between 0 and 1 inclusive.")

    if not 0.0 <= tolerance <= 1.0:
        raise ValueError("tolerance must be between 0 and 1 inclusive.")

    # -------------------------------------------------------------------------
    # Classification rules.
    #
    # Keep the order of these conditions intentional:
    # 1. Effectively fully covered.
    # 2. Mostly covered, strictly below the configured threshold.
    # 3. Completely uncovered.
    # 4. Remaining uncovered-ratio classes.
    # -------------------------------------------------------------------------

    # Effectively fully covered by priority-road buffers.
    if rem_ratio <= (1.0 - tolerance):
        return CLASS_FULLY_COVERED

    # Mostly covered.
    # With the default cv_max=0.75, this condition covers ratios below 0.25.
    elif rem_ratio < (1.0 - cv_max):
        return CLASS_MOSTLY_COVERED

    # Completely uncovered.
    # Keep this check before the general missing_2 condition.
    elif rem_ratio == 1.0:
        return CLASS_COMPLETELY_UNCOVERED

    # More than 75% remains uncovered.
    elif rem_ratio > 0.75:
        return CLASS_MOSTLY_UNCOVERED

    # More than 50%, up to and including 75%, remains uncovered.
    elif 0.50 < rem_ratio <= 0.75:
        return CLASS_HALF_TO_THREE_QUARTERS_UNCOVERED

    # More than 25%, up to and including 50%, remains uncovered.
    elif 0.25 < rem_ratio <= 0.50:
        return CLASS_QUARTER_TO_HALF_UNCOVERED

    # Retain a safe fallback for unusual parameter combinations.
    return None


# =============================================================================
# OPTIONAL REPORTING HELPER
# =============================================================================

def classify_coverage_ratio(
    rem_ratio: float,
    cv_max: float = DEFAULT_CV_MAX,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict:
    """
    Return a road classification with readable quality-assurance information.

    Parameters
    ----------
    rem_ratio : float
        Remaining/uncovered road length divided by original road length.

    cv_max : float, default 0.75
        Coverage threshold passed to refined_classify_value().

    tolerance : float, default 0.99
        Full-coverage tolerance passed to refined_classify_value().

    Returns
    -------
    dict
        Contains:
            Missing_Class : str or None
            rem_ratio     : float
            covered_ratio : float
            description   : str
    """

    # Use the main classifier to keep validation and classification consistent.
    class_code = refined_classify_value(
        rem_ratio=rem_ratio,
        cv_max=cv_max,
        tolerance=tolerance,
    )

    # Normalize the value after the main function has validated it.
    rem_ratio = float(rem_ratio)

    descriptions = {
        CLASS_FULLY_COVERED:
            "Effectively fully covered by priority-road buffers",

        CLASS_MOSTLY_COVERED:
            "More than 75% covered by priority-road buffers",

        CLASS_COMPLETELY_UNCOVERED:
            "Completely uncovered by priority-road buffers",

        CLASS_MOSTLY_UNCOVERED:
            "More than 75% of road length remains uncovered",

        CLASS_HALF_TO_THREE_QUARTERS_UNCOVERED:
            "More than 50% and up to 75% remains uncovered",

        CLASS_QUARTER_TO_HALF_UNCOVERED:
            "More than 25% and up to 50% remains uncovered",

        None:
            "No classification condition matched the supplied parameters",
    }

    return {
        "Missing_Class": class_code,
        "rem_ratio": rem_ratio,
        "covered_ratio": 1.0 - rem_ratio,
        "description": descriptions[class_code],
    }
