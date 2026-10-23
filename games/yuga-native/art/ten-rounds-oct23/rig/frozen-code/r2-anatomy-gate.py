"""R2 side-gated closest-face reuse with an explicit provisional arm repose.

This uses the same polygon-interpolated/four-weight transfer principle as the
existing shoulder study. Inferred source landmarks are not authored joints.
It never changes the donor skeleton or donor actions and never promotes assets.
"""
import hashlib, math
from collections import Counter, defaultdict
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ARM_PREFIX=('upperarm','lowerarm','wrist','finger','metacarpal')
LEG_PREFIX=('upperleg','lowerleg','foot','toe')
def family(name):
    side=name[-1] if name.endswith(('.L','.R')) else None
    if name.startswith(ARM_PREFIX):return 'arm.'+str(side)
    if name.startswith(LEG_PREFIX):return 'leg.'+str(side)
    return 'core'
def smooth(a,b,x):
    t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)
def segment(point,a,b):
    delta=b-a;t=max(0.,min(1.,(point-a).dot(delta)/delta.length_squared));q=a+delta*t
    return t,q,(point-q).length
def apply(target,surface,rig):
    source_positions=[v.co.copy() for v in target.data.vertices]
    donor_vertices=[v.co.copy() for v in surface.data.vertices]
    donor_weights=[{surface.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-8} for v in surface.data.vertices]
    surface.data.calc_loop_triangles();triangles=[tuple(t.vertices) for t in surface.data.loop_triangles if t.area>1e-12]
    source_chains={};donor_chains={}
    # Source landmarks are provisional centerline estimates in the measured
    # uniform-fit coordinate frame, with nearest surface residuals below.
    for side,sign in [('L',1),('R',-1)]:
        source_chains[side]=[Vector((sign*x,y,z)) for x,y,z in [(.25,-.02,1.47),(.40,-.025,1.20),(.47,-.04,1.02),(.48,-.055,.90)]]
        donor_chains[side]=[rig.data.bones['upperarm01.'+side].head_local.copy(),rig.data.bones['lowerarm01.'+side].head_local.copy(),rig.data.bones['wrist.'+side].head_local.copy(),rig.data.bones['finger3-3.'+side].tail_local.copy()]
    regions=defaultdict(list)
    for tri in triangles:
        totals=defaultdict(float)
        for vi in tri:
            for name,w in donor_weights[vi].items():totals[family(name)]+=w/3
        dominant=max(totals,key=totals.get)
        # Every retained corner must have compatible weights. Average-only
        # face labeling can choose an incompatible pure-limb corner.
        def all_compatible(allowed):return all(sum(w for name,w in donor_weights[vi].items() if family(name) in allowed)>1e-6 for vi in tri)
        if dominant.startswith('arm.') and all_compatible({dominant,'core'}):regions[dominant].append(tri)
        else:
            if not dominant.startswith('arm.'):regions['nonarm'].append(tri)
            if dominant not in {'leg.R'} and all_compatible({'core','leg.L'}):regions['nonarm.L'].append(tri)
            if dominant not in {'leg.L'} and all_compatible({'core','leg.R'}):regions['nonarm.R'].append(tri)
        if dominant=='core' and all_compatible({'core'}):regions['core'].append(tri)
    trees={name:BVHTree.FromPolygons(donor_vertices,faces,all_triangles=True) for name,faces in regions.items()}
    def query(point,region,allowed):
        loc,normal,index,distance=trees[region].find_nearest(point)
        tri=regions[region][index];a,b,c=[donor_vertices[x] for x in tri]
        bary=barycentric_transform(loc,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
        out=defaultdict(float)
        for vi,amount in zip(tri,bary):
            for name,w in donor_weights[vi].items():
                if allowed(family(name)):out[name]+=max(0.,amount)*w
        total=sum(out.values())
        if total<=1e-10:raise RuntimeError('Empty compatible weights '+repr({'region':region,'point':list(point),'bary':list(bary),'triangle':tri,'triangle_weights':[donor_weights[i] for i in tri]}))
        return {name:w/total for name,w in out.items()},distance
    labels=[];weights=[];counts=Counter();distances=defaultdict(list);moves=[];leg_in_arm=[];opposite_arm=[];body_arm=[]
    for vi,point in enumerate(source_positions):
        side='L' if point.x>=0 else 'R';src=source_chains[side];dst=donor_chains[side]
        nearest=[segment(point,src[i],src[i+1]) for i in range(3)];best=min(range(3),key=lambda i:nearest[i][2]);distance=nearest[best][2]
        # Capsule boundary is smooth in distance and fades onto the torso at
        # the shoulder. Rear drape outside the arm capsule remains nonarm.
        inner=.085 if best==0 else .075;outer=.15 if best==0 else .12
        blend=(1-smooth(inner,outer,distance))*smooth(.17,.29,abs(point.x))
        if point.z<.80 or point.z>1.64:blend=0.
        if blend>0:
            mapped=Vector((0,0,0));amounts=[]
            for i,(t,q,d) in enumerate(nearest):
                amount=math.exp(-((d/max(.045,.09 if i==0 else .075))**2))*max(.0001,1-d/.5)
                rot=(src[i+1]-src[i]).rotation_difference(dst[i+1]-dst[i])
                mapped+=(dst[i].lerp(dst[i+1],t)+rot@(point-q))*amount;amounts.append(amount)
            mapped/=sum(amounts);posed=point.lerp(mapped,blend)
            armw,dist=query(posed,'arm.'+side,lambda f:f in {'arm.'+side,'core'})
            if blend>=1-1e-8:out=armw;label='arm.'+side
            else:
                corew,cdist=query(posed,'core',lambda f:f=='core');distances['core_boundary'].append(cdist)
                out=defaultdict(float)
                for name,w in armw.items():out[name]+=w*blend
                for name,w in corew.items():out[name]+=w*(1-blend)
                label='arm_core_boundary.'+side
            distances['arm.'+side].append(dist)
        else:
            posed=point
            region='core' if point.z>1.02 else 'nonarm.'+side
            out,dist=query(posed,region,lambda f:f=='core' or (region!='core' and f=='leg.'+side))
            distances[region].append(dist);label=region
        target.data.vertices[vi].co=posed;moves.append((posed-point).length);labels.append(label);weights.append(dict(out));counts[label]+=1
        if label.startswith('arm'):
            leg_in_arm.append(sum(w for n,w in out.items() if family(n).startswith('leg.')))
            opposite_arm.append(sum(w for n,w in out.items() if family(n)=='arm.'+('R' if side=='L' else 'L')))
        else:body_arm.append(sum(w for n,w in out.items() if family(n).startswith('arm.')))
    for group in list(target.vertex_groups):target.vertex_groups.remove(group)
    for group in surface.vertex_groups:target.vertex_groups.new(name=group.name)
    for vi,out in enumerate(weights):
        for name,w in out.items():
            if w>1e-8:target.vertex_groups[name].add([vi],w,'REPLACE')
    target.data.update()
    def percentile(v,p):return sorted(v)[int((len(v)-1)*p)]
    info={'method':'Side-gated nearest-face interpolation after explicit capsule-blended arm-chain repose; same donor rig/actions. Core-only shoulder boundary; no cross-limb weights.',
          'module_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'source_landmarks_fit_space':{side:[list(v) for v in chain] for side,chain in source_chains.items()},
          'donor_landmarks_rest_space':{side:[list(v) for v in chain] for side,chain in donor_chains.items()},
          'source_landmark_nearest_vertex_m':{side:[min((v-q).length for v in source_positions) for q in chain] for side,chain in source_chains.items()},
          'source_label_counts':dict(counts),'donor_region_triangles':{name:len(faces) for name,faces in regions.items()},
          'repose_displacement_m':{'max':max(moves),'p95':percentile(moves,.95),'moved_vertices':sum(m>1e-7 for m in moves)},
          'distance_m':{name:{'median':percentile(v,.5),'p95':percentile(v,.95),'max':max(v)} for name,v in distances.items()},
          'maximum_leg_weight_in_source_arm':max(leg_in_arm,default=0),'maximum_opposite_arm_weight':max(opposite_arm,default=0),'maximum_arm_weight_in_source_nonarm':max(body_arm,default=0),
          'provisional_landmarks':True,'retopology_or_authored_anatomy_claimed':False}
    return info
