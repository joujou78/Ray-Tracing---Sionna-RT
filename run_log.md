
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
