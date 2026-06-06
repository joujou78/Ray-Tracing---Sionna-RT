# Blender → Sionna 2.0 Baking Guide

## Overview
This guide explains how to bake your Blender Nottingham project to Sionna 2.0 format while preserving the original.

---

## **Phase 1: Preparation (Preserve Original)**

### Step 1.1: Create a Working Copy
```bash
cd /home/georgeskai/Documents/FYP2026/nottingham900/

# Create backup of original
cp -r Nottingham Nottingham_ORIGINAL_BACKUP

# Create working copy for Sionna 2.0
cp -r Nottingham Nottingham_Sionna2_v1
cd Nottingham_Sionna2_v1
```

### Step 1.2: Verify Blender File
- Open: `Nottingham.blend` (or your main Blender file)
- Check **File → Project Settings** → confirm location
- Note the **scale unit** (should be meters for Sionna)

---

## **Phase 2: Material Preparation in Blender**

### Step 2.1: Review Existing Materials
In Blender, go to **Shading** workspace:
1. **Shader Editor** → Select objects and inspect materials
2. Document all material names currently used:
   - Building materials (brick, concrete, glass, wood, metal)
   - Terrain/ground materials (wet_ground, vegetation, asphalt)
   - Special surfaces (water, marble, plasterboard)

### Step 2.2: Check for Sionna 2.0 Incompatible Materials
**Sionna 2.0 does NOT support:**
- `itu_asphalt` → must remap to `mat-itu_concrete`
- `itu_water` → must remap to `mat-itu_wet_ground`
- `itu_vegetation` → must remap to `mat-itu_concrete`

**Rename these materials in Blender before export:**
```
Old Name          →  New Name
itu_asphalt       →  mat-itu_concrete
itu_water         →  mat-itu_wet_ground
itu_vegetation    →  mat-itu_concrete
```

### Step 2.3: Standardize Material Naming
Ensure all materials use one of these Sionna 2.0 valid names:
- `mat-itu_brick`
- `mat-itu_concrete`
- `mat-itu_glass`
- `mat-itu_metal`
- `mat-itu_wood`
- `mat-itu_wet_ground`
- `mat-itu_medium_dry_ground`
- `mat-itu_very_dry_ground`
- `mat-itu_marble`
- `mat-itu_plasterboard`
- `mat-itu_ceiling_board`
- `mat-itu_chipboard`
- `mat-itu_floorboard`
- `mat-itu_plywood`

Or use color names that will auto-map:
- `brick`, `concrete`, `glass`, `wood`, `metal`
- `wet_ground`, `dry_ground`
- `red`, `brown`, `grey`, `white`, `green`, `blue`, etc.

### Step 2.4: Verify Vertex Colors / Object Data
If using vertex paint colors:
1. **Object Data Properties** → check **Color Attributes**
2. Ensure color attribute names are clear (e.g., `Color`, `material_color`)
3. Document the RGB color assignments:
   ```
   Color Name    RGB Values        Sionna 2.0 Material
   brick_red     (255, 100, 50)  → mat-itu_brick
   concrete_grey (150, 150, 150) → mat-itu_concrete
   etc.
   ```

---

## **Phase 3: Export from Blender**

### Step 3.1: Clean Up Blender File
1. **File → Clean Up** → Remove unused materials/meshes
2. **Object → Apply All Transforms** for all geometry
3. **Mesh → Validate Geometry** to check for errors
4. Save: `Nottingham.blend`

### Step 3.2: Export as PLY Files (Per Material)
**Option A: Python Script in Blender Console**
```python
import bpy
import os

export_dir = "/home/georgeskai/Documents/FYP2026/nottingham900/Nottingham_Sionna2_v1/meshes"
os.makedirs(export_dir, exist_ok=True)

# Export each material's geometry as separate PLY
for mat in bpy.data.materials:
    # Select objects using this material
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and mat in obj.data.materials:
            obj.select_set(True)
    
    # Export PLY
    if bpy.context.selected_objects:
        ply_path = os.path.join(export_dir, f"{mat.name}.ply")
        bpy.ops.export_mesh.ply(
            filepath=ply_path,
            use_selection=True,
            use_normals=True,
            use_uv_coords=False
        )
        print(f"Exported: {ply_path}")
        
        # Deselect
        bpy.ops.object.select_all(action='DESELECT')
```

