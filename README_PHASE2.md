# Phase 2 localization build

This development build updates the feature-layer chooser and output-format selector.

1. Back up the existing `RoadNetworkIntegrationToolkit` plugin folder.
2. Extract the ZIP into the QGIS Python plugins directory, replacing the plugin folder.
3. Restart QGIS and open the plugin.
4. Test French, Spanish, Portuguese, Swahili and Arabic by opening a GeoPackage or File Geodatabase with multiple feature layers; also verify the output-format dropdown refreshes after switching languages.

The build retains English fallback for new Phase 2 strings in languages whose translations have not yet been reviewed. It is an incremental development build, not the final 33-language release.
