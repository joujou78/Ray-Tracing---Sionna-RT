"""
Terrain height providers.

TerrariumProvider
    Global elevation tiles (AWS Open Data "Terrain Tiles", Terrarium PNG
    encoding, zoom 0-15). Over England the high zooms are built from the
    Environment Agency 2 m LiDAR DTM (tile headers list e.g.
    ``uk_lidar/LIDAR-DTM-2M-TQ37.tif``); elsewhere SRTM / other sources.
    Tiles are cached on disk under data/cache/terrarium.

GeoTiffProvider
    Local DTM rasters in any CRS (e.g. EA LiDAR Composite DTM 1 m in
    EPSG:27700 from https://environment.data.gov.uk/survey). Drop .tif/.asc
    files in data/dtm/. Points not covered fall back to Terrarium.
    An optional DSM folder (data/dsm/) yields clutter heights R = DSM - DTM.
"""
from __future__ import annotations

import io
import logging
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import numpy as np
from PIL import Image

log = logging.getLogger(__name__)
DATA = Path(__file__).resolve().parents[2] / "data"


def _bilinear(grid_lookup, x, y):
    """Bilinear sample given a function returning values at integer pixel coords."""
    x0, y0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = x - x0, y - y0
    v00 = grid_lookup(x0, y0)
    v10 = grid_lookup(x0 + 1, y0)
    v01 = grid_lookup(x0, y0 + 1)
    v11 = grid_lookup(x0 + 1, y0 + 1)
    return (v00 * (1 - fx) * (1 - fy) + v10 * fx * (1 - fy)
            + v01 * (1 - fx) * fy + v11 * fx * fy)


