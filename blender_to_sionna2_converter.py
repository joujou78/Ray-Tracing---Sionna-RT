#!/usr/bin/env python3
"""
Blender → Sionna 2.0 Scene Converter

Converts Blender-exported Mitsuba XML to Sionna 2.0 compatible format:
- Maps materials to mat-itu_* naming (Sionna 2.0 standard)
- Remaps unsupported materials (asphalt→concrete, water→wet_ground, vegetation→concrete)
- Sets BSDF type to twosided (Sionna 2.0 standard)
- Adds visual colors for rendering

Usage:
    python3 blender_to_sionna2_converter.py \
        --input scene_from_blender.xml \
        --output scene_sionna2.xml \
        --meshes-dir meshes/
"""

import xml.etree.ElementTree as ET
import argparse
import os
import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# SIONNA 2.0 ITU MATERIAL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Sionna 2.0 ITU materials (14 total, mat-itu_* prefix)
ITU_MATS_020 = {
    'mat-itu_brick'             : (3.75,  0.038,  '1.0 0.498 0.055'),
    'mat-itu_concrete'          : (5.31,  0.092,  '0.539 0.539 0.539'),
    'mat-itu_glass'             : (6.27,  0.000,  '0.596 0.875 0.541'),
    'mat-itu_metal'             : (1.00, 1.0e7,  '0.220 0.220 0.254'),
    'mat-itu_wood'              : (1.99,  0.000,  '0.043 0.580 0.184'),
    'mat-itu_wet_ground'        : (30.0,  0.020,  '0.910 0.569 0.055'),
    'mat-itu_medium_dry_ground' : (4.00,  0.001,  '0.780 0.780 0.780'),
    'mat-itu_very_dry_ground'   : (2.80,  0.000,  '0.498 0.498 0.498'),
    'mat-itu_marble'            : (2.70,  0.000,  '0.701 0.644 0.485'),
    'mat-itu_plasterboard'      : (2.50,  0.000,  '1.0 0.733 0.471'),
    'mat-itu_ceiling_board'     : (1.50,  0.000,  '0.9 0.9 0.9'),
    'mat-itu_chipboard'         : (2.20,  0.000,  '0.6 0.55 0.4'),
    'mat-itu_floorboard'        : (2.20,  0.000,  '0.8 0.6 0.3'),
    'mat-itu_plywood'           : (2.80,  0.000,  '0.7 0.5 0.2'),
}

