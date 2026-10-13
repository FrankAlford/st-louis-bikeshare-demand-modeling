"""Geospatial utilities used by the bike-share and scooter comparison notebooks.

The core operation is length-weighted allocation of line-segment traversal
counts to census tract polygons. This mirrors the project notebook workflow:
intersect scooter street-segment geometries with tract boundaries, measure each
intersected piece, and assign each segment's observed traversal count in
proportion to the piece length.
"""

from __future__ import annotations

import re
from typing import Hashable

import geopandas as gpd
import numpy as np
import pandas as pd

SQ_METERS_PER_SQ_MILE = 2_589_988.110336


def parse_numeric_count(value: object) -> float:
    """Parse display counts such as ``"97,600"`` into floats.

    Some shared-mobility exports store counts as formatted strings. For
    less-than values such as ``"< 100"``, this returns the numeric bound. Use
    the result as an approximation, not a count of unique scooter trips.
    """

    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float, np.number)):
        return float(value)

    text = str(value).strip().replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    return float(match.group(0))


def clean_count_series(series: pd.Series) -> pd.Series:
    """Return a numeric count series from formatted count values."""

    return series.map(parse_numeric_count).astype(float)


def _project_for_length(
    segments: gpd.GeoDataFrame,
    polygons: gpd.GeoDataFrame,
    projected_crs: object | None,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Return both layers in a projected CRS suitable for length and area."""

    if segments.crs is None or polygons.crs is None:
        if projected_crs is None:
            raise ValueError("Both inputs need CRS metadata or projected_crs must be provided.")
        segments = segments.set_crs(projected_crs, allow_override=True)
        polygons = polygons.set_crs(projected_crs, allow_override=True)

    target_crs = projected_crs
    if target_crs is None:
        if segments.crs == polygons.crs and segments.crs and segments.crs.is_projected:
            target_crs = segments.crs
        elif segments.crs and segments.crs.is_projected:
            target_crs = segments.crs
        elif polygons.crs and polygons.crs.is_projected:
            target_crs = polygons.crs
        else:
            target_crs = segments.estimate_utm_crs() or polygons.estimate_utm_crs()

    if target_crs is None:
        raise ValueError("Could not infer a projected CRS; pass projected_crs explicitly.")

    return segments.to_crs(target_crs), polygons.to_crs(target_crs)


def allocate_line_counts_to_polygons(
    segments: gpd.GeoDataFrame,
    polygons: gpd.GeoDataFrame,
    *,
    segment_id_col: Hashable,
    polygon_id_col: Hashable,
    count_col: Hashable,
    projected_crs: object | None = None,
    output_col: str = "allocated_count",
    min_piece_length: float = 0.0,
) -> pd.DataFrame:
    """Allocate line-segment counts to polygons by intersection length.

    Parameters
    ----------
    segments:
        Line geometries with one count per segment.
    polygons:
        Polygon geometries, typically census tracts.
    segment_id_col:
        Unique segment identifier column.
    polygon_id_col:
        Polygon identifier column to aggregate to.
    count_col:
        Numeric count column to allocate.
    projected_crs:
        Optional projected CRS for length calculations. If omitted, the
        function uses the input projected CRS or estimates a local UTM CRS.
    output_col:
        Name of the allocated count column in the returned table.
    min_piece_length:
        Drop overlay fragments with length at or below this threshold.

    Returns
    -------
    pandas.DataFrame
        One row per polygon that receives a positive-length share of at least
        one segment. Counts outside the polygon layer are not reallocated.
    """

    required_segment_cols = {segment_id_col, count_col, "geometry"}
    required_polygon_cols = {polygon_id_col, "geometry"}
    missing_segments = required_segment_cols - set(segments.columns)
    missing_polygons = required_polygon_cols - set(polygons.columns)
    if missing_segments:
        raise KeyError(f"segments missing required columns: {sorted(missing_segments)}")
    if missing_polygons:
        raise KeyError(f"polygons missing required columns: {sorted(missing_polygons)}")

    seg = segments[[segment_id_col, count_col, "geometry"]].copy()
    poly = polygons[[polygon_id_col, "geometry"]].copy()
    seg[count_col] = pd.to_numeric(seg[count_col], errors="coerce").fillna(0.0)

    seg, poly = _project_for_length(seg, poly, projected_crs)
    seg["_segment_length"] = seg.geometry.length
    seg = seg[seg["_segment_length"] > 0].copy()

    pieces = gpd.overlay(
        seg[[segment_id_col, count_col, "_segment_length", "geometry"]],
        poly[[polygon_id_col, "geometry"]],
        how="intersection",
        keep_geom_type=False,
    )
    if pieces.empty:
        return pd.DataFrame(columns=[polygon_id_col, output_col])

    pieces["_piece_length"] = pieces.geometry.length
    pieces = pieces[pieces["_piece_length"] > min_piece_length].copy()
    pieces["allocation_fraction"] = pieces["_piece_length"] / pieces["_segment_length"]
    pieces[output_col] = pieces[count_col] * pieces["allocation_fraction"]

    return (
        pieces.groupby(polygon_id_col, as_index=False)[output_col]
        .sum()
        .sort_values(polygon_id_col)
        .reset_index(drop=True)
    )


def add_daily_density(
    polygons: gpd.GeoDataFrame,
    allocations: pd.DataFrame,
    *,
    polygon_id_col: Hashable,
    count_col: str = "allocated_count",
    days: float,
    projected_crs: object | None = None,
) -> gpd.GeoDataFrame:
    """Join allocated counts to polygons and add per-day and area-density fields."""

    if days <= 0:
        raise ValueError("days must be positive.")

    gdf = polygons.merge(allocations, on=polygon_id_col, how="left").copy()
    gdf[count_col] = gdf[count_col].fillna(0.0)

    projected, _ = _project_for_length(gdf, gdf[[polygon_id_col, "geometry"]].copy(), projected_crs)
    gdf["area_sqmi"] = projected.geometry.area / SQ_METERS_PER_SQ_MILE
    gdf[f"{count_col}_per_day"] = gdf[count_col] / days
    gdf[f"{count_col}_per_day_per_sqmi"] = gdf[f"{count_col}_per_day"] / gdf["area_sqmi"]
    return gdf


def z_score(series: pd.Series) -> pd.Series:
    """Return population-standardized z-scores, using 0 for constant inputs."""

    values = pd.to_numeric(series, errors="coerce")
    std = values.std(ddof=0)
    if pd.isna(std) or std == 0:
        return pd.Series(np.zeros(len(values)), index=series.index)
    return (values - values.mean()) / std
