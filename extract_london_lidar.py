#!/usr/bin/env python3
"""Standalone LiDAR zip extractor for the London scene.

Run directly from the terminal:
    python3 extract_london_lidar.py

Extracts DTM + first-return-DSM .tif tiles from
~/Downloads/lidar_composite_dtm-*.zip and
~/Downloads/lidar_composite_first_return_dsm-*.zip
into ~/sionna_rt/london_ofcom_915mhz_dem/, then merges them
into dem.tif / lidar_dsm.tif with gdal_merge.py.
"""
import os
import glob
import zipfile
import subprocess
import sys

DOWNLOADS_DIR = os.path.expanduser('~/Downloads')
LIDAR_DIR = os.path.expanduser('~/sionna_rt/london_ofcom_915mhz_dem')

os.makedirs(LIDAR_DIR, exist_ok=True)

dtm_zips = sorted(glob.glob(os.path.join(DOWNLOADS_DIR, 'lidar_composite_dtm-*.zip')))
dsm_zips = sorted(glob.glob(os.path.join(DOWNLOADS_DIR, 'lidar_composite_first_return_dsm-*.zip')))
zip_paths = dtm_zips + dsm_zips

print(f'Downloads dir : {DOWNLOADS_DIR}')
print(f'Lidar dir     : {LIDAR_DIR}')
print(f'DTM zips found: {len(dtm_zips)}')
print(f'DSM zips found: {len(dsm_zips)}')

if not zip_paths:
    print('\n[ERROR] No matching zips found. Listing everything in Downloads:')
    for p in sorted(glob.glob(os.path.join(DOWNLOADS_DIR, '*'))):
        print('  ', p)
    sys.exit(1)

extracted = []
for zpath in zip_paths:
    print(f'\nExtracting {os.path.basename(zpath)} ...')
    try:
        with zipfile.ZipFile(zpath, 'r') as zf:
            for member in zf.namelist():
                if not member.lower().endswith('.tif'):
                    continue
                out_name = os.path.basename(member)
                out_path = os.path.join(LIDAR_DIR, out_name)
                if os.path.exists(out_path):
                    print(f'  skip (exists): {out_name}')
                    continue
                with zf.open(member) as src, open(out_path, 'wb') as dst:
                    dst.write(src.read())
                extracted.append(out_path)
                print(f'  -> {out_name}')
    except zipfile.BadZipFile:
        print(f'  [WARN] not a valid zip — skipping: {zpath}')

print(f'\nExtracted {len(extracted)} new GeoTIFF tile(s) into {LIDAR_DIR}')

dtm_tiles = sorted(glob.glob(os.path.join(LIDAR_DIR, '*_DTM_1m.tif')))
dsm_tiles = sorted(glob.glob(os.path.join(LIDAR_DIR, '*_FZ_DSM_1m.tif')))
print(f'\nTotal DTM tiles on disk: {len(dtm_tiles)}')
print(f'Total DSM tiles on disk: {len(dsm_tiles)}')

if not dtm_tiles or not dsm_tiles:
    print('\n[ERROR] Missing DTM or DSM tiles after extraction — stopping before merge.')
    sys.exit(1)


def merge(tiles, out_path, label):
    if os.path.exists(out_path):
        print(f'{label}: {os.path.basename(out_path)} already exists, skipping merge.')
        return
    print(f'\n{label}: merging {len(tiles)} tiles -> {os.path.basename(out_path)} ...')
    # Deliberately no -n / -a_nodata here: passing -n with the source
    # tiles' extreme float32-min NoData sentinel made gdal_merge write
    # an entirely empty (all-NoData) output instead of the real tile
    # data. Plain gdal_merge correctly copies real elevation values, so
    # we sanitize the NoData sentinel ourselves afterwards in Python,
    # where we can verify the result directly instead of trusting CLI
    # flag interactions.
    cmd = ['gdal_merge.py', '-o', out_path, '-of', 'GTiff',
           '-co', 'COMPRESS=LZW', '-co', 'TILED=YES'] + tiles
    ret = subprocess.run(cmd)
    if ret.returncode != 0:
        print(f'[ERROR] gdal_merge.py failed for {label} (exit {ret.returncode}). Is GDAL installed?')
        sys.exit(1)
    print(f'  -> wrote {out_path}')

    import numpy as np
    import rasterio as _rio
    with _rio.open(out_path) as ds:
        profile = ds.profile
        arr = ds.read(1)
    bad = ~np.isfinite(arr) | (np.abs(arr) > 1e30)
    n_bad = int(bad.sum())
    arr[bad] = -9999.0
    profile.update(nodata=-9999.0)
    with _rio.open(out_path, 'w', **profile) as ds:
        ds.write(arr, 1)
    print(f'  sanitized {n_bad} bad/sentinel pixel(s) -> -9999, nodata set to -9999')
    valid = arr[arr != -9999.0]
    if valid.size:
        print(f'  valid data range: {valid.min():.1f} .. {valid.max():.1f}  '
              f'({valid.size}/{arr.size} pixels, {100*valid.size/arr.size:.1f}% coverage)')
    else:
        print(f'  [ERROR] {label} has NO valid data after sanitizing — merge produced an empty file.')
        sys.exit(1)



merge(dtm_tiles, os.path.join(LIDAR_DIR, 'dem.tif'), 'DTM')
merge(dsm_tiles, os.path.join(LIDAR_DIR, 'lidar_dsm.tif'), 'DSM')

print('\nDone. dem.tif and lidar_dsm.tif are ready.')
print('Next: in the notebook, run CELL 2c (coverage check) then CELL 2d (nDSM).')
