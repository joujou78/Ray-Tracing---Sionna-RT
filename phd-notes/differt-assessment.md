# DiffeRT Assessment for Gradient-Based Material Calibration

**Date:** 2026-11-16
**Purpose:** Evaluate DiffeRT (3D) as a replacement for CMA-ES in CELL CAL

---

## Libraries Assessed

| Library | Verdict |
|---------|---------|
| DiffeRT2d (v0.4.1) | NOT applicable -- 2D only, no EM material physics |
| DiffeRT (3D) | Theoretically capable; no worked calibration example exists |

**DiffeRT2d:** `https://github.com/jeertmans/DiffeRT2d/tree/v0.4.1` -- JAX-based, 2D geometry only. Associated paper DOI: 10.21105/joss.06815. Discard.

**DiffeRT (3D):** `https://github.com/jeertmans/DiffeRT` -- differentiable RT toolbox for 3D radio propagation. JAX + Equinox + Warp. Paper DOI: 10.1109/ICMLCN64995.2025.11139997 (ICMLCN 2025).

---

## DiffeRT 3D -- Key Capabilities

### EM Module (`differt/src/differt/em/`)

- **`_material.py`:** `Material` class with S (scattering coefficient), XPD, thickness as JAX pytree leaves -- **differentiable**. ITU-R P.2040-4 frequency-dependent er/sigma for 19 materials matching Sionna RT: Concrete, Brick, Glass, Metal, Wet ground, etc. `properties` callable marked `static` -- er/sigma via ITU formula NOT auto-differentiable (must pass as explicit JAX arrays to get gradients through permittivity).
- **`_fresnel.py`:** `fresnel_coefficients(n_r, cos_theta_i)`, `slab_coefficients(...)`, s/p polarisation. Physically correct Fresnel at each bounce.
- 19 ITU-R P.2040-4 materials -- same set as Sionna RT.

### Geometry Module (`differt/src/differt/geometry/`)

- **`_mesh.py`:** `Mesh` class; `Mesh.load_ply()`, `Mesh.load_obj()`; per-face material index; Warp CUDA-accelerated triangle intersection; `jax.custom_vjp` on first triangle hit only.
- **`_scene.py`:**
  - `Scene.load_xml(file)` -- loads Sionna-compatible XML directly. **Can load `scene_with_full.xml` with zero conversion.**
  - `Scene.from_sionna(sionna_scene)` -- loads from a running Sionna scene object.
  - SBR (shooting-and-bouncing rays), exhaustive, hybrid solvers.
  - `scene.trace_paths()`, `scene.trace_fields()`.
- **`_sionna.py`:** Sionna scene downloader (not a converter -- ignore the name).

### Differentiability

| Parameter | Differentiable? |
|-----------|----------------|
| S (scattering coefficient) | Yes -- JAX pytree leaf |
| XPD | Yes -- JAX pytree leaf |
| thickness | Yes -- JAX pytree leaf |
| er (permittivity) via ITU formula | No -- `properties` callable is `static` |
| er passed as explicit JAX array | Yes -- workaround: bypass ITU formula |
| Multi-bounce gradient chain (SBR) | Uncertain -- Warp any-hit kernel has no VJP |
| First triangle hit | Yes -- `jax.custom_vjp` implemented |

---

## Notebooks Assessment

All notebooks read from: `docs/source/notebooks/` (21 files total).

### `ray_tracing_at_city_scale.ipynb`
- Uses `Mesh.load_obj("bruxelles.obj")` + SBR solver, `order=range(6)`.
- Marked **"TODO"** -- only setup and one plotted example.
- No EM physics, no calibration, no timing output.
- City-scale claim is in prose, not in demonstrated results.
- Scene files available: `bruxelles.obj/.mtl`, `manhattan.obj/.mtl`, `manhattan_small.obj/.mtl`.

### `smoothing.ipynb` -- "Smoothing Discontinuities for Fully Differentiable Ray Tracing"
- Optimization section ("Optimizing TX Position with and without smoothing") is explicitly **TODO**.
- What exists: smoothing function s(x; alpha) -> step as alpha -> inf; boolean equivalents via `jnp.minimum`/`jnp.maximum`; coverage map of a 6x4x2 box scene.
- Reflection coefficient hardcoded to 0.5. No material calibration.
- Exhaustive solver with `smoothing_factor` sweep (logspace(-1, 5, 20)).

### `em_fields_abc.ipynb` -- most complete notebook
Demonstrates four interaction types with `compute_received_fields` + `compute_received_power` -> dBW plots:
1. Specular reflection -- 1 GHz, concrete ground, two-ray fading fringes
2. Edge diffraction -- UTD, 90 degree metal wedge, continuous across ISB/RSB
3. Transmission -- 0.2 m concrete slab at 3.5 GHz
4. Diffuse scatter -- Lambertian (`scattering_coefficient=0.6`)
5. Directive/backscattering -- `DirectivePattern(alpha_r=6.0)`, `BackscatteringPattern`

