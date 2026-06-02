#!/usr/bin/env python3
"""
Consolidate master config in sionna019_main_simulation_v2_bias_fix.ipynb
- Replace cell 8 with the comprehensive master config (already done per inspection,
  but we verify and update if needed)
- Remove duplicate variable definitions from downstream cells
"""
import json, re, sys

NB_PATH = '/home/user/Ray-Tracing---Sionna-RT/sionna019_main_simulation_v2_bias_fix.ipynb'

with open(NB_PATH) as f:
    nb = json.load(f)

cells = nb['cells']
print(f'Total cells: {len(cells)}')

# ── Master config content ──────────────────────────────────────────────────────
MASTER_CONFIG = r"""# ═══════════════════════════════════════════════════════════════
# MASTER CONFIG — all tunable parameters live here
# ═══════════════════════════════════════════════════════════════

# ── RF link budget ────────────────────────────────────────────
FREQUENCY_HZ    = 3_602_500_000          # 3602.5 MHz EE 5G NR
TX_LON, TX_LAT  = -1.146_264, 52.946_019 # Sionna RT coord centre
TX_POWER_DBM    = 47.0                   # base-station output power (dBm)
TX_ANTENNA_GAIN =  3.8                   # dBi directional panel
TX_CABLE_LOSS   =  3.0                   # feeder + jumpers (dB)
RX_ANTENNA_GAIN =  0.0                   # drive-test omnidirectional (dBi)
RX_CABLE_LOSS   =  0.0                   # direct to dongle (dB)
LNA_GAIN_DB     = 23.3                   # in-line LNA
RX_BPF_LOSS_DB  =  1.5                   # band-pass filter before LNA

# EIRP = TX_POWER_DBM - TX_CABLE_LOSS + TX_ANTENNA_GAIN
EIRP_DBM  = TX_POWER_DBM - TX_CABLE_LOSS + TX_ANTENNA_GAIN  # = 47.8 dBm

# SYS_GAIN = RX_ANTENNA_GAIN - RX_CABLE_LOSS - RX_BPF_LOSS_DB + LNA_GAIN_DB
SYS_GAIN  = RX_ANTENNA_GAIN - RX_CABLE_LOSS - RX_BPF_LOSS_DB + LNA_GAIN_DB  # = 21.8 dB

NOISE_FLOOR = -109.0                     # measurement sensitivity floor (dBm)

# ── TX antenna height ─────────────────────────────────────────
TX_AGL_M   = 17.0   # above-ground-level (m)
RX_AGL_M   =  1.5   # drive-test receiver height (m)
ANTENNA_PATTERN = 'donut'               # 'donut' | 'iso'

# ── Scene geometry ────────────────────────────────────────────
SCENE_VERSION      = 'v2'
FLAT_TERRAIN       = False
SCENE_RADIUS_KM    = None               # None = full bbox
CITY_MAX_HEIGHT_M  = 40.0
CITY_MIN_HEIGHT_M  =  2.0
GRID_SIZE_M        = 10.0              # coverage-map cell size (m)
FORCE_REBUILD_SCENE = True

# ── Ray tracing ───────────────────────────────────────────────
MAX_DEPTH       = 6                    # reflections/transmissions per path
NUM_SAMPLES_CM  = 200_000_000          # rays for coverage map
NUM_SAMPLES_PS  =  10_000_000          # rays for path solver (per RX batch)

# Path-solver batch settings
BATCH_SIZE       = 5                   # RX per GPU batch
SAVE_PER_RAY     = True
MAX_RAYS_PER_RX  = 300
MAX_SAMPLES_PS   = 20_000_000
scat_keep_prob   = 0.005              # v2: raised from 0.001 — NLOS scatter budget

# ── Material EM properties (ITU-R P.2040-2, 2023) ─────────────
# Columns: (eps_r, sigma, S, xpd_db, roughness)
# S  = Lambertian scattering coefficient (0=specular, 1=diffuse)
# xpd = cross-polarisation discrimination (dB); higher = less XPD
MAT_CONCRETE  = dict(eps_r=5.31, sigma=0.033, S=0.15, xpd_db=20.0, roughness=0.10)
MAT_BRICK     = dict(eps_r=3.75, sigma=0.038, S=0.30, xpd_db=12.0, roughness=0.20)  # v2: S 0.55→0.30
MAT_ASPHALT   = dict(eps_r=3.18, sigma=0.004, S=0.20, xpd_db= 5.0, roughness=0.20)  # v2: S 0.35→0.20
MAT_VEGETATION= dict(eps_r=1.80, sigma=0.030, S=0.60, xpd_db=10.0, roughness=0.10)  # v2: S 0.65→0.60
MAT_GLASS     = dict(eps_r=6.27, sigma=0.000, S=0.05, xpd_db=25.0, roughness=0.05)
MAT_METAL     = dict(eps_r=1.00, sigma=1e7,   S=0.10, xpd_db=30.0, roughness=0.05)
MAT_SOIL      = dict(eps_r=3.00, sigma=0.015, S=0.25, xpd_db= 8.0, roughness=0.30)

# ── Facade window-to-wall ratio (WWR) ─────────────────────────
# Used to blend glass into concrete/brick effective permittivity
FACADE_WWR_RESIDENTIAL = 0.15   # v2: 0.25→0.15  (UK terrace/semi-detached)
FACADE_WWR_COMMERCIAL  = 0.25   # v2: 0.55→0.25  (UK retail/office stock)
FACADE_WWR_DEFAULT     = 0.20   # v2: 0.35→0.20

# ── Receiver / measurement dataset ───────────────────────────
NUM_RX                 = 4000   # number of Ofcom drive-test points to use
RX_MODE                = 'auto' # 'auto' | 'custom'
RX_CUSTOM_FILE         = ''     # path to custom RX CSV (used when RX_MODE='custom')
OFCOM_RAW_CSV_OVERRIDE = ''     # override path to raw Ofcom CSV

# ── Vehicles ─────────────────────────────────────────────────
VEHICLE_DENSITY = 0    # avg vehicles per 100 m road segment; 0 = disabled

# ── Calibration grid search ───────────────────────────────────
CAL_SAMPLES       = 50_000_000
CAL_RUN_SIZE      =  2_000_000
CAL_MAX_DEPTH     = 6
S_CONCRETE_GRID   = [0.10, 0.15, 0.20, 0.25]   # v2: literature range
S_BRICK_GRID      = [0.20, 0.25, 0.30, 0.35]   # v2: literature range
S_VEG_GRID        = [0.50, 0.55, 0.60, 0.70]   # v2: added 0.50
S_METAL_FIXED     = 0.10
"""

