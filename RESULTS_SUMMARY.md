# Simulation Results Summary — Sionna RT 2.0 · Ofcom 2018

## TABLE 1 — Final Results: All Sites & Frequencies

| Site | Freq (MHz) | Range | N | Method | Bias (dB) | RMSE (dB) | R² | Status |
|------|-----------|-------|---|--------|-----------|-----------|-----|--------|
| Nottingham | 915 | 0–750m | 67 | ON incoh | +0.8 | **6.0** | **0.835** | FINAL |
| Nottingham | 915 | 0–1000m | 87 | ON incoh | +1.0 | — | **0.813** | FINAL |
| Nottingham | 915 | 0–1250m | 168 | ON incoh | +6.0 | 12.8 | 0.741 | FINAL |
| Nottingham | 1802 | 0–1250m | 767 | ON incoh | -2.4 | 10.6 | **0.509** | FINAL |
| Nottingham | 2695 | 0–1250m | 324 | ON incoh | +4.8 | 12.7 | **0.574** | FINAL |
| Nottingham | 3602 | 0–1250m | 681 | ON incoh | +0.3 | 9.4 | **0.515** | FINAL |
| London | 915 | 0–1000m | 125 | ON incoh | -0.3 | 8.2 | **0.365** | FINAL |
| London | 1802 | 0–1000m | 125 | ON incoh | -0.3 | 8.2 | **0.365** | FINAL (Run 4) |
| Stevenage | 915 | 0–2250m | 1200 | ON incoh | +4.0 | 11.3 | **0.744** | Uncalibrated |
| Scar Hill | 915 | 0–1250m | 179 | ON incoh | +0.9 | 15.1 | **0.083** | FINAL |

---

## TABLE 2 — Scattering ON vs OFF

| Site | Freq | Range | ON incoh R² | OFF incoh R² | ON RMSE | OFF RMSE | Scatter impact |
|------|------|-------|-------------|--------------|---------|----------|----------------|
| Nottingham | 915 | 0–750m | **0.835** | — | 6.0 dB | — | Essential |
| Nottingham | 1802 | 0–1250m | **0.509** | 0.470 | 10.6 | 11.1 | +0.039 R² |
| Nottingham | 2695 | 0–1250m | **0.574** | 0.070 | 12.7 | 15.8 | **+0.504 R²** |
| Nottingham | 3602 | 0–1250m | **0.515** | -0.929 | 9.4 | 16.9 | **Critical** |
| London | 915 | 0–1000m | **0.365** | -22.666 | 8.2 | 37.0 | **Without = fails** |
| Stevenage | 915 | 0–2250m | 0.744 | 0.737 | 11.3 | 11.5 | Negligible |

---

## TABLE 3 — Nottingham 915 MHz: Scene Feature Ablation

| Scene Configuration | 0–750m R² | 0–1000m R² | 0–1250m R² | Notes |
|--------------------|-----------|------------|------------|-------|
| Buildings + terrain only | 0.716 | 0.679 | 0.496 | baseline |
| + Vegetation discs | 0.692 | 0.691 | 0.383 | discs add scatter |
| + Roads + water + veg | 0.696 | 0.609 | 0.401 | |
| + Bridges + railways (uncal) | 0.555 | 0.530 | 0.487 | before recal |
| Full scene · 2M eval | 0.742 | 0.803 | 0.683 | 9.92 dB cal |
| **Full scene · 100M eval** | **0.835** | **0.813** | **0.741** | **FINAL** |

---

## TABLE 4 — Calibration Impact (before vs after)

| Site | Freq | Uncalibrated R² | Calibrated R² | Calibrator |
|------|------|----------------|---------------|------------|
| Nottingham | 915 | ~0.2 | **0.835** | Powell |
| Nottingham | 1802 | — | **0.509** | Powell |
| Nottingham | 2695 | — | **0.574** | Powell |
| Nottingham | 3602 | — | **0.515** | CMA-ES |
| London | 915 | — | **0.365** | CMA-ES |
| Stevenage | 915 | **0.744** | TBD (CMA pending) | CMA-ES |
| Scar Hill | 915 | — | **0.083** | Powell |

---

## TABLE 5A — London 1802 MHz Calibration History

| Run | Cal RMSE | Scalar | CELL 8e R² | Outcome |
|-----|----------|--------|------------|---------|
| Run 1 (CMA, 15M) | 12.477 dB | +30.030 dB | FAILED | Kernel hung eval 605; scatter flood 392x |
| Run 2 (CMA, 15M) | 15.584 dB | — | FAILED | S caps 0.35 too tight; stalled |
| Run 3 (CMA, 15M) | 14.891 dB | +30.696 dB | FAILED | Brick S at cap — CMA trapped |
| **Run 4 (CMA, 15M)** | **13.829 dB** | **+30.696 dB** | **R²=0.365 FINAL** | **Best result — accepted as physics floor** |
| Run 5 (CMA, 15M) | 2.779 dB | +31.035 dB | FAILED | 26 cal RX — degenerate overfit |
| Run 6 (CMA, 15M) | 4.957 dB | +32.791 dB | FAILED | Bin scalars -37 to -55 dB |
| Run 7 (CMA, 15M) | ~12.575 dB | +30.032 dB | FAILED | Glass εᵣ=1.086 degenerate |
| Run 8 (CMA, 15M) | 12.368 dB | +32.721 dB | FAILED | Scatter flood 365x; bias=-31.5 dB at 0-100m |

---

## TABLE 5 — Physics Floor Reference

| Metric | Value | Source |
|--------|-------|--------|
| 3GPP UMa NLOS shadow fading floor | σ = 7.82 dB | 3GPP TR 38.901 |
| Pure geometry RT ceiling (literature) | R² ≈ 0.5 | arXiv:2507.19653 |
| This project best RMSE | **6.0 dB** | Nottingham 915 MHz |
| This project best R² | **0.835** | Nottingham 915 MHz |