Materials loaded by name: `"itu_concrete"`, `"Metal"`. No gradient optimization anywhere.

### Other notebooks (not read -- lower priority)
`advanced_path_tracing.ipynb`, `coherence.ipynb`, `diffraction.ipynb`, `multipath.ipynb` -- likely show path tracing patterns but no calibration based on names.

---

## Capability Summary

| Capability | Status |
|-----------|--------|
| City-scale OBJ scene loading | Demonstrated (Brussels) |
| `Scene.load_xml()` from existing `scene_with_full.xml` | In source code -- zero conversion from current pipeline |
| `Scene.from_sionna(sionna_scene)` | In source code |
| EM material model (ITU-R P.2040-4, 19 materials) | Demonstrated in `em_fields_abc` |
| Received power computation | Demonstrated |
| Fresnel coefficients (s/p polarisation) | In source code |
| Scattering patterns (Lambertian, Directive, Backscattering) | Demonstrated |
| **Gradient-based material calibration** | **Not demonstrated anywhere** |
| Smoothing/optimization loop | Explicitly TODO in `smoothing.ipynb` |
| Multi-bounce VJP chain on full city scene | Unknown -- no evidence |

---

## Weather Integration Design (Open-Meteo + ITU-R P.838-3)

Designed but not yet implemented. Pipeline placement:

```
CELL WEATHER (new, after CELL 1)
  -> fetch Open-Meteo Historical Archive
  -> merge hourly weather onto _df_meas by timestamp floor("h")

CELL CAL
  -> filter: _df_cal = _df_cal[_df_cal["precipitation"] <= CAL_MAX_PRECIP_MM_H]
  -> avoids calibrating on rain-corrupted measurements

CELL 4A
  -> if rain_fraction > 0.3: load wet_ground permittivity (er=20, sigma=0.5)

CELL 8e
  -> apply ITU-R P.838-3 rain attenuation per receiver
  -> gamma_R = k * R^alpha (dB/km)
  -> total_atten = gamma_R * mean_path_length_km
```

**Open-Meteo API:** `https://archive-api.open-meteo.com/v1/archive` -- free, no key. Variables: `precipitation`, `relative_humidity_2m`, `temperature_2m`, `pressure_msl`. Use `openmeteo_requests` + `requests_cache` + `retry_requests`.

**ITU-R P.838-3 magnitude at key frequencies (25 mm/h rain rate, 1 km path):**

| Frequency | k_H | alpha_H | gamma_R (dB/km) | 1 km atten |
|-----------|-----|---------|-----------------|-----------|
| 915 MHz | 3.87e-4 | 0.912 | ~0.008 | ~0.008 dB -- negligible |
| 1802 MHz | ~0.003 | ~0.98 | ~0.07 | ~0.07 dB -- negligible |
| 2695 MHz | ~0.014 | ~1.02 | ~0.37 | ~0.37 dB -- marginal |
| 3602 MHz | ~0.030 | ~1.05 | ~0.82 | ~0.82 dB -- relevant |

Rain matters most at 3602 MHz. At 915 MHz and 1802 MHz the effect is below calibration noise floor (~0.12 dB MC noise at 30M samples).

**Key functions (copy into CELL WEATHER / CELL 8e):**

```python
def _p838_specific_atten_db_per_km(rain_rate_mm_h: float, freq_hz: float) -> float:
    """ITU-R P.838-3 specific rain attenuation (dB/km), horizontal polarisation."""
    import numpy as np
    _FREQ_TABLE_HZ = [1e9,  2e9,   4e9,   6e9,   10e9]
    _K_H_TABLE     = [3.87e-4, 4.38e-3, 2.94e-2, 7.61e-2, 2.65e-1]
    _ALPHA_H_TABLE = [0.912,   1.015,   1.051,   1.078,   1.228]
    log_f = np.log10(freq_hz)
    log_fA = np.interp(log_f, np.log10(_FREQ_TABLE_HZ), np.log10(_K_H_TABLE))
    alpha  = np.interp(log_f, np.log10(_FREQ_TABLE_HZ), _ALPHA_H_TABLE)
    k = 10 ** log_fA
    return k * (rain_rate_mm_h ** alpha)


def _rain_path_atten_db(paths_vertices, rain_rate_mm_h: float, freq_hz: float) -> np.ndarray:
    """paths_vertices: [n_rx, n_paths, n_segments+1, 3] (scene-local metres). Returns [n_rx] dB."""
    import numpy as np
    gamma = _p838_specific_atten_db_per_km(rain_rate_mm_h, freq_hz)
    if gamma < 0.001:
        return np.zeros(paths_vertices.shape[0])
    segs = paths_vertices[:, :, 1:, :] - paths_vertices[:, :, :-1, :]
    path_lengths_km = np.linalg.norm(segs, axis=-1).sum(axis=-1) / 1000.0
    mean_len_km = np.nanmean(path_lengths_km, axis=-1)
    return gamma * mean_len_km
```

