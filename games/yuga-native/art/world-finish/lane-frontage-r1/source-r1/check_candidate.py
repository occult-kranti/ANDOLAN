"""Independent real-triangle checks. Source geometry only; not Godot physics or art."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct


def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def mul(a,k):return tuple(x*k for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):return math.sqrt(dot(a,a))
def clamp(x):return max(0.,min(1.,x))


def ray(origin,direction,triangles):
    hits=[]
    for a,b,c in triangles:
        e1,e2=sub(b,a),sub(c,a);h=cross(direction,e2);det=dot(e1,h)
        if abs(det)<1e-10:continue
        inv=1/det;s=sub(origin,a);u=dot(s,h)*inv
        if u< -1e-9 or u>1+1e-9:continue
        q=cross(s,e1);v=dot(direction,q)*inv
        if v< -1e-9 or u+v>1+1e-9:continue
        t=dot(e2,q)*inv
        if t>=0:hits.append(t)
    return min(hits) if hits else None


def point_triangle(p,t):
    a,b,c=t;ab,ac,ap=sub(b,a),sub(c,a),sub(p,a);d1,d2=dot(ab,ap),dot(ac,ap)
    if d1<=0 and d2<=0:return a
    bp=sub(p,b);d3,d4=dot(ab,bp),dot(ac,bp)
    if d3>=0 and d4<=d3:return b
    vc=d1*d4-d3*d2
    if vc<=0 and d1>=0 and d3<=0:return add(a,mul(ab,d1/(d1-d3)))
    cp=sub(p,c);d5,d6=dot(ab,cp),dot(ac,cp)
    if d6>=0 and d5<=d6:return c
    vb=d5*d2-d1*d6
    if vb<=0 and d2>=0 and d6<=0:return add(a,mul(ac,d2/(d2-d6)))
    va=d3*d6-d5*d4
    if va<=0 and d4-d3>=0 and d5-d6>=0:return add(b,mul(sub(c,b),(d4-d3)/((d4-d3)+(d5-d6))))
    den=1/(va+vb+vc);return add(a,add(mul(ab,vb*den),mul(ac,vc*den)))


def segment_distance(p1,q1,p2,q2):
    d1,d2,r=sub(q1,p1),sub(q2,p2),sub(p1,p2);a,e=dot(d1,d1),dot(d2,d2);f=dot(d2,r)
    if a<=1e-20 and e<=1e-20:return norm(r)
    if a<=1e-20:s,t=0.,clamp(f/e)
    else:
        c=dot(d1,r)
        if e<=1e-20:t,s=0.,clamp(-c/a)
        else:
            b=dot(d1,d2);den=a*e-b*b;s=clamp((b*f-c*e)/den) if den else 0.;t=(b*s+f)/e
            if t<0:t,s=0.,clamp(-c/a)
            elif t>1:t,s=1.,clamp((b-c)/a)
    return norm(sub(add(p1,mul(d1,s)),add(p2,mul(d2,t))))


def capsule_clearance(segment,triangles):
    p,q=segment;direction=sub(q,p);hit=ray(p,direction,triangles)
    if hit is not None and hit<=1:return 0.
    best=float('inf')
    for t in triangles:
        best=min(best,norm(sub(p,point_triangle(p,t))),norm(sub(q,point_triangle(q,t))))
        for a,b in zip(t,[t[1],t[2],t[0]]):best=min(best,segment_distance(p,q,a,b))
    return best


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mesh',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():p.error('fresh output required')
    data=json.loads(args.mesh.read_text());repo=Path(__file__).resolve().parents[5];checks=[]
    def check(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
    manifest=json.loads((repo/'games/yuga-native/assets/world/confluence-map.json').read_text());body=next(x for x in manifest['authority_collision_boxes'] if x['id']=='authority-solid-2')
    check('actual authority ID dimensions base and planar manifest held',data['authority_id']==body['id'] and data['dimensions']==body['size'] and data['position']==body['position'])
    glb=(repo/'games/yuga-native/assets/world/architecture.glb').read_bytes();size,kind=struct.unpack_from('<II',glb,12);gltf=json.loads(glb[20:20+size]);names={x.get('name') for x in gltf['materials']}
    check('all material references exist in actual original GLB',set(data['material_names'])<=names,sorted(set(data['material_names'])-names))
    for lod,g in data['geometry'].items():
        tris=[tuple(tuple(p) for p in t) for s in g['surfaces'] for t in s['triangles']];pts=[v for t in tris for v in t]
        bounds=[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]
        check(lod+' actual broad bounds unchanged',bounds==[[-9,0,-9],[9,15,9]],bounds)
        check(lod+' finite nondegenerate triangle and surface budget',all(math.isfinite(n) for v in pts for n in v) and all(norm(cross(sub(t[1],t[0]),sub(t[2],t[0])))>1e-10 for t in tris) and len(tris)<=6000 and len(g['surfaces'])==3,{'triangles':len(tris),'surfaces':len(g['surfaces'])})
        undirected=Counter();directed=Counter()
        for t in tris:
            for a,b in zip(t,[t[1],t[2],t[0]]):undirected[tuple(sorted([a,b]))]+=1;directed[a,b]+=1
        bad=[(e,n) for e,n in undirected.items() if n!=2 or directed[e[0],e[1]]!=directed[e[1],e[0]]]
        check(lod+' watertight consistently oriented real mesh',not bad,{'bad_edges':len(bad),'examples':str(bad[:3])})
        volume=sum(dot(a,cross(b,c)) for a,b,c in tris)/6
        check(lod+' closed positive solid volume without duplicate faces',4500<volume<=4860 and len({tuple(sorted(t)) for t in tris})==len(tris),{'volume_m3':volume})
        for x,y,expected in [(0,1.4,-8.35),(6,2.1,-8.55),(2.7,6.3,-8.55),(3.95,2.1,-9)]:
            t=ray((x,y,-12),(0,0,1),tris);actual=-12+t if t is not None else None
            check(lod+f' actual closed ray contact at{x}/{y}',actual is not None and abs(actual-expected)<1e-7,{'z':actual,'expected_z':expected,'old_flat_z':-9})
        # Independent footprint sampling: every chosen street-to-body line ends at
        # solid triangles, with no new doorway/through-corridor.
        check(lod+' frontage sample rays remain closed',all(ray((x,y,-12),(0,0,1),tris) is not None for x in [-8.8,-6,-4,-2,0,2,4,6,8.8] for y in [.1,1.4,3.6,6.3,10.3,14.8]))
        top=ray((0,20,0),(0,-1,0),tris);check(lod+' existing roof support stays Y15',top is not None and abs(20-top-15)<1e-8)
        near=((0,.39,-9.1),(0,1.41,-9.1));touch=((0,.39,-8.69),(0,1.41,-8.69));clear=capsule_clearance(near,tris);contact=capsule_clearance(touch,tris)
        check(lod+' actual source-triangle capsule approach and contact',clear>.34 and abs(contact-.34)<1e-7,{'clearance_before_m':clear,'clearance_at_back_m':contact,'radius_m':.34,'scope':'Exact geometric capsule/triangle distance; not Godot sweep or locomotion acceptance.'})
        old_front=[((-9,0,-9),(-9,15,-9),(9,15,-9)),((-9,0,-9),(9,15,-9),(9,0,-9))]
        old_clear=capsule_clearance(near,old_front)
        check(lod+' old flat box standoff negative control rejects old collision',old_clear<.34 and clear>.34 and abs(ray((0,1.4,-12),(0,0,1),old_front)-ray((0,1.4,-12),(0,0,1),tris))>.6,{'old_clearance_m':old_clear,'proposed_clearance_m':clear,'old_kept_would_be_rejected':True})
        corrupted=tris[:-1];u=Counter(tuple(sorted([a,b])) for t in corrupted for a,b in zip(t,[t[1],t[2],t[0]]));check(lod+' missing real triangle negative control rejected',any(n!=2 for n in u.values()))
    check('mid reduces geometry with same3material slots',data['geometry']['mid']['triangle_count']<data['geometry']['near']['triangle_count'])
    result={'passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,'mesh_sha256':hashlib.sha256(args.mesh.read_bytes()).hexdigest(),'scope':'Offline real generated triangles/envelope/closed-volume/rays/capsule-distance and source GLB material existence. No native parse/physics, effective runtime resource identity, visual acceptance or performance claim.'}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'count':len(checks),'failures':[x for x in checks if not x['passed']]}));raise SystemExit(0 if result['passed'] else 1)

if __name__=='__main__':main()
