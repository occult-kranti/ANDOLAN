"""Render saved unit authoring files; never rewrite GLBs or their manifest."""
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_minions import UNITS, LOCAL, preview

requested = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
for unit in UNITS:
    if requested and unit['id'] not in requested:
        continue
    bpy.ops.wm.open_mainfile(filepath=str(LOCAL / (unit['id'] + '-authored.blend')))
    rig = bpy.data.objects['YugaUnitRig']
    preview(rig, {action.name: action for action in bpy.data.actions}, unit)
