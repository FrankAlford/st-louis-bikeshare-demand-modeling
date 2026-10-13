# Data

This repository intentionally excludes large raw ridership files, full ACS exports, tract shapefile folders, and scooter source exports whose redistribution rights were not verified.

Included:

- `sample/`: synthetic GeoJSON fixtures for demonstrating segment-to-tract length weighting.
- `derived/`: small derived St. Louis model outputs that support figures and documentation.

Excluded source data:

- Bike-share trip records from the 11 comparison systems. These should be downloaded from the original system operators or public open-data portals.
- U.S. Census/ACS profile tables and TIGER/Line tract geometries. Download from the U.S. Census Bureau.
- St. Louis scooter route/segment source files. Counts are treated as segment traversals, not unique scooter trips.
- QGIS/project scratch files and temporary geoprocessing outputs.

To reproduce the full notebooks, place source datasets under `data/raw/` or adapt the notebook paths to your local copies.
