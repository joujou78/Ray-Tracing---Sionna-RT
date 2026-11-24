"""
FastAPI application: propagation API + static frontend.

Run:  uvicorn rfcov.api:app --app-dir backend --port 8000
Then open http://localhost:8000
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Literal, Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import itu_maps
from .coverage import CoverageSpec, compute_coverage, compute_profile
from .terrain import make_provider

log = logging.getLogger("rfcov")
FRONTEND = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(title="RF Coverage Tool", version="0.1.0")
_providers: dict[str, object] = {}

Model = Literal["p1812", "delta_bullington", "knife_edge", "fspl"]


def provider(source: str = "auto"):
    if source not in _providers:
        _providers[source] = make_provider(source)
    return _providers[source]


class Common(BaseModel):
    freq_mhz: float = Field(900.0, ge=30, le=6000)
    tx_height: float = Field(30.0, ge=1, le=3000, description="Tx antenna height AGL, m")
    rx_height: float = Field(1.5, ge=1, le=3000, description="Rx antenna height AGL, m")
    model: Model = "p1812"
    time_pct: float = Field(50.0, ge=1, le=50)
    loc_pct: float = Field(50.0, gt=0, lt=100)
    sigma_loc: float = Field(0.0, ge=0, le=20)
    polarization: Literal["h", "v"] = "v"
    k_factor: Optional[float] = Field(None, gt=0.3, le=10, description="P.526 models only")
    terrain: Literal["auto", "terrarium", "local"] = "auto"
    clutter: bool = False


class CoverageRequest(Common):
    lat: float = Field(..., ge=-85, le=85)
    lon: float = Field(..., ge=-180, le=180)
    area: Literal["radius", "view"] = "radius"
    radius_km: float = Field(20.0, gt=0.2, le=150)
    bbox: Optional[list[float]] = Field(None, description="[south, west, north, east] for area='view'")
    resolution: Literal["draft", "standard", "high"] = "standard"


class ProfileRequest(Common):
    tx_lat: float
    tx_lon: float
    rx_lat: float
    rx_lon: float
    samples: Optional[int] = Field(None, ge=5, le=10000, description="Terrain samples; None = automatic")


@app.get("/api/health")
def health():
    prov = provider()
    return {"ok": True, "itu_maps": itu_maps.available(), "terrain": getattr(prov, "name", "?")}


@app.get("/api/elevation")
def elevation(lat: float = Query(..., ge=-85, le=85), lon: float = Query(..., ge=-180, le=180),
              terrain: str = "auto"):
    h, z = provider(terrain).elevation(np.array([lat]), np.array([lon]), res_m=5.0)
    return {"lat": lat, "lon": lon, "elevation_m": round(float(h[0]), 2), "zoom": z}


@app.post("/api/coverage")
def coverage(req: CoverageRequest):
    if req.area == "view" and (not req.bbox or len(req.bbox) != 4):
        raise HTTPException(422, "area='view' needs bbox [south, west, north, east]")
    spec = CoverageSpec(
        tx_lat=req.lat, tx_lon=req.lon, htg=req.tx_height, hrg=req.rx_height,
        f_mhz=req.freq_mhz, model=req.model, radius_km=req.radius_km,
        bbox=tuple(req.bbox) if req.area == "view" else None, resolution=req.resolution,
        p=req.time_pct, pl=req.loc_pct, sigma_l=req.sigma_loc,
        pol=1 if req.polarization == "h" else 2, k_factor=req.k_factor, use_clutter=req.clutter,
    )
    try:
        res = compute_coverage(spec, provider(req.terrain))
    except Exception as exc:  # surface terrain/network errors clearly
        log.exception("coverage failed")
        raise HTTPException(500, f"Coverage computation failed: {exc}") from exc
    lb = res.pop("lb")
    res["lb_b64"] = base64.b64encode(np.ascontiguousarray(lb, dtype="<f4").tobytes()).decode()
    res["tx"] = {"lat": req.lat, "lon": req.lon}
    return res


@app.post("/api/profile")
def profile(req: ProfileRequest):
    try:
        return compute_profile(
            provider(req.terrain), req.tx_lat, req.tx_lon, req.rx_lat, req.rx_lon,
            req.tx_height, req.rx_height, req.freq_mhz, model=req.model, p=req.time_pct,
            pl=req.loc_pct, sigma_l=req.sigma_loc, pol=1 if req.polarization == "h" else 2,
            k_factor=req.k_factor, use_clutter=req.clutter, max_points=req.samples or 2500,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        log.exception("profile failed")
        raise HTTPException(500, f"Profile computation failed: {exc}") from exc


@app.get("/api/grid")
def grid(lat: Optional[float] = None, lon: Optional[float] = None, ref: Optional[str] = None):
    """Convert WGS84 <-> OS National Grid reference (GB only)."""
    from .grid import from_osgb_ref, to_osgb_ref
    try:
        if ref is not None:
            la, lo = from_osgb_ref(ref)
            return {"lat": la, "lon": lo, "osgb": to_osgb_ref(la, lo)}
        if lat is None or lon is None:
            raise ValueError("give lat & lon, or ref")
        return {"lat": lat, "lon": lon, "osgb": to_osgb_ref(lat, lon)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


# Static frontend (mounted last so /api routes win)
@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND), name="static")
