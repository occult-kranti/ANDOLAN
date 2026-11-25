"""Reference-informed Hanuman shape and groom on the existing 167-bone studio rig.

All directions are in the authored rest pose (face -Y, Z up). The base
body keeps its topology, UVs, vertex groups, armature and action library.
The groom is separate editable geometry. The build operates on the opened
copy and uses no image texture on the anatomy.
"""
from __future__ import annotations

import math
from bisect import bisect_left
from itertools import accumulate
import random
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

PIPELINE = Path(__file__).resolve().parents[3] / "yuga" / "art" / "pipeline"
if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))
from geometry import Sculpt


def sm(a, b, v):
    t = min(1., max(0., (v-a)/(b-a)))
    return t*t*(3.-2.*t)


def bell(v, c, w):
    return math.exp(-((v-c)/w)**2)


def mix(a, b, t):
    return a+(b-a)*t


def named(scene, starts):
    found = [
        obj for obj in scene.objects
        if obj.name.startswith(starts) or obj.name.startswith("LookDev - " + starts)
    ]
    return found


def arm_axes(rig):
    tracks = {}
    for side in ("L", "R"):
        def pos(bone):
            return rig.data.bones[f"{bone}.{side}"].head_local.copy()
        shoulder, elbow, wrist = pos("upperarm01"), pos("lowerarm01"), pos("wrist")
        tracks[side] = shoulder, elbow, wrist
    return tracks


def distance_on_line(point, start, end):
    axis = end-start
    fraction = min(1., max(0., (point-start).dot(axis)/axis.length_squared))
    return start + fraction*axis, fraction


def face_shape(p):
    x,y,z = p
    mask = sm(1.724,1.797,z) * sm(.182,.030,abs(x))
    front = sm(.055,.207,-y)
    lower = bell(z,1.794,.064)
    mouth = bell(z,1.811,.049) * bell(x,0,.090) * front
    cheek = bell(abs(x),.078,.044) * bell(z,1.842,.055) * front
    brow = bell(abs(x),.045,.060) * bell(z,1.911,.018) * front
    nose = bell(abs(x),.017,.019) * bell(z,1.844,.022) * front
    lip = bell(x,0,.072) * bell(z,1.794,.017) * front
    chin = bell(x,0,.057) * bell(z,1.767,.021) * front
    # Less center projection, broader angular lower face, stronger cheek/brow.
    # Entire face and its fitted iris/lips/tilak use the same continuous field.
    return Vector((
        x*(1.+.267*mask*lower+.225*mouth+.102*cheek),
        y+.034*mouth-.018*cheek-.015*brow-.013*nose+.020*lip+.008*chin,
        z-.012*mask*lower+.004*cheek-.003*brow-.004*chin,
    ))


def body_shape(point, arms):
    x,y,z = point
    if z >= 1.72 and abs(x)<.171:
        return face_shape(point)
    p = point.copy()
    ax = abs(x)
    ribs = bell(z,1.468,.225)*sm(.38,.245,ax)
    p.x *= 1.+.102*ribs - .016*bell(z,1.155,.11)*sm(.27,.17,ax)
    p.y += (.066*ribs+.10*bell(z,1.688,.099)*sm(.225,.095,ax))*y
    # Deltoids and traps avoid a thin horizontal break under the pauldron.
    trap = bell(ax,.13,.11)*bell(z,1.663,.081)
    p.z += .023*trap
    p.y += .017*trap*sm(0,.110,y)
    shoulder, elbow, wrist = arms["L" if x>0 else "R"]
    if ax > .238 and z > 1.12:
        center, t = distance_on_line(point,shoulder,elbow)
        # Keep elbow and wrist smaller. Separate deltoid and biceps peaks.
        muscle = .25*bell(t,.16,.26) + .37*bell(t,.57,.22)
        arm = sm(.233,.350,ax) * sm(1.12,1.24,z)
        if t > .88 and (wrist-point).length < (shoulder-point).length:
            center,t = distance_on_line(point,elbow,wrist)
            muscle = (.25*bell(t,.25,.22)+.153*bell(t,.54,.20)) * sm(.98,.69,t)
        radial=point-center
        ribbed=Vector((radial.x,radial.y*(1.12 if radial.y<0 else .94),radial.z))
        p += ribbed * muscle * arm
    # Exposed calves remain natural and the tight ankle support fit is stable.
    if .105 < z < .49 and .12<ax<.36:
        p.x = x + (x - math.copysign(.265,x))*.064*bell(z,.29,.16)
    return p


