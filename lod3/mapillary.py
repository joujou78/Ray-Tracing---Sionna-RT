"""Step 2 -- Mapillary image selection (Mapillary API v4).

For each facade segment, query the Mapillary Graph API for images whose
camera looks toward the facade within a configurable angle tolerance.

Requires a Mapillary access token in the environment variable MAPILLARY_TOKEN.
See: https://www.mapillary.com/developer/api-documentation
"""

import os
import math
import logging
import requests

from .config import (
    MAPILLARY_API_BASE,
    MAPILLARY_TOKEN_ENV,
    LOD3_IMAGE_MAX_DIST_M,
    LOD3_IMAGE_DATE_RANGE,
    LOD3_IMAGE_MIN_FILL,
)

log = logging.getLogger(__name__)

_ANGLE_TOL_DEG = 45.0  # camera must look within ±45 deg of facade normal
_FIELDS = (
    "id,computed_geometry,computed_rotation,camera_parameters,"
    "captured_at,thumb_256_url,thumb_1024_url"
)


def _get_token():
    token = os.environ.get(MAPILLARY_TOKEN_ENV, "")
    if not token:
        raise EnvironmentError(
            f"Set {MAPILLARY_TOKEN_ENV} to your Mapillary access token. "
            "Create one at https://www.mapillary.com/developer"
        )
    return token


def _bbox(cx, cy, r):
    """Return (west, south, east, north) in WGS84 from BNG centre + radius m."""
    from pyproj import Transformer
    bng_to_wgs = Transformer.from_epsg(27700, 4326, always_xy=True)
    lon, lat = bng_to_wgs.transform(cx, cy)
    # rough degree offset for r metres
    dlat = r / 111_320
    dlon = r / (111_320 * math.cos(math.radians(lat)))
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


def _camera_az(computed_rotation):
    """Approximate camera azimuth from Mapillary computed_rotation (ECEF)."""
    # Mapillary rotation is [roll, pitch, yaw] in degrees (NED frame)
    # yaw: 0 = north, 90 = east
    if isinstance(computed_rotation, list) and len(computed_rotation) >= 3:
        return float(computed_rotation[2]) % 360.0
    return None


def _angle_diff(a, b):
    d = abs(a - b) % 360.0
    return d if d <= 180.0 else 360.0 - d


def select_images_for_facade(facade_row, max_images=5, session=None):
    """Return up to max_images Mapillary image records for one facade.

    Parameters
    ----------
    facade_row : dict or pd.Series
        Must have cx, cy, normal_az_deg.
    max_images : int
    session : requests.Session or None

    Returns
    -------
    list of dicts -- sorted by angular score, best first.
      Keys: id, lon, lat, az_deg, dist_m, thumb_256_url, thumb_1024_url,
            captured_at, fill_score
    """
    token = _get_token()
    s = session or requests.Session()
    s.headers.update({"Authorization": f"OAuth {token}"})

    cx, cy = float(facade_row["cx"]), float(facade_row["cy"])
    facade_az = float(facade_row["normal_az_deg"])
    # Camera looks opposite to facade normal (looks AT the wall)
    target_az = (facade_az + 180.0) % 360.0

    west, south, east, north = _bbox(cx, cy, LOD3_IMAGE_MAX_DIST_M * 1.5)
    bbox_str = f"{west},{south},{east},{north}"

    start_date, end_date = LOD3_IMAGE_DATE_RANGE
    params = {
        "fields": _FIELDS,
        "bbox": bbox_str,
        "start_captured_at": f"{start_date}T00:00:00",
        "end_captured_at": f"{end_date}T23:59:59",
        "limit": 50,
    }

    try:
        resp = s.get(f"{MAPILLARY_API_BASE}/images", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception as exc:
        log.warning("Mapillary API error for facade %s: %s", facade_row.get("facade_id"), exc)
        return []

    from pyproj import Transformer
    wgs_to_bng = Transformer.from_epsg(4326, 27700, always_xy=True)

    scored = []
    for img in data:
        geom = img.get("computed_geometry", {})
        if geom.get("type") != "Point":
            continue
        lon_i, lat_i = geom["coordinates"]
        ex, ey = wgs_to_bng.transform(lon_i, lat_i)
        dist = math.hypot(ex - cx, ey - cy)
        if dist > LOD3_IMAGE_MAX_DIST_M:
            continue

        cam_az = _camera_az(img.get("computed_rotation"))
        if cam_az is None:
            continue
        angle_err = _angle_diff(cam_az, target_az)
        if angle_err > _ANGLE_TOL_DEG:
            continue

        # Rough fill score: facade subtended angle / camera HFOV
        # Assumes 70 deg HFOV if camera_parameters unavailable
        cam_params = img.get("camera_parameters", {})
        hfov_deg = cam_params.get("hfov", 70.0)
        angular_width = math.degrees(2 * math.atan2(
            float(facade_row["length_m"]) / 2.0, max(dist, 1.0)
        ))
        fill = angular_width / hfov_deg

        scored.append({
            "id": img["id"],
            "lon": lon_i, "lat": lat_i,
            "cam_easting": ex, "cam_northing": ey,
            "az_deg": cam_az,
            "angle_err_deg": angle_err,
            "dist_m": dist,
            "fill_score": fill,
            "thumb_256_url": img.get("thumb_256_url", ""),
            "thumb_1024_url": img.get("thumb_1024_url", ""),
            "captured_at": img.get("captured_at", ""),
        })

    scored.sort(key=lambda r: (r["angle_err_deg"], -r["fill_score"]))
    good = [r for r in scored if r["fill_score"] >= LOD3_IMAGE_MIN_FILL]
    return (good or scored)[:max_images]


def download_image(url, out_path, session=None):
    """Download a Mapillary thumbnail to out_path."""
    token = _get_token()
    s = session or requests.Session()
    s.headers.update({"Authorization": f"OAuth {token}"})
    resp = s.get(url, timeout=20)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)
    return out_path
