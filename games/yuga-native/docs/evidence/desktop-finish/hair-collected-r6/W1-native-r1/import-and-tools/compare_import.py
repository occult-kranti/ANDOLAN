"""Strict imported hair census; source and all nonhair packed bytes stay exact."""
import hashlib,json,shutil,sys,tarfile
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parent;REPO=Path('/workspace/ANDOLAN/games/yuga-native')
sys.path.insert(0,str(REPO/'art/hero-rama-lod'));from glb_lod import GLB
sys.path.insert(0,str(W/'runner'));import snapshot
SOURCE=REPO/'art/hero-finish/hair-collected-r6/candidate-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def differences(a,b,path=''):
 if type(a)!=type(b):return[path]
 if isinstance(a,dict):return[d for k in sorted(set(a)|set(b))for d in(differences(a[k],b[k],path+'/'+k)if k in a and k in b else[path+'/'+k])]
 if isinstance(a,list):return[path]if len(a)!=len(b)else[d for i,(x,y)in enumerate(zip(a,b))for d in differences(x,y,path+'/'+str(i))]
 return[]if a==b else[path]
def exact(a,b,label):assert a.tobytes()==b.tobytes(),label

def exact_files(before,after,bpath,cpath,label):
 assert len(before)==len(after),label
 for i,(a,b) in enumerate(zip(before,after)):
  assert a==b,(label,i,'Metadata changed')
  if 'file'in a:assert(bpath/a['file']).read_bytes()==(cpath/b['file']).read_bytes(),(label,i,'Packed bytes changed, signed zeros included')

