"""Original R3 groom: append-only binary stage, no Blender/runtime re-export.

Authoring coordinates are glTF metres. The scalp is ray-fitted to the original
anatomy, all three LODs share the same guides, and source eyebrows/topknot survive
as exact records. Only mesh 2 primitive 0 references are replaced.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, struct, sys
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT/'art/hero-rama-lod'))
from glb_lod import GLB

PINS = {
 'near':'140f8ff3695bb3d28bd894cb74bca8cd5f1756bbffcf59dad6c4630f377c351a',
 'mid':'27d998d924d2732b13bc8e18c3e3ec1ce9d58f0408bf3fda1ff0613cf32cba9f',
 'far':'ea9818e1464c9b6bc077ae83f8354a6357fb19d2a18fc84b2deb65c58aff901a'}
RESOLUTION = {'near':(96,28,34,12), 'mid':(64,20,24,10), 'far':(40,14,16,8)}
ORIGIN = np.array([0.,1.765,.045])
# One bounded correction of the exposed lower nape, derived from the original
# collar/neck triangles posed with the 37 captured R2 samples. Posterior/lift
# metres, keyed to the same nine original nape guides. This clears the measured
# rest crossings; action clearance remains limited and must not be inferred.
NAPE_CLEARANCE_WARP = ((.065,.045),(.045,.030),(.028,.060),(.0045,.003),
                       (0.,0.),(.0045,.003),(.018,.012),(.045,.030),(.065,.045))

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def unit(a): return a / np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-15)
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)

def retained(source):
 p=source.doc['meshes'][2]['primitives'][0]
 v=source.array(p['attributes']['POSITION']); tri=source.array(p['indices']).reshape(-1,3)
 brow=(v[:,1]>1.740)&(v[:,1]<1.755)&(v[:,2]>.139)&(abs(v[:,0])<.060)
 knot=v[:,1]>1.854
 selected=tri[np.all(brow[tri],axis=1)|np.all(knot[tri],axis=1)]
 # Crown ends can reach above the knot's lower bound. Keep only source connected
 # components whose complete extent lies above it, never cut crown triangles.
 from scipy.sparse import coo_matrix
 from scipy.sparse.csgraph import connected_components
 r=np.r_[tri[:,0],tri[:,1],tri[:,2]];c=np.r_[tri[:,1],tri[:,2],tri[:,0]]
 count,label=connected_components(coo_matrix((np.ones(len(r)),(r,c)),shape=(len(v),len(v))),directed=False)
 keep=np.zeros(len(v),bool)
 for i in range(count):
  mask=label==i
  if np.all(brow[mask]) or np.all(knot[mask]): keep[mask]=True
 selected=tri[np.all(keep[tri],axis=1)]
 used,inv=np.unique(selected,return_inverse=True)
 return {k:source.array(ai)[used] for k,ai in p['attributes'].items()},inv.reshape(-1,3),used

class Skull:
 def __init__(self,source):
  p=source.doc['meshes'][2]['primitives'][11];v=source.array(p['attributes']['POSITION']).astype(float)
  t=source.array(p['indices']).reshape(-1,3);t=t[np.all(v[t,1]>1.665,axis=1)]
  self.tri=v[t];self.a=self.tri[:,0];self.e1=self.tri[:,1]-self.a;self.e2=self.tri[:,2]-self.a
  self.tvec=ORIGIN-self.a;self.q=np.cross(self.tvec,self.e1)
 def rays(self,directions):
  output=[]
  for d in directions:
   h=np.cross(d,self.e2);det=np.einsum('ij,ij->i',self.e1,h)
   inv=np.divide(1.,det,out=np.zeros_like(det),where=abs(det)>1e-12)
   u=np.einsum('ij,ij->i',self.tvec,h)*inv
   vv=(self.q@d)*inv;dist=np.einsum('ij,ij->i',self.e2,self.q)*inv
   ok=(abs(det)>1e-12)&(u>=-1e-8)&(vv>=-1e-8)&(u+vv<=1+1e-8)&(dist>0)
   if not np.any(ok):raise ValueError('Scalp ray misses actual anatomy')
   output.append(ORIGIN+d*np.min(dist[ok]))
  return np.array(output)

class Mesh:
 def __init__(self):self.positions=[];self.uv=[];self.triangles=[];self.alpha=[];self.parts=[]
 def add(self,name,v,uv,tri,alpha):
  start=len(self.positions);self.positions.extend(v);self.uv.extend(uv);self.triangles.extend(np.asarray(tri)+start)
  self.alpha.extend(np.broadcast_to(alpha,(len(v),)));self.parts.append({'name':name,'start':start,'count':len(v),'triangles':len(tri)})
 def arrays(self):
  v=np.asarray(self.positions,dtype='<f4');uv=np.asarray(self.uv,dtype='<f4');tri=np.asarray(self.triangles,dtype='<u4')
  n=np.zeros_like(v,dtype=float);tan=np.zeros_like(n);bit=np.zeros_like(n)
  e1=v[tri[:,1]]-v[tri[:,0]];e2=v[tri[:,2]]-v[tri[:,0]];fn=np.cross(e1,e2)
  d1=uv[tri[:,1]]-uv[tri[:,0]];d2=uv[tri[:,2]]-uv[tri[:,0]]
  det=d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0];inv=np.divide(1.,det,out=np.zeros_like(det),where=abs(det)>1e-12)
  ft=(e1*d2[:,1,None]-e2*d1[:,1,None])*inv[:,None];fb=(e2*d1[:,0,None]-e1*d2[:,0,None])*inv[:,None]
  for k in range(3):np.add.at(n,tri[:,k],fn);np.add.at(tan,tri[:,k],ft);np.add.at(bit,tri[:,k],fb)
  # Smooth coincident UV-seam positions without merging their UV coordinates.
  _,same=np.unique(np.round(v,7),axis=0,return_inverse=True);merged=np.zeros((same.max()+1,3));np.add.at(merged,same,n);n=merged[same]
  n=unit(n);tan=unit(tan-n*np.sum(tan*n,axis=1)[:,None]);sign=np.where(np.sum(np.cross(n,tan)*bit,axis=1)<0,-1,1)
  colors=np.full((len(v),4),65535,dtype='<u2');colors[:,3]=np.round(np.asarray(self.alpha)*65535).astype('<u2')
  joints=np.zeros((len(v),4),dtype='u1');joints[:,0]=104;weights=np.zeros((len(v),4),dtype='<f4');weights[:,0]=1
  return {'POSITION':v,'NORMAL':n.astype('<f4'),'TEXCOORD_0':uv,'TANGENT':np.c_[tan,sign].astype('<f4'),
   'COLOR_0':colors,'COLOR_1':np.full((len(v),4),65535,dtype='<u2'),'JOINTS_0':joints,'WEIGHTS_0':weights},tri

def cap(mesh,skull,columns,rows):
 # Front high enough to expose forehead/diadem, sides cover temples above ears,
 # posterior boundary drops smoothly to nape. Angles run front->right->back.
 anchors=np.array([0,.40,.80,1.15,1.57,1.90,2.25,2.65,math.pi])
 elev=np.array([.30,.27,.19,.04,-.08,-.10,-.26,-.49,-.59])
 directions=[];uv=[]
 for j in range(rows):
  f=j/rows
  for i in range(columns+1):
   theta=i/columns*2*math.pi;angle=abs((theta+math.pi)%(2*math.pi)-math.pi)
   low=np.interp(angle,anchors,elev)+.025*math.sin(theta)*math.sin(angle)
   el=low+(math.pi/2-low)*f
   directions.append([math.sin(theta)*math.cos(el),math.sin(el),math.cos(theta)*math.cos(el)])
   uv.append([i/columns,f])
 d=np.array(directions);p=skull.rays(d)
 # 4.5mm fitted coverage; restrained broad irregular waves are actual form.
 theta=np.array(uv)[:,0]*2*math.pi;f=np.array(uv)[:,1]
 offset=.0045+.0014*np.sin(theta*7+f*2)**2*np.sin(f*math.pi)
 p+=d*offset[:,None]
 apex=skull.rays(np.array([[0.,1.,0.]]))[0]+[0,.0045,0]
 tri=[]
 for j in range(rows-1):
  for i in range(columns):
   a=j*(columns+1)+i;b=a+1;c=a+columns+1;tri.extend([(a,c,b),(b,c,c+1)])
 for i in range(columns):
  a=(rows-1)*(columns+1)+i;tri.append((a,len(p),a+1))
 p=np.vstack([p,apex]);uv.append([.5,1.]);mesh.add('source-fitted scalp',p,uv,np.asarray(tri)[:,[0,2,1]],0.)

def lock(mesh,guide,steps,sides):
 pts=np.array(guide['points']);t=np.linspace(0,1,steps)
 curve=CubicSpline(np.linspace(0,1,len(pts)),pts,axis=0,bc_type='natural');centers=curve(t);tangent=unit(curve(t,1))
 reference=np.broadcast_to(np.array(guide.get('outward',[0,0,1.])),centers.shape)
 across=unit(np.cross(tangent,reference));out=unit(np.cross(across,tangent))
 vertices=[];uv=[]
 for i,tt in enumerate(t):
  taper=.07+.93*math.sin(math.pi*tt)**.56
  for j in range(sides+1):
   a=j/sides*2*math.pi
   # Flattened clumps, broad shallow groove. Deliberate irregular widths are
   # guide-scale geometry, not narrow detached strands or alpha cutouts.
   width=guide['width']*taper*(1+.10*math.sin(tt*5+guide.get('phase',0)))
   depth=guide['depth']*taper*(1+.06*math.cos(a*3+tt*4))
   vertices.append(centers[i]+across[i]*width*math.cos(a)+out[i]*depth*math.sin(a));uv.append([j/sides,tt])
 tri=[]
 for i in range(steps-1):
  for j in range(sides):
   a=i*(sides+1)+j;b=a+1;c=a+sides+1;tri.extend([(a,b,c),(b,c+1,c)])
 # Both ends are closed with separate center vertices and nondegenerate fans.
 start=len(vertices);vertices.extend([centers[0],centers[-1]]);uv.extend([[.5,.015],[.5,.985]])
 for j in range(sides):
  tri.append((start,j+1,j));a=(steps-1)*(sides+1)+j;tri.append((start+1,a,a+1))
 vertices=np.array(vertices);alpha=np.zeros(len(vertices))
 if 'clearance_warp' in guide:
  warp=guide['clearance_warp'];weight=smooth(warp['start_y'],warp['full_y'],vertices[:,1])
  vertices[:,1]+=warp['lift_m']*weight;vertices[:,2]-=warp['posterior_m']*weight
 if guide['kind']=='nape':alpha=.78*smooth(1.70,1.46,vertices[:,1])
 mesh.add(guide['name'],vertices,uv,np.asarray(tri)[:,[0,2,1]],alpha)

def guides():
 result=[]
 for i,x in enumerate([-.071,-.045,-.012,.024,.058]):
  result.append({'name':f'crown-{i}','kind':'crown','width':[.026,.032,.038,.031,.027][i],'depth':[.007,.008,.010,.008,.007][i],
   'phase':i*.8,'points':[[x,1.799+.005*(i%2),.126-.018*(abs(x)/.071)**1.6],[x*.84+.008,1.839,.103],[x*.48+.014,1.868,.045],[x*.18+.008,1.858,-.045]]})
 for side in [-1,1]:
  result.append({'name':f'temple-{side}','kind':'temple','width':.018 if side==1 else .021,'depth':.006,'outward':[side,0,0],
   'points':[[side*.052,1.813,.107],[side*.072,1.789,.094],[side*.080,1.776,.082],[side*.084,1.764,.078]]})
 for i,theta in enumerate(np.linspace(2.02,4.27,9)):
  sx=math.sin(theta);sz=math.cos(theta)
  side=1 if sx>0 else -1;phase=i*1.13;end=1.47+[.006,.029,-.006,.014,.035,.000,.022,-.012,.012][i]
  points=[[.080*sx,1.801,.045+.096*sz],[.114*sx,1.743,.025+.122*sz],
    [.122*sx+.008*math.sin(phase),1.654,.004+.143*sz],
    [.112*sx-.010*math.sin(phase),1.561,-.004+.150*sz],
    [.114*sx+.008*math.cos(phase),end,.008+.142*sz]]
  result.append({'name':f'nape-{i}','kind':'nape','width':[.024,.033,.038,.030,.042,.031,.035,.030,.025][i],
    'depth':[.009,.010,.012,.010,.013,.010,.011,.010,.009][i],'outward':[sx,0,sz],'phase':phase,'points':points,
    'clearance_warp':{'start_y':1.70,'full_y':1.50,'posterior_m':NAPE_CLEARANCE_WARP[i][0],
                      'lift_m':NAPE_CLEARANCE_WARP[i][1]}})
 return result

def append_candidate(source,arrays,tri,output):
 doc=copy.deepcopy(source.doc);binary=bytearray(source.binary);old=source.doc['meshes'][2]['primitives'][0]
 primitive=copy.deepcopy(old)
 def add(array,spec,target):
  while len(binary)%4:binary.append(0)
  view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':array.nbytes,'target':target});binary.extend(array.tobytes())
  spec=copy.deepcopy(spec)
  for k in ['min','max','byteOffset','sparse']:spec.pop(k,None)
  spec.update(bufferView=view,count=len(array))
  if spec['type']=='VEC3' and spec['componentType']==5126:spec.update(min=array.min(0).tolist(),max=array.max(0).tolist())
  index=len(doc['accessors']);doc['accessors'].append(spec);return index
 for key,array in arrays.items():primitive['attributes'][key]=add(array,doc['accessors'][old['attributes'][key]],34962)
 primitive['indices']=add(tri.reshape(-1,1).astype('<u4'),{'componentType':5125,'type':'SCALAR'},34963)
 doc['meshes'][2]['primitives'][0]=primitive;doc['buffers'][0]['byteLength']=len(binary)
 encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4);binary+=b'\0'*((-len(binary))%4)
 raw=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4E4F534A)+encoded+struct.pack('<II',len(binary),0x004E4942)+binary
 output.write_bytes(raw)

def main():
 p=argparse.ArgumentParser();p.add_argument('--near',type=Path,required=True);p.add_argument('--mid',type=Path,required=True);p.add_argument('--far',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists() or a.output.resolve().is_relative_to(PROJECT):raise ValueError('Use fresh external output')
 sources={level:GLB(getattr(a,level)) for level in PINS}
 for level,g in sources.items():
  if sha(g.path)!=PINS[level]:raise ValueError('Source pin differs '+level)
 a.output.mkdir(parents=True);skull=Skull(sources['near']);guide_set=guides();manifest={'schema':1,'task':'R3-08','generator_sha256':sha(__file__),'guides':guide_set,'levels':{}}
 for level,g in sources.items():
  columns,rows,steps,sides=RESOLUTION[level];mesh=Mesh();cap(mesh,skull,columns,rows)
  for guide in guide_set:lock(mesh,guide,steps,sides)
  generated,tri=mesh.arrays();original,old_tri,used=retained(g);offset=len(original['POSITION'])
  arrays={k:np.concatenate([original[k],generated[k]]) for k in original};alltri=np.vstack([old_tri,tri+offset]);out=a.output/f'rama-hero{("-"+level) if level!="near" else ""}.glb'
  append_candidate(g,arrays,alltri,out)
  for part in mesh.parts:part['start']+=offset
  manifest['levels'][level]={'source':str(g.path),'input_sha256':sha(g.path),'output':str(out),'output_sha256':sha(out),'vertices':len(arrays['POSITION']),'triangles':len(alltri),'retained_vertices':offset,'retained_triangles':len(old_tri),'retained_source_rows':used.tolist(),'parts':mesh.parts,'resolution':RESOLUTION[level],'original_binary_prefix_sha256':hashlib.sha256(g.binary).hexdigest()}
 (a.output/'groom-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:{x:v[x] for x in ['output_sha256','vertices','triangles','retained_vertices']} for k,v in manifest['levels'].items()},indent=2))

if __name__=='__main__':main()
