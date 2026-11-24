"""
ITU-R P.2108 §3.1: height-gain terminal clutter correction.

Used when a terminal sits inside clutter (e.g. a handset at 1.5 m in a town).
The path model is evaluated with the terminal raised to the representative
clutter height R, and the correction Ah is added (Rec. P.2108, Table 3):

    clutter type          R (m)   model
    water / sea             10    height gain
    open / rural            10    height gain
    suburban                10    diffraction
    urban / trees / forest  15    diffraction
    dense urban             20    diffraction

Height gain:  Ah = -Kh2 * log10(h / R),   Kh2 = 21.8 + 6.2 log10(f)
Diffraction:  Ah = J(nu) - 6.03,  nu = Knu * sqrt(hdif * theta_clut),
              hdif = R - h,  theta_clut = atan(hdif / ws) [deg],
              Knu = 0.342 sqrt(f),  ws = 27 m
Ah = 0 when h >= R.  f in GHz, valid 0.03 - 3 GHz.
"""
from __future__ import annotations

import math

from .p1812 import knife_edge_j

CATEGORIES = {
    "water": (10.0, "height_gain"),
    "open": (10.0, "height_gain"),
    "suburban": (10.0, "diffraction"),
    "urban": (15.0, "diffraction"),
    "dense_urban": (20.0, "diffraction"),
}
WS = 27.0


def terminal_clutter(f_ghz: float, h: float, category: str | None, r: float | None = None):
    """
    Returns (Ah dB, R m used for the path calculation, note). For category None
    or 'none' returns (0, h, None). `r` overrides the representative height.
    """
    if not category or category == "none":
        return 0.0, h, None
    if category not in CATEGORIES:
        raise ValueError(f"Unknown clutter category '{category}'")
    r_def, model = CATEGORIES[category]
    R = float(r) if r else r_def
    note = None
    if not 0.03 <= f_ghz <= 3.0:
        note = "P.2108 §3.1 is specified for 0.03-3 GHz; applied outside its range."
    if h >= R:
        return 0.0, h, note
    if model == "height_gain":
        kh2 = 21.8 + 6.2 * math.log10(f_ghz)
        ah = -kh2 * math.log10(h / R)
    else:
        hdif = R - h
        theta = math.degrees(math.atan(hdif / WS))
        nu = 0.342 * math.sqrt(f_ghz) * math.sqrt(hdif * theta)
        ah = float(knife_edge_j(nu)) - 6.03
    return ah, R, note
