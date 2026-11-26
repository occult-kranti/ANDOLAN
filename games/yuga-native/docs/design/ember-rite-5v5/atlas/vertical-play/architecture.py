"""Survey Mandala's two ritual courts and publish registered entrance cover drawings.

    python3 architecture.py             # author JSON, SVGs, and indexed PDF
    python3 architecture.py --check     # recompute the survey and vector sheets

All lengths are metres. Plan points are game (X,Z), survey triples are east,
north, elevation. Cover tops describe opaque vertical prisms on measured floors.
"""
import argparse
from collections import defaultdict, deque
import hashlib
import heapq
import json
import math
from pathlib import Path
import struct
import sys
import tempfile

ROOT=Path(__file__).resolve().parent
ATLAS=ROOT.parent
LAYOUT=ATLAS/'maps/mandala.json'
MODEL=ATLAS/'massing/mandala.glb'
EYES={'standing':1.60,'crouched':1.15}
TOPS={'standing':1.80,'crouched':1.32}
BODY=.45
CLEAR=.65
APRON=4.5
GRID=.50
WITNESS_DISTANCE=4.
ORDER=('a-bank','a-temple_s','a-temple_n','a-mid','b-pyramid_s','b-pyramid_n','b-mid')
# Both pockets have different physical bodies. Several pieces serve neighbouring approaches.
ASSIGN={
 'a-bank':('a-gauge-locker','bell-screen'),
 'a-temple_s':('bell-screen','a-trace-table'),
 'a-temple_n':('a-gauge-locker','a-float-case'),
 'a-mid':('a-river-screen','a-trace-table'),
 'b-pyramid_s':('b-receipt-shutter','b-bale-bench'),
 'b-pyramid_n':('b-cart-chest','b-stamp-screen'),
 'b-mid':('b-market-register','b-measure-post'),
}
# id / public callout / centre X,Z / width, depth, height / treatment
NEW=[
 ('a-gauge-locker','Gauge locker',[-8.3,7.45],[1.60,2.30,2.45],'hard'),
 ('a-trace-table','Trace table',[3.95,-7.05],[3.0,1.30,1.55],'hard'),
 ('a-float-case','Float case',[1.9,7.65],[2.60,1.35,1.55],'hard'),
 ('a-river-screen','River screen',[8.45,-1.5],[1.35,2.65,2.40],'hard'),
 ('b-receipt-shutter','Receipt shutter',[33.9,-6.5],[1.90,1.58,2.42],'hard'),
 ('b-bale-bench','Bale bench',[45.6,-7.55],[2.60,1.30,1.54],'hard'),
 ('b-stamp-screen','Stamp screen',[44.3,7.65],[2.30,1.45,2.40],'hard'),
 ('b-measure-post','Measure post',[31.30,2.0],[1.40,2.0,2.42],'hard'),
 ('b-cart-chest','Cart chest',[38.60,10.0],[1.25,1.10,1.62],'hard'),
 ('b-market-register','Market register',[28.44,6.70],[1.25,1.10,2.48],'hard'),
 ('a-rush-fringe','Rush fringe',[-9.,-8.20],[1.45,.38,.50],'soft'),
 ('b-twine-rack','Twine rack',[48.1,-6.50],[1.25,.38,.62],'soft'),
]


