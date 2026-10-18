"""Inactive R6 coherent collected principal hair; exact accepted-UV nonhair parent."""
import argparse,hashlib,importlib.util,json,math
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline
PROJECT=Path(__file__).resolve().parents[3]
DEPENDENCY=PROJECT/'art/hero-finish/hair-silhouette-r1/build_candidate.py'
assert hashlib.sha256(DEPENDENCY.read_bytes()).hexdigest()=='dccbbd8c25e5d093d16940a5aa53153a220408b9fcae56fa3f57d45c258c7f39'
spec=importlib.util.spec_from_file_location('sealed_r4',DEPENDENCY);r4=importlib.util.module_from_spec(spec);spec.loader.exec_module(r4)
GLB,sha,base,ORIGIN=r4.GLB,r4.sha,r4.base,r4.ORIGIN
PINS={'near':'db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e','mid':'b5949c9d427e9684a13fa525212eedc87dfa207d2c70fba5ebe6a4b1eda61005','far':'aef8ae5837c0bf0a9ed5850ae649d6368ec1e87c0728d501f1780bba325a9d6a'}
RESOLUTION={'near':(96,28,32,12),'mid':(64,20,22,8),'far':(40,14,16,6)}
GATHER_CENTER=np.array([0.,1.822,-.035]);GATHER_RADII=np.array([.070,.035,.057])

class CollectedScalp:
 """Localized authored collection union with the unmodified anatomical envelope."""
 def __init__(self,head):self.head=head
 def rays(self,d):
  head=self.head.rays(d);radius=np.linalg.norm(head-ORIGIN,axis=1)
  o=(ORIGIN-GATHER_CENTER)/GATHER_RADII;rd=d/GATHER_RADII
  aa=np.sum(rd*rd,axis=1);bb=2*(rd@o);cc=float(o@o-1);disc=bb*bb-4*aa*cc
  far=(-bb+np.sqrt(np.maximum(disc,0)))/(2*aa)
  use=(disc>=0)&(far>0);target=np.where(use,far,radius)
  fitted=.5*(radius+target+np.sqrt((radius-target)**2+.00030**2))
  return ORIGIN+d*np.where(use,fitted,radius)[:,None]

def guides(head):
 result=[]
 for i,x in enumerate([-.072,-.046,-.018,.014,.045,.070]):
  pts=[[x,1.802+.002*(i%2),.122-.010*(abs(x)/.072)**1.5],[x*.79+.006,1.836,.100],[x*.42+.011,1.851,.043],[x*.14+.004,1.844,-.032]]
  result.append(dict(name='collected-crown-'+str(i),kind='crown',width=[.017,.021,.024,.023,.021,.016][i],depth=[.0032,.0036,.0040,.0038,.0034,.0030][i],phase=i*.77,points=r4.seated(head,pts,[.007,.009,.008,.005])))
 for side in [-1,1]:
  pts=[[side*.057,1.813,.107],[side*.075,1.795,.092],[side*.086,1.776,.073],[side*.082,1.754,.051]]
  result.append(dict(name='temple-'+str(side),kind='temple',width=.0125 if side<0 else .0105,depth=.0032,outward=[side,0,0],points=r4.seated(head,pts,[.007,.008,.008,.006])))
 tips=[1.646,1.617,1.594,1.581,1.604,1.628,1.651]
 for i,theta in enumerate([2.00,2.37,2.73,3.11,3.48,3.85,4.24]):
  sx,sz=math.sin(theta),math.cos(theta);phase=i*1.13
  roots=r4.seated(head,[[.080*sx,1.813,.045+.096*sz],[.103*sx,1.755,.025+.115*sz]],[.006,.009])
  points=roots+[[.104*sx+.003*math.sin(phase),1.700,-.025+.115*sz],[.102*sx-.005*math.sin(phase),max(1.625,tips[i]+.027),-.030+.125*sz],[.099*sx+.005*math.cos(phase),tips[i],-.022+.117*sz]]
  result.append(dict(name='falling-group-'+str(i),kind='nape',width=[.018,.023,.027,.028,.026,.023,.017][i],depth=[.004,.005,.0055,.006,.0055,.0048,.0038][i],outward=[sx,0,sz],phase=phase,points=points))
 return result

