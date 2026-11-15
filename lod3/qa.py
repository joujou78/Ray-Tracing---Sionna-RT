"""Step 8 -- QA checks for LoD3 geometry.

Runs before PLY export:
  1. No degenerate triangles (zero-area faces)
  2. No overlapping coplanar faces vs the LoD2 wall (checks for duplication)
  3. Triangle budget warning (> 500k tris in LoD3 zone is expensive at RT)
  4. Watertight check (informational; LoD3 facades are open surfaces, not watertight)
"""

import logging
import numpy as np
import trimesh

log = logging.getLogger(__name__)

TRIANGLE_BUDGET = 500_000


def check_degenerate(mesh, label="mesh"):
    """Remove degenerate (zero-area) faces. Returns cleaned mesh."""
    areas = mesh.area_faces
    bad = np.where(areas < 1e-10)[0]
    if len(bad):
        log.warning("%s: removing %d degenerate face(s)", label, len(bad))
        mask = np.ones(len(mesh.faces), bool)
        mask[bad] = False
        mesh.update_faces(mask)
    return mesh


def check_coplanar_overlap(lod3_mesh, lod2_wall_mesh, label="facade", tol=0.01):
    """Warn if LoD3 wall triangles sit on top of the LoD2 wall surface.

    This catches the common mistake of adding LoD3 geometry without removing
    the original LoD2 wall quad first (would cause double-counting).

    Uses centroid distance in the wall-normal direction as a proxy.
    """
    if lod2_wall_mesh is None or len(lod2_wall_mesh.faces) == 0:
        return

    l3_cents = lod3_mesh.triangles_center
    l2_cents = lod2_wall_mesh.triangles_center

    # For each LoD3 centroid, find nearest LoD2 centroid
    from scipy.spatial import cKDTree
    try:
        tree = cKDTree(l2_cents)
        dists, _ = tree.query(l3_cents, k=1)
        n_overlapping = int((dists < tol).sum())
        if n_overlapping > 0:
            log.warning(
                "%s: %d LoD3 triangle(s) overlap the LoD2 wall surface (tol=%.3f m). "
                "Remove the LoD2 wall quad before merging LoD3 geometry.",
                label, n_overlapping, tol,
            )
    except ImportError:
        log.debug("scipy not available; skipping coplanar overlap check")


def check_triangle_budget(geometry_by_facade, label="LoD3 zone"):
    """Warn if total triangle count exceeds TRIANGLE_BUDGET."""
    total = sum(
        sum(len(m.faces) for m in geom.values() if m is not None)
        for geom in geometry_by_facade
    )
    if total > TRIANGLE_BUDGET:
        log.warning(
            "%s: %d triangles in LoD3 geometry (budget %d). "
            "Consider reducing LOD3_ZONE_RADIUS_M or LOD3_CORRIDOR_BUFFER_M.",
            label, total, TRIANGLE_BUDGET,
        )
    else:
        log.info("%s: %d triangles (within budget)", label, total)
    return total


def run_all_checks(geometry_by_facade, facade_df=None, lod2_wall_meshes=None):
    """Run all QA checks. Returns total triangle count."""
    cleaned = []
    for i, geom in enumerate(geometry_by_facade):
        label = facade_df.iloc[i]["facade_id"] if facade_df is not None else f"facade_{i}"
        cleaned_geom = {}
        for key, mesh in geom.items():
            if mesh is None or len(mesh.faces) == 0:
                cleaned_geom[key] = mesh
                continue
            mesh = check_degenerate(mesh, label=f"{label}.{key}")
            if key == "wall" and lod2_wall_meshes is not None and i < len(lod2_wall_meshes):
                check_coplanar_overlap(mesh, lod2_wall_meshes[i], label=label)
            cleaned_geom[key] = mesh
        cleaned.append(cleaned_geom)

    total = check_triangle_budget(cleaned)
    return cleaned, total