def distance(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def vround(p): return [round(float(x),4) for x in p]
def slug(s):return s.lower().replace(' ','-')
def bounds(c):return (c['min_xyz'][0],c['min_xyz'][1],c['max_xyz'][0],c['max_xyz'][1])

def pt_box(p,box):
    l,s,r,n=box
    return math.hypot(max(l-p[0],0,p[0]-r),max(s-p[1],0,p[1]-n))

def point_seg(p,a,b):
    x,z=b[0]-a[0],b[1]-a[1]
    if x*x+z*z<1e-12:return distance(p,a)
    t=max(0,min(1,((p[0]-a[0])*x+(p[1]-a[1])*z)/(x*x+z*z)))
    return distance(p,(a[0]+t*x,a[1]+t*z))

def slab(a,b,lo,hi):
    t0,t1=0.,1.
    for p,q,l,h in zip(a,b,lo,hi):
        if abs(q-p)<1e-10:
            if not l<=p<=h:return None
        else:
            u,v=sorted(((l-p)/(q-p),(h-p)/(q-p)));t0=max(t0,u);t1=min(t1,v)
            if t0>t1:return None
    return t0,t1

def room_box(node):
    x,z=node['xz'];w,d=node['size'];return (x-w/2,z-d/2,x+w/2,z+d/2)

def read_floor(path,expected):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0]
    j=json.loads(raw[20:20+n]);binary=memoryview(raw)[20+n+8:]
    obj,=(k for k in j['nodes'] if k.get('extras',{}).get('kind')=='atlas_floor')
    if obj['extras']['source_sha256']!=expected:raise ValueError('Floor GLB and source map hashes differ')
    buckets=defaultdict(list)
    def values(i):
        a=j['accessors'][i];v=j['bufferViews'][a['bufferView']]
        layout={'SCALAR':1,'VEC3':3}[a['type']];fmt='<'+{5123:'H',5125:'I',5126:'f'}[a['componentType']]*layout
        base=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',struct.calcsize(fmt))
        return [struct.unpack_from(fmt,binary,base+k*stride) for k in range(a['count'])]
    for prim in j['meshes'][obj['mesh']]['primitives']:
        if j['materials'][prim['material']]['name']=='Skirt':continue
        verts=[(x,-z,y) for x,y,z in values(prim['attributes']['POSITION'])]
        ix=[p[0] for p in values(prim['indices'])]
        for k in range(0,len(ix),3):
            a,b,c=[verts[i] for i in ix[k:k+3]]
            u,v=[b[i]-a[i] for i in range(3)],[c[i]-a[i] for i in range(3)]
            den=u[0]*v[1]-u[1]*v[0]
            if abs(den)<1e-8:continue
            tri=(a,u,v,den)
            for i in range(math.floor(min(a[0],b[0],c[0])/4),math.floor(max(a[0],b[0],c[0])/4)+1):
                for m in range(math.floor(min(a[1],b[1],c[1])/4),math.floor(max(a[1],b[1],c[1])/4)+1):buckets[i,m].append(tri)
    def height(p):
        for a,u,v,den in buckets[math.floor(p[0]/4),math.floor(p[1]/4)]:
            dx,dz=p[0]-a[0],p[1]-a[1]
            alpha=(dx*v[1]-dz*v[0])/den;beta=(u[0]*dz-u[1]*dx)/den
            if alpha>=-1e-6 and beta>=-1e-6 and alpha+beta<=1.000001:return a[2]+alpha*u[2]+beta*v[2]
        raise ValueError(f'No exported floor under {p}')
    return height


def create_cover(id,label,center,size,site,kind,source,height):
    x,z=center;w,d,h=size
    sampled=[height((x+w*i/4,z+d*j/4)) for i in (-2,-1,0,1,2) for j in (-2,-1,0,1,2)]
    y=height(center) if source=='atlas' else min(sampled)
    return dict(id=id,label=label,center_xz=center,size_xz=[w,d],base_y=round(y,4),height_m=h,
                min_xyz=vround((x-w/2,z-d/2,y)),max_xyz=vround((x+w/2,z+d/2,y+h)),site=site,kind=kind,source=source,
                collision=kind=='hard',landable=False,ground_range_y=vround((min(sampled),max(sampled))))


