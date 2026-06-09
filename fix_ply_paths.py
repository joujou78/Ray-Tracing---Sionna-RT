"""
fix_ply_paths.py — patches scene_with_roads_019.xml with absolute PLY paths.
Run once after CELL B1 if validation shows [REL] or [MISS].

Usage:
    python fix_ply_paths.py
"""
import os, xml.etree.ElementTree as ET

# ── Paths (edit if your layout differs) ──────────────────────────────────────
SCENE_DIR  = os.path.expanduser(
    '~/sionna_rt/nottingham_ofcom2018_915mhz_dem/scene')
MESH_DIR   = os.path.join(SCENE_DIR, 'meshes_roads')
XML_PATH   = os.path.join(SCENE_DIR, 'scene_with_roads_019.xml')

# ── Build PLY lookup {stem: absolute_path} ────────────────────────────────────
ply_lookup = {}
for root_dir, dirs, files in os.walk(MESH_DIR):
    for f in files:
        if f.endswith('.ply'):
            ply_lookup[f[:-4]] = os.path.join(root_dir, f)
print(f'PLY files found: {sorted(ply_lookup.keys())}')

# ── Parse XML ─────────────────────────────────────────────────────────────────
ET.register_namespace('', '')
tree = ET.parse(XML_PATH)
xml_root = tree.getroot()

fixed = 0
for shape in xml_root.findall('.//shape'):
    sid = shape.get('id', '')
    fn_elem = shape.find('string[@name="filename"]')
    if fn_elem is None:
        fn_elem = ET.SubElement(shape, 'string')
        fn_elem.set('name', 'filename')

    current = fn_elem.get('value', '')
    if current and os.path.isfile(current):
        print(f'  [OK  ] {sid} — already valid')
        continue

    # Resolve via S4: shape ID stem
    resolved = ''
    if sid.startswith('mesh-'):
        stem = sid[len('mesh-'):]
        if stem == 'ground':
            stem = 'terrain'
        if stem in ply_lookup:
            resolved = ply_lookup[stem]

    if resolved:
        fn_elem.set('value', resolved)
        fixed += 1
        print(f'  [FIXED] {sid} -> {resolved}')
    else:
        print(f'  [ERR  ] {sid} — cannot resolve (stem not in MESH_DIR)')

# ── Write back ────────────────────────────────────────────────────────────────
# Rebuild XML as string to preserve formatting
lines = ['<?xml version="1.0" encoding="utf-8"?>\n']
lines.append('<scene version="2.1.0">\n\n')

for bsdf in xml_root.findall('bsdf'):
    bid   = bsdf.get('id', '')
    btype = bsdf.get('type', 'diffuse')
    lines.append(f'  <bsdf type="{btype}" id="{bid}">\n')
    for child in bsdf:
        name = child.get('name', '')
        val  = child.get('value', '')
        lines.append(f'    <{child.tag} name="{name}" value="{val}"/>\n')
    lines.append('  </bsdf>\n\n')

for shape in xml_root.findall('shape'):
    sid   = shape.get('id', '')
    stype = shape.get('type', 'ply')
    lines.append(f'  <shape type="{stype}" id="{sid}">\n')
    for child in shape:
        tag  = child.tag
        name = child.get('name', '')
        val  = child.get('value', '') or child.get('id', '')
        if tag == 'ref':
            lines.append(f'    <ref id="{val}" name="{name}"/>\n')
        else:
            lines.append(f'    <{tag} name="{name}" value="{val}"/>\n')
    lines.append('  </shape>\n')

lines.append('\n</scene>\n')

with open(XML_PATH, 'w') as f:
    f.writelines(lines)

print(f'\nDone — fixed {fixed} PLY paths.')
print(f'Wrote: {XML_PATH}')

# ── Validate ──────────────────────────────────────────────────────────────────
print('\nValidation:')
fail = 0
for shape in ET.parse(XML_PATH).getroot().findall('.//shape'):
    fn = shape.findtext('string[@name="filename"]') or ''
    ok = os.path.isfile(fn)
    icon = 'OK  ' if ok else 'MISS'
    if not ok:
        fail += 1
    print(f'  [{icon}] {fn}')
if fail == 0:
    print('All PLY paths valid — ready for differentiable RT.')
else:
    print(f'FIX NEEDED: {fail} path(s) still invalid.')
