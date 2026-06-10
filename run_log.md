
---

## Run 3 — DEM + Limited Roads (154k verts) — 2026-06-09

**Scene:** buildings + 9 road types (limited OSM, 154,754 verts)
**Solver:** batched 5 RX/batch, 80M samples
**Scatter:** SCATTER_OVERRIDE = 0.70

### CELL 8e (in progress — partial results)

| Threshold | Method | N | RMSE | R² |
|-----------|--------|---|------|----|
| 0–750m | ON incoh | 67 | 7.9 dB | +0.715 |
| 0–900m | ON incoh | 78 | 7.7 dB | +0.750 |
| 0–1000m | ON incoh | 87 | 7.9 dB | +0.769 |
| 0–1250m | ON incoh | 179 | 11.5 dB | +0.593 |

### Comparison vs Run 2 (DEM + limited roads, previous)
- 0–750m: R² +0.715 vs +0.614 (+0.10 improvement)
- 0–1000m: RMSE 7.9 vs 8.8 dB (−0.9 dB improvement)

### Next steps
- Wait for full CELL 8e output
- Record overall RMSE
- Rebuild scene with full roads (274k verts, already built)
- Run differentiable RT calibration

### Full CELL 8e Results — Run 3 (DEM + Limited Roads)

| Threshold | Method | N | RMSE | Bias | R² |
|-----------|--------|---|------|------|----|
| 0–900m | ON incoh | 78 | 7.7 dB | −4.8 | +0.750 |
| 0–1000m | ON incoh | 87 | 7.9 dB | −5.1 | +0.769 ← peak R² |
| 0–1250m | ON incoh | 179 | 11.5 dB | −8.2 | +0.593 |
| 0–1500m | ON incoh | 221 | 11.6 dB | −8.5 | +0.522 |
| 0–1750m | ON incoh | 289 | 13.4 dB | −10.2 | +0.222 |
| 0–2000m | ON incoh | 355 | 14.1 dB | −11.0 | +0.067 |
| 0–2250m | ON incoh | 448 | 14.5 dB | −11.6 | −0.107 |
| 0–2500m | ON incoh | 482 | 15.2 dB | −12.3 | −0.215 |

**Key finding:** Systematic negative bias worsening with distance (−5 → −12 dB)
→ scatter too low at long range (per-material S: concrete=0.20, brick=0.25)
→ Fix: run differentiable RT calibration to find optimal S per material
→ Expected fix: SCATTER_OVERRIDE ~0.50 or calibrated per-material values

### Complete Results — Run 3 (DEM + Limited Roads, 154k verts)

| Range | RMSE | Bias | R² | Method |
|-------|------|------|----|--------|
| 0–900m | 7.7 dB | −4.8 | +0.750 | ON incoh |
| 0–1000m | 7.9 dB | −5.1 | +0.769 ← peak | ON incoh |
| 0–1500m | 11.6 dB | −8.5 | +0.522 | ON incoh |
| 0–2000m | 14.1 dB | −11.0 | +0.067 | ON incoh |
| 0–3000m | 15.1 dB | −12.4 | −0.166 | ON incoh |
| 0–4000m | 14.3 dB | −11.4 | −0.029 | ON incoh |

**Diagnosis:** Systematic bias −5→−12 dB growing with distance
→ Per-material scatter too low (concrete S=0.20, brick S=0.25)
→ Fix: differentiable RT calibration → expected optimal S ~0.45–0.55

**Next:** Run calibration on scene_with_roads_019.xml

---

## Run 4 — Full Scene (bridges + embankments + water + veg) — 2026-06-10

**Scene:** scene_with_full.xml — buildings + roads + bridges + embankments + water + vegetation
**Note:** ⚠ BAD SCENE — building material classification bug: 77k buildings wrongly as itu_glass
**Solver:** Sionna 2 PathSolver, 1200 RX, scatter S=0.70
**Status:** Baseline only — scene being rebuilt with correct brick/concrete classification

### Overall metrics (bad glass scene — for reference only)

| Method | N | RMSE | Bias | R² |
|--------|---|------|------|----|
| Best ON | 1199 | 19.52 dB | −13.57 | −0.635 |
| Incoh ON | 1199 | 20.30 dB | −16.18 | −0.768 |
| Best OFF | 1018 | 29.25 dB | −3.76 | −2.761 |

### Per-band RMSE (Incoh ON, dB)

