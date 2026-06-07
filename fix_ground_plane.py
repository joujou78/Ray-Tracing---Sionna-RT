"""
fix_ground_plane.py
-------------------
Reads your Sionna scene XML, finds the terrain/ground PLY,
replaces it with a new flat z=0 mesh covering the full scene extent.

Usage:
    python fix_ground_plane.py --xml "/home/georgeskai/Documents/FYP2026/nottingham900/Nottingham  meshed and untitled.xml"

Optional:
    --size 14000      # ground plane half-width in metres (default 7000 → 14km×14km)
    --grid 200        # mesh resolution N×N vertices (default 200)
"""

import argparse, os, struct, re
import numpy as np

# ── CLI ───────────────────────────────────────────────────────────────────────
ap = argparse.ArgumentParser()
ap.add_argument('--xml',  required=True, help='Path to scene_sionna2.xml')
ap.add_argument('--size', type=float, default=7000.0,
                help='Half-extent in metres (full plane = 2×size). Default 7000 → 14km×14km')
ap.add_argument('--grid', type=int,   default=200,
                help='Grid vertices per side (NxN). Default 200')
args = ap.parse_args()

xml_path = args.xml
half     = args.size
N        = args.grid

assert os.path.exists(xml_path), f"XML not found: {xml_path}"
xml_dir = os.path.dirname(xml_path)

# ── Find terrain PLY referenced in XML ───────────────────────────────────────
with open(xml_path, 'r', errors='replace') as f:
    xml_text = f.read()

# Look for shape with id containing "ground" or "terrain"
pattern = r'<shape[^>]*id="([^"]*(?:ground|terrain|Ground|Terrain)[^"]*)"[^>]*>.*?<string name="filename"\s+value="([^"]+)"'
matches = re.findall(pattern, xml_text, re.DOTALL | re.IGNORECASE)

if not matches:
    # Fallback: find any .ply filename containing ground/terrain
    matches2 = re.findall(r'<string name="filename"\s+value="([^"]*(?:ground|terrain)[^"]*\.ply)"',
                          xml_text, re.IGNORECASE)
    if matches2:
        ply_rel = matches2[0]
        shape_id = 'terrain'
    else:
        print("Could not auto-detect terrain PLY. All PLY references in XML:")
        for m in re.findall(r'<string name="filename"\s+value="([^"]+\.ply)"', xml_text):
            print(f"  {m}")
        ply_rel = input("Enter the terrain PLY path from the list above: ").strip()
        shape_id = 'manual'
else:
    shape_id, ply_rel = matches[0]

# Resolve to absolute path
ply_path = ply_rel if os.path.isabs(ply_rel) else os.path.join(xml_dir, ply_rel)
ply_path = os.path.normpath(ply_path)

print(f"Scene XML     : {xml_path}")
print(f"Terrain PLY   : {ply_path}  (shape id='{shape_id}')")
print(f"New extent    : {2*half:.0f} m × {2*half:.0f} m  (±{half:.0f} m from origin)")
print(f"Grid          : {N}×{N} = {N*N:,} vertices, {2*(N-1)**2:,} triangles")

# ── Back up original PLY ──────────────────────────────────────────────────────
backup = ply_path + '.bak'
if not os.path.exists(backup):
    import shutil
    shutil.copy2(ply_path, backup)
    print(f"Backup        : {backup}")
else:
    print(f"Backup exists : {backup}  (not overwritten)")

# ── Generate new flat z=0 PLY ─────────────────────────────────────────────────
xs = np.linspace(-half, half, N, dtype=np.float32)
ys = np.linspace(-half, half, N, dtype=np.float32)
XX, YY = np.meshgrid(xs, ys)          # shape (N, N)
verts = np.stack([XX.ravel(), YY.ravel(), np.zeros(N*N, np.float32)], axis=1)

# Build triangle faces (two per quad)
faces = []
for row in range(N - 1):
    for col in range(N - 1):
        i0 = row * N + col
        i1 = i0 + 1
        i2 = i0 + N
        i3 = i2 + 1
        faces.append((i0, i2, i1))   # lower-left triangle
        faces.append((i1, i2, i3))   # upper-right triangle
faces = np.array(faces, dtype=np.int32)

n_verts = len(verts)
n_faces = len(faces)

header = (
    "ply\n"
    "format binary_little_endian 1.0\n"
    f"element vertex {n_verts}\n"
    "property float x\n"
    "property float y\n"
    "property float z\n"
    f"element face {n_faces}\n"
    "property list uchar int vertex_indices\n"
    "end_header\n"
)

os.makedirs(os.path.dirname(ply_path), exist_ok=True)
with open(ply_path, 'wb') as f:
    f.write(header.encode('ascii'))
    f.write(verts.astype(np.float32).tobytes())
    for tri in faces:
        f.write(struct.pack('<B', 3))
        f.write(struct.pack('<3i', *tri))

size_mb = os.path.getsize(ply_path) / 1e6
print(f"\nWrote new terrain.ply: {ply_path}")
print(f"  Vertices  : {n_verts:,}")
print(f"  Triangles : {n_faces:,}")
print(f"  File size : {size_mb:.1f} MB")
print("\nDone. Re-run your simulation notebook from CELL 3 (load scene).")
