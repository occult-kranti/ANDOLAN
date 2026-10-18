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
 # Direct broad sculpt of the outer surface, with one asymmetric diagonal
 # crest. Inner coverage stays exactly seated; there are no separate panels.
 for i,p in enumerate(vertices[:SIDE]):
  x,y,z=p
  crest=math.exp(-((x+.022+.20*(z-.035))/.044)**2-((z-.040)/.095)**2)
  front=clamp((z+.04)/.13,0,1)
  high=clamp((y-1.77)/.06,0,1)
  p[1]+=.010*crest*high
  p[0]-=.004*crest*high*front
  # One subtle directional valley in the directly sculpted surface, not an
  # applied lobe or a stack of thick side plates.
  p[1]-=.0015*math.exp(-((x-.015+.30*(z-.04))/.010)**2)*high
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
 # Explicit horizontally spread filled/lobed bun contours. Heights are authored
 # directly, so a path-frame width cannot accidentally grow into another peg.
 # center x,y,z; width,depth; fold-height wave. The top stays below 1.893m.
 bun=[
  [-.002,1.849,-.035,.034,.027,.001],
  [0,1.866,-.040,.0245,.0225,0],
  [-.007,1.877,-.049,.040,.032,.002],
  [-.014,1.884,-.056,.040,.029,.004],
  [-.014,1.887,-.056,.025,.019,.003],
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
 pole=len(vertices);vertices.append([-.014,1.882,-.056])
 for k in range(len(previous)):faces.append([previous[k],previous[(k+1)%len(previous)],pole])

 # A single attached S-flow curtain replaces the two independent round straps.
 # Closed broad planes vary in thickness and fold phase, with staggered tips.
 # y,z,x, halfwidth, halfdepth; not orthogonal circular loft cross-sections.
 flow=[
  [1.705,-.068,-.005,.065,.008],
  [1.686,-.087,-.006,.064,.010],
  [1.665,-.101,.003,.060,.010],
  [1.644,-.108,.014,.054,.009],
  [1.623,-.106,.018,.048,.0085],
  [1.603,-.098,.009,.043,.008],
  [1.584,-.088,-.006,.037,.0075],
  [1.567,-.074,-.020,.032,.006],
  [1.553,-.058,-.028,.030,.004],
  [1.545,-.042,-.031,.029,.0015],
 ]
 root_outer=[outer(LEVELS,k)for k in range(tail_a,tail_b+1)]
 root_inner=[inner(LEVELS,k)for k in range(tail_a,tail_b+1)]
 previous_outer,previous_inner=root_outer,root_inner
 n=len(root_outer)
 for row_index,row in enumerate(flow):
  cy,cz,cx,w,d=row;v=(row_index+1)/len(flow)
  new_outer,new_inner=[],[]
  for side,ring in [(-1,new_outer),(1,new_inner)]:
   for k in range(n):
    u=k/(n-1);s=math.cos(math.pi*u)
    # Broad unequal folds travel obliquely through one connected surface.
    phase=2*math.pi*(u+.14*math.sin(math.pi*v))
    fold=.0035*math.sin(phase)+.0015*math.sin(2*phase+.7)
    # Three unequal terminal reaches; this closes as a thin wedge, not a pair
    # of padded rounded caps. Main lower reach lies left of the center.
    end_lift=.034*(1-math.exp(-((u-.64)/.19)**2))+.008*s
    yy=cy+(v**2.6)*end_lift+.004*math.sin(phase)*math.sin(math.pi*v)
    xx=cx+w*s+.006*math.sin(phase)*math.sin(math.pi*v)
    zz=cz+side*d*(.72+.28*math.sin(math.pi*u))+fold*math.sin(math.pi*v)
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
 report.update(scope='Pure Python prepared C5 editable cage only; no Blender, image, source fit or art acceptance',author_sha256=sha(Path(__file__)),donor_path=str(args.donor),donor_sha256=sha(args.donor),source_cage_sha256=sha(args.output/'source-cage.json.gz'),maximum_bun_y=1.890,blender_run=False,actual_review='pending',protected_reference_changes='No Blender/reference mutation occurred')
 (args.output/'preparation-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
