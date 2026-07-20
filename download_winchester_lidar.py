"""
Download Winchester LiDAR tiles from DEFRA WCS service.
Run this script ON THE VM (georgeskai@sti-virtual-machine), NOT in Claude Code.

Usage:
    python3 download_winchester_lidar.py --out-dir ~/sionna_rt/winchester_915mhz/lidar

Downloads DTM 1m + DSM 1m for all 169 SU tiles covering Winchester scene bbox.
"""

import os, sys, time, argparse
import urllib.request

# Winchester scene BNG bbox (from receiver coverage + 1km pad)
BNG_W, BNG_E = 438275, 450147
BNG_S, BNG_N = 121883, 133761

# DEFRA WCS endpoints
WCS_DTM = "https://environment.data.gov.uk/arcgis/services/EA/LidarComposite_DTM_1m/ImageServer/WCSServer"
WCS_DSM = "https://environment.data.gov.uk/arcgis/services/EA/LidarComposite_DSM_1m/ImageServer/WCSServer"

def tile_bbox(su_e, su_n):
    """Return BNG bbox for a 1km OS tile given SU-relative indices."""
    SU_E0, SU_N0 = 400000, 100000
    e0 = SU_E0 + su_e * 1000
    n0 = SU_N0 + su_n * 1000
    return e0, n0, e0 + 1000, n0 + 1000

def wcs_url(endpoint, bbox, res=1):
    e0, n0, e1, n1 = bbox
    width  = (e1 - e0) // res
    height = (n1 - n0) // res
    params = (
        f"SERVICE=WCS&VERSION=1.0.0&REQUEST=GetCoverage"
        f"&COVERAGE=coverage1"
        f"&CRS=EPSG:27700&RESPONSE_CRS=EPSG:27700"
        f"&BBOX={e0},{n0},{e1},{n1}"
        f"&WIDTH={width}&HEIGHT={height}"
        f"&FORMAT=GeoTIFF"
    )
    return f"{endpoint}?{params}"

def download_tile(url, out_path, retries=3):
    for attempt in range(retries):
        try:
            urllib.request.urlretrieve(url, out_path + ".tmp")
            os.rename(out_path + ".tmp", out_path)
            return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"    FAILED: {e}")
                return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=os.path.expanduser("~/sionna_rt/winchester_915mhz/lidar"))
    parser.add_argument("--dtm-only", action="store_true")
    parser.add_argument("--dsm-only", action="store_true")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # Build tile list
    SU_E0, SU_N0 = 400000, 100000
    tile_e_min = (BNG_W - SU_E0) // 1000
    tile_e_max = (BNG_E - SU_E0) // 1000
    tile_n_min = (BNG_S - SU_N0) // 1000
    tile_n_max = (BNG_N - SU_N0) // 1000

    tiles = [(e, n) for e in range(tile_e_min, tile_e_max + 1)
                    for n in range(tile_n_min, tile_n_max + 1)]

    print(f"Output dir : {args.out_dir}")
    print(f"Tiles      : {len(tiles)}  ({tile_e_max-tile_e_min+1} cols x {tile_n_max-tile_n_min+1} rows)")
    print()

    layers = []
    if not args.dsm_only:
        layers.append(("DTM", WCS_DTM))
    if not args.dtm_only:
        layers.append(("DSM", WCS_DSM))

    for layer_name, endpoint in layers:
        print(f"=== Downloading {layer_name} 1m ===")
        done = skipped = failed = 0
        for i, (se, sn) in enumerate(tiles):
            tile_name = f"SU{se:02d}{sn:02d}"
            fname = os.path.join(args.out_dir, f"{tile_name}_{layer_name}_1m.tif")
            if os.path.exists(fname):
                skipped += 1
                continue
            bbox = tile_bbox(se, sn)
            url  = wcs_url(endpoint, bbox)
            ok   = download_tile(url, fname)
            if ok:
                done += 1
                print(f"  [{i+1:3d}/{len(tiles)}] {tile_name} OK")
            else:
                failed += 1
                print(f"  [{i+1:3d}/{len(tiles)}] {tile_name} FAILED")
            time.sleep(0.2)  # polite delay
        print(f"  Done: {done}  Skipped: {skipped}  Failed: {failed}\n")

    print("All done. Merge tiles with:")
    print(f"  gdal_merge.py -o {args.out_dir}/../dtm.tif {args.out_dir}/*_DTM_1m.tif")
    print(f"  gdal_merge.py -o {args.out_dir}/../dsm.tif {args.out_dir}/*_DSM_1m.tif")

if __name__ == "__main__":
    main()