def lock(mesh,guide,steps,sides,head):
 pts=np.array(guide['points']);ts=np.linspace(0,1,steps);centers=CubicSpline(np.linspace(0,1,len(pts)),pts,axis=0,bc_type='natural')(ts)
 if guide['kind']in ['crown','temple']:
  radial=base.unit(centers-ORIGIN);relief=.0048+.0042*np.sin(np.pi*ts)**.7
  centers=head.rays(radial)+radial*relief[:,None];reference=radial
 else:
  upper=centers[:,1]>1.70;radial=base.unit(centers[upper]-ORIGIN);support=head.rays(radial)
  radius=np.linalg.norm(centers[upper]-ORIGIN,axis=1);required=np.linalg.norm(support-ORIGIN,axis=1)+.006+.004*(1-np.exp(-(ts[upper]/.18)**2))
  fitted=.5*(radius+required+np.sqrt((radius-required)**2+.0008**2));centers[upper]=ORIGIN+radial*fitted[:,None]
  reference=np.broadcast_to(np.array(guide.get('outward',[0,0,1.])),centers.shape)
 tangent=base.unit(np.gradient(centers,ts,axis=0));across=base.unit(np.cross(tangent,reference));out=base.unit(np.cross(across,tangent))
 vertices=[];uv=[]
 for i,t in enumerate(ts):
  # Broad overlapping roots and bodies, with taper confined to the final third.
  body=.72+.28*math.sin(math.pi*min(t/.72,1))
  tail=1-float(base.smooth(.66,1.,t));taper=.025+.975*body*tail
  if guide['kind']in ['crown','temple']:taper=(.12+.88*math.sin(math.pi*t)**.65)*(1-.25*t)
  for j in range(sides+1):
   angle=j/sides*2*math.pi;width=guide['width']*taper*(1+.035*math.sin(t*4+guide.get('phase',0)));depth=guide['depth']*taper*(1+.025*math.cos(angle*3+t*3))
   vertices.append(centers[i]+across[i]*width*math.cos(angle)+out[i]*depth*math.sin(angle));uv.append([j/sides,t])
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
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();assert not a.output.exists()and not a.output.resolve().is_relative_to(PROJECT/'assets')
 source_dir=PROJECT/'art/hero-finish/sash-texel-r1/candidate-r2';sources={level:GLB(source_dir/('rama-hero'+(''if level=='near'else'-'+level)+'.glb'))for level in PINS}
 for level,g in sources.items():assert sha(g.path)==PINS[level]
 head=r4.OuterHead(sources['near']);collected=CollectedScalp(head);guide_set=guides(head);a.output.mkdir(parents=True)
 manifest=dict(schema=1,inactive=True,task='R6 coherent collected swept principal hair; R4/R5 preserved',generator_sha256=sha(__file__),shape_brief_sha256=sha(Path(__file__).with_name('SHAPE_BRIEF.md')),r4_dependency_sha256=sha(DEPENDENCY),parent='Exact accepted smooth crown and sash UV trio; original brows/topknot retained',collected_center_m=GATHER_CENTER.tolist(),collected_radii_m=GATHER_RADII.tolist(),secondary_max_alpha=.35,guides=guide_set,levels={})
 for level,g in sources.items():
  columns,rows,steps,sides=RESOLUTION[level];mesh=base.Mesh();base.cap(mesh,collected,columns,rows)
  for guide in guide_set:lock(mesh,guide,steps,sides,head)
  generated,tri=mesh.arrays();original,oldtri,used=base.retained(g);offset=len(original['POSITION']);arrays={k:np.concatenate([original[k],generated[k]])for k in original};triangles=np.vstack([oldtri,tri+offset]);out=a.output/g.path.name;base.append_candidate(g,arrays,triangles,out)
  for part in mesh.parts:part['start']+=offset
  manifest['levels'][level]=dict(source=str(g.path),source_sha256=sha(g.path),output=str(out),output_sha256=sha(out),retained_vertices=offset,retained_triangles=len(oldtri),retained_source_rows=used.tolist(),vertices=len(arrays['POSITION']),triangles=len(triangles),parts=mesh.parts,resolution=RESOLUTION[level])
  print(level,manifest['levels'][level]['vertices'],manifest['levels'][level]['triangles'],sha(out),flush=True)
 (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
