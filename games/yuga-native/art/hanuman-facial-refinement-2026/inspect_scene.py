"""Inspect a reopened studio: blender -b candidate.blend -P inspect_scene.py -- report.json."""
import hashlib
import json
from pathlib import Path
import sys
import bpy

if '--' not in sys.argv or len(sys.argv[sys.argv.index('--')+1:]) != 1:
    raise SystemExit('Expected -- report.json')
out=Path(sys.argv[sys.argv.index('--')+1]); source=Path(bpy.data.filepath)
rigs=[o for o in bpy.data.objects if o.type=='ARMATURE']
hero=bpy.data.objects.get('Hanuman skinned hero')
if len(rigs)!=1 or not hero or hero.type!='MESH': raise ValueError('Expected one hero rig and skinned mesh')
actions=sorted(a.name for a in bpy.data.actions if a.name.endswith('_YugaHeroRig'))
result={'scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'blender':bpy.app.version_string,'armatures':len(rigs),'bones':len(rigs[0].data.bones),
        'hero_vertices':len(hero.data.vertices),'hero_materials':len(hero.data.materials),
        'actions':actions,'packed_images':sum(bool(i.packed_file) for i in bpy.data.images),
        'external_libraries':len(bpy.data.libraries),
        'scope':'Reopened file inventory only; does not validate animation or visual quality.'}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
