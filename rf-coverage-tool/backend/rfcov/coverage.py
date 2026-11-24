"""
Area coverage on radials, resampled to a Web-Mercator raster.

Pipeline
--------
1. Cast radials from the Tx (uniform azimuth step, uniform range step ds).
2. Sample terrain (and optional clutter) along every radial.
3. For every sample j on a radial, compute basic transmission loss Lb of the
   path Tx -> sample j (P.1812 / P.526 / FSPL), batched over radials.
4. Bilinear-resample the polar Lb grid onto a Web-Mercator raster, which
   Leaflet can overlay without distortion.

The raster carries *basic transmission loss* only. Tx power, antenna gains,
patterns and feeder losses are applied in the browser, so they can be changed
without recomputing (same behaviour as rfconsult.uk).
"""
from __future__ import annotations

import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field

import numpy as np

from . import geo, itu_maps
from .p1812 import P1812Params, free_space_loss, path_loss, path_loss_batch

# Samples along a radial, azimuth cap for a full circle, raster pixel cap
PRESETS = {
    "draft": dict(n_range=200, n_az=720, max_px=700),
    "standard": dict(n_range=400, n_az=1440, max_px=1100),
    "high": dict(n_range=700, n_az=2160, max_px=1500),
}
ELEMENTS_PER_BATCH = 3_000_000

_POOL: ProcessPoolExecutor | None = None


def _pool() -> ProcessPoolExecutor:
    global _POOL
    if _POOL is None:
        _POOL = ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2)))
    return _POOL


@dataclass
class CoverageSpec:
    tx_lat: float
    tx_lon: float
    htg: float = 30.0
    hrg: float = 1.5
    f_mhz: float = 900.0
    model: str = "p1812"
    radius_km: float = 20.0
    bbox: tuple | None = None          # (south, west, north, east) for "current map view"
    resolution: str = "standard"
    p: float = 50.0
    pl: float = 50.0
    sigma_l: float = 0.0
    pol: int = 2
    k_factor: float | None = None      # P.526 models; None -> from ITU DN50
    use_clutter: bool = False
    extra: dict = field(default_factory=dict)


def _worker(args, n_chunks=8):
    """
    Loss for a batch of radials. Endpoints are split into chunks and each chunk
    only carries the profile up to its furthest endpoint, which skips most of
    the unused upper triangle of the (J, n) path matrices (~45 % less work).
    """
    d, h, j_idx, prm, phi, clutter, model, k = args
    out = np.empty((h.shape[0], len(j_idx)))
    for sel in np.array_split(np.arange(len(j_idx)), n_chunks):
        if len(sel) == 0:
            continue
        m = j_idx[sel[-1]] + 1
        cl = None if clutter is None else clutter[:, :m]
        out[:, sel] = path_loss_batch(d[:m], h[:, :m], j_idx[sel], prm, phi=phi[:, sel],
                                      clutter=cl, model=model, k_factor=k)
    return out


def _area(spec: CoverageSpec):
    """Max range (m) and azimuth interval [az0, az0 + span) in degrees."""
    if spec.bbox is None:
        return spec.radius_km * 1000.0, 0.0, 360.0
    s, w, n, e = spec.bbox
    t = np.linspace(0, 1, 60)
    lat = np.concatenate([np.full_like(t, s), np.full_like(t, n), s + (n - s) * t, s + (n - s) * t])
    lon = np.concatenate([w + (e - w) * t, w + (e - w) * t, np.full_like(t, w), np.full_like(t, e)])
    dist, brg = geo.distance_bearing(spec.tx_lat, spec.tx_lon, lat, lon)
    rmax = float(dist.max()) * 1.01
    inside = s <= spec.tx_lat <= n and w <= spec.tx_lon <= e
    if inside:
        return rmax, 0.0, 360.0
    b = np.sort(brg)
    gaps = np.diff(np.concatenate([b, [b[0] + 360.0]]))
    k = int(np.argmax(gaps))              # largest empty sector is outside the box
    az0 = b[(k + 1) % len(b)] - 1.0
    span = 360.0 - gaps[k] + 2.0
    return rmax, az0 % 360.0, min(span, 360.0)


