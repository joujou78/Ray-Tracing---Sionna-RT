"""Step 3 -- Facade image rectification.

Projects the four facade corners into a Mapillary image using the camera
pose and intrinsics, then computes a homography to a metric frontal view.
Output: rectified numpy image (H x W x 3, uint8) at LOD3_PIX_PER_M px/m.
"""

import math
import numpy as np
import cv2

from .config import LOD3_DETAIL_THRESHOLD_M

LOD3_PIX_PER_M = int(1.0 / LOD3_DETAIL_THRESHOLD_M)  # 10 px/m at 0.10 m res


def _build_camera_matrix(cam_params, img_w, img_h):
    """Build 3x3 K from Mapillary camera_parameters dict."""
    focal = cam_params.get("focal_length", 0.85)
    # Mapillary stores focal as fraction of max(w, h)
    f_px = focal * max(img_w, img_h)
    cx = img_w / 2.0
    cy = img_h / 2.0
    return np.array([[f_px, 0, cx],
                     [0, f_px, cy],
                     [0,    0,  1]], dtype=np.float64)


def _rotation_from_ned_ypr(roll_deg, pitch_deg, yaw_deg):
    """NED yaw/pitch/roll to 3x3 rotation matrix (camera-to-world)."""
    r = math.radians(roll_deg)
    p = math.radians(pitch_deg)
    y = math.radians(yaw_deg)

    Rz = np.array([[math.cos(y), -math.sin(y), 0],
                   [math.sin(y),  math.cos(y), 0],
                   [0,            0,            1]])
    Ry = np.array([[ math.cos(p), 0, math.sin(p)],
                   [0,            1, 0           ],
                   [-math.sin(p), 0, math.cos(p)]])
    Rx = np.array([[1, 0,            0           ],
                   [0, math.cos(r), -math.sin(r)],
                   [0, math.sin(r),  math.cos(r)]])
    return Rz @ Ry @ Rx


def rectify_facade(image_bgr, facade_row, image_meta):
    """Return a metric frontal view of the facade.

    Parameters
    ----------
    image_bgr : np.ndarray (H x W x 3)
        Full camera image (BGR).
    facade_row : dict
        Keys: x0, y0, x1, y1, z_bottom, z_top, cx, cy,
              normal_x, normal_y, length_m (all in BNG metres).
    image_meta : dict
        Keys from Mapillary API: cam_easting, cam_northing (BNG),
        az_deg (yaw), computed_rotation ([roll, pitch, yaw]),
        camera_parameters (dict with focal_length).

    Returns
    -------
    np.ndarray (H_out x W_out x 3) or None if projection fails.
    """
    H, W = image_bgr.shape[:2]
    cam_params = image_meta.get("camera_parameters", {})
    K = _build_camera_matrix(cam_params, W, H)

    rot = image_meta.get("computed_rotation", [0, 0, image_meta.get("az_deg", 0)])
    R = _rotation_from_ned_ypr(*rot)

    cam_e = image_meta["cam_easting"]
    cam_n = image_meta["cam_northing"]
    cam_z = image_meta.get("cam_altitude_m", 1.5)  # default eye height 1.5 m

    t = np.array([cam_e, cam_n, cam_z], dtype=np.float64)

    # Four facade corners in world coords (BNG E, N, Z)
    x0, y0 = facade_row["x0"], facade_row["y0"]
    x1, y1 = facade_row["x1"], facade_row["y1"]
    zb = facade_row["z_bottom"]
    zt = facade_row["z_top"]
    world_pts = np.array([
        [x0, y0, zb],
        [x1, y1, zb],
        [x1, y1, zt],
        [x0, y0, zt],
    ], dtype=np.float64)

    # Project into image: p = K @ R.T @ (X - t)
    img_pts = []
    for wp in world_pts:
        cam_vec = R.T @ (wp - t)
        if cam_vec[2] <= 0:
            return None  # behind camera
        px = K @ (cam_vec / cam_vec[2])
        img_pts.append([px[0], px[1]])
    img_pts = np.array(img_pts, dtype=np.float32)

    # Destination rect in pixel space
    facade_w_m = facade_row["length_m"]
    facade_h_m = zt - zb
    dst_w = max(1, int(facade_w_m * LOD3_PIX_PER_M))
    dst_h = max(1, int(facade_h_m * LOD3_PIX_PER_M))

    dst_pts = np.array([
        [0,     dst_h - 1],
        [dst_w - 1, dst_h - 1],
        [dst_w - 1, 0        ],
        [0,     0            ],
    ], dtype=np.float32)

    H_mat, _ = cv2.findHomography(img_pts, dst_pts)
    if H_mat is None:
        return None

    rectified = cv2.warpPerspective(image_bgr, H_mat, (dst_w, dst_h))
    return rectified