def replace_body_skin(body):
    mesh=body.data
    pigment = mesh.color_attributes.get("Pigment")
    if pigment is None or pigment.domain != "CORNER":
        raise ValueError("Expected source Pigment color attribute in the loop domain")
    for face in mesh.polygons:
        fresh = face.material_index != 0
        face.material_index = 0
        for i in face.loop_indices:
            x,y,z = mesh.vertices[mesh.loops[i].vertex_index].co
            if fresh:
                streak = .95+.075*math.sin(53*x+36*z)+.061*math.cos(48*y-z*17)
                color = (.191*streak, .061*streak, .025*streak)
            else:
                source = pigment.data[i].color
                color = (source[0]*.77, source[1]*.98, source[2]*1.18)
            if 1.755<z<1.965 and y<-.10:
                sockets = bell(z,1.889,.026)*bell(abs(x),.050,.045)*sm(-.09,-.172,y)
                cheek_plane = bell(z,1.831,.075)*bell(abs(x),.103,.042)*sm(-.08,-.165,y)
                muzzle = bell(z,1.813,.040)*bell(x,0,.081)*sm(-.146,-.26,y)
                gray_brown = (.091,.046,.025)
                color = tuple(mix(c,t,min(.60,.34*sockets+.31*cheek_plane)) for c,t in zip(color,gray_brown))
                color = tuple(mix(c,t,.44*muzzle) for c,t in zip(color,(.25,.095,.056)))
                nose=bell(z,1.840,.015)*bell(x,0,.035)*sm(-.177,-.254,y)
                color = tuple(mix(c,t,.38*nose) for c,t in zip(color,(.30,.086,.055)))
            pigment.data[i].color = (*color,1)


def detail_skin(skin):
    # Preserve the original tangent-map normal. Add physically tiny pore depth,
    # resolved locally in asset space, under the existing anatomical pigment.
    skin=skin.copy()
    skin.name="Hanuman match · copper skin, pores and subsurface"
    nodes,links=skin.node_tree.nodes,skin.node_tree.links
    bsdf=nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value=.61
    bsdf.inputs["Specular IOR Level"].default_value=.23
    bsdf.inputs["Subsurface Weight"].default_value=.08
    bsdf.inputs["Subsurface Scale"].default_value=.017
    tex=nodes.new("ShaderNodeTexCoord")
    pores=nodes.new("ShaderNodeTexVoronoi")
    pores.feature="DISTANCE_TO_EDGE"
    pores.inputs["Scale"].default_value=305.
    links.new(tex.outputs["Object"],pores.inputs["Vector"])
    noise=nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value=104
    noise.inputs["Detail"].default_value=3
    links.new(tex.outputs["Object"],noise.inputs["Vector"])
    height=nodes.new("ShaderNodeMath")
    height.operation="MULTIPLY"
    links.new(pores.outputs["Distance"],height.inputs[0])
    links.new(noise.outputs["Fac"],height.inputs[1])
    bump=nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.45
    bump.inputs["Distance"].default_value=.0016
    bump.invert=True
    links.new(height.outputs[0],bump.inputs["Height"])
    normal=bsdf.inputs["Normal"]
    if normal.is_linked:
        links.new(normal.links[0].from_socket,bump.inputs["Normal"])
    links.new(bump.outputs["Normal"],normal)
    return skin


