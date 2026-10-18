"""R6 exact source preservation and full-triangle rest geometry. No art acceptance."""
import argparse,copy,importlib.util,json
from pathlib import Path
import numpy as np
from build_candidate import PROJECT,GLB,PINS,sha,base,ORIGIN
NARROW=PROJECT/'docs/evidence/visual-rounds/round3/role10/geometry_probe.py'
spec=importlib.util.spec_from_file_location('narrow',NARROW);narrow=importlib.util.module_from_spec(spec);spec.loader.exec_module(narrow)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--level',choices=['near','mid','far'],required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();assert not a.output.exists();manifest=json.loads(a.manifest.read_text());row=manifest['levels'][a.level];old,g=GLB(row['source']),GLB(row['output']);checks=[]
 result=dict(scope='R6 source identity and complete new triangles in rest space. No candidate import, native pose, rendered image or visual acceptance.',manifest_sha256=sha(a.manifest),checker_sha256=sha(__file__),narrow_phase_sha256=sha(NARROW),selfcheck=narrow.selfcheck(),level=a.level,checks=checks)
 def check(name,okay,**facts):
  checks.append(dict(name=name,passed=bool(okay),**facts));result.update(passed=all(c['passed']for c in checks),complete=False);a.output.write_text(json.dumps(result,indent=2)+'\n')
 check('exact source and output pins',sha(old.path)==PINS[a.level] and sha(g.path)==row['output_sha256'])
 check('complete accepted-UV binary prefix exact',g.binary[:len(old.binary)]==old.binary)
 before,after=copy.deepcopy(old.doc),copy.deepcopy(g.doc);after['accessors']=after['accessors'][:len(before['accessors'])];after['bufferViews']=after['bufferViews'][:len(before['bufferViews'])];after['meshes'][2]['primitives'][0]=before['meshes'][2]['primitives'][0];after['buffers']=before['buffers'];check('original JSON exact except hair append references',before==after)
 hp=g.doc['meshes'][2]['primitives'][0];attrs={k:g.array(v)for k,v in hp['attributes'].items()};oldattrs,oldtri,used=base.retained(old);n=row['retained_vertices'];nt=row['retained_triangles'];v=attrs['POSITION'];t=g.array(hp['indices']).reshape(-1,3);tri=v[t[nt:]]
 check('original brows and topknot byte-exact',all(attrs[k][:n].tobytes()==x.tobytes()for k,x in oldattrs.items())and t[:nt].astype('<u4').tobytes()==oldtri.astype('<u4').tobytes())
 check('original nonhair primitives exact',all(pr==g.doc['meshes'][mi]['primitives'][pi]for mi,pi,pr in old.primitives()if(mi,pi)!=(2,0)))
 check('all generated attributes finite',all(np.isfinite(x[n:]).all()for x in attrs.values()))
 check('indices in bounds and generated indices separate',t.min()>=0 and t.max()<len(v)and t[nt:].min()>=n)
 area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)*.5;check('no new degenerate triangles',np.all(area>1e-12),minimum_area_m2=float(area.min()))
 normal=attrs['NORMAL'][n:];tan=attrs['TANGENT'][n:];check('finite unit orthogonal tangent frames',np.max(abs(np.linalg.norm(normal,axis=1)-1))<1e-5 and np.max(abs(np.linalg.norm(tan[:,:3],axis=1)-1))<1e-5 and np.max(abs(np.sum(normal*tan[:,:3],axis=1)))<1e-5 and np.all(abs(tan[:,3])==1))
 uv=attrs['TEXCOORD_0'][n:];check('bounded UVs',uv.min()>=0 and uv.max()<=1)
 check('same single head104 binding',np.all(attrs['JOINTS_0'][n:]==[104,0,0,0])and np.all(attrs['WEIGHTS_0'][n:]==[1,0,0,0]))
 color=attrs['COLOR_0'][n:];moving=color[:,3]>0;check('white RGB and declared secondary alpha cap',np.all(color[:,:3]==65535)and color[:,3].max()/65535<=.35001 and np.all(v[n:][moving,1]<1.70),maximum_alpha=float(color[:,3].max()/65535))
 check('upper parts anchored',all(np.all(attrs['COLOR_0'][part['start']:part['start']+part['count'],3]==0)for part in row['parts']if not part['name'].startswith('falling-group')))
 generated=v[n:];check('declared principal silhouette bounds',np.max(abs(generated[:,0]))<=.13 and generated[:,1].min()>=1.56 and generated[:,1].max()<=1.865 and generated[:,2].min()>=-.19 and generated[:,2].max()<=.155,minimum=generated.min(0).tolist(),maximum=generated.max(0).tolist())
 for part in row['parts'][1:]:check(part['name']+' authored front bound',v[part['start']:part['start']+part['count'],2].max()<=.15)
 scalp=row['parts'][0];sv=v[scalp['start']:scalp['start']+scalp['count']];st=t[nt:nt+scalp['triangles']];fn=np.cross(v[st[:,1]]-v[st[:,0]],v[st[:,2]]-v[st[:,0]]);check('continuous scalp winding outward',np.all(np.sum(fn*(v[st].mean(1)-ORIGIN),axis=1)>0))
 check('collected scalp stays below tie upper bound',sv[:,1].max()<1.863,maximum_y_m=float(sv[:,1].max()))

 prior=json.loads((PROJECT/'art/hero-finish/hair-silhouette-r1/candidate-r4/groom-manifest.json').read_text())['levels'][a.level];priorg=GLB(PROJECT/'art/hero-finish/hair-silhouette-r1/candidate-r4-accepted-uv'/Path(prior['output']).name);priorv=priorg.array(priorg.doc['meshes'][2]['primitives'][0]['attributes']['POSITION']);priorpart=prior['parts'][0];priorfront=float(priorv[priorpart['start']:priorpart['start']+priorpart['count'],2].max());check('foundation front limit exactly inherited fitted edge',float(sv[:,2].max())==priorfront,prior_front_z_m=priorfront,current_front_z_m=float(sv[:,2].max()))
 knotfloor=float(v[:n][v[:n,1]>1.854,1].min());sections=[];scalptri=v[st]
 for edge in range(3):
  start,end=scalptri[:,edge],scalptri[:,(edge+1)%3];cross=(np.minimum(start[:,1],end[:,1])<=knotfloor)&(np.maximum(start[:,1],end[:,1])>=knotfloor)&(abs(end[:,1]-start[:,1])>1e-12);start,end=start[cross],end[cross];u=(knotfloor-start[:,1])/(end[:,1]-start[:,1]);sections.extend(start+u[:,None]*(end-start))
 sections=np.array(sections);rootwidth=float(np.ptp(sections[:,0]))if len(sections)else 0.;check('exact scalp plane cut supports actual knot root broadly',rootwidth>.060,plane_y_m=knotfloor,width_m=rootwidth,section_minimum=sections.min(0).tolist(),section_maximum=sections.max(0).tolist(),edge_intersections=len(sections))

 upper=sv[(sv[:,1]>1.849)&(sv[:,1]<1.8615)&(sv[:,2]<.015)];width=float(np.ptp(upper[:,0]))if len(upper)else 0.;check('broad continuous collected root sampled width',width>.060,width_m=width,vertices=len(upper))
 oldv=old.array(old.doc['meshes'][2]['primitives'][0]['attributes']['POSITION']);source_knots=oldv[used][oldtri[np.all(oldv[used][oldtri,1]>1.854,axis=1)]];contact=narrow.compare(v[st],source_knots,band=.012);check('foundation directly overlaps unchanged knot',contact['crossings']>0,comparison=contact)
 for label,materials,cut in [('full_head_and_features',['Rama warm skin','Natural lips','Warm sclera','Deep brown iris','Pupil'],1.65),('all_head_gold_and_gems',['Worked warm gold','Recessed antique gold','Polished sapphire'],1.75)]:
  targets=[]
  for mi,pi,pr in old.primitives():
   if old.doc['materials'][pr['material']]['name']not in materials:continue
   pv=old.array(pr['attributes']['POSITION']);pt=old.array(pr['indices']).reshape(-1,3);pt=pt[np.any(pv[pt,1]>cut,axis=1)]
   if len(pt):targets.append(pv[pt])
  contact=narrow.compare(tri,np.concatenate(targets),band=.012);check('all generated triangles clear '+label,contact['crossings']==0 and contact['guaranteed_lower_bound_m']>.0002,comparison=contact)
 result.update(passed=all(c['passed']for c in checks),complete=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.level,result['passed'],len(checks),[c for c in checks if not c['passed']]);raise SystemExit(0 if result['passed']else 1)
if __name__=='__main__':main()
