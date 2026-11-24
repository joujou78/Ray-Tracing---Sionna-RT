# RF Coverage Mapper

Browser-based, terrain-aware RF coverage prediction. Click to place a transmitter,
set the link budget, and get a received-power map (dBm), click-to-read values,
probes with full-resolution path profiles (Fresnel zones), PNG export and JSON
save/load.

Standalone project: it does not depend on the Sionna RT work in the parent repository.

## Quick start

```bash
cd rf-coverage-tool
pip install -r requirements.txt
python scripts/fetch_itu_maps.py      # once: ITU-R P.1812-8 ΔN / N0 maps (not redistributable)
./run.sh                              # http://localhost:8000
```

Press **Demo**, or place a TX and press **Compute coverage**.

## Coverage page extras

* **TX grid field**: OS National Grid reference or Maidenhead locator; the cursor position and every map popup
  show both. Clicking a spot with no coverage still gives coordinates and *Place probe here*.
* **RX environment (ITU-R P.2108 §3.1)**: none / open / suburban / urban / dense urban / water. The path is
  computed with the RX raised to the representative clutter height R (10/15/20 m) and the height-gain or
  diffraction correction A<sub>h</sub> is added. Applies to the coverage map and probes.
* **LiDAR clutter overlay**: DSM − DTM from local rasters in `data/dsm/` and `data/dtm/` (`GET /api/clutter`).
* **Drive test**: load a CSV (lat, lon, measured dBm). Ofcom drive-test files with the `Site latitude: …`
  header are read directly, and *Use site setup from file* applies TX position, frequency, heights, powers,
  gains and the RX chain loss (cable + splitter + filter − LNA). Points are coloured by measured level or by
  error. Statistics (mean error, σ, RMSE, MAE, r) update live, and *Export comparison* writes a CSV.

## Path loss calculator (`/pathloss.html`)

Point-to-point companion page (like rfconsult.uk/pathloss):

* Place TX and RX on the map, type coordinates, or enter a **grid reference**:
  OS National Grid (`SK 086 875`) or Maidenhead locator (`IO93AK`). Both forms are shown for placed sites.
* Inputs: frequency, effective Earth k (P.526 models), terrain samples (Automatic or a fixed 201 to 2001),
  model (single knife-edge, delta-Bullington, P.1812-8, free space), antenna heights and gains,
  optional TX power and feeder losses.
* Results: distance, forward/reverse bearing, free-space loss, diffraction loss, basic loss Lb,
  antenna-to-antenna loss (Lb − Gt − Gr), received level, LOS / Fresnel clearance.
* Cross-section: terrain on effective-Earth curvature, clutter, direct ray, 60 % and 100 % first Fresnel
  zones, and **diffraction control points** (dominant edge for LoS; TX/RX horizon obstacles and the
  Bullington point for NLoS), also marked on the map.
* Swap TX/RX, Clear, Notes, Save/Load JSON. Deep link: `pathloss.html?tx=lat,lon&rx=lat,lon`.

## Architecture

```
frontend/ (vanilla JS + Leaflet)          backend/rfcov (FastAPI + NumPy)
 ├─ map, TX/probe placement                ├─ api.py        REST + static files
 ├─ Prx = Ptx+Gtx-Lf+Gpat(az)-Lb+Grx-Lf    ├─ coverage.py   radials -> Lb -> Web-Mercator raster
 ├─ colour bands, contours, legend         ├─ p1812.py      P.1812-8 / P.526 / FSPL, vectorised
 ├─ profile chart (curvature, Fresnel)     ├─ terrain.py    AWS Terrain Tiles + local GeoTIFF DTM/DSM
 └─ PNG export, JSON config                └─ itu_maps.py   ΔN50 / N050 lookup
```

| Endpoint | Purpose |
|---|---|
| `POST /api/coverage` | Basic transmission loss raster (float32, base64) on Web-Mercator bounds |
| `POST /api/profile` | Full-resolution TX→RX profile, Lb, model breakdown (Lbfs, Ld, Lbs, Lba), diffraction control points |
| `GET /api/elevation` | Ground height at a point |
| `GET /api/clutter` | Clutter heights (DSM − DTM) raster for the map view, from local LiDAR |
| `GET /api/grid` | WGS84 ↔ OS National Grid reference (pyproj, OSGB36 datum shift) |
| `GET /api/health` | Status, ITU maps present, terrain source |

