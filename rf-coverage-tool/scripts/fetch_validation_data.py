"""
Fetch the ITU-R SG3 / Ofcom P.1812 validation profiles and reference results
(published with https://github.com/eeveetza/Py1812) into data/validation/,
for tests/test_p1812_validation.py. Requires git on PATH.

Usage:  python scripts/fetch_validation_data.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "https://github.com/eeveetza/Py1812.git"
DEST = Path(__file__).resolve().parents[1] / "data" / "validation"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "clone", "--depth", "1", "-q", REPO, tmp], check=True)
        for sub in ("validation_profiles", "validation_results"):
            src = Path(tmp) / "tests" / sub
            dst = DEST / sub
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  {dst}: {len(list(dst.iterdir()))} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
