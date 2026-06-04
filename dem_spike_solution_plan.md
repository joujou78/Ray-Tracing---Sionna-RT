# DEM Spike Problem — Deep Analysis & Solution Plan

## Root Cause Chain
```
Raw LiDAR DTM tiles
    → Aircraft returns classified as ground (LiDAR algorithm error)
    → Isolated pixels at 129–192m ASL in ~65m terrain
    → Three downstream failures:
        1. Terrain mesh has 50m-tall spikes → blocks TX line-of-sight
        2. Buildings extruded on spike pixels → base_z=50m → rooftops at 58–75m → TX buried
        3. RX placed at spike pixels → 50m local z → 33m above nearby TX at 18m
```

## Why the ±50m Clamp is Insufficient
Clamps spike to 50m local — still wrong, just less wrong than 65m.
Real terrain near TX is ~1m local. Clamped spike gives 50m local.

## The Real Fix: Spatial Median Filter
Aircraft returns are **isolated high pixels** (1–3 pixels wide).
Real terrain is smooth gradients. Median filter eliminates spikes, preserves hills.

```
Before: 64  65  65  130  66  65  64   ← spike
After:  64  65  65   65  66  65  64   ← spike replaced with local median
```

### Algorithm (for CELL 3)
```python
from scipy.ndimage import median_filter

# After sampling DEM into 2D grid:
z_local_median = median_filter(z_grid, size=5)            # 5×5 = 105m window
spike_mask = (z_grid - z_local_median) > DEM_SPIKE_THRESHOLD_M
z_clean = z_grid.copy()
z_clean[spike_mask] = z_local_median[spike_mask]
print(f'  Spike pixels removed: {spike_mask.sum()} ({100*spike_mask.mean():.1f}%)')
```

### Config variable (CELL 0c)
```python
DEM_SPIKE_THRESHOLD_M = 15.0  # max allowed deviation above local 5×5 median
```

### Why 15m threshold is correct for UK
- Nottingham steepest real slope: ~8° = 3m rise per 21m pixel → well under 15m
- Aircraft returns: 65m above real ground → deviation >> 15m → correctly flagged
- No false positives on genuine hills

## Three Places to Fix

| Location | Current | Fix |
|---|---|---|
| CELL 3 — terrain mesh vertices | Raw _dem_z2() per pixel | 2D grid → median filter → use z_clean |
| CELL 3 — building base_z | Raw _dem_z2() per centroid | Bilinear interp from z_clean grid |
| CELL 7 — RX heights | Raw DTM tile sampling | Apply same 15m/5×5 filter on tile data |

## Expected Improvement After Fix

| Issue | Current (±50m clamp) | After median filter |
|---|---|---|
| Spike terrain height | 50m local | ~1m local (correct) |
| Building base_z at spike | 50m | ~1m (correct) |
| TX surroundings | 6/8 BLOCKED | LOS clear |
| RX near TX | z=51.5m | z=2.7m (correct) |
| DEM mode paths at 167m | 2–5 | Expected 100–1000+ |

## Implementation Steps
1. Add `DEM_SPIKE_THRESHOLD_M = 15.0` to CELL 0c
2. Refactor CELL 3 DEM loop: sample full grid first, then apply median filter
3. Replace building base_z sampling with bilinear lookup on z_clean grid
4. In CELL 7, apply median filter to DTM tile data before sampling RX heights
5. Relax hard clamp from ±50m to ±80m (safety net only)
6. Delete scene cache, rebuild, test with DEM terrain
