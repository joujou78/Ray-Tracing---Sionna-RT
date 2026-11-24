"""
ITU-R P.1812-8 basic transmission loss, vectorised over many paths.

Design
------
Coverage maps are computed on radials. All radials share one distance grid
``d`` (km), and every sample ``j`` along a radial is the receiver end of its
own path ``0..j``. This module evaluates P.1812 for a *batch* of radials
(B) and a *set of endpoint indices* (J) in one shot, using (B, J, n) masked
arrays. A single point-to-point path is just B = 1, J = [n - 1], so the
probe/profile view and the coverage map share exactly the same code.

Scope and simplifications (stated, not hidden)
----------------------------------------------
* Land paths only: radio-climatic zone 4 (inland) along the whole path, so
  omega = 0 and dtm = dlm = d. Sea / coastal paths are not modelled yet.
* Terminal clutter: P.1812-8 no longer applies a terminal clutter loss; the
  representative clutter heights R only modify the profile used by the
  diffraction model (g = h + R), exactly as in the Recommendation.
* Location variability: Lloc = -I(pL/100) * sigmaL, sigmaL supplied by the
  caller (default 0 dB, i.e. median location).

Equation numbers in comments refer to Rec. ITU-R P.1812-8 (09/2025).
The implementation is cross-checked against the Ofcom/ITU-R WP3M reference
Python implementation (Py1812) in ``tests/test_p1812_reference.py``.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

R_EARTH_KM = 6371.0
NEG_INF = -np.inf

# Polarisation codes (same convention as the Recommendation software)
POL_H = 1
POL_V = 2


@dataclass
class P1812Params:
    """Radio and climatic parameters shared by every path in a batch."""

    f_ghz: float            # frequency, GHz (0.03 - 6)
    htg: float              # Tx antenna height above ground, m
    hrg: float              # Rx antenna height above ground, m
    p: float = 50.0         # time percentage, 1 - 50 %
    pl: float = 50.0        # location percentage, 1 - 99 %
    sigma_l: float = 0.0    # location variability std. dev., dB
    pol: int = POL_V        # 1 = horizontal, 2 = vertical
    dn: float = 45.0        # average radio-refractivity lapse rate, N-units/km
    n0: float = 325.0       # sea-level surface refractivity, N-units


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def inv_cum_norm(x):
    """Approximate inverse complementary cumulative normal, eqs (96)-(97)."""
    x = np.clip(np.asarray(x, dtype=float), 1e-6, 0.999999)

    def _t(y):
        return np.sqrt(-2.0 * np.log(y))

    def _c(z):
        t = _t(z)
        c0, c1, c2 = 2.515516698, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        return ((c2 * t + c1) * t + c0) / (((d3 * t + d2) * t + d1) * t + 1.0)

    lo = _t(x) - _c(x)
    hi = -(_t(1.0 - x) - _c(1.0 - x))
    return np.where(x <= 0.5, lo, hi)


def knife_edge_j(nu):
    """Single knife-edge diffraction loss J(nu), eq (12) (P.526)."""
    nu = np.asarray(nu, dtype=float)
    with np.errstate(invalid="ignore"):
        val = 6.9 + 20.0 * np.log10(np.sqrt((nu - 0.1) ** 2 + 1.0) + nu - 0.1)
    return np.where(nu > -0.78, val, 0.0)


def _mmax(x, mask):
    """Masked maximum along the last axis."""
    return np.where(mask, x, NEG_INF).max(axis=-1)


def _argmax_first(x, mask):
    return np.where(mask, x, NEG_INF).argmax(axis=-1)


def _argmax_last(x, mask):
    xm = np.where(mask, x, NEG_INF)[..., ::-1]
    return xm.shape[-1] - 1 - xm.argmax(axis=-1)


def free_space_loss(f_ghz, d_km, dh_m=0.0):
    """Free-space basic transmission loss including height difference, eq (8)."""
    dfs2 = np.asarray(d_km) ** 2 + (np.asarray(dh_m) / 1000.0) ** 2
    return 92.4 + 20.0 * np.log10(f_ghz) + 10.0 * np.log10(dfs2)


def beta0(phi_deg, dtm, dlm):
    """Time percentage beta0 for which refractivity lapse rates exceed 100 N/km, eqs (2)-(5)."""
    phi = np.abs(np.asarray(phi_deg, dtype=float))
    tau = 1.0 - np.exp(-(4.12e-4 * dlm ** 2.41))
    mu1 = (10 ** (-dtm / (16.0 - 6.6 * tau)) + 10 ** (-5.0 * (0.496 + 0.354 * tau))) ** 0.2
    mu1 = np.minimum(mu1, 1.0)
    mu4_lo = mu1 ** (-0.935 + 0.0176 * phi)
    b_lo = 10 ** (-0.015 * phi + 1.67) * mu1 * mu4_lo
    b_hi = 4.17 * mu1 * mu1 ** 0.3
    return np.where(phi <= 70.0, b_lo, b_hi)


# --------------------------------------------------------------------------
# Diffraction sub-models (vectorised)
# --------------------------------------------------------------------------
def bullington(di, dj, g, mask, hts, hrs, ap, lam, return_nu=False):
    """
    Bullington diffraction loss, eqs (13)-(21).

    di   : (1, 1, n) distances of profile points, km
    dj   : (1, J, 1) path lengths, km
    g    : (B, 1, n) or broadcastable profile heights (terrain + clutter), m
    mask : (1, J, n) True for intermediate points of each path
    hts, hrs : broadcastable to (B, J, 1), antenna heights amsl, m
    Returns Lbull with shape (B, J) (and numax for the knife-edge model).
    """
    ce = 1.0 / ap
    with np.errstate(divide="ignore", invalid="ignore"):
        curv = 500.0 * ce * di * (dj - di)
        stim = _mmax((g + curv - hts) / di, mask)                       # (13)
        str_ = ((hrs - hts) / dj)[..., 0]                               # (14)
        chord = (hts * (dj - di) + hrs * di) / dj
        nu = (g + curv - chord) * np.sqrt(0.002 * dj / (lam * di * (dj - di)))
        numax = _mmax(nu, mask)                                         # (15)
        srim = _mmax((g + curv - hrs) / (dj - di), mask)               # (17)
        hts2 = np.broadcast_to(hts, np.broadcast_shapes(hts.shape, hrs.shape))[..., 0]
        hrs2 = np.broadcast_to(hrs, np.broadcast_shapes(hts.shape, hrs.shape))[..., 0]
        d2 = dj[..., 0]
        dbp = (hrs2 - hts2 + srim * d2) / (stim + srim)                 # (18)
        nub = (hts2 + stim * dbp - (hts2 * (d2 - dbp) + hrs2 * dbp) / d2) * np.sqrt(
            0.002 * d2 / (lam * dbp * (d2 - dbp))
        )                                                               # (20)
    los = stim < str_
    luc = np.where(los, knife_edge_j(numax), knife_edge_j(np.where(los, 0.0, nub)))
    lbull = luc + (1.0 - np.exp(-luc / 6.0)) * (10.0 + 0.02 * d2)       # (21)
    if return_nu:
        return lbull, numax
    return lbull


def _ldft_inner(epsr, sigma, d, hte, hre, adft, f, pol):
    """First-term spherical-earth diffraction for one ground type, eqs (29)-(36)."""
    kh = 0.036 * (adft * f) ** (-1.0 / 3.0) * ((epsr - 1) ** 2 + (18 * sigma / f) ** 2) ** -0.25
    k = kh if pol == POL_H else kh * (epsr ** 2 + (18 * sigma / f) ** 2) ** 0.5
    beta = (1 + 1.6 * k ** 2 + 0.67 * k ** 4) / (1 + 4.5 * k ** 2 + 1.53 * k ** 4)
    x = 21.88 * beta * (f / adft ** 2) ** (1.0 / 3.0) * d
    y = 0.9575 * beta * (f ** 2 / adft) ** (1.0 / 3.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        fx = np.where(x >= 1.6, 11 + 10 * np.log10(x) - 17.6 * x,
                      -20 * np.log10(x) - 5.6488 * x ** 1.425)

        def gy(bv):
            gv = np.where(bv > 2, 17.6 * np.sqrt(bv - 1.1) - 5 * np.log10(bv - 1.1) - 8,
                          20 * np.log10(bv + 0.1 * bv ** 3))
            return np.maximum(gv, 2 + 20 * np.log10(k))

        return -fx - gy(beta * y * hte) - gy(beta * y * hre)


def _ldft(d, hte, hre, adft, f, pol, omega=0.0):
    """Eq (28): weighted land / sea first-term loss."""
    land = _ldft_inner(22.0, 0.003, d, hte, hre, adft, f, pol)
    if omega == 0.0:
        return land
    sea = _ldft_inner(80.0, 5.0, d, hte, hre, adft, f, pol)
    return omega * sea + (1 - omega) * land


def spherical_earth_loss(d, hte, hre, ap, f, pol, omega=0.0):
    """Spherical-earth diffraction loss Ldsph, eqs (22)-(27). Arrays broadcast."""
    lam = 0.2998 / f
    d, hte, hre = np.broadcast_arrays(np.asarray(d, float), hte, hre)
    dlos = np.sqrt(2.0 * ap) * (np.sqrt(0.001 * hte) + np.sqrt(0.001 * hre))   # (22)
    far = _ldft(d, hte, hre, ap, f, pol, omega)
    with np.errstate(divide="ignore", invalid="ignore"):
        c = (hte - hre) / (hte + hre)                                            # (24d)
        m = 250.0 * d * d / (ap * (hte + hre))                                   # (24e)
        arg = np.clip(3 * c / 2.0 * np.sqrt(3.0 * m / (m + 1.0) ** 3), -1.0, 1.0)
        b = 2 * np.sqrt((m + 1.0) / (3.0 * m)) * np.cos(np.pi / 3 + np.arccos(arg) / 3.0)
        dse1 = d / 2.0 * (1.0 + b)
        dse2 = d - dse1
        hse = ((hte - 500 * dse1 ** 2 / ap) * dse2 + (hre - 500 * dse2 ** 2 / ap) * dse1) / d
        hreq = 17.456 * np.sqrt(dse1 * dse2 * lam / d)                           # (25)
        aem = 500.0 * (d / (np.sqrt(hte) + np.sqrt(hre))) ** 2                   # (26)
        near_ft = np.maximum(_ldft(d, hte, hre, aem, f, pol, omega), 0.0)
        near = np.where(hse > hreq, 0.0, (1.0 - hse / hreq) * near_ft)           # (27)
    return np.where(d >= dlos, far, near)


# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------
def path_loss_batch(d, h, j_idx, prm: P1812Params, phi=None, clutter=None,
                    model="p1812", k_factor=None, details=False):
    """
    Basic transmission loss for paths 0..j along a batch of profiles.

    Parameters
    ----------
    d       : (n,) distances from Tx, km, d[0] = 0, increasing
    h       : (B, n) terrain heights amsl, m (h[:, 0] is Tx ground)
    j_idx   : (J,) endpoint indices, each >= 4 (at least 5 profile points)
    prm     : P1812Params
    phi     : (B, J) path-centre latitude, deg (for beta0). Default 52 deg.
    clutter : (B, n) representative clutter heights R, m, or None
    model   : "p1812" | "delta_bullington" | "knife_edge" | "fspl"
    k_factor: effective-earth k for the P.526 models (default from prm.dn)
    details : return a dict of intermediate quantities as well

    Returns
    -------
    Lb (B, J) in dB, or (Lb, details_dict)
    """
    d = np.asarray(d, dtype=float)
    h = np.atleast_2d(np.asarray(h, dtype=float))
    j_idx = np.asarray(j_idx, dtype=int)
    if np.any(j_idx < 4):
        raise ValueError("Each path needs at least 5 profile points (j >= 4).")
    bsz, n = h.shape
    f = prm.f_ghz
    lam = 0.2998 / f
    htg, hrg = prm.htg, prm.hrg

    k50 = 157.0 / (157.0 - prm.dn)                                   # (6)
    if model == "p1812":
        k_factor = None   # P.1812 always derives k50 from DN (eq 6); k is for P.526 models
    ae = R_EARTH_KM * (k_factor if k_factor else k50)                # (7a)
    ab = R_EARTH_KM * 3.0                                            # (7b)

    # Broadcast shapes: (B, J, n)
    idx = np.arange(n)
    di = d[None, None, :]
    dJ = d[j_idx][None, :]                     # (1, J)
    dj = dJ[..., None]                         # (1, J, 1)
    mask = ((idx[None, :] >= 1) & (idx[None, :] <= j_idx[:, None] - 1))[None]
    h3 = h[:, None, :]
    h0 = h[:, :1]                              # (B, 1)
    hj = h[:, j_idx]                           # (B, J)
    hts = h0 + htg                             # (B, 1)
    hrs = hj + hrg                             # (B, J)
    hts3, hrs3 = hts[..., None], hrs[..., None]
    g3 = h3 if clutter is None else (h + np.asarray(clutter, float))[:, None, :]

    lbfs = free_space_loss(f, dJ, hts - hrs)                         # (8)
    out = {"Lbfs": lbfs}

    if model == "fspl":
        lb = np.broadcast_to(lbfs, (bsz, len(j_idx))).copy()
        return (lb, out) if details else lb

    if model == "knife_edge":
        _, numax = bullington(di, dj, g3, mask, hts3, hrs3, ae, lam, return_nu=True)
        jnu = knife_edge_j(numax)
        out.update(nu_max=numax, Ld=jnu)
        lb = lbfs + jnu
        return (lb, out) if details else lb

    # ---------------- Path geometry, Attachment 1 §4-5 -------------------
    with np.errstate(divide="ignore", invalid="ignore"):
        # Smooth-earth least-squares surface, eqs (85)-(88), via prefix sums
        dd = np.diff(d)
        a = dd * (h[:, 1:] + h[:, :-1])
        b = dd * (h[:, 1:] * (2 * d[1:] + d[:-1]) + h[:, :-1] * (d[1:] + 2 * d[:-1]))
        zero = np.zeros((bsz, 1))
        v1 = np.concatenate([zero, np.cumsum(a, axis=1)], axis=1)[:, j_idx]
        v2 = np.concatenate([zero, np.cumsum(b, axis=1)], axis=1)[:, j_idx]
        hst = (2 * v1 * dJ - v2) / dJ ** 2
        hsr = (v2 - v1 * dJ) / dJ ** 2

        # Obstruction-adjusted smooth surface for diffraction, eqs (89)-(91)
        hh = h3 - (hts3 * (dj - di) + hrs3 * di) / dj
        hobs = _mmax(hh, mask)
        aobt = _mmax(hh / di, mask)
        aobr = _mmax(hh / (dj - di), mask)
        pos = hobs > 0
        gsum = np.where(pos, aobt + aobr, 1.0)
        hstp = np.where(pos, hst - hobs * aobt / gsum, hst)
        hsrp = np.where(pos, hsr - hobs * aobr / gsum, hsr)
        hstd = np.where(hstp >= h0, h0, hstp)
        hsrd = np.where(hsrp > hj, hj, hsrp)

        # Horizon angles and distances, eqs (76)-(84)
        th_tx = 1000 * np.arctan((h3 - hts3) / (1000 * di) - di / (2 * ae))
        th_max = _mmax(th_tx, mask)
        lt_trans = _argmax_first(th_tx, mask)
        th_td = 1000 * np.arctan((hrs - hts) / (1000 * dJ) - dJ / (2 * ae))
        th_rd = 1000 * np.arctan((hts - hrs) / (1000 * dJ) - dJ / (2 * ae))
        trans = th_max > th_td
        theta_t = np.maximum(th_max, th_td)

        th_rx = 1000 * np.arctan((h3 - hrs3) / (1000 * (dj - di)) - (dj - di) / (2 * ae))
        thr_max = _mmax(th_rx, mask)
        lr_trans = _argmax_last(th_rx, mask)

        nu_los = (h3 + 500.0 / ae * di * (dj - di)
                  - (hts3 * (dj - di) + hrs3 * di) / dj) * np.sqrt(
            0.002 * dj / (lam * di * (dj - di)))
        lt_los = _argmax_last(nu_los, mask)

    lt = np.where(trans, lt_trans, lt_los)
    lr = np.where(trans, lr_trans, lt_los)
    dlt = d[lt]
    dlr = np.where(trans, dJ - d[lr], dJ - d[lt])
    theta_r = np.where(trans, thr_max, th_rd)
    theta = 1e3 * dJ / ae + theta_t + theta_r

    hst2 = np.minimum(hst, h0)                                       # (92)
    hsr2 = np.minimum(hsr, hj)
    slope = (hsr2 - hst2) / dJ                                       # (93)
    hte = htg + h0 - hst2                                            # (94)
    hre = hrg + hj - hsr2
    mask_m = (idx >= lt[..., None]) & (idx <= lr[..., None])
    hm = _mmax(h3 - (hst2[..., None] + slope[..., None] * di), mask_m)   # (95)

    out.update(trans_horizon=trans, theta=theta, theta_t=theta_t, theta_r=theta_r,
               dlt=dlt, dlr=dlr, hstd=hstd, hsrd=hsrd, hte=hte, hre=hre, hm=hm)

    # ---------------- Diffraction, §4.3 ----------------------------------
    hts1 = (hts - hstd)[..., None]                                   # (37)
    hrs1 = (hrs - hsrd)[..., None]

    def delta_bull(ap):
        lbulla = bullington(di, dj, g3, mask, hts3, hrs3, ap, lam)
        lbulls = bullington(di, dj, np.zeros((1, 1, n)), mask, hts1, hrs1, ap, lam)
        ldsph = spherical_earth_loss(dJ, hts1[..., 0], hrs1[..., 0], ap, f, prm.pol)
        return lbulla + np.maximum(ldsph - lbulls, 0.0)               # (39)

    ld50 = delta_bull(ae)

    if model == "delta_bullington":
        out["Ld"] = ld50
        lb = lbfs + ld50
        return (lb, out) if details else lb
    if model != "p1812":
        raise ValueError(f"Unknown model '{model}'")

    # ---------------- P.1812 combination ---------------------------------
    p = prm.p
    phi = np.full((bsz, len(j_idx)), 52.0) if phi is None else np.asarray(phi, float)
    b0 = beta0(phi, dJ, dJ)                     # all-land path: dtm = dlm = d

    esp = 2.6 * (1 - np.exp(-0.1 * (dlt + dlr))) * np.log10(p / 50.0)    # (9a)
    esb = 2.6 * (1 - np.exp(-0.1 * (dlt + dlr))) * np.log10(b0 / 50.0)   # (9b)
    lb0p = lbfs + esp                                                 # (10)
    lb0b = lbfs + esb                                                 # (11)

    ldb = delta_bull(ab)
    if p == 50:
        ldp = ld50
    else:
        fi_d = np.where(p > b0, inv_cum_norm(p / 100.0) / inv_cum_norm(b0 / 100.0), 1.0)
        ldp = ld50 + fi_d * (ldb - ld50)                              # (41)

    lbd50 = lbfs + ld50                                               # (42)
    lbd = lb0p + ldp                                                  # (43)
    fi = inv_cum_norm(p / 100.0) / inv_cum_norm(b0 / 100.0)
    lminb0p = np.where(p >= b0, lbd50 + (lb0b + ldp - lbd50) * fi, lb0p + ldp)  # (59)

    # Tropospheric scatter, eqs (44)-(45)
    lf = 25 * np.log10(f) - 2.5 * np.log10(f / 2.0) ** 2
    lbs = (190.1 + lf + 20 * np.log10(dJ) + 0.573 * theta - 0.15 * prm.n0
           - 10.125 * np.log10(50.0 / p) ** 0.7)

    lba = _anomalous(dJ, dlt, dlr, hte, hre, hm, theta_t, theta_r, f, p, ae, b0)

    eta = 2.5
    lminbap = eta * np.logaddexp(lba / eta, lb0p / eta)              # (60)
    dsw, kappa = 20.0, 0.5
    fk = 1.0 - 0.5 * (1.0 + np.tanh(3.0 * kappa * (dJ - dsw) / dsw))  # (58)
    big_theta, ksi = 0.3, 0.8
    fj = 1.0 - 0.5 * (1.0 + np.tanh(3.0 * ksi * (theta - big_theta) / big_theta))  # (57)
    lbda = np.where(lminbap <= lbd, lminbap + (lbd - lminbap) * fk, lbd)  # (61)
    lbam = lbda + (lminb0p - lbda) * fj                               # (62)
    ln10 = np.log(10.0)
    lbc = -5.0 * np.logaddexp(-0.2 * ln10 * lbs, -0.2 * ln10 * lbam) / ln10  # (63)

    lloc = -inv_cum_norm(prm.pl / 100.0) * prm.sigma_l               # (67)
    lb = np.maximum(lb0p, lbc + lloc)                                 # (69)

    out.update(Ld=ldp, Ld50=ld50, Lb0p=lb0p, Lbs=lbs, Lba=lba, Lbc=lbc, beta0=b0)
    return (lb, out) if details else lb


def _anomalous(d, dlt, dlr, hte, hre, hm, theta_t, theta_r, f, p, ae, b0):
    """Ducting / layer reflection loss Lba, eqs (46)-(56). Land path (Act = Acr = 0)."""
    alf = 45.375 - 137.0 * f + 92.5 * f * f if f < 0.5 else 0.0
    tt2 = theta_t - 0.1 * dlt                                         # (48a)
    tr2 = theta_r - 0.1 * dlr
    with np.errstate(invalid="ignore", divide="ignore"):
        ast = np.where(tt2 > 0, 20 * np.log10(1 + 0.361 * tt2 * np.sqrt(f * dlt))
                       + 0.264 * tt2 * f ** (1 / 3), 0.0)
        asr = np.where(tr2 > 0, 20 * np.log10(1 + 0.361 * tr2 * np.sqrt(f * dlr))
                       + 0.264 * tr2 * f ** (1 / 3), 0.0)
    gamma_d = 5e-5 * ae * f ** (1 / 3)
    tt1 = np.where(theta_t > 0.1 * dlt, 0.1 * dlt, theta_t)
    tr1 = np.where(theta_r > 0.1 * dlr, 0.1 * dlr, theta_r)
    theta1 = 1e3 * d / ae + tt1 + tr1
    di = np.minimum(d - dlt - dlr, 40.0)
    mu3 = np.where(hm > 10, np.exp(-4.6e-5 * (hm - 10) * (43 + 6 * di)), 1.0)
    tau = 1 - np.exp(-(4.12e-4 * d ** 2.41))
    alpha = np.maximum(-0.6 - 3.5e-9 * d ** 3.1 * tau, -3.4)
    mu2 = np.minimum((500 / ae * d ** 2 / (np.sqrt(hte) + np.sqrt(hre)) ** 2) ** alpha, 1.0)
    beta = b0 * mu2 * mu3
    lb_ = np.log10(beta)
    gamma = 1.076 / (2.0058 - lb_) ** 1.012 * np.exp(
        -(9.51 - 4.8 * lb_ + 0.198 * lb_ ** 2) * 1e-6 * d ** 1.13)
    ap = -12 + (1.2 + 3.7e-3 * d) * np.log10(p / beta) + 12 * (p / beta) ** gamma
    adp = gamma_d * theta1 + ap
    af = 102.45 + 20 * np.log10(f) + 20 * np.log10(dlt + dlr) + alf + ast + asr
    return af + adp


def path_loss(d, h, prm: P1812Params, phi=None, clutter=None, model="p1812",
              k_factor=None, details=False):
    """Convenience wrapper: single point-to-point path, returns a float."""
    d = np.asarray(d, float)
    h = np.asarray(h, float)[None, :]
    j = np.array([len(d) - 1])
    ph = None if phi is None else np.array([[phi]])
    cl = None if clutter is None else np.asarray(clutter, float)[None, :]
    res = path_loss_batch(d, h, j, prm, phi=ph, clutter=cl, model=model,
                          k_factor=k_factor, details=details)
    if details:
        lb, info = res
        flat = {}
        for k, v in info.items():
            arr = np.asarray(v)
            flat[k] = arr.reshape(-1)[-1].item() if arr.size else None
        return float(lb[0, 0]), flat
    return float(res[0, 0])


def diffraction_points(d, g, hts, hrs, ae, f_ghz):
    """
    Geometry of the Bullington construction for one path, for display.

    d (km), g (m, terrain + clutter), hts/hrs antenna heights amsl (m).
    Heights are returned in the effective-earth frame used by eqs (13)-(20),
    i.e. terrain plus the curvature bulge, matching the profile chart.

    Returns dict(los, points=[{d_km, h_m, kind, nu?}]):
      LoS : the point with the largest Fresnel parameter nu (dominant edge).
      NLoS: the Tx-side and Rx-side horizon obstacles and the Bullington
            point where the two horizon rays intersect.
    """
    d = np.asarray(d, float)
    g = np.asarray(g, float)
    dt = d[-1]
    lam = 0.2998 / f_ghz
    di, gi = d[1:-1], g[1:-1]
    bulge = 500.0 / ae * di * (dt - di)
    stim_i = (gi + bulge - hts) / di
    srim_i = (gi + bulge - hrs) / (dt - di)
    stim, srim = stim_i.max(), srim_i.max()
    nu = (gi + bulge - (hts * (dt - di) + hrs * di) / dt) * np.sqrt(0.002 * dt / (lam * di * (dt - di)))
    if stim < (hrs - hts) / dt:
        k = int(nu.argmax())
        return dict(los=True, points=[dict(d_km=float(di[k]), h_m=float(gi[k] + bulge[k]),
                                           kind="dominant edge", nu=float(nu[k]))])
    kt, kr = int(stim_i.argmax()), int(srim_i.argmax())
    dbp = (hrs - hts + srim * dt) / (stim + srim)
    hbp = hts + stim * dbp
    nub = (hbp - (hts * (dt - dbp) + hrs * dbp) / dt) * np.sqrt(0.002 * dt / (lam * dbp * (dt - dbp)))
    pts = [dict(d_km=float(di[kt]), h_m=float(gi[kt] + bulge[kt]), kind="Tx horizon"),
           dict(d_km=float(di[kr]), h_m=float(gi[kr] + bulge[kr]), kind="Rx horizon"),
           dict(d_km=float(dbp), h_m=float(hbp), kind="Bullington point", nu=float(nub))]
    return dict(los=False, points=pts)
