# Road Network Integration Toolkit

![Road Network Integration Toolkit: merge priority and secondary road networks inside QGIS](docs/images/banner.svg)

![QGIS 3.28+](https://img.shields.io/badge/QGIS-3.28%2B-589632?logo=qgis&logoColor=white) ![Qt5 and Qt6](https://img.shields.io/badge/Qt-5%20%7C%206-41CD52?logo=qt&logoColor=white) ![Output: GeoPackage, Shapefile, File Geodatabase](https://img.shields.io/badge/output-GPKG%20%7C%20SHP%20%7C%20GDB-1E88E5) ![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-e9a23b)

**Road Network Integration Toolkit** is a QGIS plugin that combines a *priority* road network with a *secondary* one. It measures how much of each secondary road the priority network already covers, classifies what is missing, and merges the missing roads in, snapping them to the priority network when you ask it to. Everything runs inside QGIS, so you do not need GeoPandas, Shapely or a separate Python environment.

It is a PyQGIS port of a finished Spyder/GeoPandas workflow, with the same class rules and the same three methodologies.

## Contents

- [Features](#features)
- [How it works](#how-it-works)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Screenshots](#screenshots)
- [Coverage classification](#coverage-classification)
- [Methodologies](#methodologies)
- [Output](#output)
- [Under the hood](#under-the-hood)
- [Tips for good results](#tips-for-good-results)
- [Troubleshooting](#troubleshooting)
- [Compatibility](#compatibility)
- [Release notes](#release-notes)
- [Development](#development)
- [Author](#author)
- [License](#license)

## Features

- **Three methodologies:** Direct Merge, Clip + Snap and Targeted Snap, all built on one shared processing engine
- **Dominant-buffer coverage classification** that keeps the legacy `Missing_Class` rules exactly, including the `0.25` boundary
- **Guided dialog:** pick the priority roads, secondary roads and study area, choose a methodology and a projected CRS, and run
- **CRS suggestion:** one click picks the UTM zone that contains the centre of your study area
- **Editable distances:** buffer, snapping and densification distances have sensible metre defaults and unlock under *Advanced settings*
- **Three export formats:** GeoPackage, Shapefile or File Geodatabase, each checked by reopening it in QGIS
- **Optional diagnostics:** keep buffers, classified roads, snap layers and method outputs
- **Responsive interface:** processing runs as a cancellable QGIS background task with a progress bar and a live log
- **Run log on disk:** a timestamped `<output-name>_processing.log` is saved beside your output
- **GeoPackage-safe IDs:** input `fid` values are preserved as `source_fid`, so exports never collide on the reserved key
- Works on **QGIS 3.28 to 4.99** (Qt5 and Qt6)

## How it works

![Workflow: prepare inputs, classify coverage, integrate, export and log](docs/images/workflow.svg)

1. **Prepare inputs.** Both road networks are reprojected to your analysis CRS, usable geometry is repaired, and roads are clipped to the envelope of the study boundary buffered by 30 km.
2. **Classify coverage.** The plugin buffers each priority road, then gives every secondary road a `Missing_Class` from the share of its length that stays uncovered.
3. **Integrate.** Your chosen methodology merges the missing secondary roads into the priority network, with or without snapping.
4. **Export and log.** The result is written, reopened as a check, and optionally added to your project. A progress log is saved next to it.

## Installation

### From a ZIP file

1. Make sure the ZIP contains a single top-level folder named `road_network_integration_toolkit`. GitHub’s **Download ZIP** names the folder `qgis-road-network-integration-toolkit-main`, so rename it before you zip it again.
2. In QGIS, open **Plugins → Manage and Install Plugins… → Install from ZIP**.
3. Select the file and click **Install Plugin**.

### From source

Copy the `road_network_integration_toolkit` folder into your QGIS plugins directory. If an older copy is installed under a different folder name, remove it first. Then restart QGIS and enable **Road Network Integration Toolkit** under **Plugins → Manage and Install Plugins… → Installed**.

| Operating system | Plugins directory                                                          |
|------------------|----------------------------------------------------------------------------|
| Windows          | `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins`                     |
| Linux            | `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`                |
| macOS            | `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins` |

After installing, open the plugin from the **Plugins** menu or the toolbar icon.

## Quick start

### 1. Select your input data

| Input                             | What to choose                                         |
|-----------------------------------|--------------------------------------------------------|
| **Priority road network (Path)**  | The network you trust most. Its roads are always kept. |
| **Secondary road network (Path)** | The network that supplies the missing roads.           |
| **Study area boundary (Polygon)** | The area the integration covers.                       |

Use **Browse** to choose a vector file or a layer inside a GeoPackage (`.gpkg`) or File Geodatabase (`.gdb`). Only layers with the expected geometry type are offered: lines for roads and polygons for the boundary.

### 2. Choose the integration settings

- **Merging methodology:** Direct Merge, Clip + Snap or Targeted Snap. Targeted Snap is selected by default. See [Methodologies](#methodologies).
- **Analysis CRS / projection:** a projected CRS in metres, such as your local UTM zone. Click **Suggest from study area** to pick it automatically. A suggestion is also made when you choose a boundary, unless you have already chosen a CRS yourself.

### 3. Adjust distances (optional)

Tick **Advanced settings** to edit the distances. Unticking restores the defaults. All values are in metres.

| Setting                              | Default | Used for                                         |
|--------------------------------------|---------|--------------------------------------------------|
| Priority road buffer distance        | 20      | Buffers that define what is already covered      |
| Secondary road buffer distance       | 10      | Buffers around overlap portions in Targeted Snap |
| Maximum snapping distance            | 25      | How far an endpoint may move to join a road      |
| Midpoint densification interval      | 10      | Spacing of snap anchors and midpoint targets     |
| Maximum centroid adjustment distance | 15      | Centroid-to-vertex adjustment in Targeted Snap   |

### 4. Choose the output

- **Output folder:** required. It is both your working folder and the destination.
- **Output name:** a project or city code such as `KE_Nairobi`. The dialog previews the final file name as you type.
- **Output format:** GeoPackage, Shapefile or File Geodatabase.
- **Automatically add the final output to QGIS:** off by default.
- **Keep intermediate diagnostic layers:** off by default.

### 5. Validate and run

Click **Validate Inputs** to check your choices, then **Run Integration**. Watch progress in **Processing progress and log**. You can minimise the window while it works, and **Cancel Run** stops the task at the next safe checkpoint.

## Screenshots

*Screenshots coming soon.*

## Coverage classification

![The remaining-ratio scale and the class each range receives](docs/images/classes.svg)

For each secondary road, the plugin first checks whether one individual priority buffer fully covers it. If not, it measures the overlap with every buffer it touches and takes the **largest single overlap**. Overlaps are not added together across buffers.

![Dominant single buffer: only the largest overlap with one buffer counts](docs/images/coverage.svg)

The **remaining ratio** is the uncovered length divided by the original length. It decides the class:

| Remaining ratio           | Class       | Meaning                                | Merged by the methodologies |
|---------------------------|-------------|----------------------------------------|-----------------------------|
| 0 to 0.01                 | `missing_a` | Effectively fully covered              | No                          |
| Above 0.01 and below 0.25 | `missing_b` | More than 75% covered                  | No                          |
| Exactly 0.25              | none        | Left unclassified by the legacy script | No                          |
| Above 0.25, up to 0.50    | `missing_4` | 25% to 50% uncovered                   | Yes                         |
| Above 0.50, up to 0.75    | `missing_3` | 50% to 75% uncovered                   | Yes                         |
| Above 0.75, below 1.0     | `missing_2` | More than 75% uncovered                | Yes                         |
| Exactly 1.0               | `missing_1` | Completely uncovered                   | Yes                         |

> **Note:** a road at exactly `0.25` belongs to no class, so it is never merged. This matches the finalized legacy script on purpose, so results line up with the original workflow.

## Methodologies

![The three methodologies compared](docs/images/methodologies.svg)

### 1. Direct Merge

Keeps every priority feature and adds the secondary roads classified `missing_1` to `missing_4`. It does not trim or snap them, so gaps can remain between the two networks. It writes the legacy three-field schema: `coverage_ratio`, `Missing_Class` and `source`. It is the fastest option and the closest match to the legacy direct merge.

### 2. Clip + Snap

Removes the part of each missing class that lies inside the dissolved priority buffer, then places snap anchors along the priority roads at your densification interval. Both ends of each remaining secondary line are snapped to the nearest anchor within the maximum snapping distance. Cumulative merges are built class by class (base + class 1, then classes 1 to 2, 1 to 3 and 1 to 4) and saved to an intermediate GeoPackage.

### 3. Targeted Snap

Trims the missing classes against the dissolved priority buffer, then buffers the overlapping portions with square end caps. Priority roads are clipped to those local buffers, and start, end and normalised midpoint targets are extracted. Each secondary segment snaps to a nearby local midpoint first, then to local endpoints, and finally to a global priority-road target if both local steps fail. `missing_1` roads are added back without snapping, and secondary roads are merged before the priority network.

The plugin restores the intended local buffer association. The legacy script never joined `buffer_id` back to the trimmed roads, which silently skipped the local snapping stage.

|                            | Direct Merge                                         | Clip + Snap                                               | Targeted Snap                                          |
|----------------------------|------------------------------------------------------|-----------------------------------------------------------|--------------------------------------------------------|
| Changes secondary geometry | No                                                   | Yes                                                       | Yes                                                    |
| Snapping                   | None                                                 | To anchors on the priority road                           | Local targets first, global fallback                   |
| Best when                  | You want the fastest merge or will fix gaps yourself | You want gap-free joins along the whole priority network | You want joins that stay local to where roads overlap  |

## Output

![The final network, run log and optional intermediate files in your output folder](docs/images/output.svg)

### Final network

The result is written to your output folder as GeoPackage, Shapefile or File Geodatabase, with the name you entered. Existing files at that path are overwritten. The plugin reopens the result to confirm that QGIS can read it, and can add it to your project.

### Run log

Each run writes `<output-name>_processing.log`, with timestamps, in the output folder. Its path appears in the completion or failure message.

### Intermediate files

With **Keep intermediate diagnostic layers** ticked, the plugin keeps the working data:

| File                                                                    | Contents                                   |
|-------------------------------------------------------------------------|--------------------------------------------|
| `Intermediate_Files/<prefix>_<priority>_Road_Buffers.gpkg`              | Individual and dissolved priority buffers  |
| `<prefix>_<secondary>_Coverage_Classified.gpkg` (output folder)         | Secondary roads with their `Missing_Class` |
| `Intermediate_Files/<prefix>_Merged_<priority>_<secondary>_Method1.gpkg` | Direct Merge result                        |
| `Intermediate_Files/<prefix>_M2_Output.gpkg`                            | Clip + Snap layers, including the cumulative merges |
| `Intermediate_Files/<prefix>_M3_Output.gpkg`                            | Targeted Snap layers                       |

The `<priority>` and `<secondary>` parts are source labels the plugin works out from your input file, layer or folder names, such as `OSM` or `MS`.

### GeoPackage or Shapefile?

|                 | GeoPackage                             | Shapefile                               |
|-----------------|----------------------------------------|-----------------------------------------|
| Layers per file | Many                                   | One                                     |
| Field names     | Full length                            | Shortened to 10 characters              |
| Best for        | Everything, and the recommended choice | Sharing with software that needs `.shp` |

File Geodatabase output needs a GDAL build that can create `.gdb` (OpenFileGDB write support, GDAL 3.6 or later). The plugin checks this **before** processing starts, so you do not lose a long run to it.

## Under the hood

![How a run is split between the GUI thread and a background task](docs/images/pipeline.svg)

- **Background task:** preparation, overlay, snapping and export run as a `QgsTask`. Project access and output-layer loading stay on the GUI thread, and the worker receives a copy of the project transform context.
- **Cancel:** use **Cancel Run** or the QGIS task manager. The task stops at the next safe checkpoint.
- **Distances in metres:** if your projected CRS uses other units, distances are converted, but a local metric CRS is recommended.
- **Input attributes:** `fid`, `OBJECTID`, `ogc_fid` and `geom` values are preserved under safe names, and stale `Shape_Length` and `Shape_Area` values are not copied.
- **Unknown feature counts:** a provider that cannot report a feature count no longer stops the run.
- **Fresh form each time:** closing the dialog discards its run state. The last output folder is remembered only as the starting point for **Browse**.

## Tips for good results

- **Use a local projected CRS in metres.** The UTM zone for your study area is a good default.
- **Test on a small area first.** Compare the result with your existing workflow before running a whole country.
- **Prefer GeoPackage.** It keeps field names intact and holds every intermediate layer in one file.
- **Keep intermediates while you tune.** The buffers and classified roads show why a road was or was not merged.
- **Tune one distance at a time.** Change the snapping distance first if joins are missing or too eager.

## Troubleshooting

| Problem                                               | What to do                                                                                                                                                         |
|-------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Some secondary roads never appear in the result**   | Roads at exactly `0.25` remaining ratio, and classes `missing_a` and `missing_b`, are not merged by design. See [Coverage classification](#coverage-classification). |
| **File Geodatabase output is refused**                | Your GDAL build cannot create `.gdb`. Use GeoPackage, or QGIS with GDAL 3.6 or later.                                                                              |
| **Shapefile field names look shortened**              | A Shapefile limit. Use GeoPackage to keep full names.                                                                                                              |
| **My `fid` column is now `source_fid`**               | GeoPackage reserves `fid` as its unique key, so the original values are kept under `source_fid`.                                                                   |
| **Distances behave oddly**                            | Check that the analysis CRS is projected and, ideally, in metres.                                                                                                  |
| **I updated the plugin but see the old behaviour**    | Restart QGIS completely so the new code is loaded.                                                                                                                 |

If your problem is not listed, please [open an issue](https://github.com/martin-runguma/qgis-road-network-integration-toolkit/issues) and include:

- Your QGIS version and operating system
- The methodology, output format and approximate size of the study area
- The full text of the processing log

## Compatibility

| QGIS version                    | Qt          | Status    |
|---------------------------------|-------------|-----------|
| 3.28 and later (LTR and stable) | Qt5 / PyQt5 | Supported |
| 4.x (up to 4.99)                | Qt6 / PyQt6 | Supported |

Python 3.9 or later is required. All version-specific API access (enums, `QgsField` types and `QAction`) is isolated in `core/compat.py`, and `metadata.txt` declares `supportsQt6=True`.

> **Validation note:** before operational use, run the plugin in your target QGIS version on a small sample and compare it with the original Spyder scripts. QGIS/GEOS and Shapely can differ on edge-case geometry even when the workflow is equivalent.

## Release notes

**0.6.0**
- QGIS 3.28 to 4.x compatibility (Qt5 and Qt6), with `supportsQt6` declared
- Runs can be cancelled with **Cancel Run** or the QGIS task manager
- Source labels (OSM or MS) are no longer triggered by unrelated folder names in the input path
- `OBJECTID`, `ogc_fid` and `geom` inputs are preserved under safe names, and stale `Shape_Length` and `Shape_Area` are not copied
- File Geodatabase output is validated before processing starts
- Unknown provider feature counts no longer abort the run
- Faster vertex-in-buffer test in Methodology 3
- The installable ZIP has a valid folder name and no stray files

**0.5.1**
- Methodology 3 (Targeted Snap) is selected by default whenever the dialog opens or resets

**0.5.0**
- All methodologies run as a `QgsTask`, with a live progress bar, process log and per-output log file
- The dialog has a native minimise control, and the two optional checkboxes start unticked

**0.4.1**
- Input `fid` attributes are preserved as `source_fid`, which prevents GeoPackage duplicate-key failures in Methodologies 2 and 3

## Development

```
road_network_integration_toolkit/
├── __init__.py                          # QGIS entry point (classFactory)
├── road_network_integration_toolkit.py  # Plugin controller: menu, toolbar, dialog
├── metadata.txt                         # Plugin metadata
├── icon.png
├── gui/
│   └── main_dialog.py                   # Main dialog, layer chooser, progress log
├── core/
│   ├── compat.py                        # Qt5/Qt6 and QGIS 3/4 API differences
│   ├── configuration.py                 # Validated settings passed to the engine
│   ├── controller.py                    # Runs and reports a processing job
│   ├── background_task.py               # QgsTask wrapper
│   ├── datasource_utils.py              # Layer and datasource handling
│   ├── road_classification.py           # Missing_Class rules (no QGIS needed)
│   └── legacy_engine.py                 # Shared processing engine
├── algorithms/
│   ├── methodology_1.py                 # Direct Merge
│   ├── methodology_2.py                 # Clip + Snap
│   └── methodology_3.py                 # Targeted Snap
├── utils/
└── help/
    └── methodology_guide.md             # Longer methodology notes
```

To work on the plugin, clone this repository and link or copy it into your QGIS plugins directory as a folder named `road_network_integration_toolkit` (see [Installation](#installation)). Restart QGIS to be sure new code is running.

Contributions, bug reports and ideas are welcome. Please open an [issue](https://github.com/martin-runguma/qgis-road-network-integration-toolkit/issues) or a pull request.

## Author

**UN-Habitat Data and Analytics Unit (DAU)** · maintained by [Martin Runguma](https://github.com/martin-runguma)

## License

Released under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file.
