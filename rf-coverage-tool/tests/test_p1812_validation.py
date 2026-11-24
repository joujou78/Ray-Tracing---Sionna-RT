"""
Validate rfcov.p1812 against the ITU-R SG3 / Ofcom P.1812 validation set.

The validation profiles and the reference results (per-case log CSVs with every
intermediate quantity) are published with the reference implementation
(https://github.com/eeveetza/Py1812, folders tests/validation_profiles and
tests/validation_results). They are NOT vendored here; fetch them with

    python scripts/fetch_validation_data.py

which places them under data/validation/. The test is skipped if absent.

Only land paths (radio-meteorological code 4 everywhere) are compared, because
the engine models inland paths only.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path

import numpy as np
import pytest

from rfcov.p1812 import P1812Params, path_loss

ROOT = Path(__file__).resolve().parents[1]
VAL = Path(os.environ.get("P1812_VALIDATION_DIR", ROOT / "data" / "validation"))
PROFILES = VAL / "validation_profiles"
RESULTS = VAL / "validation_results"

pytestmark = pytest.mark.skipif(not PROFILES.is_dir(), reason="validation data not fetched")


def _read_profile(path: Path):
    """Parse the 'Fryderyk csv' profile: returns d, h, R, zone, lat_t, lat_r."""
    rows = list(csv.reader(path.open(encoding="utf-8", errors="replace")))
    meta, prof, in_prof = {}, [], False
    for r in rows:
        if not r:
            continue
        key = r[0].strip()
        if key == "{Begin of Profile}":
            in_prof = True
            continue
        if key == "{End of Profile}":
            in_prof = False
            continue
        if in_prof:
            if key.startswith("Number of Points"):
                continue
            prof.append([float(x) if x.strip() else np.nan for x in r[:5]])
        elif len(r) > 1:
            meta[key] = r[1]
    a = np.array(prof)
    first_tx = meta.get("First Point TX or RX:", "T").strip().upper().startswith("T")
    if not first_tx:  # profile listed from the receiver end
        a = a[::-1].copy()
        a[:, 0] = a[0, 0] - a[:, 0]
    return a[:, 0], a[:, 1], np.nan_to_num(a[:, 3]), a[:, 4]


def _read_log(path: Path) -> dict:
    out = {}
    for r in csv.reader(path.open()):
        if len(r) >= 4 and r[0].strip():
            try:
                out[r[0].strip()] = float(r[3])
            except ValueError:
                pass
    return out


def _cases():
    if not RESULTS.is_dir():
        return []
    cases = []
    for log in sorted(RESULTS.glob("*_log.csv")):
        stem, idx = log.name[: -len("_log.csv")].rsplit("_", 1)
        prof = PROFILES / f"{stem}.csv"
        if prof.exists():
            cases.append(pytest.param(prof, log, id=f"{stem}#{idx}"))
    return cases


@pytest.mark.parametrize("profile,log", _cases())
def test_against_reference(profile, log):
    d, h, R, zone = _read_profile(profile)
    if np.any(zone != 4):
        pytest.skip("sea / coastal path: not modelled by this engine")
    ref = _read_log(log)
    prm = P1812Params(
        f_ghz=ref["f (GHz)"], htg=ref["htg (m)"], hrg=ref["hrg (m)"], p=ref["p (%)"],
        pl=ref["pL (%)"], sigma_l=ref["sigmaL (dB)"], pol=int(ref["pol"]),
        dn=ref["DN"], n0=ref["N0"],
    )
    lb, info = path_loss(d, h, prm, phi=ref["phi (deg)"], clutter=R, details=True)
    assert lb == pytest.approx(ref["Lb (dB)"], abs=1e-6)
    # A few intermediates, to localise any future regression
    assert info["Lbs"] == pytest.approx(ref["Lbs (dB)"], abs=1e-6)
    assert info["Lba"] == pytest.approx(ref["Lba (dB)"], abs=1e-6)
    assert info["Ld50"] == pytest.approx(ref["Ld50 (dB)"], abs=1e-6)
