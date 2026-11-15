# =============================================================================
# CELL 4-LoD3 — Automatic LoD3 facade module
# Insert after CELL 4 (building/vegetation PLY generation).
# Requires: mat_plys (dict), MESH_DIR (str), footprints_gdf (GeoDataFrame),
#           TX_LAT / TX_LON or TX_EASTING / TX_NORTHING (from CELL 0 config).
#
# Config knobs (add to CELL 0 alongside existing params):
#   LOD3_ENABLE           = False       # master switch
#   LOD3_ZONE_RADIUS_M    = 400         # Tx-centred LoD3 zone
#   LOD3_CORRIDOR_BUFFER_M= 30          # extra buffer along drive-test route
#   LOD3_ALLOW_PROCEDURAL = True        # True → no Mapillary token required
#   LOD3_IMAGE_DATE_RANGE = ('2016-01-01', '2018-12-31')
#   LOD3_DETAIL_THRESHOLD_M = 0.10      # min facade element size
#   LOD3_DEFAULT_RECESS_M = 0.20        # window recess depth
#   MAPILLARY_TOKEN       = ''          # set env var MAPILLARY_TOKEN or here
# =============================================================================

import os, sys, logging, math, importlib
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')
_log = logging.getLogger('CELL4_LOD3')

# ------------------------------------------------------------------
# 0.  Guard — skip entire cell if not enabled
# ------------------------------------------------------------------
_LOD3_ENABLE = globals().get('LOD3_ENABLE', False)

if not _LOD3_ENABLE:
    print("CELL 4-LoD3: LOD3_ENABLE=False — skipped.")
