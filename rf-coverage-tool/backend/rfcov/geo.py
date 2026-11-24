"""Spherical-earth geodesy and Web-Mercator helpers (vectorised, degrees in/out)."""
import numpy as np

R_EARTH_M = 6371008.8
MERC_R = 6378137.0  # Web Mercator sphere radius


def destination(lat, lon, bearing_deg, dist_m):
    """Point reached from (lat, lon) after dist_m along an initial bearing (great circle)."""
    p1, l1 = np.radians(lat), np.radians(lon)
    th = np.radians(bearing_deg)
    dl = np.asarray(dist_m) / R_EARTH_M
    p2 = np.arcsin(np.sin(p1) * np.cos(dl) + np.cos(p1) * np.sin(dl) * np.cos(th))
    l2 = l1 + np.arctan2(np.sin(th) * np.sin(dl) * np.cos(p1), np.cos(dl) - np.sin(p1) * np.sin(p2))
    return np.degrees(p2), (np.degrees(l2) + 540.0) % 360.0 - 180.0


def distance_bearing(lat1, lon1, lat2, lon2):
    """Great-circle distance (m) and initial bearing (deg, 0..360) from point 1 to point 2."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(np.asarray(lon2) - lon1)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    dist = 2 * R_EARTH_M * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    y = np.sin(dl) * np.cos(p2)
    x = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    brg = (np.degrees(np.arctan2(y, x)) + 360.0) % 360.0
    return dist, brg


def lonlat_to_merc(lon, lat):
    x = MERC_R * np.radians(lon)
    y = MERC_R * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
    return x, y


def merc_to_lonlat(x, y):
    lon = np.degrees(np.asarray(x) / MERC_R)
    lat = np.degrees(2 * np.arctan(np.exp(np.asarray(y) / MERC_R)) - np.pi / 2)
    return lon, lat
