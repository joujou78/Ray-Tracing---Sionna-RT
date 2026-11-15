"""Quick smoke test for LoD3 geometry pipeline (no Mapillary, no ONNX).

Run with:
    python3 -m lod3.test_lod3_geometry

Builds a 3-building synthetic scene around the London Ofcom Tx
and exports PLY files to /tmp/lod3_test/.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from shapely.geometry import box
import geopandas as gpd

from lod3 import config, facade_extractor, detector, geometry_builder, ply_exporter, qa

# -- config
config.LOD3_ENABLE = True
config.LOD3_ALLOW_PROCEDURAL = True
config.LOD3_ZONE_RADIUS_M = 200

# London Ofcom Tx (BNG)
TX_E, TX_N = 529533.7, 182937.9

# Synthetic footprints around Tx
footprints = gpd.GeoDataFrame({
    "building_id": ["bld_A", "bld_B", "bld_C"],
    "height_m":    [15.0,    25.0,    10.0],
    "geometry": [
        box(TX_E + 20, TX_N + 10, TX_E + 50, TX_N + 40),   # east
        box(TX_E - 60, TX_N + 10, TX_E - 20, TX_N + 50),   # west
        box(TX_E + 10, TX_N - 50, TX_E + 40, TX_N - 20),   # south
    ],
}, crs="EPSG:27700")

print(f"Tx BNG: E={TX_E}, N={TX_N}")
print(f"Buildings in GDF: {len(footprints)}")

# Step 1
facades = facade_extractor.extract_facades(
    footprints, TX_E, TX_N, config.LOD3_ZONE_RADIUS_M
)
print(f"\nStep 1 -- Facades extracted: {len(facades)}")
print(facades[["building_id", "facade_id", "length_m", "normal_az_deg"]].to_string(index=False))

# Steps 4-6 (procedural, no Mapillary / ONNX)
geom_list = []
el_counts = []
for _, row in facades.iterrows():
    elements = detector.detect_elements_procedural(row)
    el_counts.append(len(elements))
    geom = geometry_builder.build_facade_geometry(row, elements)
    geom_list.append(geom)

print(f"\nStep 4 (procedural) -- Elements per facade: {el_counts}")

# Step 8 QA
geom_list, n_tris = qa.run_all_checks(geom_list, facade_df=facades)
print(f"\nStep 8 QA -- Total triangles: {n_tris}")

# Step 7 PLY export
out_dir = "/tmp/lod3_test"
mat_plys = ply_exporter.export_lod3_plys(geom_list, out_dir)
print(f"\nStep 7 PLY export -> {out_dir}")
for stem, entry in mat_plys.items():
    size_kb = os.path.getsize(entry["path"]) // 1024
    print(f"  {stem}.ply  ({size_kb} KB)  mat={entry['mat_id']}")

print("\nSMOKE TEST PASSED")
