"""Run the synthetic scooter-segment allocation demo."""

from pathlib import Path
import sys

import geopandas as gpd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from st_louis_bikeshare.geospatial import add_daily_density, allocate_line_counts_to_polygons


def main() -> None:
    tracts = gpd.read_file(REPO_ROOT / "data" / "sample" / "demo_tracts.geojson")
    segments = gpd.read_file(REPO_ROOT / "data" / "sample" / "demo_scooter_segments.geojson")

    allocations = allocate_line_counts_to_polygons(
        segments,
        tracts,
        segment_id_col="segment_id",
        polygon_id_col="tract_id",
        count_col="segment_traversals",
        projected_crs="EPSG:3857",
    )
    enriched = add_daily_density(
        tracts,
        allocations,
        polygon_id_col="tract_id",
        days=10,
        projected_crs="EPSG:3857",
    )

    cols = [
        "tract_id",
        "allocated_count",
        "allocated_count_per_day",
        "allocated_count_per_day_per_sqmi",
    ]
    print(enriched[cols].to_string(index=False))


if __name__ == "__main__":
    main()
