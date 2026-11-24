"""
Radio-meteorological inputs for P.1812: DN50 (lapse rate) and N050 (sea-level
surface refractivity), from the digital maps that are an integral part of
Rec. ITU-R P.1812-8.

ITU does not permit redistribution of these maps, so they are not committed.
Run ``python scripts/fetch_itu_maps.py`` once to download them from itu.int
into data/itu_maps/. Without them, UK-typical fallbacks are used and the API
reports ``itu_maps: false``.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

MAP_DIR = Path(__file__).resolve().parents[2] / "data" / "itu_maps"

# Fallbacks: bilinear values of the P.1812-8 maps near Nottingham (52.95N, 1.15W),
# DN50 = 41.8, N050 = 325.0. Across Great Britain they range ~39.7-42.7 / ~321-327.
FALLBACK_DN = 41.8
FALLBACK_N0 = 325.0


@lru_cache(maxsize=1)
def _maps():
    try:
        cache = MAP_DIR / "p1812_maps.npz"
        if cache.exists():
            z = np.load(cache)
            return z["DN50"], z["N050"]
        dn = np.loadtxt(MAP_DIR / "DN50.TXT")
        n0 = np.loadtxt(MAP_DIR / "N050.TXT")
        np.savez(cache, DN50=dn, N050=n0)
        return dn, n0
    except OSError:
        return None


def _interp(m, lon, lat, step=1.5):
    """Bilinear interpolation on the ITU grid (lat 90..-90, lon 0..360, 1.5 deg)."""
    lat_off = 90.0 - lat
    lon_off = lon % 360.0
    ny, nx = m.shape
    yi, xi = int(lat_off / step), int(lon_off / step)
    fy, fx = lat_off / step - yi, lon_off / step - xi
    ul, ur = m[yi, xi], m[yi, (xi + 1) % nx]
    ll, lr = m[(yi + 1) % ny, xi], m[(yi + 1) % ny, (xi + 1) % nx]
    top = ul + fx * (ur - ul)
    bot = ll + fx * (lr - ll)
    return float(top + fy * (bot - top))


def available() -> bool:
    return _maps() is not None


def dn_n0(lat: float, lon: float) -> tuple[float, float]:
    m = _maps()
    if m is None:
        return FALLBACK_DN, FALLBACK_N0
    return _interp(m[0], lon, lat), _interp(m[1], lon, lat)