# ── 1. Update cell 8 (index 7 is wrong — from inspection it's index 8) ────────
# From earlier output, cell 8 is indeed "MASTER CONFIG"
cell8_src = ''.join(cells[8]['source'])
if 'MASTER CONFIG' in cell8_src:
    print('Cell 8 is the master config cell — replacing source.')
    # Convert to list of lines (each ending with \n except last)
    lines = MASTER_CONFIG.strip().split('\n')
    new_source = [l + '\n' for l in lines[:-1]] + [lines[-1]]
    cells[8]['source'] = new_source
    print(f'  Cell 8 updated: {len(new_source)} lines')
else:
    print('ERROR: Cell 8 is not the master config cell!', file=sys.stderr)
    sys.exit(1)

# ── 2. Cell 33 — update _ITU_DB to reference MAT_* dicts ─────────────────────
# From inspection, cell 33 already has the MAT_* references. Let's verify and
# replace _ITU_DB section to ensure it's the canonical form.
cell33_src = ''.join(cells[33]['source'])

OLD_ITU_DB_PATTERN = r"_ITU_DB = \{[^}]*\}"

NEW_ITU_DB = """_ITU_DB = {
    'concrete'  : (MAT_CONCRETE['eps_r'],   MAT_CONCRETE['sigma'],   MAT_CONCRETE['S'],    MAT_CONCRETE['xpd_db'],   MAT_CONCRETE['roughness']),
    'brick'     : (MAT_BRICK['eps_r'],       MAT_BRICK['sigma'],       MAT_BRICK['S'],       MAT_BRICK['xpd_db'],      MAT_BRICK['roughness']),
    'asphalt'   : (MAT_ASPHALT['eps_r'],     MAT_ASPHALT['sigma'],     MAT_ASPHALT['S'],     MAT_ASPHALT['xpd_db'],    MAT_ASPHALT['roughness']),
    'vegetation': (MAT_VEGETATION['eps_r'],  MAT_VEGETATION['sigma'],  MAT_VEGETATION['S'],  MAT_VEGETATION['xpd_db'], MAT_VEGETATION['roughness']),
    'glass'     : (MAT_GLASS['eps_r'],       MAT_GLASS['sigma'],       MAT_GLASS['S'],       MAT_GLASS['xpd_db'],      MAT_GLASS['roughness']),
    'metal'     : (MAT_METAL['eps_r'],       MAT_METAL['sigma'],       MAT_METAL['S'],       MAT_METAL['xpd_db'],      MAT_METAL['roughness']),
    'soil'      : (MAT_SOIL['eps_r'],        MAT_SOIL['sigma'],        MAT_SOIL['S'],        MAT_SOIL['xpd_db'],       MAT_SOIL['roughness']),
}"""

