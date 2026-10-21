# Road Network Integration Toolkit

A QGIS plugin that ports the finalized Spyder/GeoPandas road-network integration workflow into PyQGIS. The established GUI layout and styling are retained. All three methodologies use a shared processing engine, and long-running preparation, overlay, snapping, and export operations run through the QGIS task manager.

## Implemented workflow

1. **Input preparation:** opens the selected priority-road, secondary-road, and study-area layers; reprojects them to the selected analysis CRS; repairs usable geometry; and clips the roads to the envelope of the study boundary buffered by 30 km.
2. **Coverage classification:** creates individual flat-ended priority-road buffers and a dissolved buffer mask. Secondary-road coverage uses the legacy dominant-single-buffer rule: the largest overlap with an individual buffer is used, rather than measuring the union of overlaps. It retains the original `Missing_Class` rules, including the exact remaining ratio `0.25` being unclassified.
3. **Methodology 1 — Direct Merge:** merges priority roads with secondary roads in `missing_1` through `missing_4` without trimming or snapping those secondary geometries. It writes the legacy three-field schema (`coverage_ratio`, `Missing_Class`, `source`).
4. **Methodology 2 — Clip + Snap:** differences each missing class against the dissolved priority-buffer mask, densifies priority lines into snap anchors at the configured interval, snaps eligible secondary endpoints within the configured join distance, and saves cumulative class merges (base + class 1; classes 1–2; 1–3; and 1–4) to an intermediate GeoPackage.
5. **Methodology 3 — Targeted Snap:** trims missing classes, buffers the overlap portions with square end caps, extracts local priority-road start/end/midpoint targets, applies local centroid-first and endpoint-second snapping with a global nearest-vertex fallback, leaves `missing_1` unsnapped, then merges secondary roads before the priority network. The local association is restored in the plugin rather than retaining the legacy script's missing-`buffer_id` bug that bypassed the local snapping stage.
6. **Export:** writes the selected final result as GeoPackage, Shapefile, or File Geodatabase and verifies that QGIS can reopen the result. When requested, intermediate buffers, classified features, snap vertices, snapped roads, and diagnostic method outputs are retained under `Intermediate_Files`. The final layer can be added to the current QGIS project.
7. **Run reporting:** a progress bar and live processing log show background task milestones. A timestamped `<output-name>_processing.log` file is written in the selected output folder and its path is shown in the completion/failure message.

## Compatibility and verification

- Designed for QGIS 3.28 or later.
- Runtime processing uses PyQGIS/Qt APIs only; GeoPandas, Shapely, and the Spyder Python environment are not required in QGIS.
- `tests/test_road_classification.py` provides QGIS-independent tests for the legacy class thresholds.
- The main processing is executed as a QGIS background task. QgsProject access and output-layer loading remain on the GUI thread; the worker receives a copy of the project transform context.
- The two optional checkboxes (auto-add final output and keep intermediate diagnostics) start unchecked. Closing the dialog destroys its current run state; reopening starts with a fresh form. The last output directory is remembered only as the Browse dialog starting location.
- Static syntax checks and classification tests can run outside QGIS. A full spatial regression run still needs to be performed in the user's QGIS installation with representative road and boundary layers, because QGIS providers/GEOS and output drivers are not available in the build environment used for this rewrite.

## Install for local testing

1. Extract the plugin folder from the ZIP.
2. Copy the `road_network_integration_toolkit` folder into the active QGIS profile's `python/plugins` directory (or use **Plugins > Manage and Install Plugins > Install from ZIP**). If an older copy was installed under another folder name, remove it first.
3. Restart QGIS or reload the plugin through the Python Console.
4. Enable **Road Network Integration Toolkit** under **Plugins → Manage and Install Plugins → Installed**.
5. Open the plugin from the Plugins menu or toolbar.

Choose a suitable projected CRS in metres (for example, the appropriate local UTM zone) for distance-based operations. Distances are converted when the selected projected CRS uses non-metre units, but a local metric CRS is recommended. GeoPackage is recommended for the final output because Shapefile limits field-name length and supports only one layer per file.


### Version 0.4.1 — GeoPackage feature-ID collision fix

Input attributes named `fid` are now preserved under a safe `source_fid` field name during road preparation. GeoPackage reserves `fid` as its unique feature key; source datasets may restart IDs independently, and split line fragments may share a source ID. Renaming the attribute prevents duplicate-key write failures in Methodologies 2 and 3 while preserving the original source ID values. If an input already has a `source_fid` field, the renamed field receives a unique suffix.


### Version 0.5.0 — background processing and run reporting

The three methodologies now run under `QgsTask` instead of executing the heavy geometry workflow synchronously in the GUI. The dialog includes a live progress bar and process log, a native minimise title-bar control, and a per-output processing log file. The auto-add-output and keep-intermediate checkboxes are off by default. Closing the dialog resets the active form/run state; it is recreated when opened again.


### Version 0.5.1 — Methodology 3 default

Methodology 3 — Targeted Snap is now selected by default whenever the plugin dialog opens or resets. Users can still select Methodology 1 or 2 manually. No processing algorithms or GUI layout were changed.


## Compatibility

* QGIS 3.28 LTR through 4.99 (Python 3.9+, PyQt5 and PyQt6). `metadata.txt` declares `supportsQt6=True`.
* All version-specific API access (enums, `QgsField` types, `QAction`) is isolated in `core/compat.py`.
* File Geodatabase output needs a GDAL build that can create `.gdb` (OpenFileGDB write support, GDAL 3.6+); the plugin checks this before processing starts.

## Running the tests

From the plugin folder: `python -m unittest discover -s tests`. The tests use fake `qgis` modules to check both API styles, so they run without QGIS; they do not replace a manual run in QGIS.
