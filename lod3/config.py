"""LoD3 module configuration knobs.

All distance values in metres (BNG / EPSG:27700).
Set LOD3_ENABLE = True in the scene builder CELL 0 to activate the pipeline.
"""

LOD3_ENABLE = False

# Zone geometry
LOD3_ZONE_RADIUS_M = 400          # radius around Tx for LoD3 buildings
LOD3_CORRIDOR_BUFFER_M = 30       # extra buffer along drive-test routes

# Detail resolution (linked to wavelength: lambda/4 at 5.85 GHz ~ 1.3 cm)
LOD3_DETAIL_THRESHOLD_M = 0.10    # minimum facade element size

# Window / door geometry defaults
LOD3_DEFAULT_RECESS_M = 0.20      # window recess depth (wall thickness proxy)
LOD3_DEFAULT_WINDOW_RATIO = 0.35  # fallback window-to-wall ratio (EPC-derived)
LOD3_DEFAULT_FLOOR_H_M = 3.0      # assumed storey height for floor snapping

# Mapillary imagery date range (match Ofcom 2017-2018 survey period)
LOD3_IMAGE_DATE_RANGE = ("2016-01-01", "2018-12-31")
LOD3_IMAGE_MAX_DIST_M = 30.0      # max camera distance from facade centre
LOD3_IMAGE_MIN_FILL = 0.20        # facade must cover >= 20 % of image width

# Procedural fallback
LOD3_ALLOW_PROCEDURAL = False     # True to allow statistical LoD3 when no imagery

# PLY naming prefix (must match mat_plys keys in scene builder)
LOD3_PLY_PREFIX = "bld_lod3"

# Mapillary API
MAPILLARY_API_BASE = "https://graph.mapillary.com"
MAPILLARY_TOKEN_ENV = "MAPILLARY_TOKEN"  # read from environment variable
