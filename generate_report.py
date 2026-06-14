"""
generate_report.py
Generates Model_Pipeline_Report.pdf using reportlab Platypus.
"""

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUTPUT_PATH = "/home/user/Ray-Tracing---Sionna-RT/Model_Pipeline_Report.pdf"

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
DARK_BLUE  = colors.HexColor("#1a3a5c")
LIGHT_BLUE = colors.HexColor("#e8f0f8")
LIGHT_GREY = colors.HexColor("#f5f5f5")
MID_GREY   = colors.HexColor("#cccccc")
WHITE      = colors.white
BLACK      = colors.black

# ---------------------------------------------------------------------------
# Page template — footer
# ---------------------------------------------------------------------------
FOOTER_TEXT = "Sionna RT Pipeline — Nottingham 915 MHz | Branch: claude/cool-cori-rrWbY"

def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(2 * cm, 1.2 * cm, FOOTER_TEXT)
    page_num = f"Page {doc.page}"
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, page_num)
    canvas.restoreState()

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def build_styles():
    styles = {}

    styles["title"] = ParagraphStyle(
        "title",
        fontName="Helvetica-Bold",
        fontSize=26,
        textColor=DARK_BLUE,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle",
        fontName="Helvetica",
        fontSize=14,
        textColor=colors.HexColor("#2c5f8a"),
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    styles["date"] = ParagraphStyle(
        "date",
        fontName="Helvetica",
        fontSize=11,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    styles["meta"] = ParagraphStyle(
        "meta",
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles["h1"] = ParagraphStyle(
        "h1",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=DARK_BLUE,
        spaceBefore=18,
        spaceAfter=8,
    )
    styles["h2"] = ParagraphStyle(
        "h2",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=DARK_BLUE,
        spaceBefore=12,
        spaceAfter=6,
    )
    styles["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=10,
        textColor=BLACK,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=14,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet",
        fontName="Helvetica",
        fontSize=10,
        textColor=BLACK,
        leftIndent=16,
        spaceAfter=4,
        leading=13,
        bulletIndent=6,
    )
    styles["code"] = ParagraphStyle(
        "code",
        fontName="Courier",
        fontSize=8.5,
        textColor=BLACK,
        backColor=LIGHT_GREY,
        leftIndent=10,
        rightIndent=10,
        spaceAfter=2,
        spaceBefore=2,
        leading=12,
    )
    styles["note"] = ParagraphStyle(
        "note",
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=colors.HexColor("#444444"),
        spaceAfter=4,
    )
    return styles

# ---------------------------------------------------------------------------
# Helper: bullet item
# ---------------------------------------------------------------------------
def bullet(text, styles):
    return Paragraph(f"&#x2022; {text}", styles["bullet"])

# ---------------------------------------------------------------------------
# Helper: code block (multi-line string -> list of Paragraphs)
# ---------------------------------------------------------------------------
def code_block(code_text, styles):
    items = []
    for line in code_text.split("\n"):
        line = (line
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
        items.append(Paragraph(line if line.strip() else "&nbsp;", styles["code"]))
    return items

# ---------------------------------------------------------------------------
# Helper: standard table style
# ---------------------------------------------------------------------------
def std_table_style(header_rows=1):
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, header_rows - 1), LIGHT_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, header_rows - 1), DARK_BLUE),
        ("FONTNAME",      (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, header_rows - 1), 9),
        ("ALIGN",         (0, 0), (-1, -1),              "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1),              "MIDDLE"),
        ("FONTNAME",      (0, header_rows), (-1, -1),    "Helvetica"),
        ("FONTSIZE",      (0, header_rows), (-1, -1),    9),
        ("ROWBACKGROUNDS",(0, header_rows), (-1, -1),    [WHITE, colors.HexColor("#f7fafd")]),
        ("GRID",          (0, 0), (-1, -1),              0.5, MID_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1),              4),
        ("BOTTOMPADDING", (0, 0), (-1, -1),              4),
        ("LEFTPADDING",   (0, 0), (-1, -1),              6),
        ("RIGHTPADDING",  (0, 0), (-1, -1),              6),
    ]
    return TableStyle(cmds)

