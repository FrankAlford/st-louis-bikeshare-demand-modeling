import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import LineString, box

from st_louis_bikeshare.geospatial import (
    add_daily_density,
    allocate_line_counts_to_polygons,
    clean_count_series,
    z_score,
)


def _tracts():
    return gpd.GeoDataFrame(
        {"tract_id": ["A", "B"]},
        geometry=[box(0, 0, 10, 10), box(10, 0, 20, 10)],
        crs="EPSG:3857",
    )


def test_length_weighting_splits_crossing_segment_evenly():
    segments = gpd.GeoDataFrame(
        {"segment_id": ["s1"], "traversals": [100]},
        geometry=[LineString([(0, 5), (20, 5)])],
        crs="EPSG:3857",
    )

    result = allocate_line_counts_to_polygons(
        segments,
        _tracts(),
        segment_id_col="segment_id",
        polygon_id_col="tract_id",
        count_col="traversals",
    )

    values = dict(zip(result["tract_id"], result["allocated_count"]))
    assert values["A"] == pytest.approx(50)
    assert values["B"] == pytest.approx(50)


def test_partial_segment_outside_study_area_uses_full_segment_length():
    segments = gpd.GeoDataFrame(
        {"segment_id": ["s1"], "traversals": [80]},
        geometry=[LineString([(-10, 5), (10, 5)])],
        crs="EPSG:3857",
    )

    result = allocate_line_counts_to_polygons(
        segments,
        _tracts().iloc[[0]],
        segment_id_col="segment_id",
        polygon_id_col="tract_id",
        count_col="traversals",
    )

    assert result.loc[0, "tract_id"] == "A"
    assert result.loc[0, "allocated_count"] == pytest.approx(40)


def test_add_daily_density_fills_missing_polygons():
    allocations = pd.DataFrame({"tract_id": ["A"], "allocated_count": [20.0]})

    result = add_daily_density(
        _tracts(),
        allocations,
        polygon_id_col="tract_id",
        days=10,
        projected_crs="EPSG:3857",
    )

    assert result.loc[result["tract_id"] == "A", "allocated_count"].item() == 20
    assert result.loc[result["tract_id"] == "B", "allocated_count"].item() == 0
    assert result["allocated_count_per_day_per_sqmi"].notna().all()


def test_count_parser_and_z_score_helpers():
    counts = clean_count_series(pd.Series(["97,600", "< 100", None]))
    assert counts.tolist() == [97600.0, 100.0, 0.0]

    scores = z_score(pd.Series([5, 5, 5]))
    assert scores.tolist() == [0.0, 0.0, 0.0]
