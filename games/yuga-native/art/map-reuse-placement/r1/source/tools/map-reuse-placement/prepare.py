#!/usr/bin/env python3
"""Pin whole connected source pieces; never generate or copy art payloads."""
import argparse,hashlib,json,math,shutil,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
ROOT=PROJECT.parents[1]
SOURCE=PROJECT/'assets/environment/lanka_courtyard.glb'
EXPECTED='1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory():
 raw=SOURCE.read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
 def read(i):
  a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];f={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']];fmt='<'+f*n;stride=v.get('byteStride',struct.calcsize(fmt));off=v.get('byteOffset',0)+a.get('byteOffset',0)
  return [struct.unpack_from(fmt,binary,off+k*stride) for k in range(a['count'])]
 selected=[];rejected=[]
 for node in doc['nodes']:
  if 'mesh' not in node or not node['name'].startswith(('COL_','DECOR_')):continue
  if set(node)!={'mesh','name'}:raise ValueError('source node transform changed')
  for pi,p in enumerate(doc['meshes'][node['mesh']]['primitives']):
   pos=read(p['attributes']['POSITION']);ind=[x[0] for x in read(p['indices'])];count=len(ind)//3;parent=list(range(count));weld={}
   def find(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
   for ti in range(count):
    for vi in ind[ti*3:ti*3+3]:
     key=tuple(round(c,5) for c in pos[vi]);other=weld.setdefault(key,ti);a,b=find(ti),find(other)
     if a!=b:parent[a]=b
   groups={}
   for i in range(count):groups.setdefault(find(i),[]).append(i)
   chosen=[];components=[]
   for ids in groups.values():
    points=[pos[v] for i in ids for v in ind[i*3:i*3+3]];lo=[min(p[k] for p in points) for k in range(3)];hi=[max(p[k] for p in points) for k in range(3)]
    # Entire existing gate pieces only, without clipping a single source face.
    if lo[0]>=-13.2 and hi[0]<=13.2 and lo[1]>=-.05 and hi[1]<=17 and lo[2]>=-30 and hi[2]<=-18.8:
     chosen.extend(ids);components.append({'first_source_triangle':min(ids),'triangles':len(ids),'min':lo,'max':hi})
   if chosen:
    selected.append({'node':node['name'],'surface':pi,'material':doc['materials'][p['material']]['name'],'collision':node['name'].startswith('COL_'),'source_triangle_ids':sorted(chosen),'source_triangles_total':count,'components':components})
   rejected.append({'node':node['name'],'source_triangles':count,'selected_triangles':len(chosen),'whole_components':len(components)})
 return {'schema':1,'source_sha256':EXPECTED,'selection_rule':'Whole position-welded connected components fully within x[-13.2,13.2],y[-.05,17],z[-30,-18.8]; no face clipping, no regenerated geometry','placement_translation':[-40,0,-29.2],'source_gate_center':[0,0,-24.8],'world_gate_center':[-40,0,-54],'units':'Source metre Y-up; rigid translation only; preserve original UV/normals/tangents/materials','canonical_enabled':False,'selected':selected,'inventory':rejected,'triangles':sum(len(s['source_triangle_ids']) for s in selected),'collision_triangles':sum(len(s['source_triangle_ids']) for s in selected if s['collision']),'surfaces':len(selected),'components':sum(len(s['components']) for s in selected)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();out=args.output.resolve()
 if out.exists() or out.is_relative_to(ROOT):raise ValueError('fresh outside-checkout scratch project required')
 if sha(SOURCE)!=EXPECTED:raise ValueError('source drift')
 meta=json.loads((SOURCE.with_suffix('.metadata.json')).read_text())
 if not meta['license'].startswith('CC0-1.0') or meta['coordinate_system']!='metres; GLB Y-up; XZ ground, y=0 walking surface':raise ValueError('licence/units changed')
 selection=inventory();out.mkdir(parents=True);(out/'assets/environment').mkdir(parents=True);(out/'assets/environment/lanka_courtyard.glb').symlink_to(SOURCE)
 (out/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
 rows=[]
 for name in ['project.godot','placement.gd','test_placement.gd','capture.gd']:
  src=HERE/name;destination=out/name if name=='project.godot' else out/'tools/map-reuse-placement'/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,destination);rows.append({'path':str(src.relative_to(ROOT)),'sha256':sha(src)})
 (out/'tools/map-reuse-intake').mkdir();shutil.copyfile(PROJECT/'tools/map-reuse-intake/map_loader.gd',out/'tools/map-reuse-intake/map_loader.gd');rows.append({'path':'games/yuga-native/tools/map-reuse-intake/map_loader.gd','sha256':sha(out/'tools/map-reuse-intake/map_loader.gd')})
 # Access current accepted native hero/world at their actual paths; no payload copies/imports.
 (out/'native').symlink_to(PROJECT,target_is_directory=True)
 manifest={'schema':1,'source':str(SOURCE.relative_to(ROOT)),'sha256':EXPECTED,'bytes':SOURCE.stat().st_size,'license':meta['license'],'payload_bytes_copied':0,'selection_sha256':sha(out/'selection.json'),'scripts':rows,'source_metadata':meta,'scope':'Isolated reuse-first lane gate, not runtime promotion or complete map'}
 (out/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:selection[k] for k in ['triangles','collision_triangles','surfaces','components']}))
if __name__=='__main__':main()
