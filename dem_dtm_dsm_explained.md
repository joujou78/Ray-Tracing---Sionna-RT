# DEM vs DTM vs DSM — Explained

## Definitions

| Term | Full name | Measures | Includes |
|------|-----------|----------|----------|
| **DEM** | Digital Elevation Model | Generic term | Any of the below |
| **DTM** | Digital Terrain Model | **Bare earth only** | Ground surface only |
| **DSM** | Digital Surface Model | **Everything on earth** | Ground + buildings + trees + cars |

---

## Visual explanation

```
DSM  ████▄▄▄███████▄▄▄▄▄████   ← top of everything (buildings, trees)
          ↑       ↑
       building  tree
DTM  ████████████████████████   ← bare ground underneath
```

---

## Real numbers at TX site (Nottingham)

| Model | Elevation at TX | What it represents |
|-------|----------------|-------------------|
| DSM | ~131 m ASL | Ground + building rooftop |
| DTM | ~65 m ASL | Bare earth only |
| Difference | **~66 m** | Building height at TX location |

This 66m difference caused the **TX underground bug** — using DTM coordinates
on a DSM scene placed the TX 49m below the surface.

---

## How each is created

| | DTM | DSM |
|--|-----|-----|
| **Source** | LiDAR + ground filtering | LiDAR raw / Radar |
| **Processing** | Ground points only extracted | All returns kept |
| **Accuracy** | ±0.05–0.15m (EA LiDAR) | ±0.3–1m (SRTM/AWS) |
| **UK free source** | EA LiDAR DTM | AWS elevation tiles |

---

## Which to use for ray tracing

| Use case | Correct model | Why |
|----------|--------------|-----|
| **Terrain mesh** | **DTM** | Ground surface — buildings modelled separately |
| **Building base Z** | **DTM** | Building sits on bare ground |
| **TX/RX height** | **DTM + AGL** | Antenna above ground, not above rooftop |
| **LOS check** | **DSM** | Need to know what is physically blocking the ray |

---

## Pipeline used in this project

```
Scene builder:
  EA DTM  → terrain.ply        (bare earth grid, 1m resolution)
  OSM     → bld_*.ply          (buildings placed at DTM elevation)

Main simulation:
  DTM + AGL → TX/RX height     (antenna above bare ground)
  ray_cast  → verify no clash  (checks against loaded scene mesh)
```

**DEM** is the umbrella term — when someone says "DEM" they usually mean DTM
unless specified otherwise.

---

## Sources

| Dataset | Type | Resolution | Coverage | Cost |
|---------|------|-----------|----------|------|
| EA LiDAR Composite DTM | DTM | 1m | England | Free |
| AWS elevation-tiles-prod | DSM | 2.4m (z=14) | Global | Free |
| OS Terrain 50 | DTM | 50m | UK | Free |
| OS MasterMap | DTM+buildings | 0.25m | UK | Academic licence |
