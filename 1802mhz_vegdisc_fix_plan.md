# 1802 MHz — Vegetation Disc Fix Plan

Date: 2026-07-19
Context: CELL CAL with DISABLE_VEG_DISCS=True stalled at 14.5 dB (3 plateaus, 173 evals).
Scalar-only result was 13.32 dB — Powell material optimisation made things worse.

---

## Root Cause

`DISABLE_VEG_DISCS=True` removes all vegetation geometry from the RT.
Vegetation attenuates measurements by mean 2.88 dB (max 6.90 dB) on 495/495 RX paths.
Weissberger pre-correction adjusts the average per path, but per-path variance
remains — some paths have 0 dB vegetation, some 7 dB.
Powell cannot fix heteroscedastic errors by tuning global material parameters.
Result: Powell walks away from scalar-only solution (13.32 dB) and stalls at 14.5 dB.

---

## Fix

Enable vegetation discs with S=0 (physical blocking, no scattering flood).

| Parameter | Old value | New value | Reason |
|-----------|-----------|-----------|--------|
| DISABLE_VEG_DISCS | True | False | Re-enable vegetation geometry |
| CAL_APPLY_WEISSBERGER | True | False | Not needed — geometry handles it |
| itu_ceiling_board S | 0 (transparent) | 0 (blocking) | No scatter flood, just absorption |

S=0 avoids the 700x scatter flood seen at 915 MHz when S>0.
The disc geometry attenuates rays passing through it — physical blocking without scatter amplification.

---

## Step-by-Step

### Step 1 — Stop current CELL CAL
Interrupt the kernel (stop the current run at eval 173, RMSE=14.5 dB).

### Step 2 — Delete stale calibration files
```bash
rm ~/sionna_rt/nottingham_ofcom2018_1802mhz_dem/calibrated_materials_1802mhz.json
rm ~/sionna_rt/nottingham_ofcom2018_1802mhz_dem/scalar_offset_1802mhz.json
```
These were produced by the bad DISABLE_VEG_DISCS=True run — must not be loaded.

### Step 3 — Update CELL 1 config
```python
DISABLE_VEG_DISCS      = False   # vegetation geometry active
CAL_APPLY_WEISSBERGER  = False   # not needed when geometry is present
CAL_MIN_DIST_KM        = 0.40   # keep — excludes near-range R²=-2.281 receivers
CAL_SAMPLES_PS         = 5_000_000
USE_CALIBRATED_FILES   = False   # start fresh
```

### Step 4 — Update CELL 4A: set S=0 on itu_ceiling_board
In the `_ITU_P2040` dict, the `vegetation` row currently has S=0.40.
The `itu_ceiling_board` material (used for all disc PLYs) must be set to S=0.

Add/confirm this block at the END of CELL 4A (after all other material assignments,
BEFORE the DISABLE_VEG_DISCS block):

```python
# Force vegetation disc material to S=0 — blocking only, no scatter flood
_cb_mat = scene.radio_materials.get('itu_ceiling_board')
if _cb_mat is not None:
    for _attr in ('scattering_coefficient', '_scattering_coefficient'):
        if hasattr(_cb_mat, _attr):
            try:
                setattr(_cb_mat, _attr, 0.0)
            except Exception:
                pass
    print("  itu_ceiling_board S=0 (blocking only, no scatter)")
```

Note: `itu_vegetation` (terrain_veg.ply) keeps S=0 as it already has — no change needed there.

### Step 5 — Run cell sequence
```
CELL 3 → CELL 3-VEG → CELL 4A → CELL 4 → CELL CAL
```
Do NOT run CELL 3b (scene rebuild) unless PLYs changed — vegetation PLYs are already present.

### Step 6 — Monitor CELL CAL
Expected behaviour with vegetation geometry active:
- Scalar phase: scalar_factor_db should be smaller in magnitude (vegetation accounts for some loss)
- RMSE after scalar: target < 13.32 dB (better than DISABLE_VEG_DISCS=True scalar-only)
- Powell: should converge lower since per-path variance is reduced

Target convergence: 10-12 dB calibration RMSE → ~7-8 dB evaluation RMSE at 100M samples.

### Step 7 — After CELL CAL converges
```
CELL 4A (apply calibrated materials) → CELL 8e at NUM_SAMPLES_PS=100_000_000
```

---

## Why This Will Help

| Scenario | RMSE floor | Why |
|----------|-----------|-----|
| DISABLE_VEG_DISCS=True, no Weissberger | 13.7 dB | Mean bias corrected but per-path variance uncorrected |
| DISABLE_VEG_DISCS=True, Weissberger | 13.32 dB (scalar) / 14.5 dB (Powell) | Per-path variance defeats Powell |
| DISABLE_VEG_DISCS=False, S=0 | ~10-12 dB (expected) | Geometry handles per-path variance; Powell navigates cleaner surface |

---

## Fallback (if S=0 discs still cause issues)

If RMSE is worse with S=0 discs than scalar-only:
- Remove nDSM extra discs only (keep OSM/VOM discs): `VEG_NDMS_EXTRA = False` in scene builder
- Or raise CAL_MIN_DIST_KM to 0.50 to exclude receivers with heavy vegetation paths
- Or try Differential Evolution (CELL CAL-DE) instead of Powell — more robust on noisy surfaces

---

## Reference: Previous Run Summary

| Run | CAL_MIN_DIST_KM | DISABLE_VEG_DISCS | Weissberger | Best CAL RMSE |
|-----|----------------|-------------------|-------------|---------------|
| Run 1 (stuck) | 0.15 | True | False | ~15.5 dB (1400+ evals, no convergence) |
| Run 2 | 0.40 | True | True | 13.32 dB scalar / 14.5 dB Powell (173 evals) |
| Run 3 (planned) | 0.40 | False | False | target 10-12 dB |