| Band | RMSE |
|------|------|
| 0–300m | 8.83 dB |
| 300–700m | 24.10 dB |
| 700–1200m | 22.55 dB |
| 1200–2000m | 26.31 dB |
| 2000–3000m | 28.01 dB |
| >3000m | 15.17 dB |

### Ray classification (246,423 rays, 1199 RX)

| Type | Count | % |
|------|-------|---|
| DIFFRACTION | 201,002 | 81.6% |
| MULTI_REFLECTION | 36,867 | 15.0% |
| LOS | 8,228 | 3.3% |
| REFLECTION | 326 | 0.1% |

**Key observation:** Diffraction-dominated (81.6%) — expected for 17m TX in dense UK urban.
Scattering ON vs OFF: at >3km, ON=15.2 dB vs OFF=33.1 dB — scattering critical for long range.
Bias source: glass buildings too transparent → signals 13–16 dB too strong.

### CELL 8e — Cumulative distance bands (Incoh ON, after P.833 correction)

| Range | N | Bias | RMSE | R² |
|-------|---|------|------|----|
| 0–100m | 8 | −9.9 dB | 11.2 dB | −8.444 |
| 0–200m | 17 | −6.2 dB | 8.1 dB | −4.127 |
| 0–300m | 26 | −7.3 dB | 8.8 dB | −1.172 |
| 0–500m | 44 | −11.8 dB | 13.6 dB | −0.739 |
| 0–750m | 67 | −17.0 dB | 19.5 dB | −0.731 |
| 0–1000m | 87 | −15.9 dB | 19.1 dB | −0.353 |
| 0–1250m | 179 | −16.7 dB | 20.0 dB | −0.231 |
| 0–1500m | 221 | −17.5 dB | 20.6 dB | −0.521 |
| 0–1750m | 289 | −19.4 dB | 22.2 dB | −1.116 |
| 0–2000m | 355 | −20.5 dB | 23.2 dB | −1.540 |
| 0–2250m | 448 | −21.4 dB | 23.9 dB | −2.029 |
| 0–2500m | 482 | −22.2 dB | 24.6 dB | −2.178 |

Avg rays: ON=~50k–117k / OFF=~35–126 (scattering spawning orders of magnitude more paths from glass surfaces)

### P.833 Vegetation Correction Summary

| Metric | Value |
|--------|-------|
| Vegetation polygons | 2,187 (16.86 km²) |
| RX with veg on path | 1,121 / 1,200 (93.4%) |
| Mean veg depth | 140.6 m |
| Max veg depth | 826.1 m |
| Mean Weissberger loss | 21.21 dB |
| Max Weissberger loss | 67.33 dB |

| Band | N | Mean veg loss | % affected |
|------|---|---------------|------------|
| 0–300m | 26 | 0.00 dB | 0.0% |
| 300–500m | 18 | 0.00 dB | 0.0% |
| 500–750m | 23 | 0.00 dB | 0.0% |
| 750–1000m | 20 | 3.32 dB | 50.0% |
| 1000–1250m | 92 | 12.79 dB | 97.8% |
| 1250–1500m | 42 | 21.66 dB | 100.0% |
| 1500–2000m | 134 | 27.10 dB | 100.0% |
| 2000–3000m | 170 | 27.67 dB | 100.0% |
| 3000–9999m | 675 | 22.17 dB | 100.0% |

### Failure mode analysis (bad glass scene)

- **Bias grows −7 dB → −22 dB with distance**: path loss exponent too shallow — glass reflections sustain energy at long range
- **Scattering ON ≈ OFF**: glass specular reflections already carry most energy; diffuse scattering adds noise only
- **Coherent combining worst** (−27 dB bias): random phases in real scene make coherent meaningless
- **OFF coherent best at <500m** (R²=+0.025): only positive R² in entire table — collapses beyond 750m
- **R² uniformly negative**: model worse than predicting the mean at every distance band
- **Root cause confirmed**: 1,664,481 glass verts → near-perfect reflectors → 15–22 dB excess power at all ranges

### Scene material comparison

| Material | Run 4 (bad — glass bug) | Run 5 (fixed) |
|----------|------------------------|---------------|
| itu_glass | 1,664,481 verts | 52,329 verts (−97%) |
| itu_brick | 0 verts | 1,626,924 verts |
| itu_concrete | ~60k verts | 61,985 verts |

### Next step
Rebuild scene with correct brick/concrete classification → re-run → expect RMSE ~8–12 dB, bias ~−5 dB