# Blender/Sionna 0.19 → Sionna 2.0 material mapping (with remapping for unsupported)
BLENDER_TO_020 = {
    # Exact mat-itu_* pass-through
    'mat-itu_brick'             : 'mat-itu_brick',
    'mat-itu_concrete'          : 'mat-itu_concrete',
    'mat-itu_glass'             : 'mat-itu_glass',
    'mat-itu_metal'             : 'mat-itu_metal',
    'mat-itu_wood'              : 'mat-itu_wood',
    'mat-itu_wet_ground'        : 'mat-itu_wet_ground',
    'mat-itu_medium_dry_ground' : 'mat-itu_medium_dry_ground',
    'mat-itu_very_dry_ground'   : 'mat-itu_very_dry_ground',
    'mat-itu_marble'            : 'mat-itu_marble',
    'mat-itu_plasterboard'      : 'mat-itu_plasterboard',
    'mat-itu_ceiling_board'     : 'mat-itu_ceiling_board',
    'mat-itu_chipboard'         : 'mat-itu_chipboard',
    'mat-itu_floorboard'        : 'mat-itu_floorboard',
    'mat-itu_plywood'           : 'mat-itu_plywood',

    # Sionna 0.19 itu_* names → mat-itu_* with remapping for unsupported
    'itu_brick'                 : 'mat-itu_brick',
    'itu_concrete'              : 'mat-itu_concrete',
    'itu_glass'                 : 'mat-itu_glass',
    'itu_metal'                 : 'mat-itu_metal',
    'itu_wood'                  : 'mat-itu_wood',
    'itu_wet_ground'            : 'mat-itu_wet_ground',
    'itu_asphalt'               : 'mat-itu_concrete',          # ← REMAPPED
    'itu_water'                 : 'mat-itu_wet_ground',        # ← REMAPPED
    'itu_vegetation'            : 'mat-itu_concrete',          # ← REMAPPED
    'itu_grass'                 : 'mat-itu_concrete',
    'itu_ground'                : 'mat-itu_wet_ground',
    'itu_marble'                : 'mat-itu_marble',
    'itu_plasterboard'          : 'mat-itu_plasterboard',
    'itu_ceiling_board'         : 'mat-itu_ceiling_board',
    'itu_chipboard'             : 'mat-itu_chipboard',
    'itu_floorboard'            : 'mat-itu_floorboard',

    # Bare names
    'concrete'                  : 'mat-itu_concrete',
    'brick'                     : 'mat-itu_brick',
    'glass'                     : 'mat-itu_glass',
    'wood'                      : 'mat-itu_wood',
    'metal'                     : 'mat-itu_metal',
    'asphalt'                   : 'mat-itu_concrete',          # ← REMAPPED
    'wet_ground'                : 'mat-itu_wet_ground',
    'vegetation'                : 'mat-itu_concrete',          # ← REMAPPED
    'water'                     : 'mat-itu_wet_ground',        # ← REMAPPED

    # Color names
    'white'                     : 'mat-itu_concrete',
    'grey'                      : 'mat-itu_concrete',
    'darkgrey'                  : 'mat-itu_concrete',
    'red'                       : 'mat-itu_brick',
    'salmon'                    : 'mat-itu_brick',
    'tan'                       : 'mat-itu_brick',
    'brown'                     : 'mat-itu_brick',
    'd5b9a3'                    : 'mat-itu_brick',
    '85552e'                    : 'mat-itu_brick',
    'ff9e6b'                    : 'mat-itu_brick',
    'green'                     : 'mat-itu_concrete',          # ← REMAPPED
    'lime'                      : 'mat-itu_concrete',          # ← REMAPPED
    'forest'                    : 'mat-itu_concrete',          # ← REMAPPED
    'darkgreen'                 : 'mat-itu_concrete',          # ← REMAPPED
    'blue'                      : 'mat-itu_wet_ground',        # ← REMAPPED
    'darkblue'                  : 'mat-itu_wet_ground',        # ← REMAPPED
    'cyan'                      : 'mat-itu_wet_ground',        # ← REMAPPED
    'yellow'                    : 'mat-itu_concrete',
    'orange'                    : 'mat-itu_brick',

    # Road/pavement surfaces (→ concrete, since asphalt not valid in 2.0)
    'road'                      : 'mat-itu_concrete',
    'pavement'                  : 'mat-itu_concrete',
    'areas_pedestrian'          : 'mat-itu_concrete',
    'areas_service'             : 'mat-itu_concrete',
    'areas_railways'            : 'mat-itu_concrete',
    'areas_footway'             : 'mat-itu_concrete',
    'areas_road'                : 'mat-itu_concrete',
}


def resolve_material(mat_id: str) -> tuple:
    """
    Resolve Blender material ID to Sionna 2.0 mat-itu_* name.

    Returns:
        (sionna2_name, was_remapped) tuple
    """
    mat_id_lower = mat_id.lower().replace('mat-', '')

    # Direct lookup
    if mat_id_lower in BLENDER_TO_020:
        final_mat = BLENDER_TO_020[mat_id_lower]
        was_remapped = (final_mat != mat_id_lower)
        return final_mat, was_remapped

    # Try original case
    if mat_id in BLENDER_TO_020:
        final_mat = BLENDER_TO_020[mat_id]
        was_remapped = (final_mat != mat_id)
        return final_mat, was_remapped

    # Unknown → default to concrete
    print(f"  [WARN] Unknown material '{mat_id}' → mat-itu_concrete (add to BLENDER_TO_020 to override)")
    return 'mat-itu_concrete', True


