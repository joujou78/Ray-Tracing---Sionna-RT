"""Step 7 -- PLY export and mat_plys registration.

Writes per-material PLY files following the scene builder naming convention
and returns a dict ready to merge into mat_plys (CELL 4).

PLY names:
  bld_lod3_itu_concrete_walls.ply
  bld_lod3_itu_glass_windows.ply
  bld_lod3_itu_concrete_balconies.ply

The corresponding Sionna 2.0 material IDs used in scene_with_full.xml:
  mat-itu_concrete  (walls + balconies)
  mat-itu_glass     (windows / glass panes)
"""

import os
import logging
import numpy as np
import trimesh

log = logging.getLogger(__name__)

# Maps geometry key -> (PLY filename stem, Sionna 2.0 material ID)
_MATERIAL_MAP = {
    "wall":    ("bld_lod3_itu_concrete_walls",    "mat-itu_concrete"),
    "glass":   ("bld_lod3_itu_glass_windows",     "mat-itu_glass"),
    "balcony": ("bld_lod3_itu_concrete_balconies","mat-itu_concrete"),
}


def export_lod3_plys(geometry_by_facade, out_dir):
    """Merge all facade geometries by material and write PLY files.

    Parameters
    ----------
    geometry_by_facade : list of dicts
        Each dict is the return value of geometry_builder.build_facade_geometry:
        {'wall': Trimesh, 'glass': Trimesh|None, 'balcony': Trimesh|None}
    out_dir : str
        Directory to write PLY files (must exist).

    Returns
    -------
    dict  mat_plys-compatible:
        {ply_filename_stem: {'mat_id': ..., 'path': absolute_path}}
    """
    os.makedirs(out_dir, exist_ok=True)
    accumulator = {k: [] for k in _MATERIAL_MAP}

    for geom in geometry_by_facade:
        for key, mesh in geom.items():
            if mesh is not None and len(mesh.faces) > 0:
                accumulator[key].append(mesh)

    mat_plys = {}
    for key, meshes in accumulator.items():
        if not meshes:
            continue
        combined = trimesh.util.concatenate(meshes)
        stem, mat_id = _MATERIAL_MAP[key]
        ply_path = os.path.join(out_dir, stem + ".ply")

        try:
            combined.export(ply_path)
            mat_plys[stem] = {"mat_id": mat_id, "path": ply_path}
            log.info("Wrote %s  (%d triangles)", ply_path, len(combined.faces))
        except Exception as exc:
            log.error("Failed to write %s: %s", ply_path, exc)

    return mat_plys


def merge_into_scene_mat_plys(existing_mat_plys, lod3_mat_plys):
    """Add LoD3 entries to the existing mat_plys dict (no duplicates)."""
    for stem, entry in lod3_mat_plys.items():
        if stem in existing_mat_plys:
            log.warning("mat_plys key '%s' already exists -- skipping LoD3 entry", stem)
            continue
        existing_mat_plys[stem] = entry
    return existing_mat_plys
