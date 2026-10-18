"""Isolated exact-component cap replacement; original BIN retained verbatim."""
import argparse,copy,hashlib,json,struct,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from build_armour import ROOT,GLB,sha
PINS={'near':'e98c9110161e49b653e98b6f4ca1dda997ad891cf73b737abd18f319bb3c2b82','mid':'dfa9a41adab7cfd5c60416a66d2b95c4d1ab06d081b64ee7a9f5ff5c7744474b','far':'8b74504c07d38416032ea22e37061d69061baaf0b86e78dec27417c8927e39f9'}
MAP={2:0,3:1,5:2}

def digest(a):return hashlib.sha256(a).hexdigest()
def transform(v,m):return (np.c_[v,np.ones(len(v))]@m.T)[:,:3]

def replace(source,sculpture,output):
 doc=copy.deepcopy(source.doc);binary=bytearray(source.binary);rows=[]
 ib=source.array(doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float);rest=np.linalg.inv(ib[49]);names=[doc['nodes'][j]['name']for j in doc['skins'][0]['joints']];assert names[49]=='shoulder01.L' and names[50]=='upperarm01.L'
 def add(array,spec,target):
  array=np.ascontiguousarray(array)
  while len(binary)%4:binary.append(0)
  view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':array.nbytes,'target':target});binary.extend(array.tobytes());spec=copy.deepcopy(spec)
  for k in ['min','max','byteOffset','sparse']:spec.pop(k,None)
  spec.update(bufferView=view,count=len(array))
  if spec['type']=='VEC3' and spec['componentType']==5126:spec.update(min=array.min(0).astype(float).tolist(),max=array.max(0).astype(float).tolist())
  index=len(doc['accessors']);doc['accessors'].append(spec);return index
 for pi in [2,3,5,6]:
  old=source.doc['meshes'][2]['primitives'][pi];assert not old.get('targets');p=copy.deepcopy(old);a={k:source.array(ai)for k,ai in old['attributes'].items()};tri=source.array(old['indices']).reshape(-1,3)
  # Original ornaments() assigns ONLY the left pauldron/lotus/scrolls to50
  # in gold/darkgold/gem. Skin and every other primitive are excluded.
  cap=np.sum(np.where(a['JOINTS_0']==50,a['WEIGHTS_0'],0),axis=1)>.999999
  remove=np.all(cap[tri],axis=1) if pi in [2,5,6] else np.zeros(len(tri),bool)
  if pi in [2,5,6]:
   assert remove.any() and np.array_equal(np.any(cap[tri],axis=1),remove),'Unexpected mixed component boundary'
   selected=a['POSITION'][np.unique(tri[remove])];assert np.all(selected[:,0]>.12) and np.all((selected[:,1]>1.42)&(selected[:,1]<1.54))
  else:selected=np.empty((0,3))
  kept=tri[~remove];newv=0;newtri=np.empty((0,3),np.uint32);attributes={}
  if pi in MAP:
   piece=sculpture.doc['meshes'][0]['primitives'][MAP[pi]];s={k:sculpture.array(ai)for k,ai in piece['attributes'].items()};newv=len(s['POSITION']);newtri=sculpture.array(piece['indices']).reshape(-1,3)+len(a['POSITION'])
   for key,oldarray in a.items():
    if key=='POSITION':new=transform(s[key],rest)
    elif key=='NORMAL':new=s[key]@rest[:3,:3].T;new/=np.linalg.norm(new,axis=1)[:,None]
    elif key=='TANGENT':new=s[key].copy();new[:,:3]=new[:,:3]@rest[:3,:3].T;new[:,:3]/=np.linalg.norm(new[:,:3],axis=1)[:,None]
    elif key=='TEXCOORD_0':new=s[key]
    elif key in ['COLOR_0','COLOR_1']:new=np.tile([65535,65535,65535,0],(newv,1))
    elif key=='JOINTS_0':new=np.tile([49,0,0,0],(newv,1))
    elif key=='WEIGHTS_0':new=np.tile([1,0,0,0],(newv,1))
    else:raise AssertionError('Unauthored source attribute '+key)
    joined=np.concatenate([oldarray,new.astype(oldarray.dtype)]);p['attributes'][key]=add(joined,source.doc['accessors'][old['attributes'][key]],34962)
    attributes[key]={'original_rows':len(oldarray),'original_array_sha256':digest(oldarray.tobytes()),'appended_rows':newv}
  indices=np.vstack([kept,newtri]).reshape(-1,1).astype('<u4');p['indices']=add(indices,{'componentType':5125,'type':'SCALAR'},34963);doc['meshes'][2]['primitives'][pi]=p
  rows.append({'primitive':pi,'material':doc['materials'][old['material']]['name'],'removed_source_triangle_ids':np.flatnonzero(remove).tolist(),'removed_triangles':int(remove.sum()),'removed_source_vertices':np.unique(tri[remove]).astype(int).tolist(),'removed_bounds_m':[selected.min(0).tolist(),selected.max(0).tolist()] if len(selected) else None,'retained_triangles':len(kept),'retained_index_values_sha256':digest(kept.astype('<u4').tobytes()),'added_vertices':newv,'added_triangles':len(newtri),'attributes':attributes})
 doc['buffers'][0]['byteLength']=len(binary);encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4);binary+=b'\0'*((-len(binary))%4)
 output.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4E4F534A)+encoded+struct.pack('<II',len(binary),0x004E4942)+binary)
 assert bytes(binary[:len(source.binary)])==source.binary
 return {'output':str(output),'sha256':sha(output),'bytes':output.stat().st_size,'source':str(source.path),'source_sha256':sha(source.path),'sculpture':str(sculpture.path),'sculpture_sha256':sha(sculpture.path),'source_bin_prefix_bytes':len(source.binary),'source_bin_prefix_sha256':digest(source.binary),'appended_bin_bytes':len(binary)-len(source.binary),'changed_primitives':rows,'primitive_draws_before':sum(len(m['primitives'])for m in source.doc['meshes']),'primitive_draws_after':sum(len(m['primitives'])for m in doc['meshes']),'active_triangles_before':sum(len(source.array(p['indices']))//3 for _,_,p in source.primitives()),'active_triangles_after':sum(len(source.array(p['indices']))//3 for mi,pi,p in source.primitives() if (mi,pi)not in[(2,2),(2,3),(2,5),(2,6)])+sum(r['retained_triangles']+r['added_triangles']for r in rows)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--sculpture',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--source',type=Path,default=ROOT/'art/hero-finish/s4-diadem-smooth/candidate-r2');args=ap.parse_args();out=args.output.resolve();assert not out.exists();out.mkdir(parents=True)
 levels={}
 for level,pin in PINS.items():
  filename='rama-hero'+(''if level=='near'else'-'+level)+'.glb';source=GLB(args.source/filename);assert sha(source.path)==pin
  sculpt=GLB(args.sculpture/('shoulder-armour-'+level+'.glb'));levels[level]=replace(source,sculpt,out/filename);assert sha(source.path)==pin
  print(level,levels[level]['sha256'],levels[level]['active_triangles_after'],flush=True)
 manifest={'schema':1,'review_only':True,'default_activation':False,'generator_sha256':sha(__file__),'sculpture_manifest_sha256':sha(args.sculpture/'source-manifest.json'),'original_authoring_source':{'path':'art/hero-rama/build_hero.py','sha256':sha(ROOT/'art/hero-rama/build_hero.py'),'ownership':'ornaments(): left pauldron lining/5leaves/lotus/rosette/scrolls are rigid upperarm01.L in gold/darkgold/gem; cuffs use lowerarm02 and stay exact.'},'new_binding':{'joint':49,'name':'shoulder01.L','weight':1,'secondary_alpha':0,'extra_bones':0,'new_runtime_writer':False},'levels':levels,'scope':'Exact isolated replacement of superseded left pauldron triangles with original compact sculpture. Original BIN prefix is retained; active old-cap indices are omitted. Every other primitive, image, rig, animation, morph and source vertex array stays exact. No canonical promotion or actual import/render acceptance.'}
 (out/'replacement-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