class Survey:
    def __init__(self):
        self.hash=hashlib.sha256(LAYOUT.read_bytes()).hexdigest()
        self.plan=json.loads(LAYOUT.read_text());self.height=read_floor(MODEL,self.hash)
        self.rooms=list(self.plan['nodes'].values());self.segments=[]
        for e in self.plan['links']:
            if e['kind']=='fold':continue
            path=self.path(e)
            self.segments.extend((a,b,e['width']/2) for a,b in zip(path,path[1:]))
        self.covers=[]
        for c in self.plan['cover']:
            site=next((k for k in ('a','b') if pt_box(c['xz'],room_box(self.plan['nodes'][k]))==0),None)
            self.covers.append(create_cover(slug(c['label']),c['label'],c['xz'],[*c['size'],c['height']],site,'hard','atlas',self.height))
        for id,label,center,size,kind in NEW:self.covers.append(create_cover(id,label,center,size,id[0],kind,'vertical-play',self.height))
        self.hard=[c for c in self.covers if c['kind']=='hard'];self.by_id={c['id']:c for c in self.covers}
        self.grid_cache={};self.solid_boxes=[bounds(c) for c in self.hard]
    def path(self,e):return [self.plan['nodes'][e['from']]['xz'],*e.get('via',[]),self.plan['nodes'][e['to']]['xz']]
    def legal(self,p):
        if any(pt_box(p,b)<CLEAR-1e-7 for b in self.solid_boxes):return False
        return any(abs(p[0]-r['xz'][0])<=r['size'][0]/2-CLEAR and abs(p[1]-r['xz'][1])<=r['size'][1]/2-CLEAR for r in self.rooms) or any(point_seg(p,a,b)<=w-CLEAR for a,b,w in self.segments)
    def walk_segment(self,a,b):
        steps=max(1,math.ceil(distance(a,b)/.15))
        return all(self.legal((a[0]+(b[0]-a[0])*i/steps,a[1]+(b[1]-a[1])*i/steps)) for i in range(steps+1))
    def hits(self,a,b):
        hits=[]
        for c in self.hard:
            out=slab(a,b,c['min_xyz'],c['max_xyz'])
            if out:hits.append((out[0],c['id']))
        return sorted(hits)
    def silhouette(self,observer,target,posture,delta=0):
        eye=[*observer,self.height(observer)+EYES['standing']+delta]
        v=[target[0]-observer[0],target[1]-observer[1]];n=math.hypot(*v);side=[-v[1]/n,v[0]/n]
        floor=self.height(target)
        return [self.hits(eye,[target[0]+off*side[0],target[1]+off*side[1],floor+h]) for h in (.15,EYES[posture],TOPS[posture]) for off in (-.28,0,.28)]
    def reachable(self,site):
        if site in self.grid_cache:return self.grid_cache[site]
        node=self.plan['nodes'][site];cx,cz=node['xz'];start=(round(cx/GRID),round(cz/GRID));queue=deque([start]);prev={start:None}
        # The local survey connects each court, mouth and approach cue over actual eroded floor.
        # Four connected neighbours avoid cutting diagonal corners. Edge bodies are checked at midpoint.
        while queue:
            i,j=queue.popleft()
            for di,dj in ((1,0),(-1,0),(0,1),(0,-1)):
                nxt=(i+di,j+dj);x,z=nxt[0]*GRID,nxt[1]*GRID
                if nxt in prev or abs(x-cx)>24 or abs(z-cz)>24:continue
                if self.legal((x,z)) and self.legal((x-di*GRID/2,z-dj*GRID/2)):
                    prev[nxt]=(i,j);queue.append(nxt)
        self.grid_cache[site]=prev
        return prev
    def reach(self,site,p):
        graph=self.reachable(site);i,j=(round(v/GRID) for v in p)
        near=sorted(((a,b) for a in range(i-2,i+3) for b in range(j-2,j+3) if (a,b) in graph),key=lambda q:distance(p,(q[0]*GRID,q[1]*GRID)))
        return next((q for q in near if self.walk_segment(p,(q[0]*GRID,q[1]*GRID))),None)


def points_on_approach(survey,site,approach):
    edge,=(e for e in survey.plan['links'] if set((e['from'],e['to']))=={site,approach} and e['kind']!='fold')
    pts=survey.path(edge)
    if edge['from']==site:pts.reverse()
    box=room_box(survey.plan['nodes'][site]);total=0
    for a,b in zip(pts,pts[1:]):
        span=slab(a,b,box[:2],box[2:]);length=distance(a,b)
        if span:
            mouth=[a[k]+span[0]*(b[k]-a[k]) for k in (0,1)]
            if pt_box(a,box)>0:
                at=total+span[0]*length
                bearing=math.degrees(math.atan2(b[0]-a[0],b[1]-a[1]))%360
                break
        total+=length
    else:raise ValueError('No site threshold for '+approach)
    remaining=at-WITNESS_DISTANCE
    for a,b in zip(pts,pts[1:]):
        length=distance(a,b)
        if remaining<=length:
            threat=[a[k]+(b[k]-a[k])*remaining/length for k in (0,1)];break
        remaining-=length
    return edge,vround(mouth),vround(threat),round(bearing,3)


