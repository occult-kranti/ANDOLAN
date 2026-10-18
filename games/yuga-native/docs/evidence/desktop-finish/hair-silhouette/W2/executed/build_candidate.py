"""One inactive principal-hair silhouette; append-only original GLB hair stage."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline

PROJECT=Path(__file__).resolve().parents[3]
DEPENDENCY=PROJECT/'art/visual-rounds/groom/build_groom.py'
DEPENDENCY_SHA='4bcdb1121a52c68f2cb3f35850ace8956fb0554d120a85ce292c4f4afa8f6044'
assert hashlib.sha256(DEPENDENCY.read_bytes()).hexdigest()==DEPENDENCY_SHA
spec=importlib.util.spec_from_file_location('retained_groom',DEPENDENCY)
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
GLB,Skull,ORIGIN,retained,sha=base.GLB,base.Skull,base.ORIGIN,base.retained,base.sha
PINS={'near':'e98c9110161e49b653e98b6f4ca1dda997ad891cf73b737abd18f319bb3c2b82','mid':'dfa9a41adab7cfd5c60416a66d2b95c4d1ab06d081b64ee7a9f5ff5c7744474b','far':'8b74504c07d38416032ea22e37061d69061baaf0b86e78dec27417c8927e39f9'}
RESOLUTION={'near':(96,28,28,10),'mid':(64,20,20,8),'far':(40,14,14,6)}

class OuterHead:
 """Fit to both existing visible head skins, without scaling either mesh."""
 def __init__(self,source):
  triangles=[]
  for mesh in source.doc['meshes']:
   for primitive in mesh['primitives']:
    if source.doc['materials'][primitive['material']]['name']!='Rama warm skin':continue
    v=source.array(primitive['attributes']['POSITION']).astype(float);t=source.array(primitive['indices']).reshape(-1,3)
    triangles.append(v[t[np.all(v[t,1]>1.665,axis=1)]])
  self.tri=np.concatenate(triangles);self.a=self.tri[:,0];self.e1=self.tri[:,1]-self.a;self.e2=self.tri[:,2]-self.a
  self.tvec=ORIGIN-self.a;self.q=np.cross(self.tvec,self.e1)
 def rays(self,directions):
  output=[]
  for d in directions:
   h=np.cross(d,self.e2);det=np.einsum('ij,ij->i',self.e1,h)
   inv=np.divide(1.,det,out=np.zeros_like(det),where=abs(det)>1e-12)
   u=np.einsum('ij,ij->i',self.tvec,h)*inv;vv=(self.q@d)*inv;dist=np.einsum('ij,ij->i',self.e2,self.q)*inv
   ok=(abs(det)>1e-12)&(u>=-1e-8)&(vv>=-1e-8)&(u+vv<=1+1e-8)&(dist>0)
   if not np.any(ok):raise ValueError('Actual outer head ray missed')
   output.append(ORIGIN+d*np.max(dist[ok]))
  return np.array(output)

Skull=OuterHead

def seated(skull,points,offsets):
 points=np.array(points,dtype=float);directions=base.unit(points-ORIGIN)
 return (skull.rays(directions)+directions*np.array(offsets)[:,None]).tolist()

def guides(skull):
 result=[]
 for i,x in enumerate([-.073,-.049,-.020,.011,.043,.069]):
  raw=[[x,1.802+.003*(i%2),.124-.012*(abs(x)/.073)**1.6],[x*.80+.009,1.839,.099],[x*.43+.014,1.858,.043],[x*.12+.008,1.849,-.043]]
  result.append({'name':f'crown-{i}','kind':'crown','width':[.013,.017,.019,.018,.016,.012][i],
   'depth':[.0035,.004,.0043,.0041,.0038,.0032][i],'phase':i*.77,'points':seated(skull,raw,[.008,.010,.010,.008])})
 for side in [-1,1]:
  raw=[[side*.058,1.812,.107],[side*.077,1.796,.092],[side*.087,1.776,.075],[side*.081,1.758,.057]]
  result.append({'name':f'temple-{side}','kind':'temple','width':.0115 if side<0 else .010,'depth':.0032,'outward':[side,0,0],
   'points':seated(skull,raw,[.008,.009,.009,.007])})
 tips=[1.662,1.624,1.588,1.572,1.592,1.578,1.607,1.633,1.651]
 for i,theta in enumerate(np.linspace(2.02,4.27,9)):
  sx,sz=math.sin(theta),math.cos(theta);phase=i*1.13
  roots=seated(skull,[[.080*sx,1.807,.045+.096*sz],[.105*sx,1.758,.025+.122*sz]],[.0048,.010])
  points=roots+[[.104*sx+.006*math.sin(phase),1.695,-.040+.130*sz],
   [.105*sx-.008*math.sin(phase),max(1.610,tips[i]+.022),-.044+.150*sz],
   [.102*sx+.009*math.cos(phase),tips[i],-.045+.135*sz]]
  result.append({'name':f'nape-{i}','kind':'nape','width':[.011,.017,.021,.023,.022,.020,.019,.015,.010][i],
   'depth':[.0045,.005,.006,.006,.007,.006,.0055,.005,.004][i],'outward':[sx,0,sz],'phase':phase,'points':points})
 assert len(result)==17
 return result

def lock(mesh,guide,steps,sides,skull):
 pts=np.array(guide['points']);ts=np.linspace(0,1,steps)
 curve=CubicSpline(np.linspace(0,1,len(pts)),pts,axis=0,bc_type='natural');centers=curve(ts)
 if guide['kind'] in ['crown','temple']:
  # Follow the unchanged anatomical surface along the authored sweep, not
  # a chord through it between four fitted control points. This is local
  # lock seating; the thin foundation is not scaled or globally inflated.
  radial=base.unit(centers-ORIGIN)
  relief=.0048+.0062*np.sin(np.pi*ts)**.55
  centers=skull.rays(radial)+radial*relief[:,None]
  tangent=base.unit(np.gradient(centers,ts,axis=0))
  reference=radial
 else:
  # Rooted nape follows the anatomical envelope before its authored backward
  # departure. A smooth maximum avoids a sharp clamp where the lock lifts.
  upper=centers[:,1]>1.70
  radial=base.unit(centers[upper]-ORIGIN)
  support=skull.rays(radial)
  radius=np.linalg.norm(centers[upper]-ORIGIN,axis=1)
  relief=.0048+.0062*(1-np.exp(-(ts[upper]/.18)**2))
  required=np.linalg.norm(support-ORIGIN,axis=1)+relief
  fitted=.5*(radius+required+np.sqrt((radius-required)**2+.001**2))
  centers[upper]=ORIGIN+radial*fitted[:,None]
  tangent=base.unit(np.gradient(centers,ts,axis=0))
  reference=np.broadcast_to(np.array(guide.get('outward',[0,0,1.])),centers.shape)
 across=base.unit(np.cross(tangent,reference));out=base.unit(np.cross(across,tangent))
 vertices=[];uv=[]
 for i,t in enumerate(ts):
  taper=(.025+.975*math.sin(math.pi*t)**.72)*(1-.45*t)
  for j in range(sides+1):
   a=j/sides*2*math.pi
   width=guide['width']*taper*(1+.045*math.sin(t*4+guide.get('phase',0)))
   depth=guide['depth']*taper*(1+.025*math.cos(a*3+t*3))
   vertices.append(centers[i]+across[i]*width*math.cos(a)+out[i]*depth*math.sin(a));uv.append([j/sides,t])
 tri=[]
 for i in range(steps-1):
  for j in range(sides):
   a=i*(sides+1)+j;b=a+1;c=a+sides+1;tri.extend([(a,b,c),(b,c+1,c)])
 start=len(vertices);vertices.extend([centers[0],centers[-1]]);uv.extend([[.5,.015],[.5,.985]])
 for j in range(sides):
  tri.append((start,j+1,j));a=(steps-1)*(sides+1)+j;tri.append((start+1,a,a+1))
 vertices=np.array(vertices);alpha=np.zeros(len(vertices))
 if guide['kind']=='nape':alpha=.35*base.smooth(1.70,1.52,vertices[:,1])
 mesh.add(guide['name'],vertices,uv,np.asarray(tri)[:,[0,2,1]],alpha)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--source-dir',type=Path,default=PROJECT/'assets/heroes');a=ap.parse_args()
 if a.output.exists() or a.output.resolve().is_relative_to(PROJECT/'assets'):raise ValueError('Fresh inactive output required')
 sources={level:GLB(a.source_dir/('rama-hero'+('' if level=='near' else '-'+level)+'.glb')) for level in PINS}
 for level,g in sources.items():assert sha(g.path)==PINS[level]
 a.output.mkdir(parents=True);skull=Skull(sources['near']);guide_set=guides(skull)
 manifest={'schema':1,'task':'W2 original hair silhouette review-only','generator_sha256':sha(__file__),'dependency_sha256':DEPENDENCY_SHA,
  'parent_stage':'accepted smooth-crown R2; complete original crown and fullhead preserved','guides':guide_set,'secondary_max_alpha':.35,'foundation':'Existing4.5mm offset, seated to complete unchanged body+face outer skin, no head scaling or blanket inflation','levels':{}}
 for level,g in sources.items():
  columns,rows,steps,sides=RESOLUTION[level];mesh=base.Mesh();base.cap(mesh,skull,columns,rows)
  for guide in guide_set:lock(mesh,guide,steps,sides,skull)
  generated,tri=mesh.arrays();original,oldtri,used=retained(g);offset=len(original['POSITION'])
  arrays={k:np.concatenate([original[k],generated[k]]) for k in original};alltri=np.vstack([oldtri,tri+offset])
  out=a.output/g.path.name;base.append_candidate(g,arrays,alltri,out)
  for part in mesh.parts:part['start']+=offset
  assert np.isfinite(arrays['POSITION']).all()
  manifest['levels'][level]={'source':str(g.path),'input_sha256':sha(g.path),'output':str(out),'output_sha256':sha(out),'vertices':len(arrays['POSITION']),
   'triangles':len(alltri),'retained_vertices':offset,'retained_triangles':len(oldtri),'retained_source_rows':used.tolist(),'parts':mesh.parts,
   'resolution':RESOLUTION[level],'original_binary_prefix_sha256':hashlib.sha256(g.binary).hexdigest()}
  print(level,len(arrays['POSITION']),'vertices',len(alltri),'triangles',sha(out),flush=True)
 (a.output/'groom-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()
