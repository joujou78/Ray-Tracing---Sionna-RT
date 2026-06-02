#!/usr/bin/env python3
"""
migrate_to_sionna20.py
======================
Copies the built scene (PLY meshes + scene.xml) from the Sionna 0.19.2 run
into results_sionna20/ and writes a standalone simulation script adapted for
Sionna 2.0 API.

Usage:
    python3 migrate_to_sionna20.py

Output:
    /home/georgeskai/Documents/FYP2026/nottingham_11km/results_sionna20/
        scene/                  ← copied PLY meshes + scene.xml
        nottingham_sionna20.py  ← standalone simulation script
        receiver_locations.csv  ← copied RX file
        transmitter_positions.csv
        measurement_data.csv    ← copied Ofcom drive-test CSV
"""

import os
import shutil

# ── Paths ────────────────────────────────────────────────────────────────────
SRC_BASE  = os.path.expanduser('~/Documents/FYP2026/nottingham_11km')
DST_BASE  = os.path.join(SRC_BASE, 'results_sionna20')

SRC_SCENE = os.path.join(SRC_BASE, 'scene')
DST_SCENE = os.path.join(DST_BASE, 'scene')

FILES_TO_COPY = [
    ('receiver_locations.csv',     'receiver_locations.csv'),
    ('transmitter_positions.csv',  'transmitter_positions.csv'),
    ('nottingham3602.csv',         'measurement_data.csv'),
]

# ── Step 1: copy scene directory ─────────────────────────────────────────────
print(f'Creating output directory: {DST_BASE}')
os.makedirs(DST_BASE, exist_ok=True)

if os.path.exists(DST_SCENE):
    shutil.rmtree(DST_SCENE)
shutil.copytree(SRC_SCENE, DST_SCENE)
ply_count = len([f for f in os.listdir(os.path.join(DST_SCENE, 'meshes')) if f.endswith('.ply')])
print(f'  Copied scene: {ply_count} PLY files + scene.xml')

# ── Step 2: copy supporting CSV files ────────────────────────────────────────
for src_name, dst_name in FILES_TO_COPY:
    src_path = os.path.join(SRC_BASE, src_name)
    dst_path = os.path.join(DST_BASE, dst_name)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dst_path)
        print(f'  Copied {src_name} → {dst_name}')
    else:
        # try results_sionna019 subfolder
        src_alt = os.path.join(SRC_BASE, 'results_sionna019', src_name)
        if os.path.exists(src_alt):
            shutil.copy2(src_alt, dst_path)
            print(f'  Copied {src_name} (from results/) → {dst_name}')
        else:
            print(f'  WARNING: {src_name} not found — skip')

# ── Step 3: write standalone Sionna 2.0 simulation script ────────────────────
script_path = os.path.join(DST_BASE, 'nottingham_sionna20.py')

