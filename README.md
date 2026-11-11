# Road Network Merging and Alignment Toolkit — Website

A lightweight, responsive, static website for the QGIS plugin.

## Contents

- `index.html` — complete product website
- `assets/css/site.css` — responsive design system and page styles
- `assets/js/site.js` — accessible mobile navigation and active-section state
- `assets/images/plugin-icon.png` — actual icon extracted from the supplied plugin package
- `LICENSE` — GNU GPL v3.0 license text copied from the supplied plugin package

## Run locally

No build step or package installation is required. Open `index.html` in a browser, or serve this folder locally:

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000`.

## Deploy with GitHub Pages

1. Copy the contents of this folder into the root of the `main` branch of:
   `https://github.com/martin-runguma/qgis-road-network-integration-toolkit`
2. Keep the plugin source, `metadata.txt`, `help/`, tests and other project files.
3. In GitHub, open **Settings → Pages**.
4. Select **Deploy from a branch**, choose `main` and `/ (root)`, then save.
5. Wait for the Pages deployment and verify the published URL.

The website uses a static HTML/CSS/JS implementation to avoid a build pipeline and unnecessary dependencies. This is compatible with GitHub Pages.

## Accuracy notes

Website content was prepared against the supplied plugin ZIP. The supplied `metadata.txt` declares:
- Plugin version `2.0.0`
- QGIS minimum `3.28`, maximum `4.99`
- Qt 5 and Qt 6 support
- GNU GPL v3.0
- GeoPackage, Shapefile and File Geodatabase output (GDB creation depends on the installed GDAL driver)

The coverage method uses the largest overlap with one individual priority-road buffer, not the union of all buffer overlaps. The exact remaining ratio `0.25` is intentionally unclassified. The Maximum centroid adjustment distance setting is validated by the UI but is not currently consumed by the processing engine.

## Source-of-truth reconciliation before publication

There is a release-content mismatch between the supplied ZIP and the public project pages checked while preparing this package: the supplied ZIP metadata declares version `2.0.0`, while the current public GitHub README references repository metadata `0.6.0` and the official QGIS plugin listing currently shows `1.0.1` as experimental. This website intentionally follows the supplied ZIP for its feature descriptions and declared QGIS compatibility, and does not display a plugin version number. Before publishing, update/synchronise the GitHub repository and QGIS Plugin Repository listing if `2.0.0` is intended to be the public release.

## Interface screenshots

The supplied ZIP did not contain a captured QGIS interface screenshot. The interface area is therefore explicitly marked as a placeholder and must be replaced with genuine screenshots from the running plugin before publication. The hero and methodology diagrams are labelled as schematic illustrations, not screenshots or measured output.

## Before publishing

- Replace the screenshot placeholder only with authentic screenshots from the plugin.
- Confirm the QGIS Plugin Repository listing and download target.
- Test the published site at desktop, tablet and mobile widths.
- Check links after deployment.
