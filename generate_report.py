"""
generate_report.py
Generates a professional PDF report: Model_Pipeline_Report.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os

OUTPUT_PATH = "/home/user/Ray-Tracing---Sionna-RT/Model_Pipeline_Report.pdf"

# ── colours ──────────────────────────────────────────────────────────────────
DARK_BLUE   = colors.HexColor("#1a3a5c")
LIGHT_BLUE  = colors.HexColor("#e8f0f8")
LIGHT_GREY  = colors.HexColor("#f5f5f5")
MID_GREY    = colors.HexColor("#cccccc")
WHITE       = colors.white
BLACK       = colors.black

# ── styles ────────────────────────────────────────────────────────────────────
def build_styles():
    styles = {}

    styles["title"] = ParagraphStyle(
        "ReportTitle",
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=32,
        textColor=DARK_BLUE,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    styles["subtitle"] = ParagraphStyle(
        "ReportSubtitle",
        fontName="Helvetica",
        fontSize=14,
        leading=18,
        textColor=DARK_BLUE,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    styles["date_info"] = ParagraphStyle(
        "DateInfo",
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#444444"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    styles["h1"] = ParagraphStyle(
        "H1",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=DARK_BLUE,
        spaceBefore=18,
        spaceAfter=6,
    )
    styles["h2"] = ParagraphStyle(
        "H2",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=DARK_BLUE,
        spaceBefore=14,
        spaceAfter=4,
    )
    styles["body"] = ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=BLACK,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    styles["bullet"] = ParagraphStyle(
        "Bullet",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=BLACK,
        leftIndent=16,
        bulletIndent=4,
        spaceAfter=3,
    )
    styles["code"] = ParagraphStyle(
        "Code",
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=BLACK,
        backColor=LIGHT_GREY,
        leftIndent=8,
        rightIndent=8,
        spaceBefore=4,
        spaceAfter=4,
    )
    styles["table_header"] = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=DARK_BLUE,
        alignment=TA_CENTER,
    )
    styles["table_cell"] = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=BLACK,
    )
    styles["note"] = ParagraphStyle(
        "Note",
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#555555"),
        spaceAfter=4,
    )
    return styles


# ── footer / header canvas callback ──────────────────────────────────────────
FOOTER_TEXT = "Sionna RT Pipeline — Nottingham 915 MHz | Branch: claude/cool-cori-rrWbY"

def on_page(canvas, doc):
    canvas.saveState()
    page_w, page_h = A4
    canvas.setStrokeColor(DARK_BLUE)
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.6*cm, page_w - 2*cm, 1.6*cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(2*cm, 1.1*cm, FOOTER_TEXT)
    canvas.drawRightString(page_w - 2*cm, 1.1*cm, f"Page {doc.page}")
    canvas.restoreState()


def on_first_page(canvas, doc):
    canvas.saveState()
    page_w, _ = A4
    canvas.setStrokeColor(DARK_BLUE)
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.6*cm, page_w - 2*cm, 1.6*cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(2*cm, 1.1*cm, FOOTER_TEXT)
    canvas.restoreState()


# ── helpers ───────────────────────────────────────────────────────────────────
def h_rule(story):
    story.append(HRFlowable(width="100%", thickness=0.5, color=DARK_BLUE,
                            spaceAfter=4, spaceBefore=4))


def code_block(text, styles):
    """Return a Table that mimics a code block with grey background."""
    lines = text.strip("\n").split("\n")
    paras = []
    for line in lines:
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # preserve leading spaces with non-breaking spaces
        n_spaces = len(safe) - len(safe.lstrip())
        safe = "&nbsp;" * n_spaces + safe.lstrip()
        paras.append(Paragraph(safe, styles["code"]))
    t = Table([[p] for p in paras], colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("BOX",        (0, 0), (-1, -1), 0.5, MID_GREY),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 1),
    ]))
    return t


def bullet(text, styles):
    return Paragraph(f"&#x2022; &nbsp;{text}", styles["bullet"])


# ── content builders ──────────────────────────────────────────────────────────

def title_page(story, styles):
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph("Ray Tracing + ML Pipeline", styles["title"]))
    story.append(Paragraph("Model Reference", styles["title"]))
    story.append(Spacer(1, 0.5*cm))
    h_rule(story)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "Sionna 0.19 Calibration &#x2192; Sionna 2 DEM Final Results",
        styles["subtitle"]))
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("June 2026", styles["date_info"]))
    story.append(Spacer(1, 0.4*cm))

    info_data = [
        ["Scene:", "Nottingham, UK"],
        ["Frequency:", "915.95 MHz"],
        ["TX Source:", "Ofcom 2018"],
    ]
    info_table = Table(info_data, colWidths=[4*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",  (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",  (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (0, 0), (-1, -1), DARK_BLUE),
        ("ALIGN",     (0, 0), (0, -1), "RIGHT"),
        ("ALIGN",     (1, 0), (1, -1), "LEFT"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(PageBreak())


def section1(story, styles):
    story.append(Paragraph("1 &#x2014; Pipeline Overview", styles["h1"]))
    h_rule(story)
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph(
        "The pipeline operates in two stages. Stage 1 (Calibration) runs in "
        "<b>sionna019_differentiable_rt_fixed.ipynb</b> using Sionna 0.19 differentiable RT. "
        "It calibrates physical and statistical models against 120 drive-test receivers. "
        "Stage 2 (Simulation) runs in <b>sionna2_915mhz_dem_simulation.ipynb</b> using "
        "Sionna 2.0 with a Digital Elevation Model. It loads calibrated parameters from "
        "Stage 1 and produces the final RSSI maps.",
        styles["body"]))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Pipeline Flow Diagram", styles["h2"]))
    story.append(Spacer(1, 0.2*cm))

    flow_data = [
        ["[Drive-test RSSI]", "->", "[Sionna 0.19 RT]", "->", "[Cell 10b]",  "->", "scalar_offset.json", "", ""],
        ["",                  "",   "",                  "->", "[Cell 11b]",  "->", "calibrated_materials.json", "->", "[Sionna 2 DEM\nCell 4A] -> RSSI_sim"],
        ["",                  "",   "",                  "->", "[Cell 16]",   "->", "material_mlp.npz",          "^/", ""],
        ["",                  "",   "",                  "->", "[Cell 15]",   "->", "residual_mlp.npz",          "->", "POST-PROCESS\n-> RSSI_final"],
        ["",                  "",   "",                  "->", "[Cell 14]",   "->", "cnn_residual.h5",           "->", "POST-PROCESS\n-> RSSI_final"],
    ]

    col_w = [3.0*cm, 0.6*cm, 2.8*cm, 0.6*cm, 2.0*cm, 0.6*cm, 3.6*cm, 0.6*cm, 4.2*cm]
    flow_table = Table(flow_data, colWidths=col_w)
    flow_table.setStyle(TableStyle([
        ("FONTNAME",     (0, 0), (-1, -1), "Courier"),
        ("FONTSIZE",     (0, 0), (-1, -1), 7.5),
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_GREY),
        ("BOX",          (0, 0), (-1, -1), 0.5, MID_GREY),
        ("INNERGRID",    (0, 0), (-1, -1), 0.25, MID_GREY),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("ALIGN",        (1, 0), (1, -1), "CENTER"),
        ("ALIGN",        (3, 0), (3, -1), "CENTER"),
        ("ALIGN",        (5, 0), (5, -1), "CENTER"),
        ("ALIGN",        (7, 0), (7, -1), "CENTER"),
        ("TEXTCOLOR",    (4, 0), (4, -1), DARK_BLUE),
        ("FONTNAME",     (4, 0), (4, -1), "Courier-Bold"),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 0.3*cm))


def section2(story, styles):
    story.append(Paragraph("2 &#x2014; Model Descriptions", styles["h1"]))
    h_rule(story)

    # 2.1
    story.append(Paragraph("2.1 Cell 10b &#x2014; Global Scalar Offset", styles["h2"]))
    for b in [
        "<b>Type:</b> Single-parameter calibration (1 tf.Variable)",
        "<b>Input:</b> rssi_sim (all 120 calib_receivers), rssi_meas (drive-test)",
        "<b>Method:</b> Minimise SMAPE loss over 200 steps, Adam LR=0.1. Best-RMSE checkpoint.",
        '<b>Output:</b> scalar_offset_915mhz.json &#x2192; {"scaling_factor_db": +5.8024}',
        "<b>Loaded in Sionna 2 DEM:</b> Cell 4A reads scalar_offset_915mhz.json, adds offset to all simulated RSSI",
        "<b>Result:</b> RSSI_sim_corrected = RSSI_sim + 5.80 dB",
        "<b>RMSE:</b> 7.90 dB (N=120, all calib receivers)",
        "<b>Portable to other scenes:</b> No &#x2014; must be re-run per scene/frequency",
    ]:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 0.3*cm))

    # 2.2
    story.append(Paragraph("2.2 Cell 11b &#x2014; Differentiable RT Material Calibration (NVLabs)", styles["h2"]))
    for b in [
        "<b>Type:</b> Per-material εr, σ, S calibration via tf.Variable (102 variables)",
        "<b>Input:</b> 173 receivers (0&#x2013;1.2 km, mat_calib_receivers), drive-test RSSI",
        "<b>Method:</b> MAE loss on RSSI, Tikhonov regularisation λ=0.001, 500 steps, Adam cosine LR 0.05&#x2192;0.001. "
        "No gradient pruning (PRUNE_ZERO_GRADS=False). Depth=8 rays. Based on NVLabs diff-rt-calibration (Hoydis et al. 2023).",
        "<b>Active materials:</b> 14/102 (concrete, brick, glass, metal, asphalt &#x2014; only materials visible to rays)",
        "<b>Output:</b> cell11b_calibrated_materials.json + cell11b_checkpoint.json",
        "<b>Loaded in Sionna 2 DEM:</b> Cell 4A reads calibrated_materials_915mhz.json, sets "
        "relative_permittivity/conductivity/scattering_coefficient on each scene material before trace_paths()",
        "<b>RMSE improvement:</b> 22.62 &#x2192; 21.94 dB (+0.67 dB). Ceiling limited by geometry approximations (OSM).",
        "<b>Portable to other scenes:</b> Limited &#x2014; values tuned for Nottingham/915 MHz",
    ]:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 0.3*cm))

    # 2.3
    story.append(Paragraph("2.3 Cell 16 &#x2014; MaterialMLP (Scene-Conditioned)", styles["h2"]))
    for b in [
        "<b>Type:</b> Neural network that predicts εr, σ, S from 8 scene features",
        "<b>Architecture:</b> Input(n_mat one-hot) + Input(8 scene feats) &#x2192; FC(64,ReLU)+BN &#x2192; FC(32,ReLU)+BN &#x2192; 3 heads (eps_r, log_sigma, scatter)",
        "<b>Input features (8):</b> freq_norm, ndsm_mean, ndsm_std, building_density, tx_height, rx_h_mean, rx_h_std, urban_density",
        "<b>Materials:</b> concrete, brick, glass, wet_ground, vegetation, water (6 materials)",
        "<b>Output:</b> material_mlp_weights.npz + material_mlp_materials.json",
        "<b>Loaded in Sionna 2 DEM:</b> Load npz weights &#x2192; compute 8 scene features for new scene &#x2192; call predict_materials() &#x2192; set εr/σ/S on scene materials",
        "<b>Portable to other scenes:</b> Yes &#x2014; designed for any city/frequency",
        "<b>Note:</b> Requires re-run of Cell 16 with dummy forward pass fix (trainable params was 0 before fix)",
    ]:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 0.3*cm))

    story.append(PageBreak())

    # 2.4
    story.append(Paragraph("2.4 Cell 15 &#x2014; Physics-Informed Residual MLP (Thrane et al.)", styles["h2"]))
    for b in [
        "<b>Type:</b> Post-simulation RSSI correction (NOT a scene material)",
        "<b>Architecture:</b> Input(45) &#x2192; Dense(128,ReLU)+Dropout(0.2) &#x2192; Dense(128,ReLU)+Dropout(0.2) + skip &#x2192; Dense(64,ReLU) &#x2192; Dense(1,linear). Based on Thrane et al. 2020 IEEE TVT.",
    ]:
        story.append(bullet(b, styles))

    story.append(Paragraph("45 Features (9 groups x 5):", styles["body"]))
    feat_data = [
        [Paragraph("<b>Group</b>", styles["table_header"]),
         Paragraph("<b>Features</b>", styles["table_header"])],
        ["G1: Power", "Strongest path, total power, dominant ratio, power spread, path count"],
        ["G2: Delay", "Min/max/mean delay, RMS delay spread, coherence BW"],
        ["G3/G4: Angular RX/TX", "Mean/std azimuth+elevation, angular spread"],
        ["G5: Path types", "LOS flag, specular/diffuse/diffraction counts, LOS power fraction"],
        ["G6: Vertex geometry", "Mean/max interaction height, mean path length"],
        ["G7: Reference PL", "FSPL, distance, log-distance, TX-RX height diff"],
        ["G8: Scene features", "Building density, mean height, terrain std"],
        ["G9: Morphology", "Reserved zeros — nDSM not loaded"],
    ]
    feat_table = Table(feat_data, colWidths=[4.5*cm, 13*cm])
    feat_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), LIGHT_BLUE),
        ("FONTNAME",      (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (1, 1), (1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("BOX",           (0, 0), (-1, -1), 0.5, DARK_BLUE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.25, MID_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
    ]))
    story.append(feat_table)
    story.append(Spacer(1, 0.2*cm))

    for b in [
        "<b>Input:</b> Pre-traced paths from _traced_list (Sionna 0.19 8-tuple format), rssi_sim_cached from Cell 10b",
        "<b>Output:</b> residual_mlp_915mhz.npz (weights + feat_mean + feat_std)",
        "<b>RMSE:</b> RT only 9.74 dB &#x2192; RT + MLP 4.83 dB (Delta = +4.92 dB, 50.5% improvement) N=15 test",
        "<b>Sionna 2 DEM compatibility:</b> PARTIAL &#x2014; MLP weights are portable BUT the 45-feature extraction code "
        "uses Sionna 0.19 paths API (8-tuple). Sionna 2 has different paths structure. "
        "Feature extraction must be adapted for Sionna 2 API before applying.",
        "<b>Recommended approach:</b> Add a post-processing cell in sionna2 DEM that: "
        "(1) loads residual_mlp_915mhz.npz, "
        "(2) extracts same 45 features from Sionna 2 paths, "
        "(3) applies RSSI_final = RSSI_sim + MLP(features_norm)",
    ]:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 0.3*cm))

    # 2.5
    story.append(Paragraph("2.5 Cell 14 &#x2014; CNN + MLP Residual Corrector (nDSM)", styles["h2"]))
    for b in [
        "<b>Type:</b> Post-simulation RSSI correction using height map patches",
        "<b>Architecture:</b> CNN branch (64x64x1 nDSM patch &#x2192; Conv32&#x2192;Conv64&#x2192;Conv128&#x2192;GAP&#x2192;Dense64) + "
        "MLP branch (5 scalar feats &#x2192; Dense32&#x2192;Dense32) &#x2192; Concat(96) &#x2192; Dense64+Dropout &#x2192; Dense1",
        "<b>5 Scalar features:</b> dist_km/10, tx_height/100, rx_height/50, sin(azimuth), cos(azimuth)",
        "<b>Input:</b> rssi_sim from Cell 10b, 64x64 nDSM patch around each receiver, 5 scalar features",
        "<b>Output:</b> cnn_residual_915mhz.h5 (full Keras model)",
        "<b>RMSE:</b> RT only 14.82 dB &#x2192; RT + CNN 5.92 dB (Delta = +8.90 dB, 60% improvement) N=16 test",
        "<b>Sionna 2 DEM compatibility:</b> YES &#x2014; CNN uses only nDSM patches and scalar geometry "
        "(distance, heights, azimuth). NO Sionna version-specific code. Can be added directly to sionna2 DEM as a post-processing cell.",
        "<b>How to add:</b> Load cnn_residual_915mhz.h5, extract receiver positions (available in Sionna 2), "
        "crop nDSM patches, compute 5 scalars, predict and add delta.",
    ]:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 0.3*cm))


def section3(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("3 &#x2014; Results Summary", styles["h1"]))
    h_rule(story)
    story.append(Spacer(1, 0.2*cm))

    hdr = [
        Paragraph("<b>Model</b>", styles["table_header"]),
        Paragraph("<b>Notebook</b>", styles["table_header"]),
        Paragraph("<b>RMSE Before</b>", styles["table_header"]),
        Paragraph("<b>RMSE After</b>", styles["table_header"]),
        Paragraph("<b>Improvement</b>", styles["table_header"]),
        Paragraph("<b>Portable</b>", styles["table_header"]),
    ]
    rows = [
        hdr,
        ["Scalar Offset\n(Cell 10b)", "sionna019", "~22 dB", "7.90 dB", "~14 dB", "No"],
        ["Material Calib\n(Cell 11b)", "sionna019", "22.62 dB", "21.94 dB", "+0.67 dB", "Limited"],
        ["MaterialMLP\n(Cell 16)", "sionna019", "---", "---", "Portable ver. of 11b", "Yes"],
        ["Residual MLP\n(Cell 15)", "sionna019", "9.74 dB", "4.83 dB", "+4.92 dB (50%)", "Partial"],
        ["CNN+MLP\n(Cell 14)", "sionna019", "14.82 dB", "5.92 dB", "+8.90 dB (60%)", "Yes"],
    ]

    col_w = [3.5*cm, 2.8*cm, 2.5*cm, 2.5*cm, 3.8*cm, 2.4*cm]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), LIGHT_BLUE),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("BOX",           (0, 0), (-1, -1), 0.75, DARK_BLUE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.25, MID_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("ALIGN",         (2, 0), (4, -1), "CENTER"),
        ("ALIGN",         (5, 0), (5, -1), "CENTER"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("FONTNAME",      (0, 1), (0, -1), "Helvetica-Bold"),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Literature Comparison", styles["h2"]))
    for b in [
        "<b>Thrane et al. 2020 IEEE TVT:</b> 4&#x2013;6 dB RMSE &#x2014; our Cell 15: 4.83 dB matches",
        "<b>NVLabs Hoydis 2023:</b> ~1&#x2013;2 dB gain from material calib on synthetic &#x2014; our: 0.67 dB on real-world matches",
    ]:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 0.3*cm))


def section4(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("4 &#x2014; Loading into Sionna 2 DEM", styles["h1"]))
    h_rule(story)
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("4.1 Currently wired (works today)", styles["h2"]))
    for b in [
        "scalar_offset_915mhz.json &#x2192; Cell 4A of sionna2 DEM (working)",
        "calibrated_materials_915mhz.json &#x2192; Cell 4A of sionna2 DEM (working)",
    ]:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("4.2 Cell 14 CNN &#x2014; can be added directly (NO Sionna version dependency)", styles["h2"]))
    cnn_code = (
        "# Add this block AFTER Sionna 2 DEM compute_fields()\n"
        "import tensorflow as tf, numpy as np, rasterio\n"
        "from pyproj import Transformer\n"
        "\n"
        "cnn = tf.keras.models.load_model('results/diff_rt/cnn_residual_915mhz.h5')\n"
        "ndsm = rasterio.open('ndsm.tif')\n"
        "\n"
        "for rx_name, rssi_sim in rssi_sim_dict.items():\n"
        "    rx_pos = scene.get(rx_name).position.numpy()\n"
        "    patch  = get_ndsm_patch(rx_pos[0], rx_pos[1])\n"
        "    scalar = [dist_km/10, tx_h/100, rx_pos[2]/50, sin_az, cos_az]\n"
        "    delta  = float(cnn.predict([patch[np.newaxis], np.array([scalar])]))\n"
        "    rssi_final[rx_name] = rssi_sim + delta"
    )
    story.append(code_block(cnn_code, styles))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("4.3 Cell 15 MLP &#x2014; requires Sionna 2 path feature adaptation", styles["h2"]))
    for b in [
        "MLP weights ARE portable (saved as numpy arrays in .npz)",
        "Feature extraction function _extract_features() uses Sionna 0.19 8-tuple paths API",
        "In Sionna 2, paths object has different structure (use paths.a, paths.tau directly)",
        "Adaptation needed: rewrite _extract_features() for Sionna 2 paths before using in sionna2 DEM",
        "This is ~50 lines of code change in the feature extraction function",
    ]:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("4.4 Cell 16 MaterialMLP &#x2014; portable, to be wired into Cell 4A", styles["h2"]))
    mlp_code = (
        "w    = np.load('results/diff_rt/material_mlp_weights.npz', allow_pickle=True)\n"
        "mlp  = MaterialMLP(n_mat=6)\n"
        "mlp(tf.eye(6), tf.zeros([1,8]))   # build\n"
        "mlp.set_weights([w[f'w{i}'] for i in range(len(w.files)-2)])\n"
        "scene_feats = compute_scene_features(freq_hz=FREQUENCY_HZ, ndsm_data=ndsm_arr, ...)\n"
        "mats = mlp.predict_materials(scene_feats)\n"
        "for name, props in mats.items():\n"
        "    scene.get(name).relative_permittivity = props['er']"
    )
    story.append(code_block(mlp_code, styles))
    story.append(Spacer(1, 0.3*cm))


def section5(story, styles):
    story.append(Paragraph("5 &#x2014; Recommendations", styles["h1"]))
    h_rule(story)
    story.append(Spacer(1, 0.2*cm))

    recs = [
        "<b>Re-run Cell 16</b> (fix pushed to branch claude/cool-cori-rrWbY) &#x2014; dummy forward pass added",
        "<b>Add Cell 14 CNN post-processing to sionna2 DEM</b> &#x2014; NO code adaptation needed, fully portable",
        "<b>Adapt Cell 15 feature extraction for Sionna 2 API</b> &#x2014; ~50 lines, then add to sionna2 DEM",
        "<b>For new cities:</b> use Cell 16 MaterialMLP (scene-conditioned, portable to any frequency/city)",
        "<b>For Nottingham only:</b> Cell 11b JSON gives best material calibration (scene-specific tuning)",
    ]
    for i, rec in enumerate(recs, 1):
        story.append(Paragraph(f"{i}.&nbsp;&nbsp;{rec}", styles["bullet"]))
    story.append(Spacer(1, 0.5*cm))


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    styles = build_styles()

    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2.5*cm,
        title="Ray Tracing + ML Pipeline — Model Reference",
        author="Sionna RT Pipeline",
    )

    story = []
    title_page(story, styles)
    section1(story, styles)
    section2(story, styles)
    section3(story, styles)
    section4(story, styles)
    section5(story, styles)

    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_page)
    print(f"PDF generated successfully: {OUTPUT_PATH}")
    print(f"File size: {os.path.getsize(OUTPUT_PATH):,} bytes")


if __name__ == "__main__":
    main()
