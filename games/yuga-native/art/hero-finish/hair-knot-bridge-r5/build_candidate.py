"""One inactive compact knot attachment; every R4 active record stays exact."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
import numpy as np
PROJECT=Path(__file__).resolve().parents[3]
R4=PROJECT/'art/hero-finish/hair-silhouette-r1'
DEPENDENCY=R4/'build_candidate.py'
assert hashlib.sha256(DEPENDENCY.read_bytes()).hexdigest()=='dccbbd8c25e5d093d16940a5aa53153a220408b9fcae56fa3f57d45c258c7f39'
spec=importlib.util.spec_from_file_location('sealed_r4',DEPENDENCY);r4=importlib.util.module_from_spec(spec);spec.loader.exec_module(r4)
GLB,sha=r4.GLB,r4.sha
PINS={'near':'ecf5d8d142ab47266d929af10c64bb993ddcef022e34a3e86edde7b73b74e6ac','mid':'445a3a63d07c9e0532fa4354f9ac691d023cc01471a749553b24233c53a64e80','far':'d72f953508e994285bab6e2a994f51574214c150193259b533aa034e7e100ae8'}
RESOLUTION={'near':(16,24),'mid':(12,16),'far':(8,12)}


def bridge(skull,rings,sides):
 theta=np.linspace(0,2*np.pi,sides+1)
 foot_guess=np.stack([-.001+.025*np.cos(theta),np.full_like(theta,1.842),-.010+.014*np.sin(theta)],axis=1)
 radial=r4.base.unit(foot_guess-r4.ORIGIN)
 foot=skull.rays(radial)+radial*.004
 top=np.stack([.024*np.cos(theta),np.full_like(theta,1.861),-.041+.017*np.sin(theta)],axis=1)
 rows=[]
 for t in np.linspace(0,1,rings+1):
  blend=t*t*(3-2*t)
  v=(1-blend)*foot+blend*top
  # A millimetre-scale gathered sweep, confined below the unchanged tie.
  v[:,0]+=.0015*np.sin(np.pi*t)
  center=v.mean(0);profile=1+.025*np.sin(np.pi*t)*np.cos(3*theta+.4*np.pi*t)
  v[:,0]=center[0]+(v[:,0]-center[0])*profile
  v[:,2]=center[2]+(v[:,2]-center[2])*profile
  # Continuous head seating prevents a root chord from cutting the head.
  radial=r4.base.unit(v-r4.ORIGIN);support=skull.rays(radial)
  radius=np.linalg.norm(v-r4.ORIGIN,axis=1);required=np.linalg.norm(support-r4.ORIGIN,axis=1)+.004
  fitted=.5*(radius+required+np.sqrt((radius-required)**2+.00025**2))
  rows.append(r4.ORIGIN+radial*fitted[:,None])
 positions=np.concatenate(rows);uv=np.array([[j/sides,t]for t in np.linspace(0,1,rings+1)for j in range(sides+1)])
 tri=[]
 for i in range(rings):
  for j in range(sides):
   a=i*(sides+1)+j;b=a+1;c=a+sides+1;tri.extend([(a,c,b),(b,c,c+1)])
 foot_center=np.array([-.001,1.842,-.010]);d=r4.base.unit((foot_center-r4.ORIGIN)[None]);foot_center=(skull.rays(d)+d*.004)[0]
 first=len(positions);positions=np.vstack([positions,foot_center,np.array([0,1.861,-.041])]);uv=np.vstack([uv,[.5,.015],[.5,.985]])
 for j in range(sides):
  tri.append((first,j,j+1));a=rings*(sides+1)+j;tri.append((first+1,a+1,a))
 mesh=r4.base.Mesh();mesh.add('compact-swept-knot-attachment',positions,uv,np.array(tri),np.zeros(len(positions)))
 return mesh.arrays(),{'foot_center_guess_m':[-.001,1.842,-.010],'top_center_m':[0,1.861,-.041],'foot_halfwidth_m':.025,'top_halfwidth_m':.024,'top_halfdepth_m':.017,'head_relief_m':.004,'secondary_alpha':0,'rings':rings,'sides':sides}


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 assert not a.output.exists() and not a.output.resolve().is_relative_to(PROJECT/'assets')
 sources={level:GLB(R4/'candidate-r4-accepted-uv'/('rama-hero'+(''if level=='near'else'-'+level)+'.glb'))for level in PINS}
 for level,g in sources.items():assert sha(g.path)==PINS[level]
 skull=r4.OuterHead(sources['near']);outputs=[]
 for level,g in sources.items():
  primitive=g.doc['meshes'][2]['primitives'][0];original={key:g.array(i)for key,i in primitive['attributes'].items()};oldtri=g.array(primitive['indices']).reshape(-1,3)
  (added,tri),guide=bridge(skull,*RESOLUTION[level]);offset=len(original['POSITION'])
  arrays={key:np.concatenate([value,added[key]])for key,value in original.items()};triangles=np.vstack([oldtri,tri+offset]);outputs.append((level,g,arrays,triangles,guide,offset,len(oldtri),len(tri)))
 a.output.mkdir(parents=True)
 manifest={'schema':1,'inactive':True,'task':'R5 compact attachment beneath unchanged knot; rejected R4 preserved','generator_sha256':sha(__file__),'r4_dependency_sha256':sha(DEPENDENCY),'r4_source_receipt_sha256':sha(PROJECT/'docs/evidence/desktop-finish/hair-silhouette/W2/receipt.json'),'r4_visual_rejection_sha256':sha(PROJECT/'docs/evidence/desktop-finish/hair-silhouette/W2-visual-r1.json'),'only_new_geometry':'One zero-alpha compact swept knot attachment; all R4 active arrays/indices exact prefix, including reduced crown/nape and original knot.','levels':{}}
 for level,g,arrays,tri,guide,offset,oldcount,addedcount in outputs:
  path=a.output/g.path.name;r4.base.append_candidate(g,arrays,tri,path)
  manifest['levels'][level]={'source':str(g.path),'source_sha256':sha(g.path),'output':str(path),'output_sha256':sha(path),'preserved_vertices':offset,'preserved_triangles':oldcount,'added_vertices':len(arrays['POSITION'])-offset,'added_triangles':addedcount,'vertices':len(arrays['POSITION']),'triangles':len(tri),'guide':guide}
  print(level,manifest['levels'][level]['added_vertices'],'newvertices',addedcount,'newtriangles',sha(path),flush=True)
 (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
