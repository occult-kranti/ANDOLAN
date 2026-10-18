"""Stored-buffer preservation and new rigid frame contracts."""
import argparse,copy,hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from build_armour import ROOT,GLB,sha

def digest(a):return hashlib.sha256(a).hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();assert not args.output.exists()
 manifest=json.loads((args.candidate/'replacement-manifest.json').read_text());rows=[]
 for level,item in manifest['levels'].items():
  g=GLB(item['output']);old=GLB(item['source']);assert sha(g.path)==item['sha256'] and sha(old.path)==item['source_sha256']
  assert g.binary[:len(old.binary)]==old.binary
  assert g.doc['accessors'][:len(old.doc['accessors'])]==old.doc['accessors'] and g.doc['bufferViews'][:len(old.doc['bufferViews'])]==old.doc['bufferViews']
  for key in old.doc:
   if key not in ['accessors','bufferViews','buffers','meshes']:assert g.doc[key]==old.doc[key],key
  assert len(g.doc['meshes'])==len(old.doc['meshes'])
  for before,after in zip(old.doc['meshes'],g.doc['meshes']):assert {k:v for k,v in before.items()if k!='primitives'}=={k:v for k,v in after.items()if k!='primitives'}
  changed={r['primitive']:r for r in item['changed_primitives']};checked=0;preserved=0;added=0;removed=0;maximum_rounding=0.0
  sculpt=GLB(item['sculpture']);ib=old.array(old.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float);rest=np.linalg.inv(ib[49]);material_map={2:0,3:1,5:2}
  for mi,pi,p in old.primitives():
   q=g.doc['meshes'][mi]['primitives'][pi]
   if mi!=2 or pi not in changed:
    assert p==q;preserved+=1;continue
   row=changed[pi];a={k:old.array(ai)for k,ai in p['attributes'].items()};b={k:g.array(ai)for k,ai in q['attributes'].items()};tri=old.array(p['indices']).reshape(-1,3);nt=g.array(q['indices']).reshape(-1,3);count=len(a['POSITION'])
   cap=np.sum(np.where(a['JOINTS_0']==50,a['WEIGHTS_0'],0),axis=1)>.999999;mask=np.all(cap[tri],axis=1)if pi in [2,5,6]else np.zeros(len(tri),bool)
   assert np.flatnonzero(mask).tolist()==row['removed_source_triangle_ids'];keep=tri[~mask];assert np.array_equal(nt[:len(keep)],keep)
   assert np.all(nt[len(keep):]>=count) and np.all(nt[len(keep):]<len(b['POSITION']))
   for key in a:assert b[key][:count].tobytes()==a[key].tobytes(),(level,pi,key)
   if row['added_vertices']:
    original_piece=sculpt.doc['meshes'][0]['primitives'][material_map[pi]];lv=sculpt.array(original_piece['attributes']['POSITION']);expected_pos=(np.c_[lv,np.ones(len(lv))]@rest.T)[:,:3];maximum_rounding=max(maximum_rounding,float(np.linalg.norm(b['POSITION'][count:]-expected_pos,axis=1).max()))
    assert b['POSITION'][count:].tobytes()==expected_pos.astype('<f4').tobytes()
    n=b['NORMAL'][count:];t=b['TANGENT'][count:];uv=b['TEXCOORD_0'][count:]
    assert all(np.isfinite(x).all()for x in b.values());assert np.max(abs(np.linalg.norm(n,axis=1)-1))<2e-6;assert np.max(abs(np.linalg.norm(t[:,:3],axis=1)-1))<2e-6;assert np.max(abs(np.sum(n*t[:,:3],axis=1)))<2e-6
    assert np.all(np.isin(t[:,3],[-1,1])) and np.all((uv>=0)&(uv<=1))
    assert np.array_equal(b['JOINTS_0'][count:],np.tile([49,0,0,0],(row['added_vertices'],1))) and np.array_equal(b['WEIGHTS_0'][count:],np.tile([1,0,0,0],(row['added_vertices'],1)))
    for key in ['COLOR_0','COLOR_1']:assert np.array_equal(b[key][count:],np.tile([65535,65535,65535,0],(row['added_vertices'],1)))
    points=b['POSITION'][nt[len(keep):]];area=np.linalg.norm(np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0]),axis=1);assert area.min()>1e-12
   expected=copy.deepcopy(p);expected['attributes']=q['attributes'];expected['indices']=q['indices'];assert expected==q
   checked+=1;added+=row['added_triangles'];removed+=row['removed_triangles']
  assert checked==4 and preserved==14 and item['primitive_draws_before']==item['primitive_draws_after']==18
  assert len(g.doc['materials'])==len(old.doc['materials']) and len(g.doc['skins'])==1 and len(g.doc['skins'][0]['joints'])==164
  rows.append({'level':level,'source_sha256':sha(old.path),'candidate_sha256':sha(g.path),'original_BIN_prefix_bytes':len(old.binary),'exact_unchanged_primitives':preserved,'bounded_changed_primitives':checked,'removed_left_cap_triangles':removed,'added_sculpture_triangles':added,'material_draws':18,'materials':len(g.doc['materials']),'joints':164,'images_exact':all(old.image(a)==g.image(b)for a,b in zip(old.doc['images'],g.doc['images'])),'noncap_vertex_records_exact':True,'new_frames_uv_masks_and_rigid49_weights_pass':True,'maximum_world_rest_storage_rounding_m':maximum_rounding})
 report={'schema':1,'passed':True,'checker_sha256':sha(__file__),'manifest_sha256':sha(args.candidate/'replacement-manifest.json'),'levels':rows,'scope':'Exact stored replacement semantics and frames, independent from action contacts/import/render. Original cap dead prefix retained as provenance/file cost; no canonical edits.'}
 args.output.write_text(json.dumps(report,indent=2)+'\n');print('all3 stored replacement preservation/frame contracts pass')
if __name__=='__main__':main()
