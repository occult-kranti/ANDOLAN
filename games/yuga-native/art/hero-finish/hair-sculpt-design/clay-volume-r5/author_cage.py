"""Author C5 as one connected closed cage. Pure Python; never launches Blender.

Coordinates: glTF metres, +Y up/+Z front. Reuses only C4's thin scalp seating
mesh; old scalp overlays, peg, loft paths and both tails are discarded. Crown,
head and fixed gold tie are never edited or imported into this mesh.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,math,collections,shutil

DONOR=Path('games/yuga-native/art/hero-finish/hair-sculpt-design/clay-volume-r4/authoring-payload/build-r2/source-lofts.json.gz')
DONOR_SHA=''
ANGULAR=128
LEVELS=32
SIDE=1+ANGULAR*LEVELS

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump_gz(p,value):
 with gzip.GzipFile(filename=str(p),mode='wb',mtime=0)as f:f.write(json.dumps(value,separators=(',',':')).encode())
def outer(j,k):return 1+(j-1)*ANGULAR+(k%ANGULAR)
def inner(j,k):return SIDE+outer(j,k)
def clamp(v,a,b):return max(a,min(b,v))

def author(donor):
 cap=json.loads(gzip.decompress(donor.read_bytes()))['parts'][0]
 assert cap['name']=='SOURCE_LOFT_00_Continuous_seated_scalp'
 vertices=[list(p)for p in cap['vertices']]
 assert len(vertices)==2*SIDE
 # Broad directional sculpt strokes directly move the outer coverage cage.
 # These are major swept planes (6-10mm), not separate lobes or fine grooves.
 sweeps=[
  (.010,.023,[[-.060,1.790,.120],[-.045,1.820,.100],[-.030,1.840,.065],[-.005,1.850,.025],[0,1.851,-.020],[0,1.860,-.040]]),
  (.008,.019,[[-.080,1.760,.080],[-.085,1.780,.050],[-.080,1.800,.015],[-.060,1.825,-.020],[-.025,1.850,-.040]]),
  (.009,.023,[[.060,1.785,.120],[.070,1.810,.075],[.060,1.830,.030],[.030,1.846,-.020],[0,1.860,-.040]]),
  (.007,.019,[[.080,1.760,.080],[.085,1.780,.040],[.075,1.800,0],[.050,1.826,-.035],[.010,1.850,-.050]]),
 ]
 def segment_distance(p,a,b):
  d=[b[i]-a[i]for i in range(3)];t=clamp(sum((p[i]-a[i])*d[i]for i in range(3))/sum(x*x for x in d),0,1)
  return math.sqrt(sum((p[i]-a[i]-t*d[i])**2 for i in range(3)))
 for i,p in enumerate(vertices[:SIDE]):
  x,y,z=p;radial=[x,y-1.765,z-.045];length=math.sqrt(sum(x*x for x in radial))
  ring=0 if i==0 else 1+(i-1)//ANGULAR
  boundary_fade=clamp((LEVELS-ring)/2.5,0,1)
  stroke=0
  for amplitude,radius,path in sweeps:
   distance=min(segment_distance(p,a,b)for a,b in zip(path,path[1:]))
   stroke+=amplitude*math.exp(-(distance/radius)**2)
  stroke=min(stroke,.014)*boundary_fade
  for axis in range(3):p[axis]+=radial[axis]/length*stroke
  # A deliberate asymmetry in the front crest routes it toward the gather.
  crest=math.exp(-((x+.025+.20*(z-.035))/.050)**2-((z-.045)/.09)**2)
  high=clamp((y-1.78)/.05,0,1);p[1]+=.004*crest*high;p[0]-=.003*crest*high
  vertices[i]=p

 faces=[]
 # Gather patch outer-grid bounds; these existing boundary vertices are shared
 # by the scalp and the new oblique gather. No overlapping connector object.
 ja,jb,ka,kb=7,14,52,76
 for offset in [0,SIDE]:
  for k in range(ANGULAR):faces.append([offset,offset+outer(1,k),offset+outer(1,k+1)])
  for j in range(1,LEVELS):
   for k in range(ANGULAR):
    if offset==0 and ja<=j<jb and ka<=k<kb:continue
    faces.append([offset+outer(j,k),offset+outer(j+1,k),offset+outer(j+1,k+1),offset+outer(j,k+1)])
 # Rear/nape rim is opened and extended into the rear mass in shared topology.
 tail_a,tail_b=38,90
 for k in range(ANGULAR):
  if tail_a<=k<tail_b:continue
  faces.append([outer(LEVELS,k),outer(LEVELS,k+1),inner(LEVELS,k+1),inner(LEVELS,k)])
 boundary=[outer(ja,k)for k in range(ka,kb+1)]
 boundary +=[outer(j,kb)for j in range(ja+1,jb+1)]
 boundary +=[outer(jb,k)for k in range(kb-1,ka-1,-1)]
 boundary +=[outer(j,ka)for j in range(jb-1,ja,-1)]
 center=[sum(vertices[v][i]for v in boundary)/len(boundary)for i in range(3)]
 angles=[math.atan2(vertices[v][2]-center[2],vertices[v][0]-center[0])for v in boundary]
 # Full asymmetric returning bun around the fixed tie, with a broad oblique
 # base and unequal folded shoulders. The prior20mm rule has no art authority.
 bun=[
  [-.007,1.846,-.035,.050,.037,.002],
  [-.004,1.855,-.038,.040,.031,.001],
  [0,1.866,-.040,.0245,.0225,0],
  [-.008,1.879,-.045,.036,.032,.006],
  [-.017,1.893,-.049,.036,.031,.010],
  [-.024,1.902,-.052,.026,.024,.008],
  [-.029,1.894,-.056,.012,.013,.004],
 ]

 previous=boundary
 for row in bun:
  cx,cy,cz,w,d,wave=row;ring=[]
  for angle in angles:
   # Two unequal returning shoulders; no torus hole or vertical stalk.
   lobes=1+.10*math.cos(2*angle+.45)+.07*math.sin(angle)
   p=[cx+w*math.cos(angle)*lobes,cy+wave*math.sin(2*angle+.8),cz+d*math.sin(angle)*lobes]
   if 1.861<p[1]<1.872:
    dx,dz=p[0],p[2]+.040;r=math.hypot(dx,dz)
    if r>.0255:p[0]=dx*.0255/r;p[2]=-.040+dz*.0255/r
   ring.append(len(vertices));vertices.append(p)
  for k in range(len(ring)):faces.append([previous[k],previous[(k+1)%len(ring)],ring[(k+1)%len(ring)],ring[k]])
  previous=ring
 pole=len(vertices);vertices.append([-.029,1.887,-.056])
 for k in range(len(previous)):faces.append([previous[k],previous[(k+1)%len(previous)],pole])

 # The connected rear mass follows the occiput/nape inward instead of
 # hanging as an open C sheet. Outer sculpt planes and a seated front plane
 # carry broad overlapping folds, with three unequal tapering lower reaches.
 # v, outer-back z, inner-front z, center x, halfwidth.
 flow=[
  [.10,-.066,-.035,-.005,.065],
  [.20,-.080,-.039,-.006,.065],
  [.30,-.090,-.042,0,.063],
  [.40,-.097,-.043,.009,.060],
  [.50,-.097,-.043,.014,.057],
  [.60,-.090,-.041,.012,.054],
  [.70,-.079,-.039,.003,.051],
  [.80,-.065,-.037,-.008,.049],
  [.90,-.049,-.035,-.015,.047],
  [1.0,-.034,-.032,-.019,.045],
 ]

 root_outer=[outer(LEVELS,k)for k in range(tail_a,tail_b+1)]
 root_inner=[inner(LEVELS,k)for k in range(tail_a,tail_b+1)]
 previous_outer,previous_inner=root_outer,root_inner
 n=len(root_outer)
 for row_index,row in enumerate(flow):
  v,back_z,front_z,cx,w=row
  new_outer,new_inner=[],[]
  for side,ring in [(-1,new_outer),(1,new_inner)]:
   for k in range(n):
    u=k/(n-1);across=math.cos(math.pi*u)
    def reach(center,width,height):return height*max(0,1-abs((u-center)/width))**.60
    end_y=1.602-reach(.58,.19,.060)-reach(.22,.15,.026)-reach(.87,.12,.018)
    root_y=(vertices[root_outer[k]][1]+vertices[root_inner[k]][1])*.5
    yy=(1-v)*root_y+v*end_y
    # Directional broad folds move through both depth and lateral flow. Their
    # centers cross as the dominant reach returns across its subordinate.
    c1=.28+.23*math.sin(math.pi*v*.90);c2=.80-.15*math.sin(math.pi*v)
    plane1=math.exp(-((u-c1)/.17)**2);plane2=math.exp(-((u-c2)/.15)**2)
    phase=math.sin(math.pi*v)
    xx=cx+w*across+.008*(plane1-plane2)*phase
    if side==-1:
     zz=back_z-(.010*plane1+.008*plane2)*phase
     yy+=.006*(plane1-plane2)*phase
    else:
     # This front surface occupies the former empty neck gap. Its depth is
     # deliberately independent of the exterior folded planes.
     zz=front_z+.003*(1-across*across)*phase
    if v>.8:
     # Curl each tapered reach slightly toward the nape; no padded end caps.
     zz+=.007*(v-.8)/.2*(plane1-.35*plane2)
    ring.append(len(vertices));vertices.append([xx,yy,zz])

  for old,new in [(previous_outer,new_outer),(previous_inner,new_inner)]:
   for k in range(n-1):faces.append([old[k],old[k+1],new[k+1],new[k]])
  for k in [0,n-1]:faces.append([previous_outer[k],new_outer[k],new_inner[k],previous_inner[k]])
  previous_outer,previous_inner=new_outer,new_inner
 for k in range(n-1):faces.append([previous_outer[k],previous_outer[k+1],previous_inner[k+1],previous_inner[k]])
 return dict(name='EDITABLE_WholeHair_CoarseClay',vertices=vertices,faces=faces),dict(gather_patch=[ja,jb,ka,kb],bun_contours=bun,rear_flow=flow,shared_surface=True,thin_seating_donor=cap['name'])

def check(mesh):
 vertices,faces=mesh['vertices'],mesh['faces']
 edges=collections.Counter();adj=[set()for _ in vertices]
 for f in faces:
  assert len(f)>=3 and len(set(f))==len(f)
  for a,b in zip(f,f[1:]+f[:1]):
   assert 0<=a<len(vertices)and 0<=b<len(vertices)
   edges[tuple(sorted((a,b)))]+=1;adj[a].add(b);adj[b].add(a)
 used={i for i,a in enumerate(adj)if a};visited=set();components=0
 for start in used:
  if start in visited:continue
  components+=1;todo=[start];visited.add(start)
  while todo:
   for j in adj[todo.pop()]:
    if j not in visited:visited.add(j);todo.append(j)
 nonmanifold=sum(c!=2 for c in edges.values())
 unused=[i for i,a in enumerate(adj)if not a]
 # Removed gather interior is unused authoring data, prune before export.
 assert components==1 and nonmanifold==0,(components,nonmanifold)
 bounds=[[min(p[i]for p in vertices)for i in range(3)],[max(p[i]for p in vertices)for i in range(3)]]
 return dict(vertices=len(vertices),used_vertices=len(used),faces=len(faces),edges=len(edges),nonmanifold_edges=nonmanifold,connected_components=components,unused_vertex_count=len(unused),bounds=bounds,passed=components==1 and nonmanifold==0)

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--donor',type=Path,default=DONOR);args=p.parse_args()
 assert not args.output.exists(),'Fresh source directory required'
 mesh,design=author(args.donor)
 # Remove vertices left behind inside the explicitly extruded gather patch.
 used=sorted({i for f in mesh['faces']for i in f});mapping={old:new for new,old in enumerate(used)}
 mesh['vertices']=[mesh['vertices'][i]for i in used];mesh['faces']=[[mapping[i]for i in f]for f in mesh['faces']]
 report=check(mesh)
 args.output.mkdir(parents=True)
 dump_gz(args.output/'source-cage.json.gz',mesh)
 (args.output/'shape-design.json').write_text(json.dumps(design,indent=2)+'\n')
 report.update(scope='Pure Python prepared C5 editable cage only; no Blender, image, source fit or art acceptance',author_sha256=sha(Path(__file__)),donor_path=str(args.donor),donor_sha256=sha(args.donor),source_cage_sha256=sha(args.output/'source-cage.json.gz'),maximum_bun_y=max(p[1]for p in mesh['vertices']),blender_run=False,actual_review='pending',protected_reference_changes='No Blender/reference mutation occurred')
 (args.output/'preparation-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