def compute_coverage(spec: CoverageSpec, provider, parallel: bool = True) -> dict:
    t0 = time.time()
    pre = PRESETS.get(spec.resolution, PRESETS["standard"])
    rmax, az0, span = _area(spec)

    # Range step: radius mode -> n_range samples; map-view -> match the raster pixel
    ds = max(rmax / pre["n_range"], 10.0)
    if spec.bbox is not None:
        s, w, n, e = spec.bbox
        width_m = geo.distance_bearing(0.5 * (s + n), w, 0.5 * (s + n), e)[0]
        ds = max(width_m / pre["max_px"], rmax / 1200.0, 10.0)
    n = int(math.ceil(rmax / ds)) + 1
    d_m = np.arange(n) * ds
    d_km = d_m / 1000.0

    arc = math.radians(span) * rmax
    n_az = int(np.clip(math.ceil(arc / ds), 90, math.ceil(pre["n_az"] * span / 360.0)))
    full = span >= 360.0
    daz = span / n_az if full else span / (n_az - 1)
    az = az0 + np.arange(n_az) * daz

    # Terrain along radials
    lat, lon = geo.destination(spec.tx_lat, spec.tx_lon, az[:, None], d_m[None, :])
    h, zoom = provider.elevation(lat, lon, res_m=ds)
    t_terrain = time.time() - t0
    clutter = None
    if spec.use_clutter and hasattr(provider, "clutter"):
        clutter = provider.clutter(lat, lon, res_m=ds)
    h[:, 0] = h[0, 0]  # identical Tx ground for every radial

    dn, n0 = itu_maps.dn_n0(spec.tx_lat, spec.tx_lon)
    prm = P1812Params(f_ghz=spec.f_mhz / 1000.0, htg=spec.htg, hrg=spec.hrg, p=spec.p,
                      pl=spec.pl, sigma_l=spec.sigma_l, pol=spec.pol, dn=dn, n0=n0)

    j_idx = np.arange(4, n)
    jm = j_idx / 2.0  # path-centre latitude for beta0
    lo_i, hi_i = np.floor(jm).astype(int), np.ceil(jm).astype(int)
    phi_all = 0.5 * (lat[:, lo_i] + lat[:, hi_i])

    lb = np.full((n_az, n), np.nan, dtype=np.float32)
    # Very short paths (< 5 profile points): free space
    lb[:, 1:4] = free_space_loss(prm.f_ghz, d_km[1:4][None, :], (h[:, :1] + spec.htg) - (h[:, 1:4] + spec.hrg))
    lb[:, 0] = lb[:, 1]

    bsz = max(1, ELEMENTS_PER_BATCH // (n * n))
    jobs = []
    for b0 in range(0, n_az, bsz):
        sl = slice(b0, min(b0 + bsz, n_az))
        cl = None if clutter is None else clutter[sl]
        jobs.append((sl, (d_km, h[sl], j_idx, prm, phi_all[sl], cl, spec.model, spec.k_factor)))
    if parallel and len(jobs) > 1:
        results = _pool().map(_worker, [a for _, a in jobs])
    else:
        results = map(_worker, [a for _, a in jobs])
    for (sl, _), res in zip(jobs, results):
        lb[sl, 4:] = res
    t_prop = time.time() - t0

    raster = _to_mercator(spec, lb, az0, daz, n_az, full, ds, rmax, pre["max_px"])
    raster["meta"] = dict(
        model=spec.model, ds_m=ds, n_radials=n_az, n_range=n, terrain_zoom=zoom,
        dn=dn, n0=n0, itu_maps=itu_maps.available(), clutter=clutter is not None,
        tx_ground_amsl=float(h[0, 0]), compute_s=round(time.time() - t0, 2),
        terrain_s=round(t_terrain, 2), propagation_s=round(t_prop - t_terrain, 2), terrain=getattr(provider, "name", "?"),
    )
    return raster


def _to_mercator(spec, lb, az0, daz, n_az, full, ds, rmax, max_px):
    """Bilinear polar -> Web-Mercator raster. Returns dict with float32 array and bounds."""
    if spec.bbox is not None:
        s, w, n, e = spec.bbox
    else:
        dlat = math.degrees(rmax / geo.R_EARTH_M)
        dlon = dlat / max(math.cos(math.radians(spec.tx_lat)), 1e-6)
        s, n = spec.tx_lat - dlat, spec.tx_lat + dlat
        w, e = spec.tx_lon - dlon, spec.tx_lon + dlon
    x0, y0 = geo.lonlat_to_merc(w, s)
    x1, y1 = geo.lonlat_to_merc(e, n)
    px = ds / math.cos(math.radians(spec.tx_lat))         # mercator metres per pixel
    px = max(px, (x1 - x0) / max_px, (y1 - y0) / max_px)
    W = int(math.ceil((x1 - x0) / px))
    H = int(math.ceil((y1 - y0) / px))
    xs = x0 + (np.arange(W) + 0.5) * (x1 - x0) / W
    ys = y1 - (np.arange(H) + 0.5) * (y1 - y0) / H           # row 0 = north
    lon, lat = geo.merc_to_lonlat(xs[None, :], ys[:, None])
    lon, lat = np.broadcast_arrays(lon, lat)
    dist, brg = geo.distance_bearing(spec.tx_lat, spec.tx_lon, lat, lon)

    fa = ((brg - az0) % 360.0) / daz
    fr = dist / ds
    nr = lb.shape[1]
    ia = np.floor(fa).astype(np.int64)
    ir = np.floor(fr).astype(np.int64)
    ta, tr = fa - ia, fr - ir
    valid = (dist <= rmax) & (ir < nr - 1)
    if full:
        ia0, ia1 = ia % n_az, (ia + 1) % n_az
    else:
        valid &= ia < n_az - 1
        ia0, ia1 = np.clip(ia, 0, n_az - 1), np.clip(ia + 1, 0, n_az - 1)
    ir0, ir1 = np.clip(ir, 0, nr - 1), np.clip(ir + 1, 0, nr - 1)
    v = (lb[ia0, ir0] * (1 - ta) * (1 - tr) + lb[ia1, ir0] * ta * (1 - tr)
         + lb[ia0, ir1] * (1 - ta) * tr + lb[ia1, ir1] * ta * tr)
    v = np.where(valid, v, np.nan).astype(np.float32)
    s2 = float(geo.merc_to_lonlat(0, y0)[1])
    n2 = float(geo.merc_to_lonlat(0, y1)[1])
    return dict(lb=v, width=W, height=H, bounds=[s2, float(w), n2, float(e)])


def compute_profile(provider, tx_lat, tx_lon, rx_lat, rx_lon, htg, hrg, f_mhz,
                    model="p1812", p=50.0, pl=50.0, sigma_l=0.0, pol=2,
                    k_factor=None, use_clutter=False, max_points=2500):
    """Full-resolution point-to-point profile and loss (used by probes)."""
    dist, brg = geo.distance_bearing(tx_lat, tx_lon, rx_lat, rx_lon)
    dist = float(dist)
    if dist < 20.0:
        raise ValueError("Receiver is within 20 m of the transmitter; move the probe further away.")
    ds = max(dist / (max_points - 1), 2.0)
    n = max(int(math.ceil(dist / ds)) + 1, 5)
    d_m = np.linspace(0.0, dist, n)
    lat, lon = geo.destination(tx_lat, tx_lon, float(brg), d_m)
    h, zoom = provider.elevation(lat, lon, res_m=max(d_m[1] - d_m[0], 2.0))
    clutter = provider.clutter(lat, lon, res_m=d_m[1]) if use_clutter and hasattr(provider, "clutter") else None
    mid = 0.5 * (tx_lat + rx_lat)
    dn, n0 = itu_maps.dn_n0(mid, 0.5 * (tx_lon + rx_lon))
    prm = P1812Params(f_ghz=f_mhz / 1000.0, htg=htg, hrg=hrg, p=p, pl=pl,
                      sigma_l=sigma_l, pol=pol, dn=dn, n0=n0)
    lb, info = path_loss(d_m / 1000.0, h, prm, phi=mid, clutter=clutter, model=model,
                         k_factor=k_factor, details=True)
    k_eff = k_factor if k_factor else 157.0 / (157.0 - dn)
    return dict(
        distance_m=dist, bearing_deg=float(brg), d_km=(d_m / 1000.0).round(5).tolist(),
        h=np.round(h, 2).tolist(),
        clutter=None if clutter is None else np.round(clutter, 1).tolist(),
        lb=lb, details={k: (None if v is None else (bool(v) if isinstance(v, (bool, np.bool_)) else float(v)))
                        for k, v in info.items()},
        k_eff=k_eff, dn=dn, n0=n0, terrain_zoom=zoom,
        tx_ground=float(h[0]), rx_ground=float(h[-1]),
    )
