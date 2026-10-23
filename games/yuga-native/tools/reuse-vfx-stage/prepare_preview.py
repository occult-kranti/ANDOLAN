#!/usr/bin/env python3
"""Assemble a small isolated Godot preview from existing project effects/assets."""
from pathlib import Path
import argparse, hashlib, json, shutil
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
EXISTING={
 'scripts/rama_ability_effects.gd':'games/yuga-native/scripts/rama_ability_effects.gd',
 'shaders/rama_ribbon.gdshader':'games/yuga-native/shaders/rama_ribbon.gdshader',
 'shaders/rama_ability_calligraphy.gdshader':'games/yuga-native/shaders/rama_ability_calligraphy.gdshader',
 'shaders/rama_ability_boundary.gdshader':'games/yuga-native/shaders/rama_ability_boundary.gdshader',
 'assets/diya.glb':'games/yuga-native/art/concepts/cloud-diya-pilot/candidate.glb',
}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 output=a.output.resolve()
 if output.exists():raise ValueError('Use a fresh project directory')
 if output.is_relative_to(ROOT):raise ValueError('Preview project must be outside canonical checkout')
 output.mkdir(parents=True);rows=[]
 for dest,src in EXISTING.items():
  source=ROOT/src;target=output/dest;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
  rows.append({'source':src,'target':dest,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bytes':source.stat().st_size,'role':'Exact reused original project source'})
 for name in ['project.godot','flame_lamp.gd','flame.gdshader','source_mask.gdshader','event_fixture.gd','source_loader.gd','preview.gd','test_stage.gd']:
  source=HERE/name;shutil.copyfile(source,output/name)
  rows.append({'source':str(source.relative_to(ROOT)),'target':name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bytes':source.stat().st_size,'role':'New isolated integration'})
 (output/'source-manifest.json').write_text(json.dumps({'schema_version':1,'files':rows,'scope':'Isolated source reuse only; no native runtime promotion.'},indent=2)+'\n')
 print(json.dumps({'project':str(output),'copied':len(rows)}))
if __name__=='__main__':main()
