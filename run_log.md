
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