**Option B: Manual Export**
1. Select objects with same material → **File → Export → Export as PLY**
2. Name file: `{material_name}.ply`
3. Repeat for each material
4. Save all to `Nottingham_Sionna2_v1/meshes/` directory

### Step 3.3: Export Scene as XML (Mitsuba Format)
Blender has Mitsuba exporter. If not installed:
```bash
# In Blender Python console or terminal
pip install blender-mitsuba-exporter
```

Then in Blender:
1. **File → Export → Mitsuba** (`.xml`)
2. Save as: `Nottingham_Sionna2_v1/scene_from_blender.xml`
3. This creates XML with all material references

---

## **Phase 4: Convert to Sionna 2.0 Format**

### Step 4.1: Use Scene Builder Converter
Use the `sionna019_scene_builder.ipynb` notebook (CELL B2):

**In Jupyter:**
```python
# Configure paths
BLENDER_XML_IN = "/home/georgeskai/Documents/FYP2026/nottingham900/Nottingham_Sionna2_v1/scene_from_blender.xml"
SIONNA2_XML_OUT = "/home/georgeskai/Documents/FYP2026/nottingham900/Nottingham_Sionna2_v1/scene_sionna2.xml"

# Run CELL B2 — this will:
# 1. Read Blender materials
# 2. Map to mat-itu_* names
# 3. Auto-remap unsupported materials (asphalt→concrete, water→wet_ground, etc.)
# 4. Output scene_sionna2.xml with twosided BSDF
```

### Step 4.2: Verify Conversion
```bash
cd /home/georgeskai/Documents/FYP2026/nottingham900/Nottingham_Sionna2_v1/

# Check output
ls -lh scene_sionna2.xml
cat scene_sionna2.xml | head -50

# Verify materials
grep "bsdf type=" scene_sionna2.xml | head -20
```

Expected output:
```xml
<bsdf type="twosided" id="mat-itu_brick">
  <float name="eta" value="3.75"/>
  <float name="k" value="0.038"/>
  <spectrum name="theta_0" value="400:0.04 700:0.04"/>
  <rgb name="diffuse_reflectance" value="1.0 0.498 0.055"/>
</bsdf>
```

---

## **Phase 5: Create PLY Mesh Files**

### Step 5.1: Ensure PLY Files Are Present
```bash
cd /home/georgeskai/Documents/FYP2026/nottingham900/Nottingham_Sionna2_v1/meshes/

# List all PLY files
ls -lh *.ply

# Verify PLY file format
head -10 mat-itu_brick.ply
```

Expected header:
```
ply
format binary_little_endian 1.0
element vertex 12345
property float x
property float y
property float z
property float nx
property float ny
property float nz
end_header
```

### Step 5.2: Fix PLY References in XML
If material names changed, update XML:
```bash
# Find all shape references
grep "filename value=" scene_sionna2.xml

# Should reference: meshes/mat-itu_brick.ply, meshes/mat-itu_concrete.ply, etc.
```

---

## **Phase 6: Validate Sionna 2.0 Scene**

### Step 6.1: Test Load in Sionna
```python
import mitsuba as mi
mi.set_variant('scalar_rgb')

scene = mi.load_file("/home/georgeskai/Documents/FYP2026/nottingham900/Nottingham_Sionna2_v1/scene_sionna2.xml")
bbox = scene.bbox()
print(f"Scene loaded successfully!")
print(f"BBox: {bbox}")
print(f"Num meshes: {len(list(scene.shapes()))}")
```

### Step 6.2: Check Material Compatibility
```python
# List all materials in scene
for shape in scene.shapes():
    bsdf = shape.bsdf()
    print(f"Shape {shape.id()}: {type(bsdf).__name__}")
```

