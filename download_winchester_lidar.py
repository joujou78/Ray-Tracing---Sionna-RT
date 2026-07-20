"""
Download Winchester LiDAR data from DEFRA/EA WCS service.
Run this script ON THE VM (georgeskai@sti-virtual-machine), NOT in Claude Code.

Downloads per tile:
  - DTM 1m  (Digital Terrain Model — bare earth)
  - DSM 1m  (Digital Surface Model — buildings + trees)
  - VOM 1m  (Vegetation Object Model — vegetation height)
  - LAZ     (Point Cloud — full waveform, optional)

Usage:
    python3 download_winchester_lidar.py --out-dir ~/sionna_rt/winchester_915mhz/lidar
    python3 download_winchester_lidar.py --out-dir ~/sionna_rt/winchester_915mhz/lidar --no-laz
    python3 download_winchester_lidar.py --out-dir ~/sionna_rt/winchester_915mhz/lidar --dtm-only

After download, merge tiles:
    gdal_merge.py -o ~/sionna_rt/winchester_915mhz/dtm.tif lidar/*_DTM_1m.tif
    gdal_merge.py -o ~/sionna_rt/winchester_915mhz/dsm.tif lidar/*_DSM_1m.tif
    gdal_merge.py -o ~/sionna_rt/winchester_915mhz/vom.tif lidar/*_VOM_1m.tif
"""

import os, sys, time, argparse
import urllib.request

# Winchester scene BNG bbox (3km radius from TX + 500m pad)
BNG_W, BNG_E = 440696, 447696
BNG_S, BNG_N = 124316, 131316

# DEFRA/EA WCS endpoints — raster layers
WCS_DTM = "https://environment.data.gov.uk/arcgis/services/EA/LidarComposite_DTM_1m/ImageServer/WCSServer"
WCS_DSM = "https://environment.data.gov.uk/arcgis/services/EA/LidarComposite_DSM_1m/ImageServer/WCSServer"
WCS_VOM = "https://environment.data.gov.uk/arcgis/services/EA/VegetationObjectModel_VOM_1m/ImageServer/WCSServer"

# EA point cloud — LAZ files (National LiDAR Programme)
LAZ_BASE = "https://environment.data.gov.uk/UserDownloads/interactive/NationalLidarProgramme"

def tile_bbox(su_e, su_n):
    SU_E0, SU_N0 = 400000, 100000
    e0 = SU_E0 + su_e * 1000
    n0 = SU_N0 + su_n * 1000
    return e0, n0, e0 + 1000, n0 + 1000

def wcs_url(endpoint, bbox, res=1):
    e0, n0, e1, n1 = bbox
    w, h = (e1-e0)//res, (n1-n0)//res
    return (f"{endpoint}?SERVICE=WCS&VERSION=1.0.0&REQUEST=GetCoverage"
            f"&COVERAGE=coverage1&CRS=EPSG:27700&RESPONSE_CRS=EPSG:27700"
            f"&BBOX={e0},{n0},{e1},{n1}&WIDTH={w}&HEIGHT={h}&FORMAT=GeoTIFF")

def laz_url(tile_name):
    # EA National LiDAR Programme LAZ naming: SU4427_P-1.laz (point cloud)
    return f"{LAZ_BASE}/{tile_name}_P-1.laz"

def download_file(url, out_path, retries=3):
    for attempt in range(retries):
        try:
            urllib.request.urlretrieve(url, out_path + ".tmp")
            size = os.path.getsize(out_path + ".tmp")
            if size < 1000:
                # Check if response is an error page
                with open(out_path + ".tmp", 'rb') as f:
                    content = f.read(200)
                if b'error' in content.lower() or b'<html' in content.lower():
                    os.remove(out_path + ".tmp")
                    raise ValueError(f"Server returned error page ({size} bytes)")
            os.rename(out_path + ".tmp", out_path)
            return True, size
        except Exception as e:
            if os.path.exists(out_path + ".tmp"):
                os.remove(out_path + ".tmp")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return False, str(e)

def build_tiles():
    SU_E0, SU_N0 = 400000, 100000
    te_min = (BNG_W - SU_E0) // 1000
    te_max = (BNG_E - SU_E0) // 1000
    tn_min = (BNG_S - SU_N0) // 1000
    tn_max = (BNG_N - SU_N0) // 1000
    return [(e, n) for e in range(te_min, te_max+1)
                   for n in range(tn_min, tn_max+1)]

def download_layer(tiles, layer_name, endpoint_or_fn, out_dir, is_laz=False):
    print(f"=== {layer_name} ===")
    done = skipped = failed = 0
    for i, (se, sn) in enumerate(tiles):
        tile_name = f"SU{se:02d}{sn:02d}"
        ext   = "laz" if is_laz else "tif"
        fname = os.path.join(out_dir, f"{tile_name}_{layer_name}.{ext}")
        if os.path.exists(fname):
            skipped += 1
            continue
        if is_laz:
            url = endpoint_or_fn(tile_name)
        else:
            url = wcs_url(endpoint_or_fn, tile_bbox(se, sn))
        ok, info = download_file(url, fname)
        tag = f"{info//1024:.0f}KB" if ok else f"FAILED: {info}"
        print(f"  [{i+1:3d}/{len(tiles)}] {tile_name}  {tag}")
        done += ok
        failed += (not ok)
        time.sleep(0.2)
    print(f"  Done:{done}  Skipped:{skipped}  Failed:{failed}\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=os.path.expanduser("~/sionna_rt/winchester_915mhz/lidar"))
    parser.add_argument("--dtm-only", action="store_true")
    parser.add_argument("--dsm-only", action="store_true")
    parser.add_argument("--no-vom",   action="store_true", help="skip VOM download")
    parser.add_argument("--no-laz",   action="store_true", help="skip point cloud download")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    tiles = build_tiles()

    print(f"Output dir : {args.out_dir}")
    print(f"Tiles      : {len(tiles)}  (8 cols x 8 rows, SU4024-SU4731)")
    print()

    if not args.dsm_only:
        download_layer(tiles, "DTM_1m", WCS_DTM, args.out_dir)
    if not args.dtm_only:
        download_layer(tiles, "DSM_1m", WCS_DSM, args.out_dir)
    if not args.no_vom and not args.dtm_only:
        download_layer(tiles, "VOM_1m", WCS_VOM, args.out_dir)
    if not args.no_laz and not args.dtm_only and not args.dsm_only:
        download_layer(tiles, "LAZ", laz_url, args.out_dir, is_laz=True)

    print("Merge commands:")
    d = args.out_dir
    p = os.path.dirname(d)
    print(f"  gdal_merge.py -o {p}/dtm.tif {d}/*_DTM_1m.tif")
    print(f"  gdal_merge.py -o {p}/dsm.tif {d}/*_DSM_1m.tif")
    print(f"  gdal_merge.py -o {p}/vom.tif {d}/*_VOM_1m.tif")
    print(f"  # LAZ files don't need merging — use as individual tiles")

if __name__ == "__main__":
    main()
