"""Step 4-5 -- Window / door detection and regularisation.

Two modes:
  'onnx'        : use a pretrained ONNX facade segmentation model.
  'procedural'  : statistical fallback (floor grids + window ratio from EPC).

The ONNX mode expects a segmentation model that outputs per-pixel class logits
for classes: background, window, door, balcony.
A compatible model (trained on CMP Facade / RueMonge 2014) can be obtained from:
  https://github.com/bohaohuang/pytorch_fcn  (convert to ONNX after training)
Place the .onnx file at the path in DETECTOR_MODEL_PATH.

Output: list of dicts with keys:
  type (window/door/balcony), u_m, v_m, width_m, height_m,
  confidence, source (image|procedural)
  (u = along wall from x0, v = from ground)
"""

import logging
import numpy as np

from .config import (
    LOD3_DEFAULT_WINDOW_RATIO,
    LOD3_DEFAULT_FLOOR_H_M,
    LOD3_DEFAULT_RECESS_M,
    LOD3_ALLOW_PROCEDURAL,
    LOD3_DETAIL_THRESHOLD_M,
)
from .rectifier import LOD3_PIX_PER_M

log = logging.getLogger(__name__)

DETECTOR_MODEL_PATH = "lod3/models/facade_seg.onnx"

# Class indices in the segmentation model (adjust to match your model)
_CLS = {"background": 0, "window": 1, "door": 2, "balcony": 3}


def _run_onnx(rectified_bgr):
    """Run ONNX facade segmentation; return (H, W) label array."""
    import onnxruntime as ort
    import cv2

    sess = ort.InferenceSession(DETECTOR_MODEL_PATH,
                                providers=["CPUExecutionProvider"])
    inp_name = sess.get_inputs()[0].name
    h, w = rectified_bgr.shape[:2]

    # Resize to model input (typically 512x512)
    model_h, model_w = 512, 512
    resized = cv2.resize(rectified_bgr, (model_w, model_h))
    rgb = resized[:, :, ::-1].astype(np.float32) / 255.0
    rgb = (rgb - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    inp = rgb.transpose(2, 0, 1)[None]  # 1 x 3 x H x W

    logits = sess.run(None, {inp_name: inp})[0][0]  # C x H x W
    labels_sm = np.argmax(logits, axis=0).astype(np.uint8)  # H x W

    # Resize back to facade resolution
    labels = np.zeros((h, w), dtype=np.uint8)
    if h > 0 and w > 0:
        import cv2
        labels = cv2.resize(labels_sm, (w, h), interpolation=cv2.INTER_NEAREST)
    return labels


def _connected_components_to_elements(labels, cls_idx, pix_per_m,
                                      min_width_m=0.3, min_height_m=0.3):
    """Extract bounding boxes of connected regions of a given class."""
    import cv2
    mask = (labels == cls_idx).astype(np.uint8)
    n, cc, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    elements = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        wm = w / pix_per_m
        hm = h / pix_per_m
        if wm < min_width_m or hm < min_height_m:
            continue
        u_m = x / pix_per_m
        # v is from ground (image row 0 = top = roof)
        facade_h_px = labels.shape[0]
        v_m = (facade_h_px - y - h) / pix_per_m
        elements.append({
            "u_m": u_m, "v_m": v_m,
            "width_m": wm, "height_m": hm,
        })
    return elements


def detect_elements_from_image(rectified_bgr, facade_row):
    """Detect facade elements using ONNX segmentation model.

    Returns list of element dicts (see module docstring).
    """
    try:
        labels = _run_onnx(rectified_bgr)
    except Exception as exc:
        log.warning("ONNX detection failed: %s. Falling back to procedural.", exc)
        from . import config as _cfg
        if _cfg.LOD3_ALLOW_PROCEDURAL:
            return detect_elements_procedural(facade_row)
        return []

    elements = []
    for cls_name, cls_idx in _CLS.items():
        if cls_name == "background":
            continue
        boxes = _connected_components_to_elements(labels, cls_idx, LOD3_PIX_PER_M)
        for b in boxes:
            b["type"] = cls_name
            b["depth_m"] = LOD3_DEFAULT_RECESS_M
            b["confidence"] = 0.8  # placeholder until model outputs scores
            b["source"] = "image"
            elements.append(b)
    return elements


def detect_elements_procedural(facade_row):
    """Statistical LoD3 fallback -- floor grids + window-to-wall ratio.

    Elements are flagged source='procedural'.
    Call this only when LOD3_ALLOW_PROCEDURAL is True; check the flag before
    calling rather than here, so the config is read at call time.
    """

    facade_w = float(facade_row["length_m"])
    facade_h = float(facade_row["z_top"]) - float(facade_row["z_bottom"])
    n_floors = max(1, int(round(facade_h / LOD3_DEFAULT_FLOOR_H_M)))
    wwr = LOD3_DEFAULT_WINDOW_RATIO

    # One window per floor, centred, 70 % of wall width, wwr of floor height
    win_w = facade_w * 0.70
    win_h = LOD3_DEFAULT_FLOOR_H_M * wwr
    u0 = (facade_w - win_w) / 2.0

    elements = []
    for floor_i in range(n_floors):
        v0 = floor_i * LOD3_DEFAULT_FLOOR_H_M + (LOD3_DEFAULT_FLOOR_H_M - win_h) / 2.0
        elements.append({
            "type": "window",
            "u_m": u0, "v_m": v0,
            "width_m": win_w, "height_m": win_h,
            "depth_m": LOD3_DEFAULT_RECESS_M,
            "confidence": 0.5,
            "source": "procedural",
        })
    return elements


def regularise(elements, floor_h_m=LOD3_DEFAULT_FLOOR_H_M,
               col_tol_m=0.3, row_tol_m=0.3):
    """Snap elements to floor and column grids.

    Elements whose v_m differ by less than row_tol_m are snapped to the
    median v_m of their floor band.  Same for horizontal alignment.

    Returns the modified list in place.
    """
    if not elements:
        return elements

    # Snap vertical (floor rows)
    v_vals = np.array([e["v_m"] for e in elements])
    floor_ids = np.round(v_vals / floor_h_m).astype(int)
    for fi in np.unique(floor_ids):
        mask = floor_ids == fi
        med_v = float(np.median(v_vals[mask]))
        for i, m in enumerate(mask):
            if m:
                elements[i]["v_m"] = round(med_v, 3)

    # Snap horizontal (column alignment)
    u_vals = np.array([e["u_m"] for e in elements])
    # Simple: cluster u values within col_tol_m
    used = np.zeros(len(u_vals), bool)
    for i in range(len(u_vals)):
        if used[i]:
            continue
        close = np.abs(u_vals - u_vals[i]) < col_tol_m
        med_u = float(np.median(u_vals[close]))
        for j in np.where(close)[0]:
            elements[j]["u_m"] = round(med_u, 3)
        used[close] = True

    return elements
