"""Step 6 -- 3D geometry construction.

For each facade + its detected elements, build:
  - Wall polygon with holes (windows/doors cut out)
  - Window/door glass panes at LOD3_DEFAULT_RECESS_M depth
  - Balcony boxes

Returns trimesh.Trimesh objects grouped by material class:
  wall  -> bld_itu_concrete_wall  (or brick depending on EPC)
  glass -> bld_itu_glass_windows
  balc  -> bld_itu_concrete_balconies

All geometry is in local BNG metres (absolute E, N, Z).
"""

import math
import numpy as np
import trimesh
from shapely.geometry import Polygon as SPolygon

from .config import LOD3_DEFAULT_RECESS_M


def _facade_local_frame(facade_row):
    """Return origin, u_vec, v_vec (all in BNG 3D metres) for a facade."""
    x0, y0 = facade_row["x0"], facade_row["y0"]
    x1, y1 = facade_row["x1"], facade_row["y1"]
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    u_vec = np.array([dx / length, dy / length, 0.0])  # along wall
    v_vec = np.array([0.0, 0.0, 1.0])                  # upward
    # Normal (into the scene, same as facade_extractor convention)
    n_vec = np.array([facade_row["normal_x"], facade_row["normal_y"], 0.0])
    origin = np.array([x0, y0, facade_row["z_bottom"]])
    return origin, u_vec, v_vec, n_vec, length


def _quad_mesh(p00, p10, p11, p01):
    """Two-triangle mesh from four corners (CCW winding when viewed from front)."""
    verts = np.array([p00, p10, p11, p01], dtype=np.float64)
    faces = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int32)
    return trimesh.Trimesh(vertices=verts, faces=faces, process=False)


def _triangulate_wall_with_holes(facade_row, elements, origin, u_vec, v_vec):
    """Wall polygon with window/door holes, triangulated via Shapely + earclip."""
    w = facade_row["length_m"]
    h = float(facade_row["z_top"]) - float(facade_row["z_bottom"])

    outer = SPolygon([(0, 0), (w, 0), (w, h), (0, h)])
    holes = []
    for el in elements:
        if el["type"] not in ("window", "door"):
            continue
        u0, v0 = el["u_m"], el["v_m"]
        u1, v1 = u0 + el["width_m"], v0 + el["height_m"]
        # Clamp to wall extents
        u0, v0 = max(0, u0), max(0, v0)
        u1, v1 = min(w, u1), min(h, v1)
        if u1 - u0 > 0.05 and v1 - v0 > 0.05:
            holes.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    wall_2d = SPolygon(outer.exterior.coords, holes) if holes else outer
    if wall_2d.is_empty or not wall_2d.is_valid:
        wall_2d = outer

    # Triangulate
    try:
        verts_2d, faces = trimesh.creation.triangulate_polygon(wall_2d, engine="earcut")
    except Exception:
        # Fallback: simple quad without holes
        verts_2d = np.array([[0, 0], [w, 0], [w, h], [0, h]])
        faces = np.array([[0, 1, 2], [0, 2, 3]])

    # Map 2D (u, v) -> 3D BNG
    verts_3d = (
        origin
        + verts_2d[:, 0:1] * u_vec
        + verts_2d[:, 1:2] * v_vec
    )
    return trimesh.Trimesh(vertices=verts_3d, faces=faces, process=False)


def _window_pane_mesh(el, origin, u_vec, v_vec, n_vec):
    """Glass pane recessed by el['depth_m'] behind the wall surface."""
    recess = el.get("depth_m", LOD3_DEFAULT_RECESS_M)
    u0, v0 = el["u_m"], el["v_m"]
    u1, v1 = u0 + el["width_m"], v0 + el["height_m"]
    offset = -recess * n_vec  # push inward (opposite to outward normal)
    p00 = origin + u0 * u_vec + v0 * v_vec + offset
    p10 = origin + u1 * u_vec + v0 * v_vec + offset
    p11 = origin + u1 * u_vec + v1 * v_vec + offset
    p01 = origin + u0 * u_vec + v1 * v_vec + offset
    return _quad_mesh(p00, p10, p11, p01)


def _balcony_box_mesh(el, origin, u_vec, v_vec, n_vec):
    """Simple box protruding 0.8 m from the facade for balconies."""
    depth = 0.8  # metres
    u0, v0 = el["u_m"], el["v_m"]
    u1, v1 = u0 + el["width_m"], v0 + el["height_m"]
    slab_h = 0.15  # slab thickness
    pts_front = [
        origin + u0 * u_vec + v0 * v_vec + depth * n_vec,
        origin + u1 * u_vec + v0 * v_vec + depth * n_vec,
        origin + u1 * u_vec + (v0 + slab_h) * v_vec + depth * n_vec,
        origin + u0 * u_vec + (v0 + slab_h) * v_vec + depth * n_vec,
    ]
    # Build a simple slab (top face only for now)
    top = [
        origin + u0 * u_vec + (v0 + slab_h) * v_vec,
        origin + u1 * u_vec + (v0 + slab_h) * v_vec,
        origin + u1 * u_vec + (v0 + slab_h) * v_vec + depth * n_vec,
        origin + u0 * u_vec + (v0 + slab_h) * v_vec + depth * n_vec,
    ]
    slab = _quad_mesh(*top)
    front = _quad_mesh(*pts_front)
    return trimesh.util.concatenate([slab, front])


def build_facade_geometry(facade_row, elements):
    """Build all meshes for one facade.

    Returns dict: {'wall': Trimesh, 'glass': Trimesh|None, 'balcony': Trimesh|None}
    """
    origin, u_vec, v_vec, n_vec, length = _facade_local_frame(facade_row)

    wall_mesh = _triangulate_wall_with_holes(facade_row, elements, origin, u_vec, v_vec)

    glass_meshes = []
    balcony_meshes = []
    for el in elements:
        if el["type"] in ("window", "door"):
            m = _window_pane_mesh(el, origin, u_vec, v_vec, n_vec)
            if m is not None:
                glass_meshes.append(m)
        elif el["type"] == "balcony":
            m = _balcony_box_mesh(el, origin, u_vec, v_vec, n_vec)
            if m is not None:
                balcony_meshes.append(m)

    glass = trimesh.util.concatenate(glass_meshes) if glass_meshes else None
    balcony = trimesh.util.concatenate(balcony_meshes) if balcony_meshes else None

    return {"wall": wall_mesh, "glass": glass, "balcony": balcony}
