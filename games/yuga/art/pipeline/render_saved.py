"""Render already built local .blends without mutating published GLBs or manifest."""
import sys
from pathlib import Path
import bpy
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build_heroes import HEROES,preview
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['rama','hanuman','sita']
for hero in HEROES:
    if hero['id'] not in args:continue
    path=Path('/workspace/tooling/yuga-art/output')/f"{hero['id']}-authored.blend"
    bpy.ops.wm.open_mainfile(filepath=str(path))
    rig=bpy.data.objects['YugaHeroRig'];actions={a.name:a for a in bpy.data.actions}
    preview(rig,actions,hero)
