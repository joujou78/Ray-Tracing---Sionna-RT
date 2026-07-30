# 1802 MHz CELL 8e Results — Calibration 3 (σ floor active)

## Calibration Summary
- Run date: 2026-07-30
- Calibration: σ floor active (brick ≥ 0.030, concrete ≥ 0.030), no upper bound
- Samples (CELL CAL): 10M per eval, 129 evals, 381 min, RMSE 11.60 dB
- Samples (CELL 8e): 100M
- Scalar offset: -6.7682 dB
- Scene: 15,486 LiDAR trees, DISABLE_VEG_DISCS=True, MAX_DEPTH=8

## Calibrated Material Parameters (CELL 4A)
| Material             | εr    | σ (S/m)     | S     | Notes                        |
|----------------------|-------|-------------|-------|------------------------------|
| itu_brick            | 4.62  | 0.0682      | 0.250 | Above σ floor ✓               |
| itu_concrete         | 6.52  | 3.9386      | 0.300 | Extreme — near-metal, wall=401dB |
| itu_wet_ground       | 32.74 | 0.0217      | 0.300 |                              |
| itu_very_dry_ground  | 3.59  | 0.0010      | 0.300 |                              |
| water_rt             | 61.74 | 0.0297      | 0.050 |                              |
| itu_glass            | 6.27  | 0.0087      | 0.080 | Fixed                        |
| itu_metal            | 1.00  | 10000000    | 0.050 | Fixed                        |
| concrete_barrier     | 5.31  | 0.0525      | 0.300 | Fixed                        |
| metal_barrier        | 1.00  | 10000000    | 0.050 | Fixed                        |
| canopy_itu_veg       | 1.50  | 0.0027      | 0.400 | Fixed                        |
| trunk_itu_wood       | 1.99  | 0.0088      | 0.150 | Fixed                        |
| itu_ceiling_board    | 1.00  | 0.0000      | 0.050 | Fixed                        |

## CELL 8e Full Results (100M samples)

| Range  | N   | Method    | Bias (dB) | RMSE (dB) | STD (dB) | R²     |
|--------|-----|-----------|-----------|-----------|----------|--------|
| 0-100m | 17  | ON incoh  | -10.7     | 11.8      | 4.9      | -1.958 |
| 0-100m | 17  | ON coh    | -16.6     | 17.5      | 5.4      | -5.468 |
| 0-200m | 125 | ON incoh  | +0.3      | 5.3       | 5.3      | -1.575 |
| 0-200m | 125 | ON coh    | -6.2      | 7.8       | 4.7      | -4.497 |
| 0-300m | 198 | ON incoh  | +1.7      | 5.4       | 5.1      | -0.697 |
| 0-300m | 198 | ON coh    | -5.0      | 7.0       | 5.0      | -1.923 |
| 0-500m | 385 | ON incoh  | +1.7      | 8.2       | 8.0      | 0.288  |
| 0-500m | 385 | ON coh    | -4.6      | 8.0       | 6.5      | 0.320  |
| 0-750m | 537 | ON incoh  | +2.3      | 9.3       | 9.0      | 0.350  |
| 0-750m | 537 | ON coh    | -3.9      | 9.0       | 8.1      | 0.388  |
| 0-900m | 635 | ON incoh  | +1.3      | 9.4       | 9.3      | 0.358  |
| 0-900m | 635 | ON coh    | -4.2      | 9.3       | 8.4      | 0.365  |
| 0-1000m| 701 | ON incoh  | +0.4      | 9.7       | 9.7      | 0.427  |
| 0-1000m| 701 | ON coh    | -4.9      | 10.0      | 8.7      | 0.391  |
| 0-1250m| 767 | ON incoh  | -0.6      | 10.4      | 10.4     | **0.530** |
| 0-1250m| 767 | ON coh    | -5.9      | 11.0      | 9.3      | 0.479  |
| 0-1500m| 808 | ON incoh  | -1.4      | 11.1      | 11.0     | **0.533** |
| 0-1500m| 808 | ON coh    | -6.5      | 11.6      | 9.6      | 0.489  |

## Comparison vs Previous Calibrations

| Range   | Old cal (486 trees) | Cal 2 (no floor) | Cal 3 (σ floor) | Best Cal 3 method |
|---------|--------------------|--------------------|-----------------|-------------------|
| 0-500m  | 0.465 ON coh       | ~0.319 ON coh      | 0.320 ON coh    | ON coh            |
| 0-750m  | **0.515** ON coh   | 0.404 ON coh       | 0.388 ON coh    | ON coh            |
| 0-1000m | 0.476 ON coh       | ~0.44 ON coh       | 0.427 ON incoh  | ON incoh          |
| 0-1250m | 0.508 ON coh       | 0.517 ON coh       | **0.530** ON incoh | ON incoh       |
| 0-1500m | 0.469 ON coh       | 0.523 ON coh       | **0.533** ON incoh | ON incoh       |

## Key Findings
- Cal 3 sets NEW BEST at 0-1250m (0.530) and 0-1500m (0.533) — 15,486 trees helping at longer range
- Cal 3 is worse at 0-750m (0.388 vs 0.515 old) due to concrete σ=3.94 over-reflecting
- Method crossover at ~1000m: ON incoh takes over from ON coh (extreme concrete σ bias)
- Fix: add σ upper bound for concrete (0.20 S/m) for Cal 4 → expect 0-750m recovery to 0.47+

## Next: Calibration 4
Add _SIG_MAX_PER_MAT = {'itu_brick': 0.20, 'itu_concrete': 0.20}
Constrains Powell to physical range [0.030, 0.20] S/m for both materials.
