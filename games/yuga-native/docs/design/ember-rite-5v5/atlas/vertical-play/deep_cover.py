"""Certify full 0.45 m receiver concealment close to each surveyed shoulder mark."""
import math
from architecture import APRON,BODY,CLEAR,EYES,TOPS,distance,point_seg,slab,vround


def certificate(survey,cover,observer,shoulder,posture,site):
    cx,cz=cover['center_xz'];w,d=cover['size_xz'];goal=survey.plan['nodes'][site]['xz']
    eye=[*observer,survey.height(observer)+EYES['standing']]
    # A circumscribed regular octagon contains the circular receiver cross-section.
    radius=BODY/math.cos(math.pi/8)
    rim=[(radius*math.cos((i+.5)*math.tau/8),radius*math.sin((i+.5)*math.tau/8)) for i in range(8)]
    def prove(p):
        if distance(p,goal)<APRON+CLEAR or not survey.walk_segment(p,shoulder):return False
        y=survey.height(p)
        for h in (0,TOPS[posture]):
            for dx,dz in rim:
                corner=(p[0]+dx,p[1]+dz,y+h)
                if slab(eye,corner,cover['min_xyz'],cover['max_xyz']) is None:return False
                if survey.hits(eye,corner)[0][1]!=cover['id']:return False
        return True
    candidates=[shoulder]
    for nx,nz in ((1,0),(-1,0),(0,1),(0,-1)):
        if (observer[0]-cx)*nx+(observer[1]-cz)*nz>0:continue
        for pad in (.66,.70,.76,.85,1.0):
            for fraction in (0.,.18,-.18,.36,-.36,.54,-.54,.72,-.72,.90,-.90):
                extent=(w if nx else d)/2;half=(d if nx else w)/2
                candidates.append(vround((cx+nx*(extent+pad)-nz*half*fraction,cz+nz*(extent+pad)+nx*half*fraction)))
    cases=sorted(candidates,key=lambda p:distance(p,shoulder))
    found=next((p for p in cases if prove(p)),None)
    if found is None:
        # Where the ramp wraps a tight corner, step diagonally beside the jamb.
        cases=(vround((cx+i*.08,cz+j*.08)) for i in range(-40,41) for j in range(-40,41))
        found=next((p for p in sorted(cases,key=lambda p:distance(p,shoulder)) if prove(p)),None)
    if found is None:raise ValueError(f"Whole receiver remains exposed at {cover['id']} from {observer}")
    return found


def build(survey,data,architecture_hash):
    entries=[]
    for e in data['entrances']:
        choices=[]
        for p in e['pockets']:
            entry={'cover_id':p['cover_id'],'posture':p['posture']};cover=survey.by_id[p['cover_id']]
            for name,prefix in (('forward',''),('reverse','reverse_')):
                shoulder=p[prefix+'hide_xz'];target=certificate(survey,cover,p[prefix+'threat_xz'],shoulder,p['posture'],e['site'])
                entry[name]=dict(hide_xz=target,shoulder_xz=shoulder,peek_xz=p[prefix+'peek_xz'],
                                 step_to_shoulder_m=round(distance(target,shoulder),3),corner_rays_blocked=16)
            choices.append(entry)
        for k in (0,1):
            for name in ('forward','reverse'):
                guard=choices[1-k][name]['hide_xz'];p=e['pockets'][k];pose=choices[k][name]
                way=p[name+'_walk_xz']+[pose['hide_xz']]
                if any(point_seg(guard,a,b)<2*CLEAR-1e-5 for a,b in zip(way,way[1:])):
                    raise ValueError(f"The deep alternative blocks its partner at {e['id']}")
                if point_seg(guard,pose['hide_xz'],pose['shoulder_xz'])<2*CLEAR:
                    raise ValueError(f"Paired deep stances overlap at {e['id']}")
        entries.append(dict(id=e['id'],site=e['site'],pockets=choices))
    return dict(schema='yuga.vertical-play.body-cover.v1',architecture_sha256=architecture_hash,body_radius_m=BODY,
                method='From each fixed ground observer, the named opaque box is first hit on rays to all 16 vertices of a full-height regular octagonal prism circumscribing the 0.45 m receiver cylinder. The shadow of a convex box from a point is convex, so it contains the entire cylinder. The short path to the shoulder witness clears the 0.65 m movement envelope.',
                standing_height_m=TOPS['standing'],crouched_height_m=TOPS['crouched'],
                limit='The certification applies to the declared ground eye and stance. A raised or laterally moved eye changes the occluded volume.',entrances=entries)