def pocket_side(survey,c,observer,site,posture,avoid_face=None):
    l,s,r,n=bounds(c);cx,cz=c['center_xz'];pad=CLEAR+.11;goal=survey.plan['nodes'][site]['xz'];candidates=[]
    # The usable stance lies on the far solid face. Search for a short lateral move
    # along that face that genuinely reveals the observer over the full clear path.
    directions=(('west',(-1,0)),('east',(1,0)),('south',(0,-1)),('north',(0,1)))
    for face,(nx,nz) in directions:
        if face==avoid_face:continue
        if (observer[0]-cx)*nx+(observer[1]-cz)*nz>0:continue
        axial=(r-l if nx else n-s)/2
        half=(n-s if nx else r-l)/2
        for fraction in (0.,.28,-.28,.58,-.58):
            mid=(cx+nx*(axial+pad),cz+nz*(axial+pad));off=half*fraction
            hide=vround((mid[0]-nz*off,mid[1]+nx*off))
            if distance(hide,goal)<APRON+CLEAR or not survey.legal(hide):continue
            rays=survey.silhouette(observer,hide,posture)
            if not all(hits and hits[0][1]==c['id'] for hits in rays):continue
            for sign in (-1,1):
                for extra in (.32,.60,.95,1.30,1.70,2.10):
                    walk=sign*(half+extra)
                    peek=vround((mid[0]-nz*walk,mid[1]+nx*walk))
                    if distance(peek,goal)<APRON+CLEAR or not survey.walk_segment(hide,peek):continue
                    h=survey.height(peek)+EYES[posture];view=survey.height(observer)+EYES['standing']
                    if survey.hits([*observer,view],[*peek,h]):continue
                    if survey.reach(site,hide) is None or survey.reach(site,peek) is None:continue
                    cost=distance(hide,peek)+.15*abs(off)
                    candidates.append((cost,face,hide,peek));break
    if not candidates:return None
    return min(candidates,key=lambda c:c[0])


def pocket(survey,c,forward,reverse,site):
    posture='standing' if c['height_m']>=TOPS['standing']+.08 else 'crouched'
    f=pocket_side(survey,c,forward,site,posture)
    if f is None:raise ValueError(f"{site}/{c['id']}: no {posture} shelter from {forward}")
    r=pocket_side(survey,c,reverse,site,posture,f[1]);
    if r is None:raise ValueError(f"{site}/{c['id']}: no distinct reverse shelter from {reverse}; forward face {f[1]}")
    air=survey.silhouette(forward,f[2],posture,4.)
    standing=survey.silhouette(forward,f[2],'standing')
    return dict(cover_id=c['id'],posture=posture,threat_xz=forward,threat_floor_y=round(survey.height(forward),3),
                hide_xz=f[2],sheltered_face=f[1],peek_xz=f[3],peek_distance_m=round(distance(f[2],f[3]),2),
                reverse_threat_xz=reverse,reverse_threat_floor_y=round(survey.height(reverse),3),reverse_hide_xz=r[2],
                reverse_sheltered_face=r[1],reverse_peek_xz=r[3],reverse_peek_distance_m=round(distance(r[2],r[3]),2),
                silhouette_rays_each_direction=9,air_eye_lift_m=4.,visible_air_rays=sum(not p for p in air),
                visible_standing_rays=sum(not p for p in standing))