else:
    # ------------------------------------------------------------------
    # 1.  Import lod3 module (repo root must be on sys.path)
    # ------------------------------------------------------------------
    _repo_root = os.path.dirname(os.path.abspath('__file__'))
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)

    # Reload sub-modules so config changes in CELL 0 are picked up
    for _m in ['lod3.config', 'lod3.facade_extractor', 'lod3.mapillary',
               'lod3.rectifier', 'lod3.detector', 'lod3.geometry_builder',
               'lod3.ply_exporter', 'lod3.qa', 'lod3']:
        if _m in sys.modules:
            importlib.reload(sys.modules[_m])

    import lod3
    from lod3 import config as _lod3_cfg
    from lod3 import (facade_extractor as _fa, mapillary as _ml,
                      rectifier as _rect, detector as _det,
                      geometry_builder as _gb, ply_exporter as _pe, qa as _qa)

    # ------------------------------------------------------------------
    # 2.  Push CELL 0 knobs into lod3.config
    # ------------------------------------------------------------------
    _lod3_cfg.LOD3_ENABLE             = True
    _lod3_cfg.LOD3_ZONE_RADIUS_M      = float(globals().get('LOD3_ZONE_RADIUS_M', 400))
    _lod3_cfg.LOD3_CORRIDOR_BUFFER_M  = float(globals().get('LOD3_CORRIDOR_BUFFER_M', 30))
    _lod3_cfg.LOD3_ALLOW_PROCEDURAL   = bool(globals().get('LOD3_ALLOW_PROCEDURAL', True))
    _lod3_cfg.LOD3_DETAIL_THRESHOLD_M = float(globals().get('LOD3_DETAIL_THRESHOLD_M', 0.10))
    _lod3_cfg.LOD3_DEFAULT_RECESS_M   = float(globals().get('LOD3_DEFAULT_RECESS_M', 0.20))

    _date_range = globals().get('LOD3_IMAGE_DATE_RANGE', ('2016-01-01', '2018-12-31'))
    _lod3_cfg.LOD3_IMAGE_DATE_RANGE = _date_range

    # Optional: set Mapillary token from CELL 0 variable (fallback: env var)
    _tok = globals().get('MAPILLARY_TOKEN', '').strip()
    if _tok:
        os.environ['MAPILLARY_TOKEN'] = _tok

    _log.info("LoD3 config: zone=%.0f m  procedural=%s  date=%s–%s",
              _lod3_cfg.LOD3_ZONE_RADIUS_M,
              _lod3_cfg.LOD3_ALLOW_PROCEDURAL,
              *_lod3_cfg.LOD3_IMAGE_DATE_RANGE)

    # ------------------------------------------------------------------
    # 3.  Resolve Tx position in BNG (EPSG:27700)
    # ------------------------------------------------------------------
    if 'TX_EASTING' in globals() and 'TX_NORTHING' in globals():
        _tx_e = float(TX_EASTING)
        _tx_n = float(TX_NORTHING)
    elif 'TX_LAT' in globals() and 'TX_LON' in globals():
        from pyproj import Transformer as _Tr
        _wgs_bng = _Tr.from_epsg(4326, 27700, always_xy=True)
        _tx_e, _tx_n = _wgs_bng.transform(float(TX_LON), float(TX_LAT))
    else:
        raise RuntimeError(
            "CELL 4-LoD3: define TX_EASTING/TX_NORTHING or TX_LAT/TX_LON in CELL 0."
        )
    _log.info("Tx BNG: E=%.1f  N=%.1f", _tx_e, _tx_n)

    # ------------------------------------------------------------------
    # 4.  Validate footprints_gdf
    # ------------------------------------------------------------------
    if 'footprints_gdf' not in globals() or footprints_gdf is None:
        raise RuntimeError(
            "CELL 4-LoD3: footprints_gdf not found. "
            "Ensure CELL 3b / CELL 4 has run and produced footprints_gdf."
        )

    _fp = footprints_gdf.copy()

    # Ensure required columns exist
    if 'building_id' not in _fp.columns:
        _fp['building_id'] = _fp.index.astype(str)
    if 'height_m' not in _fp.columns:
        # Try common alternative column names from the scene builder
        for _alt in ['ndsm_height_m', 'height', 'bldg_height']:
            if _alt in _fp.columns:
                _fp['height_m'] = _fp[_alt]
                break
        else:
            _log.warning("height_m column not found — defaulting to 10 m")
            _fp['height_m'] = 10.0

    # Reproject to BNG if necessary
    if _fp.crs is not None and _fp.crs.to_epsg() != 27700:
        _fp = _fp.to_crs(epsg=27700)
    elif _fp.crs is None:
        _log.warning("footprints_gdf has no CRS — assuming EPSG:27700")

    _log.info("Footprints loaded: %d buildings", len(_fp))

    # ------------------------------------------------------------------
    # 5.  Step 1 — Facade extraction
    # ------------------------------------------------------------------
    _z_bottom = float(globals().get('origin_elev_asl_m', 0.0))

    _facades = _fa.extract_facades(
        _fp, _tx_e, _tx_n,
        zone_radius_m=_lod3_cfg.LOD3_ZONE_RADIUS_M,
        z_bottom=_z_bottom,
    )
    _log.info("Step 1: %d facades extracted from %d buildings inside %.0f m zone",
              len(_facades),
              _facades['building_id'].nunique() if len(_facades) else 0,
              _lod3_cfg.LOD3_ZONE_RADIUS_M)

    if len(_facades) == 0:
        print("CELL 4-LoD3: No buildings found in LoD3 zone — nothing to do.")
    else:
        # Optional: further filter facades to drive-test corridor
        # Uncomment if you have a route GeoDataFrame called `route_gdf`:
        # if 'route_gdf' in globals() and route_gdf is not None:
        #     _facades = _fa.filter_facades_by_route(
        #         _facades, route_gdf, _lod3_cfg.LOD3_CORRIDOR_BUFFER_M
        #     )
        #     _log.info("After corridor filter: %d facades remain", len(_facades))

        # ------------------------------------------------------------------
        # 6.  Steps 2-5 — Image selection / detection / regularisation
        # ------------------------------------------------------------------
        _has_token = bool(os.environ.get('MAPILLARY_TOKEN', '').strip())
        _has_model = os.path.isfile(
            os.path.join(_repo_root, 'lod3', 'models', 'facade_seg.onnx')
        )
        _use_image_pipeline = _has_token and _has_model

        if _use_image_pipeline:
            _log.info("Step 2-5: image pipeline (Mapillary + ONNX)")
        elif _lod3_cfg.LOD3_ALLOW_PROCEDURAL:
            _log.info("Step 2-5: procedural fallback (LOD3_ALLOW_PROCEDURAL=True)")
        else:
            raise RuntimeError(
                "CELL 4-LoD3: no Mapillary token / ONNX model found and "
                "LOD3_ALLOW_PROCEDURAL=False. Set LOD3_ALLOW_PROCEDURAL=True "
                "in CELL 0 to use statistical LoD3, or provide a Mapillary "
                "token in MAPILLARY_TOKEN and an ONNX model in lod3/models/."
            )

        import requests as _req
        _session = _req.Session() if _use_image_pipeline else None

        _elements_per_facade = []  # list of element lists

        for _idx, (_row_idx, _row) in enumerate(
                _facades.iterrows(), start=1):

            if _idx % 20 == 0 or _idx == len(_facades):
                print(f"  Processing facade {_idx}/{len(_facades)} "
                      f"({_row['building_id']} / {_row['facade_id']}) ...",
                      end='\r')

            if _use_image_pipeline:
                # Steps 2-3: Mapillary image selection + rectification
                _imgs = _ml.select_images_for_facade(_row, max_images=5,
                                                      session=_session)
                _elements = []
                for _img_meta in _imgs:
                    # Download thumbnail
                    import tempfile, cv2
                    _tmp = tempfile.mktemp(suffix='.jpg')
                    try:
                        _ml.download_image(_img_meta['thumb_1024_url'],
                                           _tmp, session=_session)
                        _bgr = cv2.imread(_tmp)
                        if _bgr is None:
                            continue
                    except Exception as _e:
                        _log.debug("Image download failed: %s", _e)
                        continue
                    finally:
                        if os.path.exists(_tmp):
                            os.remove(_tmp)

                    # Step 3: rectification
                    _rect_img = _rect.rectify_facade(_bgr, _row, _img_meta)
                    if _rect_img is None:
                        continue

                    # Steps 4-5: detection + regularisation
                    _raw = _det.detect_elements_from_image(_rect_img, _row)
                    _elements.extend(_raw)

                _det.regularise(_elements)

                # Fallback to procedural if no imagery detected anything
                if not _elements and _lod3_cfg.LOD3_ALLOW_PROCEDURAL:
                    _elements = _det.detect_elements_procedural(_row)
            else:
                # Pure procedural
                _elements = _det.detect_elements_procedural(_row)

            _elements_per_facade.append(_elements)

        print()  # newline after \r progress

        _log.info("Steps 2-5: %d total elements detected across %d facades",
                  sum(len(e) for e in _elements_per_facade), len(_facades))

        # ------------------------------------------------------------------
        # 7.  Step 6 — 3D geometry construction
        # ------------------------------------------------------------------
        _geom_list = []
        for (_row_idx, _row), _elements in zip(_facades.iterrows(),
                                                _elements_per_facade):
            _geom = _gb.build_facade_geometry(_row, _elements)
            _geom_list.append(_geom)

        # ------------------------------------------------------------------
        # 8.  Step 8 — QA (degenerate triangles, overlap, budget)
        # ------------------------------------------------------------------
        _geom_list, _n_tris = _qa.run_all_checks(
            _geom_list, facade_df=_facades.reset_index(drop=True)
        )
        _log.info("Step 8 QA: %d total triangles across all LoD3 facades", _n_tris)

        # ------------------------------------------------------------------
        # 9.  Step 7 — PLY export and mat_plys merge
        # ------------------------------------------------------------------
        # Confirm MESH_DIR exists (defined in CELL 0 / CELL 1)
        if 'MESH_DIR' not in globals():
            raise RuntimeError(
                "CELL 4-LoD3: MESH_DIR not defined. "
                "Ensure CELL 1 has run and set MESH_DIR."
            )

        _lod3_mat_plys = _pe.export_lod3_plys(_geom_list, out_dir=MESH_DIR)

        if not _lod3_mat_plys:
            _log.warning("Step 7: no LoD3 PLY files written (all meshes empty).")
        else:
            _log.info("Step 7: wrote %d LoD3 PLY file(s):", len(_lod3_mat_plys))
            for _stem, _entry in _lod3_mat_plys.items():
                _sz = os.path.getsize(_entry['path']) // 1024
                _log.info("  %s.ply  (%d KB)  mat=%s", _stem, _sz, _entry['mat_id'])

            # Merge into existing mat_plys (defined by CELL 4)
            if 'mat_plys' not in globals():
                _log.warning("mat_plys not found in globals — creating it.")
                mat_plys = {}

            # Duplicate-safe merge
            for _stem, _entry in _lod3_mat_plys.items():
                if _stem in mat_plys:
                    _log.warning(
                        "mat_plys key '%s' already exists — LoD3 entry skipped. "
                        "Delete the existing PLY first if you want to replace it.",
                        _stem
                    )
                else:
                    mat_plys[_stem] = _entry

        # ------------------------------------------------------------------
        # 10.  Summary
        # ------------------------------------------------------------------
        _n_bld = _facades['building_id'].nunique()
        _n_win = sum(
            sum(1 for e in els if e['type'] == 'window')
            for els in _elements_per_facade
        )
        _n_door = sum(
            sum(1 for e in els if e['type'] == 'door')
            for els in _elements_per_facade
        )
        _n_balc = sum(
            sum(1 for e in els if e['type'] == 'balcony')
            for els in _elements_per_facade
        )
        _sources = set(
            e['source']
            for els in _elements_per_facade for e in els
        ) or {'none'}

        print(f"\n--- CELL 4-LoD3 summary ---")
        print(f"  Zone radius     : {_lod3_cfg.LOD3_ZONE_RADIUS_M:.0f} m around Tx")
        print(f"  Buildings in zone: {_n_bld}")
        print(f"  Facades extracted: {len(_facades)}")
        print(f"  Elements detected: {_n_win} windows | {_n_door} doors "
              f"| {_n_balc} balconies")
        print(f"  Detection source : {', '.join(sorted(_sources))}")
        print(f"  Triangles total  : {_n_tris:,}")
        print(f"  PLY files written: {len(_lod3_mat_plys)}")
        for _stem in _lod3_mat_plys:
            print(f"    {_stem}.ply  -> mat_plys['{_stem}']")
        print(f"  mat_plys entries : {len(mat_plys)} total (LoD3 added "
              f"{len(_lod3_mat_plys)})")
        print(f"---------------------------")
        print("CELL 4-LoD3: DONE — run CELL B3 to export XML with LoD3 geometry.")