def hair_bounds(surface,source,directory):
 arrays=surface['arrays'];p=source.doc['meshes'][2]['primitives'][0]
 expected_v=source.array(p['attributes']['POSITION']);expected_i=source.array(p['indices']).reshape(-1)
 assert arrays[0]['type']=='PackedVector3Array' and arrays[0]['count']==len(expected_v),'Imported hair vertex census differs from declared raw source'
 assert arrays[12]['type']=='PackedInt32Array' and arrays[12]['count']==len(expected_i),'Imported hair index census differs from declared raw source'
 positions=np.fromfile(directory/arrays[0]['file'],dtype='<f4').reshape(-1,3);indices=np.fromfile(directory/arrays[12]['file'],dtype='<i4')
 assert len(positions)==len(expected_v) and len(indices)==len(expected_i)
 assert len(indices)%3==0 and indices.min()>=0 and indices.max()<len(positions)
 assert np.isfinite(positions).all()
 delta=float(max(np.max(abs(positions.min(0)-expected_v.min(0))),np.max(abs(positions.max(0)-expected_v.max(0)))))
 assert delta<=.00002,('Imported hair bounds exceed20um source packing tolerance',delta)
 float_types={'PackedFloat32Array':('<f4',1),'PackedFloat64Array':('<f8',1),'PackedVector2Array':('<f4',2),'PackedVector3Array':('<f4',3),'PackedColorArray':('<f4',4)}
 finite=[]
 for row in arrays:
  if row['type'] not in float_types:continue
  dtype,width=float_types[row['type']];raw=(directory/row['file']).read_bytes();v=np.frombuffer(raw,dtype=dtype)
  assert len(raw)==row['bytes'] and len(v)==row['count']*width and np.isfinite(v).all(),('Nonfinite or wrong-size imported hair array',row['index'])
  finite.append(row['index'])
 return {'declared_raw_vertices':len(expected_v),'declared_raw_triangles':len(expected_i)//3,'actual_imported_vertices':len(positions),'actual_imported_triangles':len(indices)//3,'source_bounds_min':expected_v.min(0).tolist(),'source_bounds_max':expected_v.max(0).tolist(),'imported_bounds_min':positions.min(0).tolist(),'imported_bounds_max':positions.max(0).tolist(),'maximum_bounds_error_m':delta,'packing_tolerance_m':.00002,'finite_float_arrays':finite}

def main():
 prep=json.loads((W/'import-preparation.json').read_text());frozen=Path(prep['frozen_source']);baseline=Path(prep['baseline_cached_project']);imported=Path(prep['candidate_project'])
 manifest=json.loads((SOURCE/'manifest.json').read_text());assert sha(SOURCE/'manifest.json')==prep['candidate_manifest_sha256']
 assert manifest['inactive']
 bpath=W.parent/'semantics-baseline';cpath=W.parent/'semantics-candidate';b=json.loads((bpath/'semantics.json').read_text());c=json.loads((cpath/'semantics.json').read_text());assert b['complete']and c['complete']and len(b['lods'])==len(c['lods'])==3
 allowed=set();required=set();levels=[]
 for lod,(level,row) in enumerate(manifest['levels'].items()):
  before,after=b['lods'][lod],c['lods'][lod];filename=Path(row['output']).name;rel=Path('assets/heroes')/filename;oldg=GLB(frozen/rel);newg=GLB(SOURCE/filename)
  assert sha(oldg.path)==before['raw_sha256']==prep['canonical_raw_pins'][level];assert sha(newg.path)==after['raw_sha256']==row['output_sha256']
  assert newg.binary[:len(oldg.binary)]==oldg.binary,'Accepted canonical UV binary prefix changed'
  for mi,pi,p in oldg.primitives():
   if (mi,pi)==(2,0):continue
   assert p==newg.doc['meshes'][mi]['primitives'][pi]
   for index in set(p['attributes'].values())|{p['indices']}|{i for t in p.get('targets',[])for i in t.values()}:exact(oldg.array(index),newg.array(index),'Nonhair source bytes changed')
  for key in ['path','descriptor_sha256','imported_path']:assert before[key]==after[key]
  required.update([f'/lods/{lod}/raw_sha256',f'/lods/{lod}/imported_sha256']);allowed.update(required)
  hair=[]
  assert len(before['nodes'])==len(after['nodes'])
  for ni,(bn,cn) in enumerate(zip(before['nodes'],after['nodes'])):
   if 'surfaces'not in bn:continue
   assert len(bn['surfaces'])==len(cn['surfaces'])
   for si,(bs,cs) in enumerate(zip(bn['surfaces'],cn['surfaces'])):
    is_hair=bn['path'].endswith('/RamaHero')and bs['material']['name']=='Swept black hair'
    if is_hair:
     assert cs['material']==bs['material']and cs['morph_arrays']==bs['morph_arrays']and cs['morphs']==bs['morphs']
     assert len(bs['arrays'])==len(cs['arrays'])
     for ai,(ba,ca) in enumerate(zip(bs['arrays'],cs['arrays'])):
      assert ba['type']==ca['type']and ba['index']==ca['index']
      if 'file'in ba:assert ba['file']==ca['file']
      prefix=f'/lods/{lod}/nodes/{ni}/surfaces/{si}/arrays/{ai}'
      allowed.update(prefix+'/'+field for field in ['digest','bytes','count'])
     hair.append((ni,si,hair_bounds(cs,newg,cpath)))
    else:exact_files(bs['arrays'],cs['arrays'],bpath,cpath,'Nonhair surface'+str((lod,ni,si)))
    for shape,bshape in zip(bs['morph_arrays'],cs['morph_arrays']):exact_files(shape,bshape,bpath,cpath,'Morph packed arrays'+str((lod,ni,si)))
  assert len(hair)==1;ni,si,bounds=hair[0]
  required.add(f'/lods/{lod}/nodes/{ni}/surfaces/{si}/arrays/0/digest')
  rigs=[n for n in after['nodes']if n['class']=='Skeleton3D'];assert len(rigs)==1 and len(rigs[0]['bone_order'])==164
  names=[newg.doc['nodes'][i]['name']for i in newg.doc['skins'][0]['joints']];assert names==[n['name']for n in rigs[0]['bone_order']]
  levels.append({'level':level,'baseline_sha256':prep['canonical_raw_pins'][level],'candidate_sha256':row['output_sha256'],'hair_node_index':ni,'hair_surface_index':si,'source_nonhair_prefix_and_arrays_exact':True,'actual_nonhair_arrays_and_morphs_byte_exact':True,'hair_finite_census':bounds,'actual164_bone_order_matches_source':True})
 actual=set(differences(b,c));assert required<=actual and actual<=allowed,{'unexpected':sorted(actual-allowed),'missing_required':sorted(required-actual)}
 for root,key in [(frozen,'frozen_before'),(baseline,'baseline_before')]:
  for rel,item in prep[key].items():p=root/rel;assert p.stat().st_size==item['bytes']and sha(p)==item['sha256']
 for rel,item in prep['current_capture_source']['files'].items():assert snapshot.metadata(Path(prep['current_capture_source']['source_map'][rel]))==item,('Frozen current source changed',rel)
 shared=snapshot.verify(Path(prep['shared_base']));frozen_record=snapshot.verify(frozen);assert sha(frozen/snapshot.MARKER)==prep['frozen_marker_sha256'];assert sha(Path(prep['shared_base'])/snapshot.MARKER)==prep['shared_marker_sha256']
 files={};scenes=[];texture_matches=[]
 for p in sorted(imported.rglob('*')):
  if not p.is_file()or p.suffix not in['.scn','.ctex','.md5','.import','.png','.glb']:continue
  rel=str(p.relative_to(imported));files[rel]={'sha256':sha(p),'bytes':p.stat().st_size}
  if p.suffix in['.ctex','.png','.import']:assert(frozen/rel).is_file()and sha(frozen/rel)==sha(p);texture_matches.append(rel)
  if p.suffix=='.scn':scenes.append(rel)
 assert len(scenes)==3;imports=snapshot.imports(imported)
 with tarfile.open(W/'semantic-payloads-r1.tar.gz','w:gz')as tar:
  for label,directory in [('baseline',bpath),('candidate',cpath)]:
   for p in sorted(directory.iterdir()):tar.add(p,arcname=label+'/'+p.name)
 with tarfile.open(W/'candidate-import-cache-r1.tar.gz','w:gz')as tar:
  for rel in scenes:
   for p in[imported/rel,(imported/rel).with_suffix('.md5')]:tar.add(p,arcname=str(p.relative_to(imported)))
  for p in sorted((imported/'assets/heroes').glob('*.glb.import')):tar.add(p,arcname=str(p.relative_to(imported)))
 for name,path in [('baseline',bpath),('candidate',cpath)]:shutil.copyfile(path/'semantics.json',W/(name+'-import-semantics-r1.json'))
 report={'schema':1,'passed':True,'scope':'Actual3LOD imported resource census; only hair arrays/topology differ. No runtime, pixel, canonical or wholehero acceptance.','current_capture_source_overlay':prep['current_capture_source'],'comparison_script_sha256':sha(__file__),'probe_sha256':sha(W/'import_semantics.gd'),'preparation_sha256':sha(W/'import-preparation.json'),'candidate_manifest_sha256':sha(SOURCE/'manifest.json'),'exact_semantic_difference_paths':sorted(actual),'allowed_difference_paths':sorted(allowed),'levels':levels,'unchanged':['all nonhair source and imported packed bytes, signedzero included','all morph arrays/names/modes','all164bones/parents/rests/poses/skinbinds','all materials and actual texture pixels/payloads','all animations/node transforms/meshAABBs'],'frozen_source_inventory_unchanged':len(frozen_record['files']),'shared_base_and_store_unchanged':len(shared['files']),'baseline_cached_files_unchanged':len(prep['baseline_before']),'imported_resources':files,'verified_import_pairs':len(imports),'exact_texture_or_descriptor_files':texture_matches,'archives':{n:{'sha256':sha(W/n),'bytes':(W/n).stat().st_size}for n in['semantic-payloads-r1.tar.gz','candidate-import-cache-r1.tar.gz']},'remaining':['same4actualoriginals','independent visual review','no canonical activation']}
 (W/'import-comparison-r1.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS hair-only actual imported census; all nonhair bytes and resource semantics exact.')
if __name__=='__main__':main()
