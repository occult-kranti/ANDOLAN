"""Independent candidate geometry/contact/semantic-mask checks. Not art acceptance."""
from pathlib import Path
import sys, json, hashlib, importlib.util
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('original_validator',ROOT/'games/yuga-native/art/hero-rama/validate_hero.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def bow_records(doc,binary):
 node=next(n for n in doc['nodes'] if n.get('name')=='RamaBow')
 result={}
 for p in doc['meshes'][node['mesh']]['primitives']:
  m=doc['materials'][p['material']]['name'];a=p['attributes']
  cols=[v.accessor(doc,binary,a[k]).astype(float) for k in ('POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0')]
  data=np.concatenate(cols,axis=1);data=np.unique(np.round(data,6),axis=0)
  order=np.lexsort(tuple(data[:,i] for i in range(data.shape[1]-1,-1,-1)));result[m]=data[order]
 return result

def main():
 path=Path(sys.argv[1]);baseline=ROOT/'games/yuga-native/assets/heroes/rama-hero.glb';raw,doc,binary=v.read(path);oldraw,old,oldbin=v.read(baseline)
 checks=[];summaries=[]
 assert hashlib.sha256(oldraw).hexdigest()=='667f3a215a7b868e3bdbcde880a73d42b68b29af1303db4e1d99b93f73cf2b50','ExpectedacceptedR7baseline'
 assert {m['name'] for m in doc['materials']}=={m['name'] for m in old['materials']}
 assert all(m.get('alphaMode','OPAQUE')=='OPAQUE' for m in doc['materials']);checks.append('Original material names preserved; every material opaque')
 oldbow=bow_records(old,oldbin);newbow=bow_records(doc,binary)
 assert set(oldbow)==set(newbow)
 for mat in oldbow:
  assert oldbow[mat].shape==newbow[mat].shape,(mat,oldbow[mat].shape,newbow[mat].shape)
  assert np.allclose(oldbow[mat],newbow[mat],atol=1e-6,rtol=0),(mat,float(np.max(np.abs(oldbow[mat]-newbow[mat]))))
 checks.append('Every unique bow position/normal/UV/skin record matches accepted R7 within 1e-6')
 changed={}
 for mesh in doc['meshes']:
  for p in mesh['primitives']:
   a=p['attributes'];assert 'COLOR_0' in a
   col=v.accessor(doc,binary,a['COLOR_0']);pos=v.accessor(doc,binary,a['POSITION']);mat=doc['materials'][p['material']]['name']
   assert col.shape==(len(pos),4) and np.isfinite(col).all()
   assert np.all(np.abs(col[:,:3]-1)<1e-6),'VertexRGBwouldtintbasePBR'
   alpha=col[:,3];assert alpha.min()>=0 and alpha.max()<=1
   if mesh.get('name')=='RamaBow' or mat not in ('Swept black hair','Cobalt handwoven silk','Cobalt lotus brocade','Worked warm gold'):
    assert np.max(alpha)==0,(mesh.get('name'),mat,'Unexpecteddynamicmask')
   if mat in ('Cobalt handwoven silk','Cobalt lotus brocade','Worked warm gold'):
    assert np.max(alpha[pos[:,1]>=1.36],initial=0)==0,'Shouldersmustanchor'
    assert np.max(alpha[-pos[:,2]<=.175],initial=0)==0,'Frontbodyfittedclothmustanchor'
   if mat=='Swept black hair':
    # Face eyebrows and scalp remain anchored; clumptipsmusthaveauthoredmotion.
    assert np.max(alpha)>0.99 and np.min(alpha)==0
   summaries.append({'mesh':mesh.get('name'),'material':mat,'vertices':len(pos),'dynamicVertices':int(np.count_nonzero(alpha>0)),'maximumWeight':float(alpha.max())})
 checks.extend(['White RGB plus finite semantic alpha on every primitive','Only authored hair and trailing cloth/trim may move','Every bow, skin, eye, gemstone and fitted front/shoulder anchor is zero'])
 report={'schema':1,'candidate':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'baselineSha256':hashlib.sha256(oldraw).hexdigest(),'checks':checks,'primitives':summaries,'limitations':['Structural and source-contact invariants do not establish visual quality, intersection-free motion or physical GPU performance.']}
 (path.parent/'quality-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
