"""
Download the DN50 / N050 digital maps that form part of Rec. ITU-R P.1812-8
from itu.int into data/itu_maps/. ITU does not allow redistribution, so the
files are fetched by each user and are git-ignored.

Usage:  python scripts/fetch_itu_maps.py
"""
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.1812-8-202509-I!!ZIP-E.zip"
DEST = Path(__file__).resolve().parents[1] / "data" / "itu_maps"
WANTED = ("DN50.TXT", "N050.TXT")


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {URL}")
    with urllib.request.urlopen(URL, timeout=120) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            base = Path(name).name
            if base.upper() in WANTED:
                (DEST / base.upper()).write_bytes(z.read(name))
                print(f"  wrote {DEST / base.upper()}")
    cache = DEST / "p1812_maps.npz"
    if cache.exists():
        cache.unlink()
    missing = [w for w in WANTED if not (DEST / w).exists()]
    if missing:
        print(f"Missing from archive: {missing}", file=sys.stderr)
        return 1
    print("Done. Restart the server to pick up the maps.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