def grooming_material(name, color, roughness):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*color,1)
    mat.use_nodes=True
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    bsdf=nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(*color,1)
    bsdf.inputs["Roughness"].default_value=roughness
    bsdf.inputs["Anisotropic"].default_value=.44
    bsdf.inputs["Sheen Weight"].default_value=.18
    bsdf.inputs["Sheen Roughness"].default_value=.44
    bsdf.inputs["Specular IOR Level"].default_value=.27
    # A coarse color field between dark roots, golden upper filaments and the
    # reddish lowlights prevents the larger locks from reading as uniform wires.
    texture=nodes.new("ShaderNodeTexNoise")
    texture.inputs["Scale"].default_value=95
    texture.inputs["Detail"].default_value=2
    coords=nodes.new("ShaderNodeTexCoord")
    links.new(coords.outputs["Object"],texture.inputs["Vector"])
    ramp=nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position=.24
    ramp.color_ramp.elements[0].color=(*(v*.44 for v in color),1)
    ramp.color_ramp.elements[1].position=.79
    ramp.color_ramp.elements[1].color=(*(min(1,v*1.35) for v in color),1)
    links.new(texture.outputs["Fac"],ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"],bsdf.inputs["Base Color"])
    return mat


class Groom:
    """One editable skinned mesh per groom region, with per-strand tapers."""
    def __init__(self):
        self.points=[]
        self.faces=[]
        self.weights=[]
        self.strands=0

    def add(self, points, radius, weights, sides=4):
        first=len(self.points)
        count=len(points)
        for i,p in enumerate(points):
            tangent=(points[min(i+1,count-1)]-points[max(0,i-1)]).normalized()
            right=tangent.cross(Vector((0,1,0)))
            if right.length_squared<.02:
                right=tangent.cross(Vector((1,0,0)))
            right.normalize()
            up=tangent.cross(right).normalized()
            radius_i = radius*mix(1,.03,(i/(count-1))**.9)
            for j in range(sides):
                a=math.tau*j/sides
                self.points.append(p+radius_i*(right*math.cos(a)+up*math.sin(a)))
                self.weights.append(weights)
        for i in range(count-1):
            for j in range(sides):
                a=first+i*sides+j
                b=first+i*sides+(j+1)%sides
                self.faces.append((a,b,b+sides,a+sides))
        self.strands+=1

    def make(self, sculpt, label, mat):
        return sculpt.mesh(label,self.points,self.faces,mat,weights=self.weights)


def arm_fur(sculpt, arms, material, density, seed):
    body = sculpt.body.data
    body.calc_loop_triangles()
    region=[]
    for tri in body.loop_triangles:
        verts=[body.vertices[i] for i in tri.vertices]
        p=sum((v.co for v in verts),Vector((0,0,0)))/3
        x,y,z=p
        side="L" if x>0 else "R"
        shoulder, elbow, wrist=arms[side]
        is_arm = abs(x) > .29 and 1.15<z<1.675
        is_shin = .17<abs(x)<.36 and .135<z<.56
        is_flank = .17<abs(x)<.28 and 1.19<z<1.47
        if not (is_arm or is_shin or is_flank):
            continue
        if is_arm:
            t=distance_on_line(p,elbow,wrist)[1]
            direction=(wrist-elbow if abs(x)>.51 else elbow-shoulder).normalized()
            severity=(.72+.25*tri.normal.y**2)*sm(.76,.64,t)
            if abs(x)<.51:
                severity = .96*sm(.27,.43,abs(x))
            length=(.006,.020)
        elif is_shin:
            direction=Vector((.02,-.04,-1)).normalized()
            severity=.86
            length=(.006,.017)
        else:
            direction=Vector((math.copysign(.16,x),-.1,-1)).normalized()
            severity=.42
            length=(.004,.010)
        area=tri.area*severity
        if area>0:
            region.append((tri,direction,area,length))
    rng=random.Random(seed)
    totals=list(accumulate(r[2] for r in region))
    fur=Groom()
    for _ in range(round(totals[-1]*density)):
        tri,drift,_,length=region[bisect_left(totals,rng.random()*totals[-1])]
        u,v=rng.random(),rng.random()
        if u+v>1:
            u,v=1-u,1-v
        bary=(1-u-v,u,v)
        vs=[body.vertices[k] for k in tri.vertices]
        origin=sum((weight*v.co for weight,v in zip(bary,vs)),Vector())
        normal=sum((weight*v.normal for weight,v in zip(bary,vs)),Vector()).normalized()
        tangent=(drift-normal*drift.dot(normal)).normalized()
        tangent+=normal.cross(tangent)*rng.uniform(-.26,.26)
        l=rng.uniform(*length)
        start=origin-normal*.0008
        points=[
            start+u*l*tangent + normal*l*(.35*u+.34*math.sin(math.pi*u))
            + normal.cross(tangent)*l*(.1*math.sin(u*math.pi)*rng.uniform(-1,1))
            for u in (0.,.22,.5,.76,1.)
        ]
        weights={}
        for v,factor in zip(vs,bary):
            for group in v.groups:
                name=sculpt.body.vertex_groups[group.group].name
                weights[name]=weights.get(name,0)+factor*group.weight
        entries=sorted(weights.items(),key=lambda row:row[1],reverse=True)[:4]
        total=sum(w for _,w in entries)
        if total>.001:
            fur.add(points,rng.uniform(.00042,.0011),[(name,w/total) for name,w in entries])
    fur.make(sculpt,"Hanuman match · arm and calf guard hairs",material)
    return fur.strands


def swept_mane(sculpt, lo, hi, seed, count):
    body=sculpt.body.data
    surface=BVHTree.FromPolygons([v.co for v in body.vertices],[tuple(p.vertices) for p in body.polygons])
    # Variable brow line and directional fore-to-aft rise are built into an
    # elliptical scalp. Main locks sweep away from the face rather than a fringe.
    def cap(u,v):
        a=math.tau*u
        q=.018+v*(1.62+.41*math.sin(a)+.14*math.cos(2*a))
        ridge=(.0036*math.cos(31*a-8*v)+.0026*math.cos(17*a+2*v))*v
        crown_depth=.135+.025*max(0,-math.sin(a))**1.6
        lean = -.046*(1-v)**1.6
        # Asymmetric crest above the temple. The front profile rises from the
        # low nape to a swept peak, with the fitted forehead left exposed.
        crest = .014*(1-v)**1.9 + .021*bell(u%1,.60,.17)*math.sin(v*math.pi)**2
        point=Vector(((.120+ridge)*math.sin(q)*math.cos(a)+lean,
            -.030+(crown_depth+ridge)*math.sin(q)*math.sin(a)+.043*(1-v),
            1.951+(.146+ridge)*math.cos(q)+.005*math.cos(a*3)*v+crest))
        if v>.71:
            # Close the helmet-like gap at the temples by burying only the cap
            # edge in the authored scalp. Main locks inherit the same contact.
            direction=Vector((point.x,point.y+.057,0)).normalized()
            contact,_,_,_=surface.ray_cast(point+direction*.14,-direction,.28)
            if contact is None:
                contact,direction,_,_=surface.find_nearest(point)
            point=point.lerp(contact-direction*.002,sm(.71,.98,v))
        return point
    sculpt.cloth("Hanuman match · swept mane foundation",lambda u,v:cap(u,v),lo,
                 rows=34,columns=112,wrap=True,bone="head")
    rng=random.Random(seed)
    geom=Groom()
    def swath(u, d, lift):
        # Front paths run to crown, temple paths curve to nape; avoid the pole.
        direction=1 if u<.5 else -1
        for i in range(15):
            t=i/14
            az=u+direction*(.092+.153*d)*t+.009*math.sin(math.pi*t)
            radial=mix(.97-.28*d,.31+.49*d,t)+.058*math.sin(math.pi*t)
            p=cap(az,radial)
            n=(p-Vector((0,-.008,1.95))).normalized()
            yield p+n*(lift*math.sin(math.pi*t)**.95)
    for k in range(205):
        u=k/205+rng.uniform(-.0014,.0014)
        d=.51+.26*math.sin(math.tau*(k//15)/9)+rng.uniform(-.045,.045)
        geom.add(list(swath(u,d,rng.uniform(.005,.016))),rng.uniform(.0024,.0043),[("head",1.)],sides=5)
    for k in range(count):
        u=rng.random()
        d=min(.98,max(.02,.51+.25*math.sin(math.tau*(int(u*205)//15)/9)+rng.uniform(-.22,.22)))
        geom.add(list(swath(u,d,rng.uniform(.003,.014))),rng.uniform(.00022,.00071),[("head",1.)])
    for _ in range(66):
        # A small number of longer tapered silhouette wisps stand out from the
        # packed filaments, following the same flow through the mane crest.
        u=rng.uniform(.53,.73)
        points=list(swath(u,rng.uniform(.04,.2),rng.uniform(.017,.028)))
        for i,p in enumerate(points):
            t=i/(len(points)-1)
            p.x-=.019*t*t
            p.z+=.017*t*t
        geom.add(points,rng.uniform(.00055,.0013),[("head",1.)])
    for i in range(142):
        # Lower locks rooted at the rear cap, curled toward the neck behind
        # the ears. They soften the shell's former hard cutoff in profile.
        u=.042+.420*i/141+rng.uniform(-.0025,.0025)
        root=cap(u,rng.uniform(.84,.98))
        direction=Vector((-root.x*.47,.025,-rng.uniform(.068,.117)))
        arc=Vector((root.x*.11,.017,rng.uniform(-.012,.002)))
        path=[root+direction*t+arc*math.sin(math.pi*t) for t in (j/12 for j in range(13))]
        geom.add(path,rng.uniform(.00135,.0032),[("head",1.)],sides=5)
    geom.make(sculpt,"Hanuman match · lifted copper mane locks",hi)
    return geom.strands


def beard(sculpt, material, seed, count):
    surface=sculpt.body.data
    surface.calc_loop_triangles()
    # Sample the actual sculpted jaw and cheek, tapering up toward the ears.
    choices=[]
    for tri in surface.loop_triangles:
        vs=[surface.vertices[i] for i in tri.vertices]
        p=sum((v.co for v in vs),Vector())/3
        x,y,z=p
        if not 1.726<z<1.890 or y>-.063:
            continue
        beard_line=1.776+.62*max(0,abs(x)-.040)
        if z<beard_line and z>1.733+abs(x)*.12:
            p0=sm(1.734,1.771,z)*sm(-.052,-.136,y)
            if p0>.03:
                choices.append((tri,tri.area*p0))
        elif .075<abs(x)<.133 and 1.786<z<1.878:
            choices.append((tri,.9*tri.area))
    accum=list(accumulate(weight for _,weight in choices))
    rng=random.Random(seed)
    groom=Groom()
    lock_count=min(count//8,190)
    for i in range(count):
        tri=choices[bisect_left(accum,rng.random()*accum[-1])][0]
        u,v=rng.random(),rng.random()
        if u+v>1:
            u,v=1-u,1-v
        bary=(1-u-v,u,v)
        verts=[surface.vertices[k] for k in tri.vertices]
        root=sum((f*v.co for f,v in zip(bary,verts)),Vector())
        normal=sum((f*v.normal for f,v in zip(bary,verts)),Vector()).normalized()
        sign=-1 if root.x<0 else 1
        motion=Vector((sign*(.29+.24*bell(root.z,1.835,.055)),.03,-.89))
        tangent=(motion-normal*motion.dot(normal)).normalized()
        tangent+=normal.cross(tangent)*rng.uniform(-.25,.25)
        is_guard=i < lock_count
        length=rng.uniform(.016,.031) if is_guard else rng.uniform(.008,.022)
        length*=.75+.37*sm(.071,.119,abs(root.x))
        points=[root-normal*.001+length*(t*tangent+normal*(.59*t+.29*math.sin(math.pi*t)))
                for t in (0.,.2,.45,.72,1.)]
        radius=rng.uniform(.0012,.0020) if is_guard else rng.uniform(.00039,.00093)
        groom.add(points,radius,[("head",1.)],sides=5 if is_guard else 4)
    groom.make(sculpt,"Hanuman match · closed jaw and swept cheek groom",material)
    return groom.strands


def skin_fitter(*meshes):
    surfaces=[BVHTree.FromPolygons([v.co for v in mesh.vertices],[tuple(p.vertices) for p in mesh.polygons])
              for mesh in meshes]

    def fitted(x, z, offset):
        position=Vector((x,-.54,z))
        hits=[surface.ray_cast(position,Vector((0,1,0)),.55)[0] for surface in surfaces]
        valid=[p for p in hits if p is not None]
        if not valid:
            raise ValueError(f"No facial support at {x:.4f}, {z:.4f}")
        return min(valid,key=lambda p:p.y)+Vector((0,-offset,0))
    return fitted

def pigment_material(name, rgb, roughness=.71, specular=.14):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*rgb,1)
    mat.use_nodes=True
    shader=mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(*rgb,1)
    shader.inputs["Roughness"].default_value=roughness
    shader.inputs["Specular IOR Level"].default_value=specular
    return mat


def refine_eyes(scene, rig):
    """Adjust the native eye pieces, keeping the original eye-bone binding."""
    sclera=pigment_material("Hanuman match · warm hydrated sclera",(.36,.275,.20),.33,.35)
    iris=pigment_material("Hanuman match · dark amber iris",(.28,.104,.035),.25,.37)
    pupil=pigment_material("Hanuman match · hydrated pupil",(.016,.009,.005),.20,.42)
    lids=pigment_material("Hanuman match · warm orbital folds",(.112,.049,.023),.59,.24)
    changed=[]
    parts=(('Eye · ',sclera),('Limbal ring · ',None),('Iris · ',iris),('Pupil · ',pupil),
           ('Orbital brow lid · ',lids),('Upper lid fold · ',lids))
    for side in ("L","R"):
        center=rig.data.bones["eye."+side].head_local+Vector((0,-.006,-.001))
        for prefix,mat in parts:
            obj=named(scene,prefix+side)[0]
            if obj.data.users>1:
                obj.data=obj.data.copy()
            if mat:
                obj.data.materials[0]=mat
            focus=sum((vert.co for vert in obj.data.vertices),Vector())/len(obj.data.vertices)
            for vert in obj.data.vertices:
                point=vert.co
                dx=point.x-center.x
                dz=point.z-center.z
                inner=bell(dx,0,.025)*bell(dz,0,.022)
                reference=face_shape(point)
                if prefix.startswith(("Orbital","Upper")):
                    reference.y-=.008*inner
                    compression=.0026 if dz>0 else .0009
                    reference.z-=math.copysign(compression,dz)*inner*sm(0,.004,abs(dz))
                else:
                    reference.y-=.006
                    if not prefix.startswith("Eye"):
                        radial=point-focus
                        reference.x+=.0011+.14*radial.x
                        reference.z+=.10*radial.z
                vert.co=reference
            obj.data.update()
            changed.append(obj.name)
    return changed


def face_marks(sculpt):
    """Fit the joined U pigment and serious, natural brow onto the new skin."""
    fitted=skin_fitter(sculpt.body.data)

    ivory=pigment_material("Hanuman match · ivory forehead pigment",(.81,.69,.50))
    vermilion=pigment_material("Hanuman match · vermilion forehead pigment",(.54,.047,.016))
    pale=[]
    for j in range(49):
        t=j/48
        angle=mix(-.05,math.pi+.05,t)
        x=-.0181*math.cos(angle)
        z=1.933+.0275*(math.cos(angle)**2)
        pale.append(fitted(x,z,.0025))
    sculpt.tube("Hanuman match · single joined white U",pale,.0041,ivory,"head",9,
                lambda t:.58+.42*math.sin(math.pi*t)**.58)
    saffron=[fitted(.00065*math.sin(t*math.pi),1.935+.026*t,.0024) for t in (j/24 for j in range(25))]
    sculpt.tube("Hanuman match · fitted red center",saffron,.0053,vermilion,"head",10,
                lambda t:.26+.74*(math.sin(math.pi*t)**.55))
    shade=grooming_material("Hanuman match · warm angular eyebrows",(.089,.028,.013),.63)
    brow_fibers=Groom()
    rng=random.Random(229)

    def brow_point(t, side, lift, offset):
        x=side*(.016+.074*t)
        z=1.909+.011*math.sin(math.pi*t*.80)+.002*t
        return fitted(x,z+lift,offset)

    for side in (-1,1):
        guide=[brow_point(j/34,side,0,.00085) for j in range(35)]
        sculpt.tube("Hanuman match · angular brow ridge",guide,.0033,shade,"head",8,
                    lambda t:.17+.83*math.sin(math.pi*t)**.59)
        for j in range(140):
            t=rng.uniform(.02,.93)
            extent=rng.uniform(.035,.11)
            height=rng.uniform(.002,.0064)*math.sin(math.pi*t)**.5
            root_height=rng.uniform(-.0033,.0028)
            path=[brow_point(min(1,t+extent*v),side,root_height+height*v,.0015+.0018*math.sin(math.pi*v))
                  for v in (0.,.25,.5,.75,1.)]
            brow_fibers.add(path,rng.uniform(.00025,.00066),[("head",1.)])
    brow_fibers.make(sculpt,"Hanuman match · directional eyebrow hairs",shade)
    seam=pigment_material("Hanuman match · narrow umber mouth seam",(.071,.029,.016))
    upper=pigment_material("Hanuman match · upper lip plane",(.182,.068,.040),.72,.15)
    lower=pigment_material("Hanuman match · lower lip plane",(.202,.083,.053),.69,.16)

    def lip_point(t,height,up):
        x=(t-.5)*.112
        width=math.sin(math.pi*t)**.82
        z=1.789+(.005 if up else -.008)*height*width+.0012*width
        offset=(.0009+.0017*math.sin(math.pi*height)-.0019*height)*width
        return fitted(x,z,offset)

    sculpt.cloth("Hanuman match · fitted upper lip",lambda t,v:lip_point(t,v,True),upper,
                 rows=7,columns=46,bone="head")
    sculpt.cloth("Hanuman match · fitted lower lip",lambda t,v:lip_point(t,v,False),lower,
                 rows=7,columns=46,bone="head")
    line=[lip_point(j/48,0,False)+Vector((0,-.0012,0)) for j in range(49)]
    sculpt.tube("Hanuman match · closed mouth seam",line,.00075,seam,"head",8,
                lambda t:.17+.83*math.sin(math.pi*t)**.7)


def diadem(sculpt, foundation):
    """Fit the small antique gold circlet over the hairline."""
    fitted=skin_fitter(sculpt.body.data,foundation.data)
    bronze=pigment_material("Hanuman match · circlet antimony gold",(.36,.191,.063),.44,.33)
    red=pigment_material("Hanuman match · red jasper cabochon",(.55,.039,.017),.34,.39)
    bronze.node_tree.nodes.get("Principled BSDF").inputs["Metallic"].default_value=.52
    center_z=1.991
    halo=[]
    for j in range(49):
        a=math.tau*j/48
        halo.append(fitted(.014*math.cos(a),center_z+.018*math.sin(a),.006))
    sculpt.tube("Hanuman match · cast diadem bezel",halo,.0038,bronze,"head",8)
    gem_center=fitted(0,center_z,.0063)
    sculpt.ellipsoid("Hanuman match · oval jasper diadem",gem_center,(.011,.007,.014),red)
    for side in (-1,1):
        def strand(t,offset):
            return fitted(side*(.011+.084*t),center_z-.010-.028*t**1.35,offset)
        sculpt.tube("Hanuman match · diadem bead binding",[strand(j/31,.002) for j in range(32)],
                    .0026,bronze,"head",7)
        for j in range(7):
            t=.12+.135*j
            bead=strand(t,.0038)
            size=mix(.0065,.0036,t)
            sculpt.ellipsoid("Hanuman match · cast diadem bead",bead,(size,size*.65,size),bronze,
                             segments=10,rings=8)


def apply(scene, reference_profile=None):
    """Evolve an editable studio scene and return geometry/groom counts."""
    profile=(reference_profile or {}).get("character", {})
    if not profile.get("enabled",True):
        return {"enabled": False}
    if scene != bpy.context.scene:
        raise ValueError("Activate the character's editable working scene before sculpting")
    if named(scene, "Hanuman match · swept mane foundation"):
        raise ValueError("The reference-informed groom is already present in this scene")
    mane_strands = int(profile.get("mane_strands", 2300))
    beard_strands = int(profile.get("beard_strands", 1950))
    limb_density = int(profile.get("limb_density", 12600))
    if not (1 <= mane_strands <= 6000 and 1 <= beard_strands <= 6000 and 1 <= limb_density <= 25000):
        raise ValueError("The specified groom density exceeds its editable asset budget")
    rig=next(obj for obj in scene.objects if obj.type=="ARMATURE")
    body=named(scene,"Hanuman · contiguous skinned anatomy")[0]
    if body.data.users>1:
        body.data=body.data.copy()
    arms=arm_axes(rig)
    face_prefixes=("Nostril","Vanara ear","Ear concha","Rounded helix","Earring loop")
    hide_prefixes=("Swept cheek fur","Swept Vanara mane cap","Mane crest",
                   "Sandal soles","Sandal leather straps","Sacred forehead pigment",
                   "Angular expressive brow","Upper fitted muzzle lip","Lower fitted muzzle lip",
                   "Closed mouth corner crease")
    hidden=0
    for obj in list(scene.objects):
        name=obj.name.removeprefix("LookDev - ")
        if name.startswith(hide_prefixes):
            obj.hide_render=True
            obj.hide_set(True)
            hidden+=1
        elif name.startswith(face_prefixes):
            if obj.data.users>1:
                obj.data=obj.data.copy()
            for vert in obj.data.vertices:
                vert.co=face_shape(vert.co)
            obj.data.update()
        if name.startswith("Swept cheek fur"):
            obj["Superseded effect"]="May be unhidden for source comparison"
    for vert in body.data.vertices:
        vert.co=body_shape(vert.co,arms)
    body.data.update()
    replace_body_skin(body)
    body.data.materials[0]=detail_skin(body.data.materials[0])
    lo=grooming_material("Hanuman match · deep chestnut growth",(.072,.022,.009),.55)
    hi=grooming_material("Hanuman match · burnished copper groom",(.274,.088,.031),.49)
    beard_material=grooming_material("Hanuman match · jaw and sideburns",(.205,.073,.030),.58)
    fur_material=grooming_material("Hanuman match · warmer limb hairs",(.197,.064,.026),.66)
    tree=KDTree(len(body.data.vertices))
    weights=[]
    for vertex in body.data.vertices:
        tree.insert(vertex.co,vertex.index)
        weights.append([(body.vertex_groups[g.group].name,g.weight) for g in vertex.groups])
    tree.balance()
    sculpt=Sculpt(rig,body,weights,tree)
    rec={
        "enabled":True,"anatomy_vertices":len(body.data.vertices),"source_bones":len(rig.data.bones),
        "mane_strands":swept_mane(sculpt,lo,hi,161,mane_strands),
        "beard_strands":beard(sculpt,beard_material,919,beard_strands),
        "limb_strands":arm_fur(sculpt,arms,fur_material,limb_density,771),
        "hidden_source_shells":hidden,
        "groom_meshes":[o.name for o in sculpt.objects[1:]],
    }
    n=len(sculpt.objects)
    face_marks(sculpt)
    rec["fitted_face_shapes"]=[o.name for o in sculpt.objects[n:]]
    rec["reused_eye_meshes"]=refine_eyes(scene,rig)
    n=len(sculpt.objects)
    diadem(sculpt,sculpt.objects[1])
    rec["diadem_meshes"]=[o.name for o in sculpt.objects[n:]]
    return rec
