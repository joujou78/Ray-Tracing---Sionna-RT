"""OS National Grid references (EPSG:27700) <-> WGS84, via pyproj (includes the OSGB36 datum shift)."""
from __future__ import annotations

import re
from functools import lru_cache

LETTERS = "ABCDEFGHJKLMNOPQRSTUVWXYZ"  # no I


@lru_cache(maxsize=1)
def _tf():
    from pyproj import Transformer
    return (Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True),
            Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True))


def to_osgb_ref(lat: float, lon: float, digits: int = 10) -> str | None:
    """'SK 57012 39876' style reference, or None outside the grid."""
    e, n = _tf()[0].transform(lon, lat)
    if not (0 <= e < 700000 and 0 <= n < 1300000):
        return None
    e100, n100 = int(e // 100000), int(n // 100000)
    l1 = (19 - n100) - (19 - n100) % 5 + (e100 + 10) // 5
    l2 = (19 - n100) * 5 % 25 + e100 % 5
    half = digits // 2
    ee = int(e % 100000) // 10 ** (5 - half)
    nn = int(n % 100000) // 10 ** (5 - half)
    return f"{LETTERS[l1]}{LETTERS[l2]} {ee:0{half}d} {nn:0{half}d}"


def from_osgb_ref(ref: str) -> tuple[float, float]:
    """Parse 'SK5701239876', 'SK 570 398' etc. Returns (lat, lon) of the square centre."""
    s = re.sub(r"\s+", "", ref.upper())
    m = re.fullmatch(r"([A-HJ-Z]{2})(\d*)", s)
    if not m or len(m.group(2)) % 2 or len(m.group(2)) > 10:
        raise ValueError(f"Not an OS grid reference: {ref!r}")
    l1, l2 = LETTERS.index(m.group(1)[0]), LETTERS.index(m.group(1)[1])
    e100 = ((l1 - 2) % 5) * 5 + l2 % 5
    n100 = (19 - (l1 // 5) * 5) - l2 // 5
    digits = m.group(2)
    half = len(digits) // 2
    scale = 10 ** (5 - half)
    e = e100 * 100000 + (int(digits[:half]) if half else 0) * scale + scale / 2
    n = n100 * 100000 + (int(digits[half:]) if half else 0) * scale + scale / 2
    lon, lat = _tf()[1].transform(e, n)
    return lat, lon
