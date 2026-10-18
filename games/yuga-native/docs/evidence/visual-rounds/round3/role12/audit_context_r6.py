"""Independent revision audit and dense backdrop rays; no engine work."""
from pathlib import Path
import sys,json,hashlib,copy,math
import numpy as np
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'art/hero-rama-lod'));from glb_lod import GLB
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def diffs(a,b,path=''):
 if type(a)!=type(b):return [path]
 if isinstance(a,dict):return [p for k in set(a)|set(b) for p in ([path+'/'+k]if k not in a or k not in b else diffs(a[k],b[k],path+'/'+k))]
 if isinstance(a,list):return [path]if len(a)!=len(b)else[p for i,(x,y)in enumerate(zip(a,b))for p in diffs(x,y,path+'/'+str(i))]
 return []if a==b else[path]
levels=[]
for name in ['rama-hero.glb','rama-hero-mid.glb','rama-hero-far.glb']:
 a=GLB('/workspace/scratch/visual-round3/role-08/groom-r5/'+name);b=GLB('/workspace/scratch/visual-round3/role-08/groom-r6/'+name);changed=diffs(a.doc,b.doc);attrs=all(np.array_equal(a.array(i),b.array(i))for i in range(len(a.doc['accessors'])))
 allowed=all(p.split('/')[1]=='accessors'and p.split('/')[3]in ['min','max']for p in changed)
 levels.append({'file':name,'r5_sha256':sha(a.path),'r6_sha256':sha(b.path),'binary_exact':a.binary==b.binary,'all_accessor_arrays_exact':attrs,'raw_exact':a.raw==b.raw,'metadata_differences':changed,'only_accessor_minmax_changed':allowed,'passed':a.binary==b.binary and attrs and allowed})
assert all(r['passed']for r in levels)
env=GLB(ROOT/'assets/environment/lanka_courtyard.glb');triangles=[];labels=[];objects=[]
for n in env.doc['nodes']:
 if'mesh'not in n:continue
 assert not any(k in n for k in ['rotation','translation','scale','matrix'])
 for p in env.doc['meshes'][n['mesh']]['primitives']:
  t=env.array(p['attributes']['POSITION'])[env.array(p['indices']).reshape(-1,3)].astype(float);triangles.append(t);labels.extend([env.doc['materials'][p['material']]['name']]*len(t));objects.extend([n['name']]*len(t))
tri=np.vstack(triangles);edge1=tri[:,1]-tri[:,0];edge2=tri[:,2]-tri[:,0];normal=np.cross(edge1,edge2);d00=np.sum(edge1*edge1,1);d01=np.sum(edge1*edge2,1);d11=np.sum(edge2*edge2,1);den=d00*d11-d01*d01
# Different ray formulation than role02 Moller-Trumbore: ray-plane, then Gram barycentrics.
def first_hit(origin,direction):
 direction=direction/np.linalg.norm(direction);nd=normal@direction;valid=(abs(nd)>1e-12)&(abs(den)>1e-24);t=np.divide(np.sum((tri[:,0]-origin)*normal,1),nd,out=np.full(len(tri),np.inf),where=valid);q=origin+np.where(valid,t,0)[:,None]*direction-tri[:,0];d20=np.sum(q*edge1,1);d21=np.sum(q*edge2,1);u=np.divide(d11*d20-d01*d21,den,out=np.full(len(tri),-1.),where=valid);v=np.divide(d00*d21-d01*d20,den,out=np.full(len(tri),-1.),where=valid);valid&=(t>1e-6)&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)
 if not valid.any():return None
 index=int(np.argmin(np.where(valid,t,np.inf)));return {'distance_m':float(t[index]),'material':labels[index],'object':objects[index]}
old=json.loads((OUT.parent/'role02/geometry-verification.json').read_text());rayrows=[]
ground_hits=[first_hit(np.array([19.,3.,z]),np.array([0.,-1.,0.]))for z in [-1.,-15.]]
assert all(h and h['object']=='COL_BEVEL_Indigo_glazed_stone' for h in ground_hits)
ground_y=3-ground_hits[0]['distance_m'];assert abs(ground_y-(3-ground_hits[1]['distance_m']))<1e-8
corrected_y=ground_y+.0001; vertical_delta=corrected_y-.05
for shot in old['shots']:
 for field in ['player_position_m','camera_position_m','look_at_m']:shot[field][1]+=vertical_delta
