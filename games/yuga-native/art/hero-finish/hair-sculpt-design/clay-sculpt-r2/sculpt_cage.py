"""One direct edit of the first editable clay cage; no GLB or render."""
import argparse,hashlib,importlib.util,json,math
from pathlib import Path
import numpy as np
PROJECT=Path(__file__).resolve().parents[4]
MASTER=PROJECT/'art/hero-finish/hair-sculpt-design/clay-r1/master-cage.json'
MASTER_SHA='db4d81f252a1edb2e90f1f667dfe6a5aa8bdc83669c8cab410e42e50365710fc'
PARENT=PROJECT/'art/hero-finish/hair-sculpt-design/clay-r1/authoring-payload/seated-cage.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();assert not a.output.exists()
 assert sha(MASTER)==MASTER_SHA
 master=json.loads(MASTER.read_text());data=json.loads(PARENT.read_text());v=np.array(master['vertices']);faces=master['faces'];groups=master['groups']
 scalp=set(groups['Scalp sweep']);fold=set(groups['Folded gather']);falls=set(groups['Dominant S fall'])|set(groups['Returning S fall']);old_generated=falls-scalp-fold
 keep_faces=[f for f in faces if not any(i in old_generated for i in f)]
 # Direct broad-plane edits of the existing scalp cage, not a new cap union.
 for i in sorted(scalp):
  x,y,z=v[i]
  if y<1.775:continue
  crown=smooth(1.775,1.815,y)*(1-smooth(1.845,1.861,y))
  along=np.clip((z+.050)/.185,0,1)
  sweep_x=-.038+.040*math.sin(along*math.pi*.80)
  shoulder=math.exp(-((x-sweep_x)/.032)**2)*math.exp(-((z-.055)/.105)**4)
  opposite=math.exp(-((x-.048)/.028)**2)*math.exp(-((z-.050)/.105)**2)
  v[i,1]+=crown*(.0105*shoulder-.0010*opposite)
  v[i,0]-=.0030*crown*shoulder
  # A shallow broad parting plane, not a fine strand groove.
  part=math.exp(-((x+.056-.012*along)/.012)**2)*math.exp(-((z-.050)/.10)**2)
  v[i,1]-=.0012*crown*part
 # Roll only the upper fold; keep the fixed-tie aperture section intact.
 for i in sorted(fold):
  x,y,z=v[i];w=float(smooth(1.872,1.888,y))
  v[i,1]=y-(max(0,y-1.872)*.38)+.0030*(x/.040)*w
  v[i,0]+=.010*w;v[i,2]-=.006*w
 # Evaluated-r1 witness: the lower rolled fold smoothed through the fixed tie.
 # Seat only this concealed aperture section; preserve the authored upper
 # fold, all principal planes/falls, and the actual gold reference.
 for i in sorted(fold):
  x,y,z=v[i]
  if 1.853<y<1.886:
   dx,dz=x,z+.040;r=math.hypot(dx,dz)
   influence=math.exp(-((y-1.868)/.010)**4)
   if r>.028:
    scale=1-influence+influence*.028/r
    v[i,0]=dx*scale;v[i,2]=-.040+dz*scale
 # Existing rear hairline is recovered by exact original row positions.
 # It is the same shared edge that rooted the failed straps.
 sourcev=np.array(master['vertices']);root_candidates=sorted(scalp&falls)
 root=sorted(root_candidates,key=lambda i:math.atan2(sourcev[i,0],sourcev[i,2]-.045)%(2*math.pi))
 assert len(root)==23
 vertices=v.tolist();all_faces=list(keep_faces);newgroups={k:list(groups[k])for k in ['Scalp sweep','Folded gather']}
 rootv=v[root];previous=root;collected=list(root);width=len(root)
 # Shared broad C-shaped sections: continuity persists past the upper neck.
 sections=[(1.690,-.091,.083,.039,.001),(1.665,-.112,.078,.034,.004),
           (1.640,-.134,.072,.028,.008),(1.615,-.151,.065,.023,.010),
           (1.593,-.160,.060,.020,.008)]
 for row,(cy,cz,half,depth,center)in enumerate(sections):
  ring=[]
  for k in range(width):
   u=1-2*k/(width-1);target=np.array([center+half*u,cy+.006*u,cz+depth*u*u])
   if row==0:target=rootv[k]*.28+target*.72
   ring.append(len(vertices));vertices.append(target.tolist())
  for k in range(width-1):all_faces.append([previous[k],ring[k],ring[k+1],previous[k+1]])
  collected.extend(ring);previous=ring
 newgroups['Collected rear']=collected
 depth_weight={i:0. for i in range(len(vertices))}
 for i in collected:depth_weight[i]=float(smooth(1.725,1.665,vertices[i][1]))
 # Lower-third branching only; transverse convexity gives a rounded mass,
 # and the two falls overlap in depth rather than exposing an upper diamond.
 # Fixed-view witness: the first terminal point fell outside profile/rear.
 # Compact only the lower-third lengths, keeping the four cameras fixed and
 # the broad root/body, transverse volume and lateral S flow unchanged.
 branches=[('Dominant S fall',previous[:12],[(1.574,-.179,.046,.020,.022),(1.554,-.189,.035,.017,-.003),(1.540,-.178,.020,.012,-.008),(1.532,-.158,.003,.004,.010)]),
           ('Returning S fall',previous[11:],[(1.577,-.148,.037,.018,-.018),(1.560,-.156,.027,.014,.003),(1.548,-.148,.015,.010,.016),(1.544,-.133,.003,.003,.009)])]
 for name,start,rows in branches:
  previous=start;ids=list(start);w=len(start)
  for cy,cz,half,depth,center in rows:
   ring=[]
   for k in range(w):
    u=1-2*k/(w-1);p=[center+half*u,cy+.004*u,cz+depth*u*u]
    ring.append(len(vertices));vertices.append(p);depth_weight[ring[-1]]=1.
   for k in range(w-1):all_faces.append([previous[k],ring[k],ring[k+1],previous[k+1]])
   ids.extend(ring);previous=ring
  newgroups[name]=ids
 # Keep only referenced vertices. All new sections share their actual edges.
 used=np.unique(np.concatenate([np.array(f)for f in all_faces]));remap=np.full(len(vertices),-1,int);remap[used]=np.arange(len(used));vertices=np.array(vertices)[used]
 all_faces=[[int(remap[i])for i in f]for f in all_faces]
 newgroups={name:sorted(set(int(remap[i])for i in ids if remap[i]>=0))for name,ids in newgroups.items()}
 weights=[float(depth_weight.get(int(i),0))for i in used]
 data.update(kind='One direct-cage coarse sculpt revision, inactive authoring clay only',vertices=vertices.tolist(),faces=all_faces,groups=newgroups,
             local_depth_weights=weights,generator_sha256=sha(__file__),source_master_sha256=MASTER_SHA,
             modifiers=dict(subdivision_levels=1,render_levels=1,solidify_thickness_m=.016,solidify_minimum_factor=.125,solidify_offset=-1),
             edit_scope='Only hair cage and localized depth; locked head/crown/tie and authoring scene controls preserved')
 a.output.mkdir();(a.output/'sculpt-cage.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
 print('ONE_DIRECT_CAGE',len(vertices),len(all_faces),vertices.min(0).tolist(),vertices.max(0).tolist(),sha(a.output/'sculpt-cage.json'))
if __name__=='__main__':main()