class TerrariumProvider:
    name = "terrarium"
    URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
    MAX_ZOOM = 15
    TILE = 256

    def __init__(self, cache_dir: Path | None = None, max_tiles: int = 400):
        self.cache_dir = Path(cache_dir or DATA / "cache" / "terrarium")
        self.max_tiles = max_tiles
        self._mem: dict[tuple[int, int, int], np.ndarray] = {}
        self._lock = threading.Lock()
        self._client = httpx.Client(timeout=30.0, headers={"User-Agent": "rf-coverage-tool/0.1"})

    # -- tile I/O ---------------------------------------------------------
    def _tile(self, z: int, x: int, y: int) -> np.ndarray:
        key = (z, x, y)
        with self._lock:
            if key in self._mem:
                return self._mem[key]
        path = self.cache_dir / str(z) / str(x) / f"{y}.png"
        if path.exists():
            data = path.read_bytes()
        else:
            data = self._download(self.URL.format(z=z, x=x, y=y))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        rgb = np.asarray(Image.open(io.BytesIO(data)).convert("RGB"), dtype=np.float32)
        elev = rgb[..., 0] * 256.0 + rgb[..., 1] + rgb[..., 2] / 256.0 - 32768.0
        with self._lock:
            if len(self._mem) > 2000:   # crude memory bound (~0.5 GB)
                self._mem.clear()
            self._mem[key] = elev
        return elev

    def _download(self, url: str, attempts: int = 4) -> bytes:
        """GET with retry/back-off: S3 occasionally returns transient 5xx."""
        for k in range(attempts):
            try:
                r = self._client.get(url)
                r.raise_for_status()
                return r.content
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                status = getattr(getattr(exc, "response", None), "status_code", 0)
                if k == attempts - 1 or 400 <= status < 500:
                    raise
                time.sleep(0.5 * 2 ** k)
        raise RuntimeError("unreachable")

    @staticmethod
    def _pixel(lat, lon, z):
        n = 2.0 ** z * 256
        x = (np.asarray(lon) + 180.0) / 360.0 * n
        lr = np.radians(lat)
        y = (1.0 - np.log(np.tan(lr) + 1.0 / np.cos(lr)) / np.pi) / 2.0 * n
        return x - 0.5, y - 0.5   # pixel centres

    def choose_zoom(self, lat, lon, res_m: float) -> int:
        lat0 = float(np.nanmean(lat))
        z = self.MAX_ZOOM
        for zz in range(8, self.MAX_ZOOM + 1):
            if 156543.03 * math.cos(math.radians(lat0)) / 2 ** zz <= res_m / 2:
                z = zz
                break
        while z > 8:
            x, y = self._pixel(lat, lon, z)
            tiles = np.unique((np.floor(x / 256).astype(np.int64) << 32) | np.floor(y / 256).astype(np.int64))
            if len(tiles) <= self.max_tiles:
                break
            z -= 1
        return z

    def elevation(self, lat, lon, res_m: float = 30.0, zoom: int | None = None):
        lat = np.asarray(lat, float)
        lon = np.asarray(lon, float)
        shape = lat.shape
        lat, lon = lat.ravel(), lon.ravel()
        z = zoom if zoom is not None else self.choose_zoom(lat, lon, res_m)
        x, y = self._pixel(lat, lon, z)
        x0, y0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
        ntile = 2 ** z
        tx = np.concatenate([x0, x0 + 1]) // 256 % ntile
        ty = np.clip(np.concatenate([y0, y0 + 1]) // 256, 0, ntile - 1)
        keys = np.unique(tx * ntile + ty)
        with ThreadPoolExecutor(max_workers=16) as ex:
            tiles = list(ex.map(lambda k: self._tile(z, int(k // ntile), int(k % ntile)), keys))
        stack = np.stack(tiles)

        def lookup(px, py):
            px = px % (ntile * 256)
            py = np.clip(py, 0, ntile * 256 - 1)
            k = (px // 256) * ntile + (py // 256)
            i = np.searchsorted(keys, k)
            return stack[i, py % 256, px % 256]

        h = _bilinear(lookup, x, y)
        # Sea and bathymetry: treat the sea surface as 0 m for propagation.
        return np.maximum(h, 0.0).reshape(shape), z


class GeoTiffProvider:
    """Local rasters (any CRS) with Terrarium fallback. Requires rasterio + pyproj."""

    name = "local"

    def __init__(self, dtm_dir: Path | None = None, dsm_dir: Path | None = None,
                 fallback: TerrariumProvider | None = None):
        import rasterio  # noqa: F401  (fail early if missing)

        self.fallback = fallback or TerrariumProvider()
        self.dtm = self._index(Path(dtm_dir or DATA / "dtm"))
        self.dsm = self._index(Path(dsm_dir or DATA / "dsm"))

    @staticmethod
    def _index(folder: Path):
        import rasterio
        from pyproj import Transformer

        items = []
        if not folder.is_dir():
            return items
        for f in sorted(list(folder.glob("**/*.tif")) + list(folder.glob("**/*.asc"))):
            try:
                with rasterio.open(f) as ds:
                    if ds.crs is None:
                        log.warning("%s has no CRS; assuming EPSG:27700 (British National Grid)", f)
                    crs = ds.crs or "EPSG:27700"
                    items.append(dict(path=f, bounds=ds.bounds, res=abs(ds.res[0]),
                                      tf=Transformer.from_crs("EPSG:4326", crs, always_xy=True)))
            except Exception as exc:  # noqa: BLE001
                log.warning("Skipping %s: %s", f, exc)
        return items

    @property
    def has_data(self) -> bool:
        return bool(self.dtm)

    def _sample(self, items, lat, lon, res_m):
        import rasterio
        from rasterio.windows import Window
        from rasterio.enums import Resampling

        out = np.full(lat.shape, np.nan)
        for it in items:
            x, y = it["tf"].transform(lon, lat)
            b = it["bounds"]
            inside = (x >= b.left) & (x <= b.right) & (y >= b.bottom) & (y <= b.top) & np.isnan(out)
            if not inside.any():
                continue
            with rasterio.open(it["path"]) as ds:
                col, row = ~ds.transform * (x[inside], y[inside])
                c0 = max(int(np.floor(col.min())) - 1, 0)
                r0 = max(int(np.floor(row.min())) - 1, 0)
                c1 = min(int(np.ceil(col.max())) + 2, ds.width)
                r1 = min(int(np.ceil(row.max())) + 2, ds.height)
                # Decimate when the requested resolution is much coarser than the raster
                f = max(1, int(res_m / (2 * it["res"])))
                w, hgt = c1 - c0, r1 - r0
                ow, oh = max(2, w // f), max(2, hgt // f)
                arr = ds.read(1, window=Window(c0, r0, w, hgt), out_shape=(oh, ow),
                              resampling=Resampling.average if f > 1 else Resampling.nearest,
                              masked=True).astype(float).filled(np.nan)
                # Continuous source coords (pixel centre at i + 0.5) -> output pixel index
                sx, sy = ow / w, oh / hgt
                px = np.clip((col - c0) * sx - 0.5, 0, ow - 1)
                py = np.clip((row - r0) * sy - 0.5, 0, oh - 1)

                def lookup(ix, iy):
                    return arr[np.clip(iy, 0, oh - 1), np.clip(ix, 0, ow - 1)]

                vals = _bilinear(lookup, px, py)
            sub = out[inside]
            sub[np.isnan(sub)] = vals[np.isnan(sub)]
            out[inside] = sub
        return out

    def elevation(self, lat, lon, res_m: float = 30.0, zoom=None):
        lat = np.asarray(lat, float)
        lon = np.asarray(lon, float)
        shape = lat.shape
        la, lo = lat.ravel(), lon.ravel()
        h = self._sample(self.dtm, la, lo, res_m)
        miss = np.isnan(h)
        z = None
        if miss.any():
            fb, z = self.fallback.elevation(la[miss], lo[miss], res_m, zoom)
            h[miss] = fb
        return h.reshape(shape), z

    def clutter(self, lat, lon, res_m: float = 30.0):
        """Representative clutter height R = DSM - DTM (clipped 0..60 m), or None."""
        if not self.dsm:
            return None
        lat = np.asarray(lat, float)
        lon = np.asarray(lon, float)
        dsm = self._sample(self.dsm, lat.ravel(), lon.ravel(), res_m)
        dtm = self._sample(self.dtm, lat.ravel(), lon.ravel(), res_m)
        r = np.nan_to_num(np.clip(dsm - dtm, 0.0, 60.0), nan=0.0)
        return r.reshape(lat.shape)


def make_provider(source: str = "auto"):
    """'terrarium', 'local', or 'auto' (local if any DTM rasters exist)."""
    terr = TerrariumProvider()
    if source in ("auto", "local"):
        try:
            gp = GeoTiffProvider(fallback=terr)
            if gp.has_data or source == "local":
                return gp
        except ImportError:
            if source == "local":
                raise
    return terr