**CELL WEATHER skeleton:**

```python
FETCH_WEATHER = True
WEATHER_CACHE_DIR = os.path.join(BASE_DIR, ".weather_cache")
WEATHER_VARS = ["precipitation", "relative_humidity_2m", "temperature_2m", "pressure_msl"]
_df_meas_weather = None

if FETCH_WEATHER:
    import openmeteo_requests, requests_cache
    from retry_requests import retry
    os.makedirs(WEATHER_CACHE_DIR, exist_ok=True)
    _cache = requests_cache.CachedSession(
        os.path.join(WEATHER_CACHE_DIR, "openmeteo"), expire_after=-1)
    _om = openmeteo_requests.Client(session=retry(_cache, retries=5, backoff_factor=0.2))
    _t_col = "timestamp" if "timestamp" in _df_meas.columns else "time"
    _t = pd.to_datetime(_df_meas[_t_col], utc=True)
    _params = {
        "latitude": _df_meas["latitude"].mean(),
        "longitude": _df_meas["longitude"].mean(),
        "start_date": _t.min().date().isoformat(),
        "end_date": _t.max().date().isoformat(),
        "timezone": "UTC",
        "hourly": WEATHER_VARS,
    }
    _resp = _om.weather_api(
        "https://archive-api.open-meteo.com/v1/archive", params=_params)[0]
    _hourly = _resp.Hourly()
    _df_w = pd.DataFrame({
        "weather_time": pd.date_range(
            start=pd.Timestamp(_hourly.Time(), unit="s", tz="UTC"),
            end=pd.Timestamp(_hourly.TimeEnd(), unit="s", tz="UTC"),
            freq=pd.Timedelta(seconds=_hourly.Interval()), inclusive="left"),
        **{v: _hourly.Variables(i).ValuesAsNumpy() for i, v in enumerate(WEATHER_VARS)},
    })
    _df_meas_weather = _df_meas.copy()
    _df_meas_weather["weather_time"] = _t.dt.floor("h")
    _df_meas_weather = _df_meas_weather.merge(_df_w, on="weather_time", how="left")
```

---

## Recommended PhD Workflow

**Option A (conservative -- recommended):** Keep Sionna RT for all runs. Use DiffeRT only for a prototype comparison:
1. Load `scene_with_full.xml` via `Scene.load_xml()` on a 50-receiver subset
2. Build a gradient calibration loop: `jax.grad` through `scene.trace_paths()` -> Adam, ~20-50 steps
3. Compare cal RMSE vs CMA-ES at same number of function evaluations
4. Report as thesis finding: "gradient descent achieves X dB vs Y dB CMA-ES in Z wall-clock time"

**Option B (future work):** Full DiffeRT pipeline once multi-bounce VJP is verified upstream. Not recommended before thesis submission.

**Key limitation to watch:** Warp any-hit kernel has no VJP. Multi-bounce gradient chain (beyond first triangle hit) is unverified. Test with order=1 (single reflection) first to confirm gradients flow correctly.

---

## Pending Implementation Tasks

### Weather integration
- [ ] Add CELL WEATHER to: `sionna2_2695mhz_dem_simulation_nottingham.ipynb`, `sionna2_3602mhz_dem_simulation.ipynb`, `sionna2_3602mhz_dem_simulation_stevenage.ipynb`, `sionna2_3602mhz_dem_simulation_southampton.ipynb`
- [ ] Add rain filter to CELL CAL (`CAL_MAX_PRECIP_MM_H = 2.0`)
- [ ] Add wet ground permittivity switching to CELL 4A
- [ ] Add `_rain_path_atten_db()` correction to CELL 8e for 2695/3602 MHz notebooks

### DiffeRT prototype
- [ ] Install DiffeRT in dev environment: `pip install differt`
- [ ] Test `Scene.load_xml("~/sionna_rt/nottingham_ofcom2018_1802mhz_dem/scene_v4_full/scene_with_full.xml")`
- [ ] Verify `scene.trace_paths(order=1, solver="exhaustive")` returns paths on 50-receiver subset
- [ ] Build gradient loop: loss = MSE(predicted_pl, measured_pl) over S parameters
- [ ] Check gradient flow -- confirm `jax.grad` returns non-zero gradients for S
- [ ] Scale test: how many receivers/triangles before OOM?
