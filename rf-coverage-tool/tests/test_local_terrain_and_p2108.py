"""Local GeoTIFF DTM/DSM provider (synthetic BNG rasters) and P.2108 terminal clutter."""
import numpy as np
import pytest

from rfcov.p2108 import terminal_clutter

rasterio = pytest.importorskip("rasterio")
from rasterio.transform import from_origin  # noqa: E402

from rfcov.terrain import GeoTiffProvider  # noqa: E402


class ZeroFallback:
    name = "zero"

    def elevation(self, lat, lon, res_m=30.0, zoom=None):
        return np.zeros(np.shape(lat)), None


def _write(path, arr, e0, n0, res):
    with rasterio.open(path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                       dtype="float32", crs="EPSG:27700", transform=from_origin(e0, n0, res, res),
                       nodata=-9999) as ds:
        ds.write(arr.astype("float32"), 1)


@pytest.fixture()
def tiles(tmp_path):
    # 1 km x 1 km at 1 m, SK 57x 39x (Nottingham). DTM is a plane rising 1 m per 100 m east.
    e0, n0, size = 457000.0, 340000.0, 1000
    ee = e0 + (np.arange(size) + 0.5)
    dtm = np.tile(50.0 + (ee - e0) / 100.0, (size, 1))
    dsm = dtm.copy()
    dsm[400:600, 400:600] += 12.0          # a 200 m block of 12 m "buildings"
    (tmp_path / "dtm").mkdir()
    (tmp_path / "dsm").mkdir()
    _write(tmp_path / "dtm" / "t.tif", dtm, e0, n0, 1.0)
    _write(tmp_path / "dsm" / "t.tif", dsm, e0, n0, 1.0)
    return tmp_path


def _latlon(e, n):
    from pyproj import Transformer
    lon, lat = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True).transform(e, n)
    return np.array([lat]), np.array([lon])


def test_local_dtm_sampling_and_fallback(tiles):
    gp = GeoTiffProvider(tiles / "dtm", tiles / "dsm", fallback=ZeroFallback())
    lat, lon = _latlon(457250.0, 339500.0)
    h, _ = gp.elevation(lat, lon, res_m=1.0)
    assert h[0] == pytest.approx(52.5, abs=0.05)
    # decimated read (coarse request) still lands on the plane
    h2, _ = gp.elevation(lat, lon, res_m=50.0)
    assert h2[0] == pytest.approx(52.5, abs=0.5)
    # outside the tile -> fallback (zeros)
    lat, lon = _latlon(470000.0, 339500.0)
    assert gp.elevation(lat, lon, res_m=1.0)[0][0] == 0.0


def test_local_clutter_heights(tiles):
    gp = GeoTiffProvider(tiles / "dtm", tiles / "dsm", fallback=ZeroFallback())
    lat, lon = _latlon(457500.0, 339500.0)   # inside the block
    assert gp.clutter(lat, lon, res_m=1.0)[0] == pytest.approx(12.0, abs=0.05)
    lat, lon = _latlon(457100.0, 339100.0)   # open ground
    assert gp.clutter(lat, lon, res_m=1.0)[0] == pytest.approx(0.0, abs=0.05)


def test_p2108_terminal_clutter():
    assert terminal_clutter(1.0, 1.5, "none") == (0.0, 1.5, None)
    ah, r, _ = terminal_clutter(1.0, 1.5, "urban")            # hand-checked value
    assert r == 15.0 and ah == pytest.approx(23.04, abs=0.02)
    ah, r, _ = terminal_clutter(1.0, 1.5, "open")              # -21.8 log10(0.15)
    assert ah == pytest.approx(17.96, abs=0.02)
    assert terminal_clutter(1.0, 25.0, "dense_urban")[0] == 0.0   # above clutter