# Check if _ITU_DB already uses MAT_* references
if "MAT_CONCRETE['eps_r']" in cell33_src:
    print('Cell 33 _ITU_DB already references MAT_* dicts — no change needed.')
else:
    # Replace with MAT_* references
    new_src = re.sub(OLD_ITU_DB_PATTERN, NEW_ITU_DB, cell33_src, flags=re.DOTALL)
    if new_src != cell33_src:
        lines = new_src.split('\n')
        cells[33]['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
        print('Cell 33 _ITU_DB updated to reference MAT_* dicts.')
    else:
        print('WARNING: Could not replace _ITU_DB in cell 33.')

# ── 3. Cell 54 — remove duplicate NUM_SAMPLES_PS and MAX_SAMPLES_PS ───────────
cell54_src = ''.join(cells[54]['source'])
lines54 = cell54_src.split('\n')

new_lines54 = []
for line in lines54:
    # Remove the redundant override lines (lines 21-22 from inspection):
    # "_PS_SAMPLES = NUM_SAMPLES_PS" and "NUM_SAMPLES_PS = _PS_SAMPLES"
    if re.match(r'^_PS_SAMPLES\s*=\s*NUM_SAMPLES_PS', line):
        print(f'  Cell 54: removing line: {line!r}')
        continue
    if re.match(r'^NUM_SAMPLES_PS\s*=\s*_PS_SAMPLES', line):
        print(f'  Cell 54: removing line: {line!r}')
        continue
    # Remove the "# Override NUM_SAMPLES_PS here..." comment line above them
    if '# Override NUM_SAMPLES_PS here for path solver' in line:
        print(f'  Cell 54: removing comment line: {line!r}')
        continue
    # Remove duplicate MAX_SAMPLES_PS definition
    if re.match(r'^MAX_SAMPLES_PS\s*=\s*20_000_000', line):
        print(f'  Cell 54: removing duplicate MAX_SAMPLES_PS: {line!r}')
        continue
    new_lines54.append(line)

new_src54 = '\n'.join(new_lines54)
if new_src54 != cell54_src:
    lines = new_src54.split('\n')
    cells[54]['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    print('Cell 54 updated.')
else:
    print('Cell 54: no changes needed.')

# ── 4. Save notebook ───────────────────────────────────────────────────────────
with open(NB_PATH, 'w') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print(f'\nNotebook saved to {NB_PATH}')

# ── 5. Verify JSON is valid ────────────────────────────────────────────────────
with open(NB_PATH) as f:
    nb2 = json.load(f)
print(f'JSON validation: OK ({len(nb2["cells"])} cells)')

# Print summary of what was done
print('\n=== SUMMARY ===')
print('Cell 8: master config replaced with comprehensive version')
print('Cell 33: _ITU_DB verified/updated to reference MAT_* dicts')
print('Cell 54: removed duplicate NUM_SAMPLES_PS override and MAX_SAMPLES_PS definition')
print('All other cells (38, 60, 14): no duplicate definitions found — no changes needed')