for s in old['shots']:
 lo=np.min([s['projection'][k]['head']['min']for k in ['baseline','candidate']],0)-12;hi=np.max([s['projection'][k]['head']['max']for k in ['baseline','candidate']],0)+12;origin=np.array(s['camera_position_m']);target=np.array(s['look_at_m']);forward=target-origin;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,1,0]);right/=np.linalg.norm(right);up=np.cross(right,forward);scale=960/(2*math.tan(math.radians(s['fov_degrees'])/2));hits=[]
 for y in np.linspace(lo[1],hi[1],9):
  for x in np.linspace(lo[0],hi[0],9):hits.append(first_hit(origin,forward+(x-640)/scale*right-(y-480)/scale*up))
 expected='Indigo_glazed_stone'if s['id'].startswith('dark')else'Warm_carved_sandstone';match=sum(bool(h and h['material']==expected)for h in hits);foreground=sum(bool(h and h['distance_m']<np.linalg.norm(target-origin)-.5)for h in hits)
 rayrows.append({'id':s['id'],'grid':[9,9],'first_hit_material_expected':expected,'matched':match,'samples':81,'foreground':foreground,'hits':hits,'passed':match==81 and foreground==0})
 print(s['id'],match,'/81',flush=True)
# Conservative capsule-sized box excludes floor and tests source COL triangles' AABBs.
collision=[]
for station,z in [('dark',-1),('light',-15)]:
 lo=np.array([18.35,corrected_y+.001,z-.65]);hi=np.array([19.65,corrected_y+2,z+.65]);overlap=np.all(tri.max(1)>=lo,axis=1)&np.all(tri.min(1)<=hi,axis=1);selected=[i for i in np.flatnonzero(overlap)if objects[i].startswith('COL_')]
 collision.append({'station':station,'conservative_box_min':lo.tolist(),'conservative_box_max':hi.tolist(),'COL_triangle_AABB_overlap_count':len(selected),'overlap_objects':sorted(set(objects[i]for i in selected)),'east_boundary_horizontal_clearance_m':22-19-.65,'ground_surface_y_m':ground_y,'player_origin_y_m':corrected_y,'scope':'Conservative visual/actor box above proven floor plane; actual capsule radius.29m,height1.8m; no actual capsule sweep. Noncolliding decorations still affect pixels.'})
drift=[]
for path,expected in old['source_sha256'].items():
 p=Path(path)
 if p.exists() and sha(p)!=expected:drift.append({'path':path,'role02_sha256':expected,'current_sha256':sha(p)})
contract=copy.deepcopy(json.loads((OUT.parent/'role02/capture-contract.json').read_text()));contract['task']='R3-12';contract['supersedes']='role02 capture-contract.json: r6 source pins plus raised gallery floor correction; relative framing and controls preserved';
for shot in contract['stills']:
 if 'player_position_m' in shot:
  for field in ['player_position_m','camera_position_m','look_at_m']:shot[field][1]+=vertical_delta
contract['ground_correction']={'original_player_y_m':.05,'existing_gallery_surface_y_m':ground_y,'corrected_player_y_m':corrected_y,'camera_target_translation_y_m':vertical_delta,'reason':'Original station embeds capsule in existing raised gallery deck; preserve historical role02 and use this corrected contract.'};contract['groom_revision']='r6';contract['groom_sources']=[{'path':'/workspace/scratch/visual-round3/role-08/groom-r6/'+x['file'],'sha256':x['r6_sha256']}for x in levels];contract['revision_basis']='Near GLB is raw byte-identical; every BIN and accessor payload at all LODs exact; only optional lower-LOD NORMAL/TANGENT min/max JSON corrected.'
(OUT/'capture-contract-r6.json').write_text(json.dumps(contract,indent=2)+'\n')
report={'task':'R3-12','source_commit':'0437ea91edf6989ff78c1eeadb3661f4825b60f2','levels':levels,'dense_backdrop_grid':rayrows,'ground_downward_ray_hits':ground_hits,'obstacle_broadphase':collision,'role02_source_drift':drift,'passed':all(r['passed']for r in levels+rayrows)and all(r['COL_triangle_AABB_overlap_count']==0 for r in collision),'source_sha256':{str(p):sha(p)for p in [Path(__file__),env.path,OUT.parent/'role02/geometry-verification.json',OUT.parent/'role02/capture-contract.json',ROOT/'scripts/courtyard.gd',ROOT/'scripts/player.gd']},'limits':['Different source ray equation independently validates all81 grid positions against same current existing scene geometry.','Dense material-hit grid is not a rendered luminance, actual imported pose or final visible silhouette test.','Camera projection values transfer because exact near source geometry is proven; no new runtime pose is assumed.','Dark indigo stone deliberately replaces the failed foliage station; dark foliage remains untested.']}
(OUT/'context-r6-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'source_drift':drift,'obstacles':collision,'levels':[{'file':r['file'],'metadata_differences':len(r['metadata_differences']),'passed':r['passed']}for r in levels]},indent=2));assert report['passed']
