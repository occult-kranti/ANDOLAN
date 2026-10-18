"""Isolated caller presentation candidate only; never edits canonical runtime."""
from pathlib import Path
import hashlib
import difflib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE='6e9d88657b5b3a69b67e0bc93e4f45988faa65d5206d9cabdaea45543e2d19bf'
original=(ROOT/'scripts/confluence_world.gd').read_text()
assert hashlib.sha256(original.encode()).hexdigest()==BASE
text=original
anchor='var overview := false'
assert text.count(anchor)==1
text=text.replace(anchor,anchor+'''
var _overview_copy: VBoxContainer
var _overview_heading: Label
var _overview_content_rect:=Rect2()
var _overview_geometry_points:=PackedVector3Array()
var _overview_layout_busy:=false''')
anchor='\tvar screen := get_viewport().get_visible_rect().size\n\tvar compact := screen.x < 1100'
assert text.count(anchor)==1
text=text.replace(anchor,'\tif overview:\n\t\t_layout_overview_composition()\n\t\treturn\n\trama_hud.show()\n\t_restore_overview_map_parent()\n'+anchor)
start=text.index('func _build_atlas_guide()')
end=text.index('func _layout_atlas()',start)
block=text[start:end]
block=block.replace('var copy:=VBoxContainer.new()','var copy:=VBoxContainer.new()\n\t_overview_copy=copy')
block=block.replace('copy.add_child(_label("TACTICAL KEY",HeroUI.TYPE_SECTION,HeroUI.GOLD))','_overview_heading=_label("TACTICAL KEY",HeroUI.TYPE_SECTION,HeroUI.GOLD)\n\tcopy.add_child(_overview_heading)')
text=text[:start]+block+text[end:]
anchor='func _layout_atlas() -> void:\n\tif not is_inside_tree() or not is_instance_valid(map_control) or not is_instance_valid(rama_hud): return'
assert text.count(anchor)==1
text=text.replace(anchor,anchor+'\n\tif overview:\n\t\t_layout_overview_composition()\n\t\treturn\n\t_restore_overview_map_parent()')
start=text.index('func set_overview(value: bool)')
end=text.index('func get_review_camera_views()',start)
block=text[start:end]
block=block.replace('\n\tInput.mouse_mode=','\n\t_layout_world_hud()\n\tInput.mouse_mode=')
text=text[:start]+block+text[end:]
anchor='\t\tatlas_live_details.text="\\n".join(detail_rows)'
assert text.count(anchor)==1
text=text.replace(anchor,'\t\tif overview: detail_rows.insert(1,"Rama health "+rama_hud.life_text.text)\n'+anchor)
text=text.replace('atlas_live_details.text="\\n".join(detail_rows)', 'if overview: detail_rows.append("Reading: ↑ / ↓ · PgUp / PgDn · Home / End")\n\t\tatlas_live_details.text="\\n".join(detail_rows)')
text+='\n'+(HERE/'overview_methods.gd.inc').read_text()
(HERE/'confluence_world.candidate.gd').write_text(text)
(HERE/'confluence_world.baseline.gd.txt').write_text(original)
(HERE/'presentation-only.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='canonical6e9d/confluence_world.gd',tofile='isolated-overview/confluence_world.gd')))
print(hashlib.sha256(text.encode()).hexdigest())