def convert_blender_to_sionna2(input_xml: str, output_xml: str, verbose: bool = True) -> dict:
    """
    Convert Blender-exported Mitsuba XML to Sionna 2.0 compatible format.

    Args:
        input_xml: Path to Blender-exported scene.xml
        output_xml: Path to output Sionna 2.0 scene.xml
        verbose: Print conversion details

    Returns:
        dict with conversion statistics
    """

    if not os.path.exists(input_xml):
        raise FileNotFoundError(f"Input XML not found: {input_xml}")

    if verbose:
        print("="*70)
        print("BLENDER → SIONNA 2.0 CONVERTER")
        print("="*70)
        print(f"Input:  {input_xml}")
        print(f"Output: {output_xml}")
        print()

    # Parse input XML
    tree = ET.parse(input_xml)
    root = tree.getroot()

    # Collect all materials used
    used_mat_ids = set()
    for shape in root.findall('.//shape'):
        ref = shape.find('ref[@name="bsdf"]')
        if ref is not None:
            used_mat_ids.add(ref.get('id'))

    if verbose:
        print(f"Found {len(used_mat_ids)} materials in input:")
        for mat in sorted(used_mat_ids):
            print(f"  - {mat}")
        print()

    # Resolve to Sionna 2.0 names
    mat_resolved = {}
    remappings = []
    for mat_id in used_mat_ids:
        sionna2_name, was_remapped = resolve_material(mat_id)
        mat_resolved[mat_id] = sionna2_name
        if was_remapped:
            remappings.append((mat_id, sionna2_name))

    if verbose and remappings:
        print("Material Remappings (unsupported → nearest valid):")
        for orig, final in remappings:
            print(f"  {orig:<35} → {final}")
        print()

    used_sionna2_mats = sorted(set(mat_resolved.values()))

    # Build output XML
    out_lines = []
    out_lines.append('<?xml version="1.0" encoding="utf-8"?>')
    out_lines.append('<scene version="2.1.0">')
    out_lines.append('')
    out_lines.append('  <!-- ── ITU-R P.2040-2 Materials (Sionna 2.0) ────────── -->')
    out_lines.append('  <!-- NOTE: Sionna 2.0 EXCLUDES asphalt, water, vegetation -->')
    out_lines.append('')

    # Write material definitions
    for mat_name in used_sionna2_mats:
        if mat_name not in ITU_MATS_020:
            print(f"  [ERROR] Material '{mat_name}' not in Sionna 2.0 definitions!")
            continue

        eps, sigma, rgb = ITU_MATS_020[mat_name]
        out_lines.append(f'  <bsdf type="twosided" id="{mat_name}">')
        out_lines.append(f'    <float name="eta" value="{eps}"/>')
        out_lines.append(f'    <float name="k"   value="{sigma}"/>')
        out_lines.append(f'    <spectrum name="theta_0" value="400:0.04 700:0.04"/>')
        out_lines.append(f'    <rgb name="diffuse_reflectance" value="{rgb}"/>')
        out_lines.append(f'  </bsdf>')
        out_lines.append('')

    out_lines.append('  <!-- ── Shapes ─────────────────────────────────────────── -->')
    out_lines.append('')

    # Write shapes with resolved materials
    num_shapes = 0
    for shape in root.findall('.//shape'):
        stype = shape.get('type', 'ply')
        sid = shape.get('id', '')
        filename = shape.findtext('string[@name="filename"]') or ''
        ref = shape.find('ref[@name="bsdf"]')

        if ref is None:
            continue

        orig_mat = ref.get('id')
        sionna2_mat = mat_resolved.get(orig_mat, 'mat-itu_concrete')

        out_lines.append(f'  <shape type="{stype}" id="{sid}">')
        out_lines.append(f'    <string name="filename" value="{filename}"/>')
        out_lines.append(f'    <ref id="{sionna2_mat}" name="bsdf"/>')
        out_lines.append(f'    <boolean name="face_normals" value="true"/>')
        out_lines.append(f'  </shape>')
        num_shapes += 1

    out_lines.append('')
    out_lines.append('</scene>')

    # Write output
    os.makedirs(os.path.dirname(output_xml) or '.', exist_ok=True)
    with open(output_xml, 'w') as f:
        f.write('\n'.join(out_lines))

    if verbose:
        print(f"Wrote: {output_xml}")
        print()
        print("Conversion Summary:")
        print(f"  Input materials  : {len(used_mat_ids)}")
        print(f"  Output materials : {len(used_sionna2_mats)}")
        print(f"  Remappings       : {len(remappings)}")
        print(f"  Shapes           : {num_shapes}")
        print(f"  BSDF Type        : twosided (Sionna 2.0 standard)")
        print()

    return {
        'input_materials': len(used_mat_ids),
        'output_materials': len(used_sionna2_mats),
        'remappings': len(remappings),
        'shapes': num_shapes,
        'output_file': output_xml,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Convert Blender-exported XML to Sionna 2.0 compatible format'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input Blender XML file (scene_from_blender.xml)'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output Sionna 2.0 XML file (scene_sionna2.xml)'
    )
    parser.add_argument(
        '--meshes-dir', '-m',
        default='meshes/',
        help='Directory containing PLY mesh files (for validation)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress verbose output'
    )

    args = parser.parse_args()

    try:
        stats = convert_blender_to_sionna2(
            args.input,
            args.output,
            verbose=not args.quiet
        )

        # Verify mesh files exist if directory provided
        if os.path.exists(args.meshes_dir) and not args.quiet:
            ply_files = list(Path(args.meshes_dir).glob('*.ply'))
            print(f"✓ Found {len(ply_files)} PLY mesh files in {args.meshes_dir}")

        print("\n✓ Conversion completed successfully!")
        return 0

    except Exception as e:
        print(f"\n✗ Conversion failed: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