**Key design choice:** the server returns *basic transmission loss* only. Power,
gains, feeder losses, the azimuth pattern and colour settings are applied in the
browser, so they update instantly without a new propagation run.

**Coverage engine:** radials from the TX share one distance grid, so each radial
sample is the RX end of its own path. `p1812.path_loss_batch` evaluates all
endpoints of a batch of radials at once with masked (B, J, n) arrays, and the
probe/profile view calls the same code with B = J = 1. Batches run on a process
pool and the result is bilinearly resampled to a Web-Mercator grid (exact overlay
in Leaflet).

Typical timings, 4 CPU cores, 20 km radius: Draft about 1 s, Standard about 6 s, High about 25 s
(plus first-time terrain tile download).

## Propagation models

| Model | Notes |
|---|---|
| ITU-R P.1812-8 | Full method: LoS with multipath/focusing (Esp), delta-Bullington diffraction with spherical-earth correction, troposcatter, ducting/layer reflection, combination (Fj, Fk), time % (1-50), location % with σL, polarisation. ΔN and N0 from the ITU maps at the path centre. |
| Delta-Bullington | Lbfs + P.1812/P.526 delta-Bullington diffraction (median, user k or k50). |
| Single knife-edge | Lbfs + J(ν) of the dominant edge (P.526). |
| Free space | Lbfs including TX/RX height difference. |

### Validation

`tests/test_p1812_validation.py` compares against the ITU-R SG3 / Ofcom
validation set published with the reference implementation
([eeveetza/Py1812](https://github.com/eeveetza/Py1812)):

```bash
python scripts/fetch_validation_data.py
python -m pytest -q tests
```

All 51 land-path cases agree with the reference Lb to within 1e-6 dB, including
the intermediate terms Lbs, Lba and Ld50. The 12 cases that contain sea segments
are skipped (see limitations). `tests/test_p1812_batch.py` checks that the
batched radial engine equals standalone point-to-point calls.

## Terrain data

* **Default: AWS Terrain Tiles** (Mapzen Terrarium encoding, zoom ≤ 15), the same
  family of source rfconsult.uk credits. Over England the tile metadata shows they
  are built from the **EA 2 m LiDAR DTM** (for example `uk_lidar/LIDAR-DTM-2M-TQ37.tif`).
  Outside England they come from SRTM and other sources, which smooth peaks
  (Ben Nevis reads about 1316 m against 1345 m). Tiles are cached in `data/cache/`.
* **Local DTM (better):** put GeoTIFF/ASC tiles in `data/dtm/` (any CRS, BNG
  assumed if missing), for example the EA *LiDAR Composite DTM 1 m* from
  <https://environment.data.gov.uk/survey>. With terrain set to "Auto" they take
  priority and the tiles fill gaps. Coarse runs decimate the raster by averaging.
* **Clutter:** put matching DSM tiles in `data/dsm/` and tick *Use clutter*.
  R = DSM − DTM (0-60 m) feeds the P.1812 profile (g = h + R).

## Limitations (current)

* **Land paths only.** Every profile point is treated as radio-climatic zone 4
  (inland). Sea and coastal paths (ω, dct/dcr) are not modelled yet.
* **Azimuth pattern only.** No vertical pattern or downtilt yet.
* ΔN / N0 for coverage maps are taken at the TX location (they vary on a 1.5° grid).
* Sea and bathymetry are clamped to 0 m.
* Planning aid only. Predictions must be checked against measurements by a qualified RF engineer before any licensing or design decision.

## Roadmap

1. P.2109 building entry loss; P.2108 §3.2 statistical clutter loss for the TX side.
2. Land/sea zones from a coastline dataset, to enable the full P.1812 mixed-path terms.
3. Vertical antenna pattern (downtilt), and multiple TX with best-server and SINR maps.
4. Building-level mode: export the area around a TX to a Sionna RT scene for
   site-specific ray tracing, and compare with the P.1812 layer.
5. Automatic per-model calibration (offset/slope fit) from a loaded drive test.
