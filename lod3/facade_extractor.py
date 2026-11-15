"""Step 1 -- Facade extraction.

Input : GeoDataFrame of building footprints (Polygon, EPSG:27700 BNG).
Output: DataFrame with one row per facade segment, including:
  building_id, facade_id, x0, y0, x1, y1, z_bottom, z_top,
  length_m, cx, cy, normal_x, normal_y, normal_az_deg
"""

import math
import numpy as np
import pandas as pd
from shapely.geometry import Point


def extract_facades(footprints_gdf, tx_easting, tx_northing,
                    zone_radius_m, z_bottom=0.0):
    """Return a DataFrame of facade segments for buildings inside zone_radius_m.

    Parameters
    ----------
    footprints_gdf : GeoDataFrame
        Must have columns: geometry (Polygon), building_id (str/int),
        height_m (float, roof height above ground).
    tx_easting, tx_northing : float
        Transmitter position in BNG metres.
    zone_radius_m : float
        Only buildings whose centroid is within this radius are processed.
    z_bottom : float
        Ground z for all facades (metres ASL, or 0 for relative height).

    Returns
    -------
    pd.DataFrame with columns:
        building_id, facade_id, x0, y0, x1, y1, z_bottom, z_top,
        length_m, cx, cy, normal_x, normal_y, normal_az_deg
    """
    tx = Point(tx_easting, tx_northing)
    rows = []

    for _, row in footprints_gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        centroid = geom.centroid
        if centroid.distance(tx) > zone_radius_m:
            continue

        bid = row["building_id"]
        z_top = z_bottom + float(row.get("height_m", 10.0))

        coords = list(geom.exterior.coords)
        # Remove duplicate closing vertex
        if coords[0] == coords[-1]:
            coords = coords[:-1]

        for i, (x0, y0) in enumerate(coords):
            x1, y1 = coords[(i + 1) % len(coords)]
            length = math.hypot(x1 - x0, y1 - y0)
            if length < 0.01:
                continue

            cx = (x0 + x1) / 2.0
            cy = (y0 + y1) / 2.0

            # Outward normal (90 deg CCW from edge direction)
            dx, dy = (x1 - x0) / length, (y1 - y0) / length
            nx, ny = -dy, dx

            # Flip normal to face away from centroid
            to_cx = cx - centroid.x
            to_cy = cy - centroid.y
            if nx * to_cx + ny * to_cy < 0:
                nx, ny = -nx, -ny

            az = math.degrees(math.atan2(nx, ny)) % 360.0  # north = 0

            rows.append({
                "building_id": bid,
                "facade_id": f"{bid}_f{i:04d}",
                "x0": x0, "y0": y0,
                "x1": x1, "y1": y1,
                "z_bottom": z_bottom,
                "z_top": z_top,
                "length_m": length,
                "cx": cx, "cy": cy,
                "normal_x": nx, "normal_y": ny,
                "normal_az_deg": az,
            })

    return pd.DataFrame(rows)


def filter_facades_by_route(facades_df, route_gdf, buffer_m):
    """Keep only facades within buffer_m of a drive-test route LineString."""
    from shapely.ops import unary_union
    route_union = unary_union(route_gdf.geometry.values)
    buffered = route_union.buffer(buffer_m)

    keep = []
    for _, row in facades_df.iterrows():
        pt = Point(row["cx"], row["cy"])
        keep.append(buffered.contains(pt))

    return facades_df[keep].reset_index(drop=True)