def approach_path(survey,site,start,finish,occupied,avoid_apron):
    """Path with the other pocket occupied. Forward paths also reserve the site apron."""
    graph=survey.reachable(site)
    keepouts=[(occupied,2*CLEAR)]
    if avoid_apron:keepouts.append((survey.plan['nodes'][site]['xz'],APRON+CLEAR))
    def gap(a,b):
        return all(point_seg(center,a,b)>=radius-1e-6 for center,radius in keepouts)
    def clear(a,b):
        return gap(a,b) and survey.walk_segment(a,b)
    def xy(key):return [key[0]*GRID,key[1]*GRID]
    def anchor(p):
        i,j=[round(n/GRID) for n in p]
        choices=sorted(((a,b) for a in range(i-3,i+4) for b in range(j-3,j+4) if (a,b) in graph),
                       key=lambda key:distance(p,xy(key)))
        return next(key for key in choices if clear(p,xy(key)))
    if clear(start,finish):return [start,finish]
    a,b=anchor(start),anchor(finish)
    came={a:None};cost={a:0};todo=[(distance(xy(a),xy(b)),a)]
    while todo:
        _,u=heapq.heappop(todo)
        if u==b:break
        for di,dj in ((1,0),(-1,0),(0,1),(0,-1)):
            v=u[0]+di,u[1]+dj
            if v not in graph or cost.get(v,math.inf)<=cost[u]+GRID or not clear(xy(u),xy(v)):continue
            came[v]=u;cost[v]=cost[u]+GRID
            heapq.heappush(todo,(cost[v]+distance(xy(v),xy(b)),v))
    if b not in came:raise ValueError(f'No independent route from {start} to {finish} on {site}')
    chain=[finish];u=b
    while u is not None:
        chain.append(xy(u));u=came[u]
    chain.append(start);chain.reverse()
    route=[start];i=0
    while i<len(chain)-1:
        nxt=len(chain)-1
        while nxt>i+1 and not clear(chain[i],chain[nxt]):nxt-=1
        route.append(chain[nxt]);i=nxt
    return route


def corridor_audit(survey):
    sample_count=0;minimum=(math.inf,'')
    for e in survey.plan['links']:
        if e['kind']=='fold':continue
        pts=survey.path(e)
        for a,b in zip(pts,pts[1:]):
            steps=math.ceil(distance(a,b)/.25)
            for i in range(steps+1):
                p=[a[k]+(b[k]-a[k])*i/steps for k in (0,1)];sample_count+=1
                for c in survey.hard:
                    if c['source']=='atlas':continue
                    clearance=pt_box(p,bounds(c))
                    minimum=min(minimum,(clearance,c['id']))
                    if clearance<CLEAR-1e-5:raise ValueError(f"{c['id']} blocks {e['from']}–{e['to']}")
    for c in survey.covers:
        for site in ('a','b'):
            if pt_box(survey.plan['nodes'][site]['xz'],bounds(c))<APRON:
                raise ValueError(f"{c['id']} intrudes into {site}'s protected disk")
    return dict(physical_links=sum(e['kind']!='fold' for e in survey.plan['links']),centreline_samples=sample_count,
                least_new_cover_clearance_m=round(minimum[0],3),nearest_new_cover=minimum[1])


def build():
    survey=Survey();entrances=[]
    for key in ORDER:
        site,approach=key.split('-',1);edge,mouth,forward,bearing=points_on_approach(survey,site,approach)
        reverse=survey.plan['nodes'][site]['xz']
        if survey.reach(site,forward) is None:raise ValueError(f'{key}: observation point unreachable')
        entries=[pocket(survey,survey.by_id[id],forward,reverse,site) for id in ASSIGN[key]]
        for index,p in enumerate(entries):
            other=entries[1-index]
            for prefix,witness,hide,other_hide in (
                    ('forward',forward,p['hide_xz'],other['hide_xz']),
                    ('reverse',reverse,p['reverse_hide_xz'],other['reverse_hide_xz'])):
                path=approach_path(survey,site,witness,hide,other_hide,prefix=='forward')
                p[prefix+'_walk_xz']=path
                p[prefix+'_walk_m']=round(sum(distance(a,b) for a,b in zip(path,path[1:])),2)
        angle=math.radians(bearing);right=[math.cos(angle),-math.sin(angle)]
        centerline=[math.sin(angle),math.cos(angle)]
        # A furnished threshold can put the passing pair off the exact centreline.
        # Slide the two lanes together, keeping both centres inside the corridor width.
        shoulders=[]
        shifts=sorted([i*.10 for i in range(-25,26)],key=abs)
        for shift in shifts:
            if abs(shift)+.68+CLEAR>edge['width']/2:continue
            trial=[]
            for sign in (-1,1):
                p=[mouth[i]+(shift+sign*.68)*right[i] for i in (0,1)]
                s=[p[i]-centerline[i]*.9 for i in (0,1)]
                t=[p[i]+centerline[i]*.9 for i in (0,1)]
                if survey.walk_segment(s,t):trial.append(vround(p))
            if len(trial)==2:
                shoulders=trial
                break
        if not shoulders:raise ValueError(f'{key} two-body gate is blocked')
        entrances.append(dict(id=key,site=site,approach=approach,mouth_xz=mouth,width_m=edge['width'],inbound_bearing_deg=bearing,
                              two_body_mouth_xz=shoulders,two_body_center_separation_m=1.36,
                              two_body_offset_from_mouth_m=round(shift,2),two_body_clearance_radius_m=CLEAR,pockets=entries))
    return dict(schema='yuga.vertical-play.cover.v1',district='Mandala Rift',units='metres',axes='2D X/Z east/north; survey xyz triples east/north/elevation; game Y is up',
                source_sha256=survey.hash,floor_glb_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),body_radius_m=BODY,movement_clearance_m=CLEAR,
                eye_height_m=EYES,silhouette_top_m=TOPS,protected_apron_m=APRON,silhouette_shoulder_halfwidth_m=.28,
                approach_observer_distance_m=WITNESS_DISTANCE,circulation=corridor_audit(survey),
                visibility_policy='Soft dressings permit movement and sight. Ground observations classify a specific view; the +4 m lifted view is checked independently. These probes grant no minimap marker, enemy location or landing permission.',
                covers=survey.covers,entrances=entrances),survey


