# Source Inventory

The original working folder was inspected before creating this public repository. It was not an existing Git repository.

## Original Workspace Structure

- Root notebooks: city-level aggregation notebooks, modeling notebooks, St. Louis analysis notebooks, correlation analysis, and trip-distribution summaries.
- `bikeshare_data/`: large raw and intermediate bike-share ridership files, including Bay Wheels and Pogoh files plus tract-level trip summaries.
- `census_data/`: ACS/Census profile tables for 2010, 2020, and 2023 workflows; several files are too large for a portfolio repository.
- `tract_shapefiles/`: TIGER/Line tract shapefiles for the comparison regions.
- `multiple_regression/`: merged tract-level modeling tables and feature-selection outputs.
- `corr_outputs/` and `correlation_results*`: correlation screens and selected-variable outputs.
- `stl/`: St. Louis predictions, scooter route/segment exports, city street data, and local exploratory files.
- `maps/`, `histograms/`, and top-level PNGs: generated visualizations.
- `phase_files/`: shapefiles and Quarto files for phased map outputs.
- `parks/`, `tl_2019_29_prisecroads/`, `tl_2022_us_primaryroads/`: supporting geospatial layers.

## Repository Selection

This public version keeps the reusable source code, selected stripped notebooks, small derived prediction outputs, generated figures, and synthetic demo data. It excludes raw ridership tables, large Census exports, shapefile folders, scratch files, and datasets with unverified redistribution rights.

## Verification Notes

- No QGIS `.qgs` or `.qgz` project file was found; shapefiles and `.qmd` phase files were present.
- No dependency or environment file was found in the original workspace, so `requirements.txt` and `pyproject.toml` were inferred from imports.
- `Tech Writing Final (5).pdf` was not found in the accessible workspace or user home search results, so the README has not been checked against the report.
- The cover/report-date discrepancy requested in the task cannot be checked until the report PDF is available.