SCRIPT = r'''#!/usr/bin/env python3
"""
Nottingham 3.6 GHz Sionna 2.0 Simulation
=========================================
Adapted from sionna019_main_simulation.ipynb (Sionna 0.19.2).
Scene geometry (PLY + XML) is identical — only the Python API changes.

Key Sionna 2.0 API differences vs 0.19:
  - scene.tx_array / scene.rx_array replace per-object antenna assignment
  - compute_paths() returns a Paths object with updated attribute names
  - coverage_map() → scene.coverage_map() with updated signature
  - RadioMaterial constructor uses keyword args directly
  - No more is_placeholder flag issues
"""

import os, time
import numpy as np
import pandas as pd
import tensorflow as tf
import sionna
import sionna.rt as rt
from pyproj import Transformer

# ── Configuration ─────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
SCENE_XML    = os.path.join(SCRIPT_DIR, 'scene', 'scene.xml')
RX_CSV       = os.path.join(SCRIPT_DIR, 'receiver_locations.csv')
MEAS_CSV     = os.path.join(SCRIPT_DIR, 'measurement_data.csv')
RESULTS_DIR  = os.path.join(SCRIPT_DIR, 'outputs')
os.makedirs(RESULTS_DIR, exist_ok=True)

# Radio parameters (Ofcom 3602.5 MHz drive-test, Nottingham)
FREQUENCY_HZ  = 3_602_500_000.0   # 3602.5 MHz
EIRP_DBM      = 54.0              # TX EIRP (47.8 dBm - 2.8 dB cable + 2.8 dBi ant + 6.2 EIRP offset)
SYS_GAIN      = 16.0              # RX chain: -2.0 - 3.8 + 23.3 - 1.5 dB
TX_AGL_M      = 17.0              # TX height above ground (m)
RX_AGL_M      =  1.5              # RX height above ground (m)
TX_LON        = -1.2559
TX_LAT        =  52.9863
UTM_EPSG      = 32630             # UTM zone 30N

# Scene origin (set to DEM elevation at scene centre)
ORIGIN_ELEV_M = 64.27             # m ASL — subtract to get scene-local Z

# Simulation parameters
MAX_DEPTH     = 6
NUM_SAMPLES   = 10_000_000
BATCH_SIZE    = 5                  # receivers per compute_paths call

# ── Coordinate helpers ────────────────────────────────────────────────────────
_wgs_to_utm = Transformer.from_crs('EPSG:4326', f'EPSG:{UTM_EPSG}', always_xy=True)
_utm_to_wgs = Transformer.from_crs(f'EPSG:{UTM_EPSG}', 'EPSG:4326', always_xy=True)

_utm_cx, _utm_cy = _wgs_to_utm.transform(TX_LON, TX_LAT)

def gps_to_local(lon, lat):
    ux, uy = _wgs_to_utm.transform(lon, lat)
    return ux - _utm_cx, uy - _utm_cy

def local_to_gps(lx, ly):
    return _utm_to_wgs.transform(lx + _utm_cx, ly + _utm_cy)

# ── Load scene ────────────────────────────────────────────────────────────────
print(f'Sionna version : {sionna.__version__}')
print(f'Loading scene  : {SCENE_XML}')
scene = rt.load_scene(SCENE_XML)
scene.frequency = FREQUENCY_HZ
print(f'  Materials    : {list(scene.radio_materials.keys())}')

# ── Apply ITU-R P.2040-2 materials ───────────────────────────────────────────
# S values calibrated for Nottingham 3.6 GHz via grid search CELL CAL:
#   S_brick=0.55, S_veg=0.65, S_concrete=0.15
_MAT_PARAMS = {
    # name                eps_r    sigma     S      xpd   thick
    'itu_concrete'     : (5.31,   0.0920,  0.15,  0.10,  0.20),
    'itu_brick'        : (3.75,   0.0380,  0.55,  0.10,  0.12),
    'itu_glass'        : (6.27,   0.0198,  0.04,  0.10,  0.01),
    'itu_wood'         : (1.99,   0.0186,  0.30,  0.30,  0.05),
    'itu_metal'        : (1.00,   1e7,     0.05,  0.10,  0.01),
    'itu_asphalt'      : (3.18,   0.0580,  0.35,  0.20,  0.05),
    'itu_vegetation'   : (1.70,   0.1079,  0.65,  0.10,  0.15),
    'itu_water'        : (81.0,   0.500,   0.02,  0.05,  0.01),
    'itu_medium_dry_ground': (15.0, 0.035, 0.25,  0.20,  0.50),
    'itu_very_dry_ground'  : (3.0,  0.0038,0.20,  0.20,  0.50),
    'itu_wet_ground'   : (30.0,   0.150,   0.30,  0.20,  0.50),
    'itu_marble'       : (7.07,   0.0195,  0.08,  0.10,  0.05),
    'itu_plasterboard' : (2.73,   0.0283,  0.40,  0.20,  0.02),
    'itu_plywood'      : (2.90,   0.0456,  0.50,  0.25,  0.02),
}

for mat_name, (eps_r, sigma, S, xpd, thick) in _MAT_PARAMS.items():
    try:
        # Sionna 2.0: RadioMaterial accepts kwargs in constructor
        mat = rt.RadioMaterial(
            mat_name,
            relative_permittivity=float(eps_r),
            conductivity=float(sigma),
            scattering_coefficient=float(S),
            xpd_coefficient=float(xpd),
        )
        if mat_name not in scene.radio_materials:
            scene.add(mat)
        else:
            # Update existing
            m = scene.radio_materials[mat_name]
            m.relative_permittivity = float(eps_r)
            m.conductivity          = float(sigma)
            m.scattering_coefficient = float(S)
            m.xpd_coefficient        = float(xpd)
    except Exception as e:
        print(f'  WARNING: {mat_name}: {e}')

print('  Materials configured.')

# ── Antenna arrays ─────────────────────────────────────────────────────────
# Sionna 2.0: use PlanarArray for TX/RX antenna configuration
# TX: vertical omni +2.8 dBi (collinear), RX: isotropic (vehicle-mount)
tx_array = rt.PlanarArray(
    num_rows=1, num_cols=1,
    vertical_spacing=0.5, horizontal_spacing=0.5,
    pattern='dipole',        # closest built-in to collinear omni
    polarization='V',
)
rx_array = rt.PlanarArray(
    num_rows=1, num_cols=1,
    vertical_spacing=0.5, horizontal_spacing=0.5,
    pattern='iso',           # isotropic RX (drive-test vehicle mount)
    polarization='V',
)
scene.tx_array = tx_array
scene.rx_array = rx_array
print('  Antenna arrays configured.')

# ── Place transmitter ─────────────────────────────────────────────────────────
tx_lx, tx_ly = gps_to_local(TX_LON, TX_LAT)
# TX Z: terrain at TX location + AGL
# Using scene-local Z = ASL - ORIGIN_ELEV_M
# Nottingham TX site ASL ≈ 65.4m → scene-local terrain = 65.4 - 64.27 = 1.13m
# Approx: use known value from Sionna 0.19 run
TX_TERRAIN_Z  = 65.4 - ORIGIN_ELEV_M   # scene-local terrain at TX (≈1.13m)
tx_z = TX_TERRAIN_Z + TX_AGL_M          # scene-local TX position

tx = rt.Transmitter(
    name='tx_ofcom',
    position=[float(tx_lx), float(tx_ly), float(tx_z)],
)
scene.add(tx)
print(f'  TX placed at ({tx_lx:.1f}, {tx_ly:.1f}, {tx_z:.2f}) m scene-local')

# ── Load receivers from CSV ───────────────────────────────────────────────────
df_rx = pd.read_csv(RX_CSV)
print(f'  Loaded {len(df_rx)} receivers from {RX_CSV}')

receivers = []
for _, row in df_rx.iterrows():
    lx = float(row['x_m'])
    ly = float(row['y_m'])
    lz = float(row.get('z_m', RX_AGL_M))
    rx = rt.Receiver(name=str(row['name']), position=[lx, ly, lz])
    scene.add(rx)
    receivers.append(rx)

print(f'  Added {len(receivers)} receivers to scene.')

# ── Path solver ───────────────────────────────────────────────────────────────
PS_CONFIG = dict(
    max_depth        = MAX_DEPTH,
    los              = True,
    reflection       = True,
    diffraction      = True,
    scattering       = True,
    edge_diffraction = True,
    scat_keep_prob   = 0.010,
    num_samples      = NUM_SAMPLES,
)
print(f'\nPath solver config:')
for k, v in PS_CONFIG.items():
    print(f'  {k:<18}: {v}')

results = []
n_rx = len(receivers)
t0 = time.time()

print(f'\nProcessing {n_rx} receivers in batches of {BATCH_SIZE} ...')

rx_names = [r.name for r in receivers]
rx_pos   = np.array([[float(r.position[0]), float(r.position[1]), float(r.position[2])]
                      for r in receivers])

for i in range(0, n_rx, BATCH_SIZE):
    batch_names = rx_names[i:i+BATCH_SIZE]

    # Remove all receivers, add batch
    for nm in list(scene.receivers.keys()):
        scene.remove(nm)
    for j, nm in enumerate(batch_names):
        pos = rx_pos[i+j]
        scene.add(rt.Receiver(name=nm, position=pos.tolist()))

    try:
        paths = scene.compute_paths(**PS_CONFIG)

        # path_gain: sum of |a|^2 over all paths (Sionna 2.0 uses paths.a for CIR)
        # paths.a shape: [batch_size, num_rx, num_rx_ant, num_tx, num_tx_ant, num_paths, num_time]
        a = paths.a.numpy()           # complex CIR coefficients
        tau = paths.tau.numpy()       # delays

        for j, nm in enumerate(batch_names):
            rx_idx = j
            try:
                a_rx = a[0, rx_idx, 0, 0, 0, :, 0]  # [num_paths]
                pg_linear = float(np.sum(np.abs(a_rx)**2))
                if pg_linear > 0:
                    rssi = EIRP_DBM + 10*np.log10(pg_linear) + SYS_GAIN
                    n_paths = int(np.sum(np.abs(a_rx) > 0))
                else:
                    rssi = float('nan')
                    n_paths = 0
            except Exception:
                rssi = float('nan')
                n_paths = 0

            row_idx = i + j
            if row_idx < len(df_rx):
                row = df_rx.iloc[row_idx]
                dist = float(np.sqrt((rx_pos[row_idx,0] - tx_lx)**2 +
                                     (rx_pos[row_idx,1] - tx_ly)**2))
                results.append({
                    'name'    : nm,
                    'dist_m'  : dist,
                    'rssi_sim': rssi,
                    'n_paths' : n_paths,
                    'lon'     : float(row.get('lon', 0)),
                    'lat'     : float(row.get('lat', 0)),
                })

    except Exception as e:
        for j, nm in enumerate(batch_names):
            results.append({'name': nm, 'dist_m': 0, 'rssi_sim': float('nan'),
                            'n_paths': 0, 'lon': 0, 'lat': 0})
        print(f'  Batch {i//BATCH_SIZE} error: {e}')

    if (i // BATCH_SIZE) % 20 == 0:
        elapsed = time.time() - t0
        eta = elapsed / max(i+BATCH_SIZE, 1) * n_rx
        print(f'  [{i+BATCH_SIZE:4d}/{n_rx}]  {elapsed:.0f}s elapsed  ETA {eta-elapsed:.0f}s')

print(f'\nDone in {time.time()-t0:.1f}s')

# ── Save results ──────────────────────────────────────────────────────────────
df_sim = pd.DataFrame(results)
out_csv = os.path.join(RESULTS_DIR, 'simulated_rssi.csv')
df_sim.to_csv(out_csv, index=False)
print(f'Saved: {out_csv}')

# ── Compare against measurements ─────────────────────────────────────────────
if os.path.exists(MEAS_CSV):
    df_meas = pd.read_csv(MEAS_CSV)
    df_merged = df_sim.merge(
        df_meas[['name', 'local_measurement_dBm']].rename(
            columns={'local_measurement_dBm': 'rssi_meas'}),
        on='name', how='inner'
    )
    valid = df_merged.dropna(subset=['rssi_sim', 'rssi_meas'])
    if len(valid) > 0:
        err = valid['rssi_sim'] - valid['rssi_meas']
        bias = float(err.mean())
        rmse = float(np.sqrt((err**2).mean()))
        print(f'\n{"="*50}')
        print(f'  RESULTS — Sionna 2.0  vs  Ofcom measurements')
        print(f'{"="*50}')
        print(f'  Valid pairs : {len(valid)} / {len(df_merged)}')
        print(f'  Bias        : {bias:+.1f} dB')
        print(f'  RMSE        : {rmse:.1f} dB')
        print(f'{"="*50}')

        # Band breakdown
        bands = [('<300m', 0, 300), ('300-700m', 300, 700),
                 ('700-1.2km', 700, 1200), ('1.2-2km', 1200, 2000), ('>2km', 2000, 1e9)]
        print(f'\n  {"Band":<12} {"N":>5}  {"Bias":>8}  {"RMSE":>8}  {"Paths":>7}')
        print(f'  {"-"*50}')
        for bname, blo, bhi in bands:
            bdf = valid[(valid['dist_m'] >= blo) & (valid['dist_m'] < bhi)]
            if len(bdf) == 0:
                continue
            berr  = bdf['rssi_sim'] - bdf['rssi_meas']
            brmse = float(np.sqrt((berr**2).mean()))
            bbias = float(berr.mean())
            bpath = float(bdf['n_paths'].mean())
            print(f'  {bname:<12} {len(bdf):>5}  {bbias:>+8.1f}  {brmse:>8.1f}  {bpath:>7.1f}')

        comp_csv = os.path.join(RESULTS_DIR, 'comparison.csv')
        df_merged.to_csv(comp_csv, index=False)
        print(f'\n  Saved comparison: {comp_csv}')
    else:
        print('  No valid pairs for comparison.')
'''

with open(script_path, 'w') as f:
    f.write(SCRIPT)

print(f'\nSimulation script written: {script_path}')

# ── Step 4: copy Untitled.ipynb (Sionna 2.0 notebook) ────────────────────────
src_nb  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Untitled.ipynb')
dst_nb  = os.path.join(DST_BASE, 'nottingham_sionna20.ipynb')
if os.path.exists(src_nb):
    shutil.copy2(src_nb, dst_nb)
    print(f'  Copied notebook → {dst_nb}')
else:
    print(f'  WARNING: Untitled.ipynb not found at {src_nb}')

print('\nDone. To run in Sionna 2.0:')
print(f'  jupyter notebook {dst_nb}')
print(f'  -- or --')
print(f'  cd {DST_BASE} && python3 nottingham_sionna20.py')
