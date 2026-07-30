# 1802 MHz CELL 8e Results — Calibration 3 (σ floor active)

## Calibration Summary
- Run date: 2026-07-30
- Calibration: σ floor active (itu_brick ≥ 0.030 S/m, itu_concrete ≥ 0.030 S/m)
- Samples (CELL CAL): 10M per eval, 129 evals, 381 min
- Samples (CELL 8e): 100M
- Scene: 15,486 LiDAR trees, DISABLE_VEG_DISCS=True, MAX_DEPTH=8

## Calibrated Material Parameters (CELL 4A)
| Material           | εr    | σ (S/m)     | S     | Notes                     |
|--------------------|-------|-------------|-------|---------------------------|
| itu_brick          | 4.62  | 0.0682      | 0.250 | Above σ floor ✓            |
| itu_concrete       | 6.52  | 3.9386      | 0.300 | Extreme — near-metal       |
| itu_wet_ground     | 32.74 | 0.0217      | 0.300 |                            |
| itu_very_dry_ground| 3.59  | 0.0010      | 0.300 |                            |
| water_rt           | 61.74 | 0.0297      | 0.050 |                            |
| itu_glass          | 6.27  | 0.0087      | 0.080 | Fixed                      |
| itu_metal          | 1.00  | 10000000    | 0.050 | Fixed                      |
| concrete_barrier   | 5.31  | 0.0525      | 0.300 | Fixed                      |
| metal_barrier      | 1.00  | 10000000    | 0.050 | Fixed                      |
| canopy_itu_veg     | 1.50  | 0.0027      | 0.400 | Fixed                      |
| trunk_itu_wood     | 1.99  | 0.0088      | 0.150 | Fixed                      |
| itu_ceiling_board  | 1.00  | 0.0000      | 0.050 | Fixed                      |

Scalar offset: -6.7682 dB

## CELL 8e Evaluation Results (100M samples)

### 0–100m
| Method    | N  | Bias (dB) | RMSE (dB) | STD (dB) | R²     |
|-----------|----|-----------|-----------|----------|--------|
| ON incoh  | 17 | -10.7     | 11.8      | 4.9      | -1.958 |
| OFF incoh | 17 | -10.7     | 11.8      | 4.9      | -1.958 |
| ON coh    | 17 | -16.6     | 17.5      | 5.4      | -5.468 |
| OFF coh   | 17 | -10.8     | 11.9      | 4.9      | -1.998 |
| ON best   | 17 | -10.7     | 11.8      | 4.9      | -1.954 |
| OFF best  | 17 | -10.7     | 11.8      | 4.9      | -1.954 |

*Note: 0–100m negative R² is structural — 8 LOS mast-shadow receivers, not a calibration issue.*

### 0–200m
| Method    | N   | Bias (dB) | RMSE (dB) | STD (dB) | R²     |
|-----------|-----|-----------|-----------|----------|--------|
| ON incoh  | 125 | +0.3      | 5.3       | 5.3      | -1.575 |
| OFF incoh | 125 | +0.3      | 5.3       | 5.3      | -1.577 |
| ON coh    | 125 | -6.2      | 7.8       | 4.7      | -4.497 |
| OFF coh   | 125 | +0.4      | 5.4       | 5.4      | -1.673 |
| ON best   | 125 | +0.4      | 5.3       | 5.3      | -1.588 |
| OFF best  | 125 | +0.4      | 5.3       | 5.3      | -1.588 |

### 0–300m
| Method    | N   | Bias (dB) | RMSE (dB) | STD (dB) | R²     |
|-----------|-----|-----------|-----------|----------|--------|
| ON incoh  | 198 | +1.7      | 5.4       | 5.1      | -0.697 |
| OFF incoh | 198 | +1.7      | 5.4       | 5.1      | -0.700 |
| ON coh    | 198 | -5.0      | 7.0       | 5.0      | -1.923 |
| OFF coh   | 198 | +2.0      | 5.8       | 5.5      | -1.007 |
| ON best   | 198 | +1.7      | 5.4       | 5.1      | -0.713 |
| OFF best  | 198 | +1.7      | 5.4       | 5.1      | -0.713 |

### 0–500m
| Method    | N   | Bias (dB) | RMSE (dB) | STD (dB) | R²    |
|-----------|-----|-----------|-----------|----------|-------|
| ON incoh  | 385 | +1.7      | 8.2       | 8.0      | 0.288 |
| OFF incoh | 385 | +1.8      | 8.7       | 8.5      | 0.188 |
| ON coh    | 385 | -4.6      | 8.0       | 6.5      | 0.320 |
| OFF coh   | 385 | +3.6      | 9.7       | 9.0      | 0.003 |
| ON best   | 385 | +2.5      | 8.9       | 8.5      | 0.164 |
| OFF best  | 385 | +2.5      | 8.9       | 8.5      | 0.161 |

---
### 0–750m
| Method    | N   | Bias (dB) | RMSE (dB) | STD (dB) | R²    |
|-----------|-----|-----------|-----------|----------|---------|
| ON incoh  | 537 | +2.3      | 9.3       | 9.0      | 0.350 |
| OFF incoh | 537 | +2.4      | 9.7       | 9.4      | 0.291 |
| ON coh    | 537 | -3.9      | 9.0       | 8.1      | 0.388 |
| OFF coh   | 537 | +4.7      | 11.1      | 10.0     | 0.072 |
| ON best   | 537 | +3.2      | 9.7       | 9.2      | 0.281 |
| OFF best  | 537 | +3.2      | 9.8       | 9.3      | 0.265 |

---
### 0–900m
| Method    | N   | Bias (dB) | RMSE (dB) | STD (dB) | R²    |
|-----------|-----|-----------|-----------|----------|---------|
| ON incoh  | 635 | +1.3      | 9.4       | 9.3      | 0.358 |
| OFF incoh | 635 | +1.5      | 10.0      | 9.9      | 0.267 |
| ON coh    | 635 | -4.2      | 9.3       | 8.4      | 0.365 |
| OFF coh   | 635 | +3.6      | 11.2      | 10.6     | 0.084 |
| ON best   | 635 | +2.2      | 9.7       | 9.5      | 0.315 |
| OFF best  | 635 | +2.2      | 10.1      | 9.8      | 0.259 |

---
### 0–1000m
| Method    | N   | Bias (dB) | RMSE (dB) | STD (dB) | R²    |
|-----------|-----|-----------|-----------|----------|---------|
| ON incoh  | 701 | +0.4      | 9.7       | 9.7      | 0.427 |
| OFF incoh | 701 | +0.6      | 10.4      | 10.4     | 0.339 |
| ON coh    | 701 | -4.9      | 10.0      | 8.7      | 0.391 |
| OFF coh   | 701 | +2.8      | 11.4      | 11.1     | 0.206 |
| ON best   | 701 | +1.4      | 9.9       | 9.8      | 0.399 |
| OFF best  | 701 | +1.5      | 10.4      | 10.3     | 0.343 |

---
*Results to be updated as CELL 8e continues (0-1250m, 0-1500m, 0-2000m, 0-2500m)*
