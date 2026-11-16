#!/usr/bin/env python3
"""Bind shipped tactical art/code to exact source files, excluding import caches."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]/'games/yuga-native'
TARGET=ROOT/'assets/tactical/content-manifest.json'
def main():
    files=set()
    for folder,pattern in [('scripts','tactical_*.gd'),('shaders','tactical_*.gdshader'),('scenes','tactical_*.tscn')]:
        files.update((ROOT/folder).glob(pattern))
    files.update(p for p in (ROOT/'assets/tactical').rglob('*') if p.is_file() and p!=TARGET and p.suffix not in ('.import','.uid'))
    files.update(ROOT/relative for relative in json.loads((ROOT/'assets/tactical/map.json').read_text()).get('reused_sources',{}))
    for relative in ['project.godot','scripts/lane_infantry_art.gd','scripts/hero_ui_theme.gd','scripts/world_ground.gdshader','scripts/world_ground_common.gdshaderinc','shaders/sangam_masonry.gdshader','assets/world/sangam-district.glb','assets/world/sangam-district.json','assets/fonts/NotoSans-Regular.ttf','assets/fonts/NotoSerif-Regular.ttf','assets/fonts/DejaVuSans.ttf']:
        files.add(ROOT/relative)
    result={'schema_version':1,'id':'yuga-sanctum-casual-v1','entry_scene':'res://scenes/tactical_frontend.tscn','authority':'local offline, one human and nine bots','format':{'players_per_team':5,'rounds_to_win':13,'swap_after_round':12,'ranked_available':False},'legacy_catalog_scope':'Existing native-contracts-v1.json profiles retain historical practice/army identity. This separate tactical content manifest does not change browser protocol or claim network authority.','notices':['NOTICE/TACTICAL-ART.md','NOTICE/TACTICAL-MAP.md'],'files':{}}
    for p in sorted(files):
        data=p.read_bytes();result['files'][p.relative_to(ROOT).as_posix()]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    TARGET.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'files':len(files),'manifest':str(TARGET),'sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