def crosscheck(data):
    hero=json.loads((ROOT/'heroes.json').read_text())['field_rig']['common']
    expected={'standing_height_m':TOPS['standing'],'crouch_height_m':TOPS['crouched'],'standing_eye_m':EYES['standing'],
              'crouch_eye_m':EYES['crouched'],'hurt_radius_m':BODY,'route_clearance_radius_m':CLEAR,
              'shoulder_ray_offsets_m':[-.28,.28]}
    if any(hero[key]!=value for key,value in expected.items()):raise ValueError('Hero rig and architecture probes disagree')
    physics=json.loads((ROOT/'physics.json').read_text())
    if physics['rules']['wind']['height_m']!=4.:raise ValueError('Wind and architecture witness heights disagree')
    matched={(p['entrance'],p['cover']):p for p in physics['cover_crosscheck']}
    pairs=[(e['id'],p) for e in data['entrances'] for p in e['pockets']]
    for key,p in pairs:
        fresh=matched[key,p['cover_id']]
        if (fresh['visible_ground'],fresh['visible_reverse'],fresh['visible_air'])!=(0,0,p['visible_air_rays']):
            raise ValueError('Independent physics sightlines disagree at '+key)
    print(f'Hero common rig, 4 m lift and {len(pairs)*27} independent physics sight samples agree.')


def main():
    sys.path.insert(0, str(ROOT))
    import architecture_draw
    import deep_cover
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true',help='compare JSON, SVGs and a fresh PDF to the checked-in files')
    p.add_argument('--check-vectors',action='store_true',help='verify registered geometry and SVGs using the standard library')
    p.add_argument('--cross-check-panels',action='store_true',help='also compare independent hero and physics results')
    p.add_argument('--out',type=Path,default=ROOT)
    args=p.parse_args()
    data,survey=build()
    if args.cross_check_panels:crosscheck(data)
    encoded=(json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode()
    deep=deep_cover.build(survey,data,hashlib.sha256(encoded).hexdigest())
    files=architecture_draw.build_pages(data,survey.plan,deep)
    files['architecture.json']=encoded
    files['mandala-body-cover.json']=(json.dumps(deep,indent=2,ensure_ascii=False)+'\n').encode()
    if args.check_vectors:
        for name,body in files.items():
            if (args.out/name).read_bytes()!=body:raise ValueError(f'{name} disagrees with this survey')
        print('Registered geometry, full-body certificates and all three SVG sheets agree.')
        return
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp) if args.check else args.out
        out.mkdir(parents=True,exist_ok=True)
        for name,body in files.items():(out/name).write_bytes(body)
        architecture_draw.pdf(out)
        if args.check:
            for name in [*files,'mandala-cover-atlas.pdf']:
                if (out/name).read_bytes()!=(args.out/name).read_bytes():
                    raise ValueError(f'{name} disagrees with this survey')
    print(f"Verified {len(data['entrances'])} mouths, 14 independently reachable pairs of reciprocal stances, 14 peeks each way, and {data['circulation']['centreline_samples']} route samples.")


if __name__=='__main__':
    main()
