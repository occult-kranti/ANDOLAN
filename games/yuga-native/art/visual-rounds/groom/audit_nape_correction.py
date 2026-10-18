"""Verify the bounded r6-to-r7 lower-nape edit independently of its recipe."""
import argparse,json,sys,hashlib
from pathlib import Path
import numpy as np
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'art/hero-rama-lod'))
from glb_lod import GLB
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 before=json.loads(a.before.read_text());after=json.loads(a.after.read_text());checks=[];levels={}
 def check(name,passed,**observed):checks.append({'name':name,'passed':bool(passed),**observed})
 check('same original guide control points widths depths and order',
       [{k:v for k,v in guide.items() if k!='clearance_warp'} for guide in after['guides']]==before['guides'])
 for level in ('near','mid','far'):
  b,c=before['levels'][level],after['levels'][level];old,new=GLB(b['output']),GLB(c['output'])
  op,np_=old.doc['meshes'][2]['primitives'][0],new.doc['meshes'][2]['primitives'][0]
  ov={k:old.array(i) for k,i in op['attributes'].items()};nv={k:new.array(i) for k,i in np_['attributes'].items()}
  count=len(ov['POSITION']);nape=np.zeros(count,bool)
  for part in b['parts']:
   if part['name'].startswith('nape-'):nape[part['start']:part['start']+part['count']]=True
  changed=np.any(ov['POSITION']!=nv['POSITION'],axis=1);movable=nape&(ov['POSITION'][:,1]<1.70)
  delta=np.linalg.norm(nv['POSITION'].astype(float)-ov['POSITION'],axis=1)
  check(level+' source and candidate hashes match manifests',sha(old.path)==b['output_sha256'] and sha(new.path)==c['output_sha256'])
  check(level+' unchanged input form identity',b['input_sha256']==c['input_sha256'])
  check(level+' topology and guide part partitions exact',np.array_equal(old.array(op['indices']),new.array(np_['indices'])) and b['parts']==c['parts'])
  check(level+' scalp crown temple retained brows topknot arrays exact',all(np.array_equal(ov[k][~nape],nv[k][~nape]) for k in ov))
  check(level+' only lower nape positions change',not np.any(changed&~movable),changed_vertices=int(changed.sum()))
  check(level+' UVs joints weights and second color exact',all(np.array_equal(ov[k],nv[k]) for k in ('TEXCOORD_0','JOINTS_0','WEIGHTS_0','COLOR_1')))
  check(level+' white RGB exact and alpha bounded',np.array_equal(ov['COLOR_0'][:,:3],nv['COLOR_0'][:,:3]) and nv['COLOR_0'][nape,3].max()<=round(.78*65535))
  check(level+' displacement stays within79.1mm',delta.max()<.0791,maximum_displacement_m=float(delta.max()))
  check(level+' original nonhair primitive JSON exact',all(p==new.doc['meshes'][mi]['primitives'][pi] for mi,mesh in enumerate(old.doc['meshes']) for pi,p in enumerate(mesh['primitives']) if (mi,pi)!=(2,0)))
  check(level+' only posterior and upward change',np.array_equal(ov['POSITION'][:,0],nv['POSITION'][:,0]) and np.all(nv['POSITION'][:,1]>=ov['POSITION'][:,1]-1e-7) and np.all(nv['POSITION'][:,2]<=ov['POSITION'][:,2]+1e-7))
  levels[level]={'before_sha256':b['output_sha256'],'after_sha256':c['output_sha256'],'changed_vertices':int(changed.sum()),'maximum_displacement_m':float(delta.max()),'before_bounds':[ov['POSITION'].min(0).tolist(),ov['POSITION'].max(0).tolist()],'after_bounds':[nv['POSITION'].min(0).tolist(),nv['POSITION'].max(0).tolist()]}
 result={'task':'R3-08 reopened nape clearance','passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,'levels':levels,'before_manifest_sha256':sha(a.before),'after_manifest_sha256':sha(a.after),'auditor_sha256':sha(__file__),'scope':'Exact edit boundary and silhouette/displacement accounting. Does not qualify action intersections, imported pixels or runtime performance.'}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'count':len(checks),'failures':[c for c in checks if not c['passed']]},indent=2))
if __name__=='__main__':main()
