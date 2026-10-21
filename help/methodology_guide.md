# Road Network Integration Toolkit — Methodology Guide

The dialog provides the same input selection, CRS, method, distance, output, and intermediate-retention controls as the supplied plugin. Select a priority road network, a secondary road network, a polygon study boundary, and a suitable projected analysis CRS. Distances are specified in metres, so a local metric CRS is recommended.

## Shared preparation

The engine transforms both road networks to the analysis CRS, prepares the study-area union, and clips roads to the envelope of a 30 km buffer around the study boundary. It creates individual flat-ended priority-road buffers using the configured base-buffer distance. For each secondary road, it first checks whether one individual buffer fully covers the road. Otherwise it computes overlap lengths against all intersecting individual buffers, chooses the largest one, calculates the remaining-length ratio, and assigns the legacy class. The classifier intentionally leaves a ratio exactly equal to `0.25` unclassified.

## Methodology 1 — Direct Merge

Retains all priority features and adds the secondary features classified `missing_1`, `missing_2`, `missing_3`, or `missing_4`. It does not trim or snap secondary geometries. This is the closest match to the legacy direct-merge method and is the fastest option.

## Methodology 2 — Clip + Snap

Differences each missing class by the dissolved priority-road buffer, creates endpoint/midpoint-style anchors along priority roads at the selected interval, and snaps both ends of each secondary line part to its nearest anchor within the join gap. It creates cumulative merged layers by adding missing-road classes progressively from 1 to 4.

## Methodology 3 — Targeted Snap

Differences the missing classes by the dissolved priority buffer. The overlapping portions are square-buffered; priority roads are clipped against those local buffers; and start, end, and normalized midpoint targets are extracted. Secondary segments are snapped first to a nearby local midpoint target, then to local endpoints, and finally to a global priority-road target when neither local step succeeds. `missing_1` segments are added back without snapping. The implementation deliberately restores the intended local buffer association that the legacy script lost because it never joined `buffer_id` back to the trimmed roads.

## Outputs

The selected final network is written to the requested output path as GeoPackage, Shapefile, or File Geodatabase. When intermediate retention is enabled, the plugin preserves coverage classification, priority buffers, and method-specific diagnostics in `Intermediate_Files`. Existing output paths are overwritten, matching the legacy script's `OVERWRITE_EXISTING=True` setting.

## Validation note

This rewrite includes syntax and classifier regression checks. Before operational use, test it in the target QGIS version with a small sample first, and compare its outputs with the Spyder scripts. Numerical/geometry comparison is important because QGIS/GEOS and Shapely versions may differ in edge-case handling even when the workflow is equivalent.
