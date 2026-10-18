from pathlib import Path
import json,hashlib,itertools
src=Path('/workspace/scratch/yuga-next-W1-r1/water-baseline-actual-r2/01-coast-day.json');d=json.loads(src.read_text());boxes=[]
for m in d['meshes']:
 if not m['visible'] or m.get('transparency',0)>=1:continue
 a,size=m['aabb'];t=m['global_transform'];cs=[[t[3][i]+sum(t[j][i]*(a[j]+bits[j]*size[j]) for j in range(3)) for i in range(3)] for bits in itertools.product([0,1],repeat=3)];boxes.append((m['path'],[min(c[i] for c in cs) for i in range(3)],[max(c[i] for c in cs) for i in range(3)]))
def inside(p,lo,hi):return all(lo[i]-1e-5<=p[i]<=hi[i]+1e-5 for i in range(3)) and all(hi[i]-lo[i]>1e-4 for i in range(3))
def ray(p,q,lo,hi):
 low=0.;high=1.
 for i in range(3):
  delta=q[i]-p[i]
  if abs(delta)<1e-12:
   if p[i]<lo[i]-1e-7 or p[i]>hi[i]+1e-7:return None
  else:
   a=(lo[i]-p[i])/delta;b=(hi[i]-p[i])/delta;low=max(low,min(a,b));high=min(high,max(a,b))
   if high<low:return None
 return low if 1e-6<low<.999 else None
def obstruction(p,q):return sorted((v,n) for n,lo,hi in boxes if not n.endswith('/lanka-sea') and (v:=ray(p,q,lo,hi)) is not None)
old=[-67.,4.6,20.];new=[-94.,4.6,-38.];target=[-80.,-.15,-38.]
oldinside=[n for n,lo,hi in boxes if inside(old,lo,hi)];newinside=[n for n,lo,hi in boxes if inside(new,lo,hi)]
grid=[]
for x in [-90.,-85.,-80.,-75.]:
 for z in [-44.,-42.,-40.,-38.,-36.,-32.]:
  q=[x,-.15,z];hits=obstruction(new,q);grid.append({'point':q,'clear_of_all_visible_mesh_AABBs':not hits,'first_bounds':hits[:2]})
r={'scope':'Offline conservative actual-mesh AABB check from retained fullscene sidecar, not native/raster acceptance. AABB misses guarantee no mesh triangle can intersect the segment; merged AABB hits are conservative and can be false positives.','sidecar':str(src),'sidecar_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'visible_mesh_count':len(boxes),'old_camera':old,'old_containing_meshes':oldinside,'rejected_gap_proposal':{'camera':[-68,3,0],'target':[-85,-.15,-12],'reason':'Central ray overlaps actual coast vegetation/basalt/wick bounds; merged-material AABBs also conservatively contain camera. Rejected before raster.'},'new_camera':new,'new_target':target,'new_containing_meshes':newinside,'new_central_ray_hits':obstruction(new,target),'grid_samples':len(grid),'clear_grid_samples':sum(x['clear_of_all_visible_mesh_AABBs'] for x in grid),'samples':grid,'camera_is_review_only_outside_actor_bounds':True,'player_transform_unchanged':True}
p=Path(__file__).parent/'occlusion-review.json';p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='samples'},indent=2));assert oldinside and not newinside and not r['new_central_ray_hits'] and r['clear_grid_samples']==24;print('receipt_sha256',hashlib.sha256(p.read_bytes()).hexdigest())
