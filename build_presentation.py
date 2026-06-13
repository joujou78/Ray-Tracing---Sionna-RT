"""
FYP Presentation Builder — Ray Tracing for Path Loss Prediction
Dark academic theme, high-level design
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ── Colour palette ────────────────────────────────────────────────────────────
C_BG        = RGBColor(0x0D, 0x1B, 0x2A)   # deep navy
C_ACCENT    = RGBColor(0x00, 0xB4, 0xD8)   # cyan accent
C_ACCENT2   = RGBColor(0x90, 0xE0, 0xEF)   # light cyan
C_WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
C_LIGHT     = RGBColor(0xCA, 0xD3, 0xDF)   # soft grey text
C_GREEN     = RGBColor(0x2D, 0xCB, 0x7F)   # success green
C_ORANGE    = RGBColor(0xFF, 0x9F, 0x1C)   # warning orange
C_RED       = RGBColor(0xFF, 0x4D, 0x6D)   # error red
C_PANEL     = RGBColor(0x11, 0x2A, 0x40)   # slightly lighter panel
C_DIVIDER   = RGBColor(0x1E, 0x3A, 0x52)   # divider line

W = Inches(13.33)   # widescreen 16:9
H = Inches(7.5)

prs = Presentation()
prs.slide_width  = W
prs.slide_height = H

blank_layout = prs.slide_layouts[6]  # completely blank


def add_slide():
    return prs.slides.add_slide(blank_layout)


def bg(slide, color=C_BG):
    """Fill slide background."""
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def rect(slide, x, y, w, h, color, alpha=None):
    """Add a filled rectangle."""
    shape = slide.shapes.add_shape(1, x, y, w, h)  # MSO_SHAPE_TYPE.RECTANGLE = 1
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def txt(slide, text, x, y, w, h, size, color=C_WHITE, bold=False,
        align=PP_ALIGN.LEFT, italic=False, wrap=True):
    txb = slide.shapes.add_textbox(x, y, w, h)
    tf  = txb.text_frame
    tf.word_wrap = wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size   = Pt(size)
    run.font.color.rgb = color
    run.font.bold   = bold
    run.font.italic = italic
    return txb


def accent_bar(slide, y=Inches(0.08), h=Inches(0.06)):
    """Top accent bar."""
    rect(slide, 0, y, W, h, C_ACCENT)


def slide_number(slide, n, total=12):
    txt(slide, f"{n} / {total}", Inches(12.0), Inches(7.1), Inches(1.2), Inches(0.35),
        size=9, color=C_LIGHT, align=PP_ALIGN.RIGHT)


def section_tag(slide, label, x=Inches(0.35), y=Inches(0.22)):
    """Small uppercase tag top-left."""
    txt(slide, label.upper(), x, y, Inches(4), Inches(0.28),
        size=8, color=C_ACCENT, bold=True)


def panel(slide, x, y, w, h):
    """Dark panel box."""
    return rect(slide, x, y, w, h, C_PANEL)


def divider(slide, x, y, w, thickness=Inches(0.018)):
    rect(slide, x, y, w, thickness, C_DIVIDER)


def bullet_block(slide, items, x, y, w, size=12, color=C_LIGHT, spacing=0.38):
    """Render a list of bullet strings as separate textboxes."""
    cy = y
    for item in items:
        prefix = "  •  " if not item.startswith("◆") else ""
        txt(slide, prefix + item.lstrip("◆").strip(), x, cy, w, Inches(spacing),
            size=size, color=color)
        cy += Inches(spacing)
    return cy


def kv_row(slide, key, val, x, y, w, key_color=C_ACCENT2, val_color=C_WHITE,
           size=11, row_h=Inches(0.38)):
    """Key | value row."""
    col1 = w * 0.42
    col2 = w * 0.58
    txt(slide, key, x, y, col1, row_h, size=size, color=key_color, bold=True)
    txt(slide, val, x + col1, y, col2, row_h, size=size, color=val_color)
    return y + row_h


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
accent_bar(s)

# Large cyan decorative bar on left
rect(s, 0, 0, Inches(0.25), H, C_ACCENT)

# Main title
txt(s, "Ray Tracing for Path Loss Prediction",
    Inches(0.55), Inches(1.6), Inches(9.5), Inches(1.2),
    size=40, bold=True, color=C_WHITE)

txt(s, "in Urban Environments",
    Inches(0.55), Inches(2.7), Inches(9.5), Inches(0.8),
    size=32, bold=False, color=C_ACCENT2)

divider(s, Inches(0.55), Inches(3.55), Inches(5.5))

# Subtitle details
details = [
    ("Scene",     "Nottingham · Ofcom 2018 Drive Test"),
    ("Frequency", "915.95 MHz  (IoT / LoRaWAN band)"),
    ("Tool",      "Sionna RT 2.0  +  Sionna 0.19 Differentiable RT"),
    ("Goal",      "Minimise RMSE against 1 200 real Ofcom measurements"),
]
cy = Inches(3.75)
for k, v in details:
    txt(s, k, Inches(0.55), cy, Inches(2.2), Inches(0.38), size=11,
        color=C_ACCENT, bold=True)
    txt(s, v, Inches(2.75), cy, Inches(7.0), Inches(0.38), size=11,
        color=C_LIGHT)
    cy += Inches(0.42)

# Right-side decorative ray-tracing pattern suggestion (text placeholder)
rect(s, Inches(10.0), Inches(1.2), Inches(3.0), Inches(5.2), C_PANEL)
txt(s, "[ Scene Render\nor Coverage Map ]",
    Inches(10.1), Inches(2.8), Inches(2.8), Inches(1.5),
    size=11, color=C_DIVIDER, align=PP_ALIGN.CENTER, italic=True)

slide_number(s, 1)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — PURPOSE & MOTIVATION
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
accent_bar(s)
section_tag(s, "Motivation")
slide_number(s, 2)

txt(s, "Purpose & Motivation", Inches(0.45), Inches(0.5), Inches(10), Inches(0.7),
    size=28, bold=True, color=C_WHITE)
divider(s, Inches(0.45), Inches(1.18), Inches(12.4))

# Three columns
cols = [
    {
        "icon": "⚠",
        "title": "The Problem",
        "color": C_RED,
        "items": [
            "Empirical models (COST-231,\nOkumura-Hata) give 20–36 dB errors",
            "No terrain, no building geometry,\nno material physics",
            "Fixed-environment formulas —\nbreak in new cities",
        ]
    },
    {
        "icon": "🎯",
        "title": "Our Goal",
        "color": C_ACCENT,
        "items": [
            "Minimise RMSE against\n1 200 real Ofcom measurements",
            "Reproduce physical propagation:\ndiffraction, reflection, scatter",
            "Differentiable RT calibration\n(NVLabs Hoydis et al. 2023)",
        ]
    },
    {
        "icon": "📡",
        "title": "The Dataset",
        "color": C_GREEN,
        "items": [
            "Ofcom 2018 drive test\n915.95 MHz, Nottingham UK",
            "1 200 receivers  |  0.3–9 km",
            "RSSI range: −118 to −23 dBm\nNoise floor: −124 dBm",
        ]
    },
]

cw = Inches(4.0)
cx_starts = [Inches(0.35), Inches(4.55), Inches(8.75)]

for i, col in enumerate(cols):
    cx = cx_starts[i]
    panel(s, cx, Inches(1.35), cw, Inches(5.7))
    rect(s, cx, Inches(1.35), cw, Inches(0.07), col["color"])

    txt(s, col["icon"] + "  " + col["title"],
        cx + Inches(0.18), Inches(1.5), cw - Inches(0.3), Inches(0.5),
        size=14, bold=True, color=col["color"])

    cy2 = Inches(2.1)
    for item in col["items"]:
        txt(s, "›  " + item, cx + Inches(0.18), cy2, cw - Inches(0.3), Inches(0.9),
            size=11, color=C_LIGHT)
        cy2 += Inches(1.05)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — RESEARCH QUESTIONS
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
accent_bar(s)
section_tag(s, "Research Questions")
slide_number(s, 3)

txt(s, "Research Questions", Inches(0.45), Inches(0.5), Inches(10), Inches(0.7),
    size=28, bold=True, color=C_WHITE)
divider(s, Inches(0.45), Inches(1.18), Inches(12.4))

rqs = [
    ("RQ 1", C_ACCENT,
     "Flat Terrain vs DEM",
     "How much does digital elevation modelling (DEM) improve path loss\n"
     "prediction accuracy over a flat z = 0 scene in Nottingham?"),
    ("RQ 2", C_GREEN,
     "Differentiable RT Calibration",
     "Can Sionna 0.19 differentiable RT (NVLabs approach) achieve\n"
     "< 5 dB RMSE on the Ofcom 2018 UK dataset after calibration?"),
    ("RQ 3", C_ORANGE,
     "Optimal Scene Configuration",
     "Which combination of scene geometry, material parameters, and\n"
     "ray-tracing settings best represents urban Nottingham at 915 MHz?"),
]

cy = Inches(1.4)
for tag, color, title, body in rqs:
    rect(s, Inches(0.35), cy + Inches(0.12), Inches(0.06), Inches(0.85), color)
    rect(s, Inches(0.41), cy, Inches(12.5), Inches(1.12), C_PANEL)
    txt(s, tag, Inches(0.55), cy + Inches(0.06), Inches(1.0), Inches(0.4),
        size=10, color=color, bold=True)
    txt(s, title, Inches(1.55), cy + Inches(0.05), Inches(4.5), Inches(0.4),
        size=13, color=C_WHITE, bold=True)
    txt(s, body, Inches(6.3), cy + Inches(0.05), Inches(6.4), Inches(1.0),
        size=11, color=C_LIGHT)
    cy += Inches(1.28)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — METHODOLOGY PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
accent_bar(s)
section_tag(s, "Methodology")
slide_number(s, 4)

txt(s, "Simulation & Calibration Pipeline", Inches(0.45), Inches(0.5),
    Inches(12), Inches(0.7), size=28, bold=True, color=C_WHITE)
divider(s, Inches(0.45), Inches(1.18), Inches(12.4))

stages = [
    ("01", "INPUT DATA",      C_ACCENT,  "OSM + EA LiDAR\n+ Ofcom CSV"),
    ("02", "SCENE BUILDER",   C_ACCENT2, "nDSM + ITU-R P.2040-2\n+ Terrain PLY"),
    ("03", "RAY TRACING",     C_GREEN,   "Sionna 2.0 PathSolver\n+ Sionna 0.19 Diff RT"),
    ("04", "CALIBRATION",     C_ORANGE,  "Scalar (Cell 10b)\nMaterial (Cell 11b)"),
    ("05", "ML RESIDUAL",     C_RED,     "ResidualMLP (Cell 15)\nCNN+MLP (Cell 14)\nMaterialMLP (Cell 16)"),
    ("06", "VALIDATION",      C_ACCENT,  "RMSE · MAE · Bias\nSTD · R² per band"),
]

bw = Inches(2.05)
bh = Inches(4.5)
gap = Inches(0.08)
bx = Inches(0.28)

for i, (num, label, color, detail) in enumerate(stages):
    cx = bx + i * (bw + gap)
    panel(s, cx, Inches(1.38), bw, bh)
    rect(s, cx, Inches(1.38), bw, Inches(0.06), color)

    txt(s, num, cx + Inches(0.12), Inches(1.5), bw, Inches(0.45),
        size=22, bold=True, color=color)
    txt(s, label, cx + Inches(0.12), Inches(1.95), bw - Inches(0.15), Inches(0.5),
        size=10, bold=True, color=C_WHITE)
    divider(s, cx + Inches(0.12), Inches(2.48), bw - Inches(0.25))
    txt(s, detail, cx + Inches(0.12), Inches(2.58), bw - Inches(0.15), Inches(1.8),
        size=10, color=C_LIGHT)

    # Arrow between stages
    if i < len(stages) - 1:
        ax = cx + bw + Inches(0.01)
        txt(s, "▶", ax, Inches(3.35), gap + Inches(0.06), Inches(0.4),
            size=9, color=C_DIVIDER, align=PP_ALIGN.CENTER)

# Validation metrics row
txt(s, "Output Metrics per Distance Band:   RMSE  |  MAE  |  Bias  |  STD  |  R²",
    Inches(0.35), Inches(6.1), Inches(12.6), Inches(0.4),
    size=11, color=C_ACCENT2, align=PP_ALIGN.CENTER)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — OFCOM DATA PROCESSING
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
accent_bar(s)
section_tag(s, "Input Data")
slide_number(s, 5)

txt(s, "Ofcom Dataset — GPS to Sionna Receivers",
    Inches(0.45), Inches(0.5), Inches(12), Inches(0.7),
    size=28, bold=True, color=C_WHITE)
divider(s, Inches(0.45), Inches(1.18), Inches(12.4))

# Left: pipeline steps
panel(s, Inches(0.35), Inches(1.35), Inches(7.0), Inches(5.7))

steps = [
    ("1", C_ACCENT,  "Raw Ofcom CSV",
     "GPS (WGS84 lat/lon)  +  RSSI (dBm)  per measurement point"),
    ("2", C_ACCENT,  "Filter & Clean",
     "Keep 915.95 MHz  ·  drop RSSI < −124 dBm  ·  remove duplicates"),
    ("3", C_GREEN,   "Coordinate Transform",
     "WGS84  →  UTM Zone 30N (EPSG:32630)  →  local scene XY (metres)"),
    ("4", C_GREEN,   "Height Assignment",
     "RX Z = EA LiDAR DTM elevation  +  1.5 m AGL"),
    ("5", C_ORANGE,  "Sionna RX Array",
     "Each point  →  Receiver object  ·  isotropic antenna  ·  1 200 total"),
    ("6", C_ACCENT2, "PL Reference",
     "PL_meas = TX_EIRP − RSSI_meas  (dB)  →  ground truth for RMSE"),
]

cy = Inches(1.5)
for num, color, title, body in steps:
    rect(s, Inches(0.5), cy + Inches(0.08), Inches(0.32), Inches(0.32), color)
    txt(s, num, Inches(0.5), cy + Inches(0.05), Inches(0.32), Inches(0.32),
        size=10, bold=True, color=C_BG, align=PP_ALIGN.CENTER)
    txt(s, title, Inches(0.95), cy + Inches(0.03), Inches(2.0), Inches(0.35),
        size=11, bold=True, color=color)
    txt(s, body, Inches(3.0), cy + Inches(0.03), Inches(4.2), Inches(0.35),
        size=10, color=C_LIGHT)
    cy += Inches(0.87)

# Right: key numbers panel
panel(s, Inches(7.6), Inches(1.35), Inches(5.4), Inches(5.7))
rect(s, Inches(7.6), Inches(1.35), Inches(5.4), Inches(0.06), C_ACCENT)

txt(s, "Key Numbers", Inches(7.75), Inches(1.5), Inches(5.0), Inches(0.45),
    size=14, bold=True, color=C_ACCENT)

kvs = [
    ("Raw Ofcom points",    "~4 000"),
    ("After filtering",     "1 200 receivers"),
    ("Coverage range",      "0.3 km – 9 km from TX"),
    ("TX location",         "(−1.2559°, 52.9863°)"),
    ("TX height",           "17 m AGL"),
    ("Frequency",           "915.95 MHz"),
    ("RSSI range (meas)",   "−118 to −22.9 dBm"),
    ("Noise floor",         "−124 dBm"),
    ("PL_meas range",       "93.7 – 142.4 dB"),
]

cy2 = Inches(2.1)
for k, v in kvs:
    txt(s, k, Inches(7.75), cy2, Inches(2.8), Inches(0.38), size=10,
        color=C_ACCENT2, bold=True)
    txt(s, v, Inches(10.55), cy2, Inches(2.3), Inches(0.38), size=10,
        color=C_WHITE)
    cy2 += Inches(0.52)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — SCENE CONSTRUCTION
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
accent_bar(s)
section_tag(s, "Scene Construction")
slide_number(s, 6)

txt(s, "Scene Construction — Blender → OSM → Merged PLY",
    Inches(0.45), Inches(0.5), Inches(12.5), Inches(0.7),
    size=26, bold=True, color=C_WHITE)
divider(s, Inches(0.45), Inches(1.18), Inches(12.4))

# Three panels side by side
panels_data = [
    {
        "title": "Stage 1 · Blender (Flat)",
        "color": C_ORANGE,
        "sub": "Manual · OSM importer plugin",
        "pros": ["Fast to build — one import/export", "Full geometry cleanup in GUI",
                 "Single merged PLY → Sionna loads in seconds"],
        "cons": ["No terrain — flat z=0 plane", "Nottingham hills completely absent",
                 "Manual — not reproducible", "8–15 dB error at 300–1500 m"],
    },
    {
        "title": "Stage 2 · OSM Direct (DEM)",
        "color": C_GREEN,
        "sub": "Automated · Python OSMnx + scene builder",
        "pros": ["Fully automated & reproducible", "ITU-R P.2040-2 materials per building type",
                 "Real terrain from EA LiDAR (2 m res)"],
        "cons": ["OSM heights often missing → estimated", "OSM tags inconsistent across Nottingham",
                 "Longer scene build time"],
    },
    {
        "title": "Stage 3 · Merged PLY",
        "color": C_ACCENT,
        "sub": "Why we merged 150 k files → one per material",
        "pros": ["Scene load: 20 min → 45 sec", "Single BVH → 50× faster ray traversal",
                 "No GPU memory fragmentation", "Solve rate improved directly"],
        "cons": ["Per-material merge requires preprocessing", "Harder to inspect individual buildings"],
    },
]

pw = Inches(4.2)
gap2 = Inches(0.12)
for i, pd in enumerate(panels_data):
    cx = Inches(0.3) + i * (pw + gap2)
    panel(s, cx, Inches(1.35), pw, Inches(5.75))
    rect(s, cx, Inches(1.35), pw, Inches(0.07), pd["color"])

    txt(s, pd["title"], cx + Inches(0.15), Inches(1.5), pw - Inches(0.2), Inches(0.42),
        size=12, bold=True, color=pd["color"])
    txt(s, pd["sub"], cx + Inches(0.15), Inches(1.93), pw - Inches(0.2), Inches(0.38),
        size=9.5, color=C_LIGHT, italic=True)
    divider(s, cx + Inches(0.15), Inches(2.32), pw - Inches(0.3))

    txt(s, "✔  Pros", cx + Inches(0.15), Inches(2.4), pw, Inches(0.35),
        size=10, bold=True, color=C_GREEN)
    cy3 = Inches(2.76)
    for p in pd["pros"]:
        txt(s, "   " + p, cx + Inches(0.15), cy3, pw - Inches(0.2), Inches(0.45),
            size=9.5, color=C_LIGHT)
        cy3 += Inches(0.44)

    txt(s, "✘  Cons", cx + Inches(0.15), cy3 + Inches(0.05), pw, Inches(0.35),
        size=10, bold=True, color=C_RED)
    cy3 += Inches(0.43)
    for c in pd["cons"]:
        txt(s, "   " + c, cx + Inches(0.15), cy3, pw - Inches(0.2), Inches(0.45),
            size=9.5, color=C_LIGHT)
        cy3 += Inches(0.44)

# ══════════════════════════════════════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════════════════════════════════════
out = "/home/user/Ray-Tracing---Sionna-RT/FYP_RayTracing_Presentation.pptx"
prs.save(out)
print(f"Saved → {out}")