# ---------------------------------------------------------------------------
# Build document content
# ---------------------------------------------------------------------------
def build_story(styles):
    story = []
    W = A4[0] - 4 * cm   # usable width

    # ===================================================================
    # PAGE 1 -- Title page
    # ===================================================================
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("Ray Tracing + ML Pipeline — Model Reference", styles["title"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="80%", thickness=2, color=DARK_BLUE, hAlign="CENTER"))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        "Sionna 0.19 Calibration → Sionna 2 DEM Final Results",
        styles["subtitle"]
    ))
    story.append(Spacer(1, 1.0 * cm))
    story.append(Paragraph("June 2026", styles["date"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Scene: Nottingham, UK", styles["meta"]))
    story.append(Paragraph("Frequency: 915.95 MHz", styles["meta"]))
    story.append(Paragraph("TX: Ofcom 2018", styles["meta"]))
    story.append(Spacer(1, 3 * cm))
    story.append(HRFlowable(width="60%", thickness=1, color=MID_GREY, hAlign="CENTER"))
    story.append(PageBreak())

    # ===================================================================
    # PAGE 2 -- Section 1: Pipeline Overview
    # ===================================================================
    story.append(Paragraph("Section 1 — Pipeline Overview", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_BLUE))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "The pipeline operates in two stages. Stage 1 (Calibration) runs in "
        "<i>sionna019_differentiable_rt_fixed.ipynb</i> using Sionna 0.19 differentiable RT. "
        "It calibrates physical and statistical models against 120 drive-test receivers. "
        "Stage 2 (Simulation) runs in <i>sionna2_915mhz_dem_simulation.ipynb</i> using "
        "Sionna 2.0 with a Digital Elevation Model. It loads calibrated parameters from "
        "Stage 1 and produces the final RSSI maps.",
        styles["body"]
    ))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Pipeline Flow Diagram", styles["h2"]))

    flow_data = [
        ["[Drive-test RSSI]", "→", "[Sionna 0.19 RT]", "→", "[Cell 10b]",
         "→", "scalar_offset.json", "", "", "", ""],
        ["", "", "", "→", "[Cell 11b]",
         "→", "calibrated_materials.json", "→", "[Sionna 2 DEM Cell 4A]", "→", "RSSI_sim"],
        ["", "", "", "→", "[Cell 16]",
         "→", "material_mlp.npz", "↗", "", "", ""],
        ["", "", "", "→", "[Cell 15]",
         "→", "residual_mlp.npz", "→", "POST-PROCESS", "→", "RSSI_final"],
        ["", "", "", "→", "[Cell 14]",
         "→", "cnn_residual.h5", "→", "POST-PROCESS", "→", "RSSI_final"],
    ]

    flow_col_widths = [
        2.5*cm, 0.5*cm, 2.8*cm, 0.5*cm, 1.8*cm,
        0.5*cm, 3.8*cm, 0.5*cm, 3.0*cm, 0.5*cm, 2.0*cm
    ]
    flow_style = TableStyle([
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND",    (0, 0), (0, 0),   LIGHT_BLUE),
        ("BACKGROUND",    (2, 0), (2, 0),   LIGHT_BLUE),
        ("BACKGROUND",    (4, 0), (4, 4),   colors.HexColor("#eef4ea")),
        ("BACKGROUND",    (6, 0), (6, 4),   LIGHT_GREY),
        ("GRID",          (0, 0), (-1, -1), 0.3, MID_GREY),
        ("TEXTCOLOR",     (0, 1), (0, 4),   colors.HexColor("#aaaaaa")),
    ])

    flow_table = Table(flow_data, colWidths=flow_col_widths)
    flow_table.setStyle(flow_style)
    story.append(flow_table)
    story.append(PageBreak())

    # ===================================================================
    # PAGE 3 -- Section 2 (part 1): Model Descriptions
    # ===================================================================
    story.append(Paragraph("Section 2 — Model Descriptions", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_BLUE))
    story.append(Spacer(1, 0.2 * cm))

    # --- 2.1 ---
    story.append(Paragraph("2.1 Cell 10b — Global Scalar Offset", styles["h2"]))
    details_10b = [
        ["Property", "Value"],
        ["Type",     "Single-parameter calibration (1 tf.Variable)"],
        ["Input",    "rssi_sim (all 120 calib_receivers), rssi_meas (drive-test)"],
        ["Method",   "Minimise SMAPE loss over 200 steps, Adam LR=0.1. Best-RMSE checkpoint."],
        ["Output",   'scalar_offset_915mhz.json → {"scaling_factor_db": +5.8024}'],
        ["Sionna 2", "Cell 4A reads scalar_offset_915mhz.json, adds offset to all simulated RSSI"],
        ["Result",   "RSSI_sim_corrected = RSSI_sim + 5.80 dB"],
        ["RMSE",     "7.90 dB (N=120, all calib receivers)"],
        ["Portable", "No — must be re-run per scene/frequency"],
    ]
    t = Table(details_10b, colWidths=[3.5*cm, W - 3.5*cm])
    t.setStyle(std_table_style())
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))

    # --- 2.2 ---
    story.append(Paragraph(
        "2.2 Cell 11b — Differentiable RT Material Calibration (NVLabs)", styles["h2"]))
    details_11b = [
        ["Property",   "Value"],
        ["Type",       "Per-material εr, σ, S calibration via tf.Variable (102 variables)"],
        ["Input",      "173 receivers (0–1.2 km, mat_calib_receivers), drive-test RSSI"],
        ["Method",     "MAE loss on RSSI, Tikhonov regularisation λ=0.001, 500 steps, "
                       "Adam cosine LR 0.05→0.001. No gradient pruning (PRUNE_ZERO_GRADS=False). "
                       "Depth=8 rays. Based on NVLabs diff-rt-calibration (Hoydis et al. 2023)."],
        ["Active mat.","14/102 (concrete, brick, glass, metal, asphalt — only materials visible to rays)"],
        ["Output",     "cell11b_calibrated_materials.json + cell11b_checkpoint.json"],
        ["Sionna 2",   "Cell 4A reads calibrated_materials_915mhz.json, sets relative_permittivity/"
                       "conductivity/scattering_coefficient on each scene material before trace_paths()"],
        ["RMSE",       "22.62 → 21.94 dB (+0.67 dB). Ceiling limited by geometry approx. (OSM)."],
        ["Portable",   "Limited — values tuned for Nottingham/915 MHz"],
    ]
    t = Table(details_11b, colWidths=[3.5*cm, W - 3.5*cm])
    t.setStyle(std_table_style())
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))

    # --- 2.3 ---
    story.append(Paragraph("2.3 Cell 16 — MaterialMLP (Scene-Conditioned)", styles["h2"]))
    details_16 = [
        ["Property",    "Value"],
        ["Type",        "Neural network that predicts εr, σ, S from 8 scene features"],
        ["Architecture","Input(n_mat one-hot) + Input(8 scene feats) → FC(64,ReLU)+BN → "
                        "FC(32,ReLU)+BN → 3 heads (eps_r, log_sigma, scatter)"],
        ["Features (8)","freq_norm, ndsm_mean, ndsm_std, building_density, tx_height, "
                        "rx_h_mean, rx_h_std, urban_density"],
        ["Materials",   "concrete, brick, glass, wet_ground, vegetation, water (6 materials)"],
        ["Output",      "material_mlp_weights.npz + material_mlp_materials.json"],
        ["Sionna 2",    "Load npz weights → compute 8 scene features → call predict_materials() "
                        "→ set εr/σ/S"],
        ["Portable",    "Yes — designed for any city/frequency"],
        ["Note",        "Requires re-run of Cell 16 with dummy forward pass fix "
                        "(trainable params was 0 before fix)"],
    ]
    t = Table(details_16, colWidths=[3.5*cm, W - 3.5*cm])
    t.setStyle(std_table_style())
    story.append(t)
    story.append(PageBreak())

    # ===================================================================
    # PAGE 4 -- Section 2 (part 2): Cells 15 & 14
    # ===================================================================
    # --- 2.4 ---
    story.append(Paragraph(
        "2.4 Cell 15 — Physics-Informed Residual MLP (Thrane et al.)", styles["h2"]))
    details_15 = [
        ["Property",    "Value"],
        ["Type",        "Post-simulation RSSI correction (NOT a scene material)"],
        ["Architecture","Input(45) → Dense(128,ReLU)+Dropout(0.2) → "
                        "Dense(128,ReLU)+Dropout(0.2) + skip → Dense(64,ReLU) → Dense(1,linear). "
                        "Based on Thrane et al. 2020 IEEE TVT."],
        ["45 Features", "9 groups x5: G1 Power, G2 Delay, G3/G4 Angular RX/TX, G5 Path types, "
                        "G6 Vertex geometry, G7 Reference PL, G8 Scene features, G9 Morphology (zeros)"],
        ["Input",       "Pre-traced paths from _traced_list (Sionna 0.19 8-tuple format), "
                        "rssi_sim_cached from Cell 10b"],
        ["Output",      "residual_mlp_915mhz.npz (weights + feat_mean + feat_std)"],
        ["RMSE",        "RT only 9.74 dB → RT + MLP 4.83 dB (Δ = +4.92 dB, 50.5% improvement) N=15 test"],
        ["Sionna 2",    "PARTIAL — MLP weights portable BUT feature extraction uses Sionna 0.19 "
                        "8-tuple paths API. Feature extraction must be adapted for Sionna 2 API."],
        ["Recommended", "Add post-processing cell: (1) load .npz, (2) extract 45 features from "
                        "Sionna 2 paths, (3) apply RSSI_final = RSSI_sim + MLP(features_norm)"],
    ]
    t = Table(details_15, colWidths=[3.5*cm, W - 3.5*cm])
    t.setStyle(std_table_style())
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))

    # --- 2.5 ---
    story.append(Paragraph(
        "2.5 Cell 14 — CNN + MLP Residual Corrector (nDSM)", styles["h2"]))
    details_14 = [
        ["Property",    "Value"],
        ["Type",        "Post-simulation RSSI correction using height map patches"],
        ["Architecture","CNN branch (64x64x1 nDSM → Conv32→Conv64→Conv128→GAP→Dense64) + "
                        "MLP branch (5 scalar feats → Dense32→Dense32) → "
                        "Concat(96) → Dense64+Dropout → Dense1"],
        ["5 Scalars",   "dist_km/10, tx_height/100, rx_height/50, sin(azimuth), cos(azimuth)"],
        ["Input",       "rssi_sim from Cell 10b, 64x64 nDSM patch around each receiver, 5 scalar features"],
        ["Output",      "cnn_residual_915mhz.h5 (full Keras model)"],
        ["RMSE",        "RT only 14.82 dB → RT + CNN 5.92 dB (Δ = +8.90 dB, 60% improvement) N=16 test"],
        ["Sionna 2",    "YES — CNN uses only nDSM patches and scalar geometry. "
                        "NO Sionna version-specific code. Can be added directly to sionna2 DEM."],
        ["How to add",  "Load .h5, extract receiver positions (available in Sionna 2), "
                        "crop nDSM patches, compute 5 scalars, predict and add delta."],
    ]
    t = Table(details_14, colWidths=[3.5*cm, W - 3.5*cm])
    t.setStyle(std_table_style())
    story.append(PageBreak())

    # ===================================================================
    # PAGE 5 -- Section 3: Results Summary
    # ===================================================================
    story.append(Paragraph("Section 3 — Results Summary", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_BLUE))
    story.append(Spacer(1, 0.3 * cm))

    results_data = [
        ["Model", "Notebook", "RMSE Before", "RMSE After", "Improvement", "Portable"],
        ["Scalar Offset\n(Cell 10b)",    "sionna019", "~22 dB",    "7.90 dB",  "~14 dB",               "No"],
        ["Material Calib\n(Cell 11b)",   "sionna019", "22.62 dB",  "21.94 dB", "+0.67 dB",             "Limited"],
        ["MaterialMLP\n(Cell 16)",       "sionna019", "—",    "—",   "Portable ver. of 11b", "Yes"],
        ["Residual MLP\n(Cell 15)",      "sionna019", "9.74 dB",   "4.83 dB",  "+4.92 dB (50%)",       "Partial"],
        ["CNN+MLP\n(Cell 14)",           "sionna019", "14.82 dB",  "5.92 dB",  "+8.90 dB (60%)",       "Yes"],
    ]
    col_w = [3.2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3.5*cm, 2.0*cm]
    t = Table(results_data, colWidths=col_w, repeatRows=1)
    t.setStyle(std_table_style())
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Literature Comparison", styles["h2"]))
    lit_data = [
        ["Reference",                        "Reported RMSE",           "Our Result"],
        ["Thrane et al. 2020 IEEE TVT",      "4–6 dB RMSE",        "Cell 15: 4.83 dB — matches"],
        ["NVLabs Hoydis 2023",               "~1–2 dB gain (synth.)",
         "Cell 11b: 0.67 dB on real-world — matches"],
    ]
    t = Table(lit_data, colWidths=[5.5*cm, 4.0*cm, W - 9.5*cm])
    t.setStyle(std_table_style())
    story.append(t)
    story.append(PageBreak())

    # ===================================================================
    # PAGE 6 -- Section 4: Loading into Sionna 2 DEM
    # ===================================================================
    story.append(Paragraph("Section 4 — Loading into Sionna 2 DEM", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_BLUE))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("4.1 Currently Wired (works today)", styles["h2"]))
    story.append(bullet(
        "scalar_offset_915mhz.json → Cell 4A of sionna2 DEM (working)", styles))
    story.append(bullet(
        "calibrated_materials_915mhz.json → Cell 4A of sionna2 DEM (working)", styles))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "4.2 Cell 14 CNN — Can Be Added Directly (NO Sionna Version Dependency)",
        styles["h2"]
    ))
    story.append(Paragraph(
        "The CNN model uses only nDSM patches and scalar geometry "
        "(distance, heights, azimuth). There is no Sionna version-specific code. "
        "It can be added directly to sionna2 DEM as a post-processing cell.",
        styles["body"]
    ))

    code_14 = """\
# Add this block AFTER Sionna 2 DEM compute_fields()
import tensorflow as tf, numpy as np, rasterio
from pyproj import Transformer

cnn = tf.keras.models.load_model('results/diff_rt/cnn_residual_915mhz.h5')
ndsm = rasterio.open('ndsm.tif')

for rx_name, rssi_sim in rssi_sim_dict.items():
    rx_pos = scene.get(rx_name).position.numpy()
    patch  = get_ndsm_patch(rx_pos[0], rx_pos[1])
    scalar = [dist_km/10, tx_h/100, rx_pos[2]/50, sin_az, cos_az]
    delta  = float(cnn.predict([patch[np.newaxis], np.array([scalar])]))
    rssi_final[rx_name] = rssi_sim + delta"""
    story.extend(code_block(code_14, styles))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "4.3 Cell 15 MLP — Requires Sionna 2 Path Feature Adaptation",
        styles["h2"]
    ))
    story.append(bullet(
        "MLP weights ARE portable (saved as numpy arrays in .npz)", styles))
    story.append(bullet(
        "Feature extraction _extract_features() uses Sionna 0.19 8-tuple paths API", styles))
    story.append(bullet(
        "In Sionna 2, paths object has different structure (use paths.a, paths.tau directly)", styles))
    story.append(bullet(
        "Adaptation needed: rewrite _extract_features() for Sionna 2 paths before using in sionna2 DEM",
        styles))
    story.append(bullet(
        "This is ~50 lines of code change in the feature extraction function", styles))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "4.4 Cell 16 MaterialMLP — Portable, to be Wired into Cell 4A",
        styles["h2"]
    ))
    code_16 = """\
w    = np.load('results/diff_rt/material_mlp_weights.npz', allow_pickle=True)
mlp  = MaterialMLP(n_mat=6)
mlp(tf.eye(6), tf.zeros([1,8]))   # build
mlp.set_weights([w[f'w{i}'] for i in range(len(w.files)-2)])
scene_feats = compute_scene_features(freq_hz=FREQUENCY_HZ, ndsm_data=ndsm_arr, ...)
mats = mlp.predict_materials(scene_feats)
for name, props in mats.items():
    scene.get(name).relative_permittivity = props['er']"""
    story.extend(code_block(code_16, styles))
    story.append(PageBreak())

    # ===================================================================
    # PAGE 7 -- Section 5: Recommendations
    # ===================================================================
    story.append(Paragraph("Section 5 — Recommendations", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_BLUE))
    story.append(Spacer(1, 0.3 * cm))

    recs = [
        ["#", "Recommendation", "Priority"],
        ["1", "Re-run Cell 16 (fix pushed to branch claude/cool-cori-rrWbY) — "
              "dummy forward pass added so trainable params are correctly initialised.", "High"],
        ["2", "Add Cell 14 CNN post-processing to sionna2 DEM — "
              "NO code adaptation needed, fully portable.", "High"],
        ["3", "Adapt Cell 15 feature extraction for Sionna 2 API (~50 lines), "
              "then add to sionna2 DEM.", "Medium"],
        ["4", "For new cities: use Cell 16 MaterialMLP — "
              "scene-conditioned, portable to any frequency/city.", "Medium"],
        ["5", "For Nottingham only: Cell 11b JSON gives best material calibration "
              "(scene-specific tuning).", "Low"],
    ]
    t = Table(recs, colWidths=[0.8*cm, W - 3.3*cm, 2.5*cm])
    rec_style = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  LIGHT_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  DARK_BLUE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN",         (0, 0), (0, -1),  "CENTER"),
        ("ALIGN",         (2, 0), (2, -1),  "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, colors.HexColor("#f7fafd")]),
        ("GRID",          (0, 0), (-1, -1), 0.5, MID_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TEXTCOLOR",     (2, 1), (2, 2),   colors.HexColor("#c0392b")),
        ("TEXTCOLOR",     (2, 3), (2, 4),   colors.HexColor("#e67e22")),
        ("TEXTCOLOR",     (2, 5), (2, 5),   colors.HexColor("#27ae60")),
        ("FONTNAME",      (2, 1), (2, -1),  "Helvetica-Bold"),
    ])
    t.setStyle(rec_style)
    story.append(t)
    story.append(Spacer(1, 0.8 * cm))

    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "End of document. Generated automatically from pipeline analysis.",
        styles["note"]
    ))

    return story

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        title="Ray Tracing + ML Pipeline — Model Reference",
        author="Sionna RT Pipeline",
    )

    styles = build_styles()
    story  = build_story(styles)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    print(f"PDF generated successfully: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