All BSDFs should be `TwoSidedBSDF` (Sionna 2.0 type).

---

## **Phase 7: Organize Final Output**

### Step 7.1: Final Directory Structure
```
Nottingham_Sionna2_v1/
├── scene_sionna2.xml          # Main scene file
├── meshes/
│   ├── mat-itu_brick.ply
│   ├── mat-itu_concrete.ply
│   ├── mat-itu_glass.ply
│   ├── mat-itu_wood.ply
│   ├── mat-itu_metal.ply
│   ├── mat-itu_wet_ground.ply
│   ├── terrain.ply             # If generated from OSM workflow
│   └── ...
├── scene_parameters.json       # (Optional) metadata
└── README.txt                  # Document material mappings
```

### Step 7.2: Create README for Material Mappings
```bash
cat > Nottingham_Sionna2_v1/README.txt << 'EOF'
# Nottingham Sionna 2.0 Scene

Generated from Blender project: Nottingham.blend
Baked to Sionna 2.0 format (mat-itu_* materials, twosided BSDF)

## Material Mapping
Original Blender     → Sionna 2.0 ITU
brick                → mat-itu_brick
concrete             → mat-itu_concrete
glass                → mat-itu_glass
wood                 → mat-itu_wood
metal                → mat-itu_metal
wet_ground           → mat-itu_wet_ground
asphalt (REMAPPED)   → mat-itu_concrete
water (REMAPPED)     → mat-itu_wet_ground
vegetation (REMAPPED)→ mat-itu_concrete

## Usage
Load scene_sionna2.xml in Sionna 2.0:
  import mitsuba as mi
  scene = mi.load_file("scene_sionna2.xml")

## Original Backup
Preserved in: Nottingham_ORIGINAL_BACKUP/
EOF
```

---

## **Summary Checklist**

- [ ] Created backup: `Nottingham_ORIGINAL_BACKUP/`
- [ ] Created working copy: `Nottingham_Sionna2_v1/`
- [ ] Renamed incompatible materials (asphalt, water, vegetation)
- [ ] Standardized all material names to `mat-itu_*` format
- [ ] Exported PLY files to `meshes/` directory
- [ ] Exported Mitsuba XML from Blender
- [ ] Ran CELL B2 (Blender → Sionna 2.0 converter)
- [ ] Generated `scene_sionna2.xml`
- [ ] Verified PLY file references match XML
- [ ] Tested scene load in Sionna 2.0 Python
- [ ] Created README with material mappings
- [ ] Original file remains untouched: `Nottingham.blend`

---

## **Troubleshooting**

### Issue: "Unknown material 'mat-itu_asphalt'"
**Cause:** Sionna 2.0 doesn't support asphalt  
**Fix:** Rename to `mat-itu_concrete` in Blender before export

### Issue: PLY files not found
**Cause:** File paths in XML don't match disk  
**Fix:** Ensure `meshes/` directory exists and PLY files are there  
```bash
ls -lh meshes/*.ply
# Should show all referenced PLY files
```

### Issue: Scene won't load in Sionna
**Cause:** Invalid BSDF or missing material definition  
**Fix:** Check XML has `type="twosided"` and all required parameters:
```xml
<bsdf type="twosided" id="mat-itu_brick">
  <float name="eta" value="..."/>
  <float name="k" value="..."/>
  <rgb name="diffuse_reflectance" value="..."/>
</bsdf>
```

### Issue: Materials look wrong in rendering
**Cause:** RGB colors not set correctly  
**Fix:** Verify `diffuse_reflectance` RGB values in XML match Sionna 2.0 ITU colors:
- `mat-itu_brick`: `1.0 0.498 0.055` (orange-red)
- `mat-itu_concrete`: `0.539 0.539 0.539` (grey)
- `mat-itu_glass`: `0.596 0.875 0.541` (light green)

---

## **Next Steps**

Once Sionna 2.0 scene is ready:
1. Copy to main simulation directory
2. Update notebook configuration paths
3. Run propagation simulation
4. Compare results with Sionna 0.19 version

