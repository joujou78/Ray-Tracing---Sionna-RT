"""
Cell 11c — CDF Evaluation: Path Loss Error + Channel Gain RAE/SMAPE
====================================================================
Run AFTER Cell 11b completes.
Requires in memory:
  - pl_sim_pre_11b   : PL_sim at step 0  (before training)
  - pl_sim_final_11b : PL_sim after training
  - pl_meas_11b      : PL_meas matched to Cell 11b valid pairs
  - pl_sim_10b       : PL_sim from Cell 10b
  - pl_meas_10b      : PL_meas from Cell 10b
  - _best_sf         : best-RMSE scalar from Cell 10b
  - rmse_pre_11b     : RMSE before training (32.65 dB)
  - rmse_final_11b   : RMSE after training (fill when known)
  - OUTPUT_DIR       : output directory path
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import os

# ── Colour palette (matches FYP presentation theme) ──────────────────────
C_BG      = '#0D1B2A'
C_PANEL   = '#112A40'
C_GRID    = '#1E3A52'
C_ORANGE  = '#FF9F1C'   # ITU
C_CYAN    = '#90E0EF'   # Scalar
C_GREEN   = '#2DCB7F'   # Learned
C_WHITE   = 'white'


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def pl_to_gain(pl_db):
    """Path loss dB → linear channel gain (dimensionless)."""
    return np.power(10.0, -np.asarray(pl_db, dtype=np.float64) / 10.0)


def rae(g_sim, g_meas):
    """Relative Absolute Error: |G_sim - G_meas| / |G_meas|."""
    return np.abs(g_sim - g_meas) / (np.abs(g_meas) + 1e-30)


def smape_arr(g_sim, g_meas):
    """SMAPE per sample (×100 = %)."""
    return 100.0 * np.abs(g_sim - g_meas) / (
        np.abs(g_sim) + np.abs(g_meas) + 1e-30)


def plot_cdf_line(ax, data, label, color, linestyle='-', mark_median=True):
    data_s = np.sort(np.asarray(data))
    cdf    = np.arange(1, len(data_s) + 1) / len(data_s)
    ax.plot(data_s, cdf, color=color, linestyle=linestyle,
            linewidth=2.2, label=label)
    if mark_median:
        med = np.median(data_s)
        ax.axvline(med, color=color, linestyle=':', alpha=0.45, linewidth=1.2)


def style_ax(ax, xlabel, title, xlim):
    ax.set_facecolor(C_PANEL)
    ax.set_xlabel(xlabel, color=C_WHITE, fontsize=9)
    ax.set_ylabel('CDF', color=C_WHITE, fontsize=10)
    ax.set_title(title, color=C_WHITE, fontsize=11, fontweight='bold')
    ax.tick_params(colors=C_WHITE)
    for spine in ax.spines.values():
        spine.set_color(C_GRID)
    ax.set_ylim(0, 1.02)
    ax.set_xlim(*xlim)
    ax.grid(True, color=C_GRID, linestyle='--', alpha=0.6)
    ax.legend(facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_WHITE, fontsize=9)


# ═════════════════════════════════════════════════════════════════════════════
# PLOT 1 — CDF of Absolute Path Loss Error
# ═════════════════════════════════════════════════════════════════════════════

def plot_pl_error_cdf():
    errors_itu    = np.abs(pl_sim_pre_11b   - pl_meas_11b)
    errors_scalar = np.abs((np.asarray(pl_sim_10b) + _best_sf) - pl_meas_10b)
    errors_learned= np.abs(pl_sim_final_11b - pl_meas_11b)

    rmse_itu     = float(np.sqrt(np.mean((pl_sim_pre_11b    - pl_meas_11b)**2)))
    rmse_scalar  = float(np.sqrt(np.mean(((np.asarray(pl_sim_10b)+_best_sf) - pl_meas_10b)**2)))
    rmse_learned = float(np.sqrt(np.mean((pl_sim_final_11b  - pl_meas_11b)**2)))

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor(C_BG)

    plot_cdf_line(ax, errors_itu,     f'ITU-R P.2040-2  RMSE={rmse_itu:.1f} dB',    C_ORANGE)
    plot_cdf_line(ax, errors_scalar,  f'Scalar offset   RMSE={rmse_scalar:.1f} dB',  C_CYAN, '--')
    plot_cdf_line(ax, errors_learned, f'Learned mats    RMSE={rmse_learned:.1f} dB', C_GREEN)

    # 10 dB reference line
    ax.axvline(10, color='#FF4D6D', linestyle='--', alpha=0.5, linewidth=1)
    ax.text(10.2, 0.12, '10 dB', color='#FF4D6D', fontsize=8)

    style_ax(ax,
             xlabel='Absolute Path Loss Error  |PL_sim − PL_meas|  (dB)',
             title='CDF of Path Loss Prediction Error — Calibration Stages',
             xlim=(0, 40))

    out = os.path.join(OUTPUT_DIR, 'cdf_pl_error_comparison.png')
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.show()
    print(f'Saved → {out}')
    return rmse_itu, rmse_scalar, rmse_learned


# ═════════════════════════════════════════════════════════════════════════════
# PLOT 2 — CDF of Channel Gain RAE + SMAPE
# ═════════════════════════════════════════════════════════════════════════════

def plot_channel_gain_cdf():
    G_meas_11b = pl_to_gain(pl_meas_11b)
    G_meas_10b = pl_to_gain(pl_meas_10b)

    G_sim_itu     = pl_to_gain(pl_sim_pre_11b)
    G_sim_scalar  = pl_to_gain(np.asarray(pl_sim_10b) + _best_sf)
    G_sim_learned = pl_to_gain(pl_sim_final_11b)

    curves = [
        (rae(G_sim_itu,     G_meas_11b), smape_arr(G_sim_itu,     G_meas_11b),
         'ITU-R P.2040-2 (initial)', C_ORANGE, '-'),
        (rae(G_sim_scalar,  G_meas_10b), smape_arr(G_sim_scalar,  G_meas_10b),
         f'Scalar offset  sf={_best_sf:+.2f} dB', C_CYAN, '--'),
        (rae(G_sim_learned, G_meas_11b), smape_arr(G_sim_learned, G_meas_11b),
         'Learned materials (Cell 11b)', C_GREEN, '-'),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor(C_BG)

    for rae_v, smape_v, label, color, ls in curves:
        plot_cdf_line(ax1, rae_v,   label, color, ls)
        plot_cdf_line(ax2, smape_v, label, color, ls)

    # RAE = 1.0 reference (100% error ≈ 3 dB)
    ax1.axvline(1.0, color='#FF4D6D', linestyle='--', alpha=0.5, linewidth=1)
    ax1.text(1.05, 0.08, 'RAE=1.0\n(3 dB)', color='#FF4D6D', fontsize=7.5)

    style_ax(ax1,
             xlabel='Relative Absolute Error  |G_sim−G_meas| / |G_meas|',
             title='Channel Gain CDF — RAE (linear power)',
             xlim=(0, 5))
    ax1.xaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, _: f'{x:.0f}×'))

    style_ax(ax2,
             xlabel='SMAPE (%)   100 × |G_sim−G_meas| / (|G_sim|+|G_meas|)',
             title='Channel Gain CDF — SMAPE',
             xlim=(0, 100))

    # Summary table
    rows = []
    for rae_v, smape_v, label, _, _ in curves:
        rows.append({
            'Model':          label,
            'Median RAE':     f'{np.median(rae_v):.3f}×',
            '90th pct RAE':   f'{np.percentile(rae_v, 90):.3f}×',
            'Mean SMAPE (%)': f'{np.mean(smape_v):.1f}',
            'Median SMAPE (%)': f'{np.median(smape_v):.1f}',
        })
    df = pd.DataFrame(rows)
    print('\nChannel Gain Error Summary:')
    print(df.to_string(index=False))

    out = os.path.join(OUTPUT_DIR, 'cdf_channel_gain_rae_smape.png')
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.show()
    print(f'Saved → {out}')


# ═════════════════════════════════════════════════════════════════════════════
# RUN BOTH PLOTS
# ═════════════════════════════════════════════════════════════════════════════

print('=' * 65)
print('Cell 11c — CDF Evaluation')
print('=' * 65)
rmse_itu, rmse_scalar, rmse_learned = plot_pl_error_cdf()
plot_channel_gain_cdf()

print('\nSummary:')
print(f'  ITU-R initial  RMSE : {rmse_itu:.2f} dB')
print(f'  Scalar offset  RMSE : {rmse_scalar:.2f} dB  (sf={_best_sf:+.2f} dB)')
print(f'  Learned mats   RMSE : {rmse_learned:.2f} dB')
print(f'  RMSE improvement    : {rmse_itu - rmse_learned:+.2f} dB  (ITU → Learned)')
