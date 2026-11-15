"""lod3 -- Automatic LoD3 facade module for Sionna RT scene builder.

Pipeline stages:
  1. facade_extractor  -- footprint edges -> facade DataFrame
  2. mapillary         -- Mapillary API v4 image selection
  3. rectifier         -- homography to metric frontal view
  4. detector          -- window/door/balcony detection (ONNX or procedural)
  5. detector          -- grid regularisation (same module)
  6. geometry_builder  -- wall-with-holes + glass panes + balcony boxes
  7. ply_exporter      -- per-material PLY files + mat_plys dict
  8. qa                -- degenerate triangles, overlap, budget checks

Minimum usage (procedural fallback, no Mapillary token needed):
    from lod3 import config, facade_extractor, detector, geometry_builder, ply_exporter, qa
    config.LOD3_ENABLE = True
    config.LOD3_ALLOW_PROCEDURAL = True
    facades = facade_extractor.extract_facades(footprints_gdf, tx_e, tx_n, 400)
    geom_list = []
    for _, row in facades.iterrows():
        elements = detector.detect_elements_procedural(row)
        geom_list.append(geometry_builder.build_facade_geometry(row, elements))
    geom_list, n_tris = qa.run_all_checks(geom_list)
    mat_plys = ply_exporter.export_lod3_plys(geom_list, out_dir='scene/meshes')
"""

from . import config
from . import facade_extractor
from . import mapillary
from . import rectifier
from . import detector
from . import geometry_builder
from . import ply_exporter
from . import qa

__version__ = "0.1.0"
