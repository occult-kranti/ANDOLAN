"""Build the original Hanuman redesign from the YUGA Hanuman anatomy and actions.

blender -b --factory-startup -t 2 --python build.py -- --output /absolute/output
Use --render to produce studio, face and rear views after the source and GLB.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Euler, Matrix, Vector
from mathutils.kdtree import KDTree

NATIVE = Path(__file__).resolve().parents[2]
ART = NATIVE.parent / 'yuga/art'
sys.path.insert(0, str(ART / 'pipeline'))
from anatomy import bind, build_anatomy
from animations import FPS, _planted, _sample, author_animations
from build_heroes import material
from geometry import Sculpt

TAU = math.tau
HEIGHT = 2.02
REST_WIDTH = 1.25
FACE_WIDTH = 1.2


def smooth(a, b, x):
    unit = min(1.0, max(0.0, (x - a) / (b - a)))
    return unit * unit * (3.0 - 2.0 * unit)


def mix(a, b, t):
    return (1.0-t)*a + t*b


def bell(x, center, sigma):
    return math.exp(-((x-center)/sigma)**2)


def pixels(name, rgb, colorspace):
    size = rgb.shape[0]
    image = bpy.data.images.new(name, width=size, height=size, alpha=False)
    image.colorspace_settings.name = colorspace
    rgba = np.ones((size, size, 4), dtype=np.float32)
    rgba[..., :3] = rgb
    image.pixels.foreach_set(rgba.reshape(-1))
    image.pack()
    return image


def texture_material(name, color, metal, rough, finish):
    """Tileable authored PBR detail which stays with the exported game model."""
    mat = material(name, color, metal, rough)
    size = 384
    x, y = np.meshgrid(np.arange(size)/size, np.arange(size)/size)
    a = TAU
    p = np.sin(a*(5*x+7*y))*np.cos(a*(3*x-11*y))
    q = np.sin(a*(19*x+7*y)+p)*np.cos(a*(11*x-13*y))
    fine = np.sin(a*(122*x+42*y))*np.cos(a*(36*x-94*y))
    if finish == 'cloth':
        thread = np.cos(a*128*x)*np.cos(a*128*y)
        cells = np.sin(a*8*x)*np.sin(a*8*y)
        weave = .42*thread + .24*q + .34*p
        dye = 1 + weave*.16 + .05*cells
        elevation = .20*thread + .1*q
    elif finish == 'fur':
        streaks = np.sin(a*(73*x+7*y)+p+q*.8)
        dye = 1 + .17*p + .08*q + .065*streaks
        elevation = .18*streaks + .1*q
    else:
        patina = np.sin(a*(4*x-3*y)+p*.82)*np.cos(a*(9*x+8*y)+q*.6)
        dye = 1 + .14*patina + .10*p + .07*q + .03*fine
        elevation = .17*q + .045*fine + .055*patina
    # Packed byte images retain encoded values. Encode sRGB color only; normals
    # are raw vectors and retain their linear channel values.
    albedo = np.clip(dye[..., None]*np.array(color), 0, 1)
    albedo = np.where(albedo < .0031308, albedo*12.92, 1.055*albedo**(1/2.4)-.055)
    dudu = np.roll(elevation, -1, axis=1) - np.roll(elevation, 1, axis=1)
    dvdv = np.roll(elevation, -1, axis=0) - np.roll(elevation, 1, axis=0)
    norm = np.stack((-dudu*.5, -dvdv*.5, np.ones_like(x)), axis=-1)
    norm /= np.linalg.norm(norm, axis=-1, keepdims=True)
    normal = norm*.5 + .5
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    base_node = nodes.new('ShaderNodeTexImage')
    base_node.image = pixels(name + ' color', albedo, 'sRGB')
    base_node.location = (-470, 150)
    normal_node = nodes.new('ShaderNodeTexImage')
    normal_node.image = pixels(name + ' normal', normal, 'Non-Color')
    normal_node.location = (-470, -145)
    bump = nodes.new('ShaderNodeNormalMap')
    bump.inputs['Strength'].default_value = .58 if finish == 'bronze' else .48
    bump.location = (-200, -160)
    shader = nodes.get('Principled BSDF')
    links.new(base_node.outputs['Color'], shader.inputs['Base Color'])
    links.new(normal_node.outputs['Color'], bump.inputs['Color'])
    links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    return mat


def palette():
    skin = material('Vanara · painted copper anatomy', (.32,.115,.037), rough=.63)
    vert = skin.node_tree.nodes.new('ShaderNodeVertexColor')
    vert.layer_name = 'Pigment'
    shader = skin.node_tree.nodes.get('Principled BSDF')
    skin.node_tree.links.new(vert.outputs['Color'], shader.inputs['Base Color'])
    shader.inputs['Subsurface Weight'].default_value = .07
    shader.inputs['Subsurface Radius'].default_value = (1.0,.38,.22)
    shader.inputs['Subsurface Scale'].default_value = .028
    result = {
        'skin': skin,
        'fur': texture_material('Fur · reddish umber strand pigment', (.17,.054,.022), 0,.79,'fur'),
        'mane': texture_material('Fur · dark copper clumps', (.105,.027,.009), 0,.76,'fur'),
        'eyelid': material('Eyelids · roasted umber',(.22,.072,.028),rough=.57),
        'eye': material('Eyes · warm sclera',(.23,.169,.114),rough=.39),
        'iris': material('Eyes · dark amber iris',(.148,.044,.009),rough=.43),
        'dark': material('Face lines and pupil',(.016,.004,.002),rough=.65),
        'muzzle_crease': material('Face · warm recessed lines',(.064,.012,.005),rough=.66),
        'inner': material('Ear · warm inner skin',(.28,.087,.043),rough=.69),
        'red': material('Sindoor mineral vermilion',(.53,.042,.012),rough=.77),
        'ivory': material('Ivory ritual pigment',(.76,.665,.44),rough=.71),
        'cloth': texture_material('Drapery · red madder dyed weave',(.185,.013,.008),0,.73,'cloth'),
        'saffron': texture_material('Drapery · woven saffron silk',(.31,.074,.012),0,.69,'cloth'),
        'leather': texture_material('Straps · dark oiled hide',(.032,.016,.012),0,.78,'cloth'),
        'bronze': texture_material('Armor · hammered bell metal',(.193,.086,.027),.72,.43,'bronze'),
        'gold': texture_material('Edges · warm antiqued brass',(.38,.170,.037),.72,.36,'bronze'),
        'ember': material('Gada jewel · carnelian',(.46,.048,.012),.35,.28),
    }
    result['dark'].node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value = .13
    normal = skin.node_tree.nodes.new('ShaderNodeTexImage')
    normal.image = bpy.data.images['Fur · reddish umber strand pigment normal']
    bump = skin.node_tree.nodes.new('ShaderNodeNormalMap')
    bump.inputs['Strength'].default_value = .31
    skin.node_tree.links.new(normal.outputs['Color'], bump.inputs['Color'])
    skin.node_tree.links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    return result


def sculpt_anatomy(body, m):
    """Preserve the donor topology and weights; model new skin as one surface."""
    body.name = 'Hanuman · contiguous skinned anatomy'
    for mat in (m['skin'],m['cloth'],m['leather']):
        body.data.materials.append(mat)
    color = body.data.color_attributes.new(name='Pigment', type='FLOAT_COLOR', domain='CORNER')
    body.data.color_attributes.active_color = color
    body.data.color_attributes.render_color_index = body.data.color_attributes.active_color_index
    pigment=[]
    for v in body.data.vertices:
        x,y,z = v.co
        # Lift an angular brow and broaden muzzle in the actual donor topology.
        muzzle = bell(z,1.807,.044)*bell(x,0,.088)*smooth(.075,.214,-y)
        brow = bell(z,1.913,.019)*bell(abs(x),.054,.041)*smooth(.10,.195,-y)
        nose = bell(z,1.843,.022)*bell(x,0,.030)*smooth(.182,.217,-y)
        chin = bell(z,1.782,.035)*bell(x,0,.062)*smooth(.08,.2,-y)
        v.co.y -= .114*muzzle+.019*brow + .032*nose
        v.co.x *= 1 + .47*muzzle + .52*nose + .105*chin
        v.co.z -= .012*chin
        # Deltoid and chest strength without changing rest joint coordinates.
        shoulder = bell(abs(x),.349,.108)*bell(z,1.54,.115)
        v.co.y += y*.23*shoulder
        ribs = bell(z,1.445,.245)*bell(x,0,.35)
        if z < 1.65:
            v.co.x += x*.32*ribs
            v.co.y += y*.16*ribs
        pectoral = bell(abs(x),.10,.11)*bell(z,1.491,.084)*smooth(.08,.16,-y)
        v.co.y -= .028*pectoral
        variation = .5 + .22*math.sin(x*41 + z*32) + .16*math.cos(y*37 - z*22)
        base = tuple(k*(.77+variation*.42) for k in (.255,.068,.021))
        cheek = smooth(.048,.126,abs(x))*bell(z,1.849,.083)
        forehead = bell(z,1.957,.075)*smooth(.1,.195,-y)
        eye_socket = bell(abs(x),.043,.037)*bell(z,1.891,.026)*smooth(.113,.185,-y)
        face = tuple(mix(a,b,min(1,muzzle*.91+brow*.13)) for a,b in zip(base,(.28,.069,.020)))
        face = tuple(mix(a,b,min(1,cheek*.67+forehead*.25+eye_socket*.55))
                     for a,b in zip(face,(.115,.027,.011)))
        forward=smooth(.138,.254,-v.co.y)
        muzzle_light=bell(z,1.802,.047)*bell(x,0,.082)*forward
        face=tuple(mix(a,b,.29*muzzle_light) for a,b in zip(face,(.365,.112,.041)))
        lower_cheek=bell(z,1.815,.067)*bell(abs(x),.075,.051)*forward
        undertone=.36+.17*math.sin(abs(x)*63+z*43)+.10*math.cos(z*102+y*51)
        face=tuple(mix(a,b,lower_cheek*undertone) for a,b in zip(face,(.160,.035,.013)))
        forearm = bell(abs(x),.582,.118)*bell(z,1.343,.164)
        shade = tuple(mix(a,b,.47*forearm) for a,b in zip(face,(.39,.047,.014)))
        pigment.append((*shade,1))
    body.data.update()
    for polygon in body.data.polygons:
        z=polygon.center.z
        if .44 < z < 1.12:
            polygon.material_index=1
        elif .145 < z <= .44:
            polygon.material_index=2
        for loop in polygon.loop_indices:
            vid=body.data.loops[loop].vertex_index
            color.data[loop].color = (1,1,1,1) if polygon.material_index else pigment[vid]
    tree = KDTree(len(body.data.vertices))
    for vert in body.data.vertices:
        tree.insert(vert.co, vert.index)
    tree.balance()
    return tree


def skin_contact(sculpt, x, z, inset=.008):
    """Find the donor front skin before laying ceremonial pigment on it."""
    # Ray casts against raw mesh; the armature stays at its rest transform.
    hit, position, _, _ = sculpt.body.ray_cast((x,-.75,z),(0,1,0))
    return (x, position.y-inset if hit else -.235, z)


def face(s, m):
    h = HEIGHT
    for sign, side in ((-1,'R'),(1,'L')):
        eye = s.rig.data.bones['eye.'+side].head_local
        e = eye + Vector((0,-.006,-.001))
        s.ellipsoid('Eye · '+side,e,(.025,.024,.023),m['eye'],'eye.'+side,24,16)
        iris=e+Vector((.0014*sign,-.0228,.0007))
        s.ellipsoid('Limbal ring · '+side,iris,(.0112,.0026,.0106),m['dark'],'eye.'+side,24,14)
        s.ellipsoid('Iris · '+side,iris+Vector((0,-.0012,0)),(.0094,.0020,.0090),m['iris'],'eye.'+side,24,14)
        s.ellipsoid('Pupil · '+side,iris+Vector((0,-.0028,0)),(.0057,.0017,.0061),m['dark'],'eye.'+side,20,12)
        def lid(u, v):
            angle=TAU*u
            dx=(.020+v*.009)*math.cos(angle)
            dz=(.0083+v*.016)*math.sin(angle) - .12*sign*dx
            y=e.y-math.sqrt(max(.000014,.026**2-dx*dx-dz*dz))+.008*v
            return e.x+dx,y,e.z+dz
        s.cloth('Orbital brow lid · '+side,lid,m['eyelid'],rows=8,columns=38,wrap=True,bone='head')
        rim=[Vector(lid(k/38,0))+Vector((0,-.001,0)) for k in range(20)]
        s.tube('Upper lid fold · '+side,rim,.0019,m['dark'],'head',7,
               lambda t:.3+.7*math.sin(math.pi*t)**.6)
        brow = [skin_contact(s,sign*(.015+.072*j/28),
                             1.898+.015*math.sin(math.pi*j/28)+.004*j/28,.004)
                for j in range(29)]
        s.tube('Angular expressive brow · '+side,brow,.0042,m['mane'],'head',9,lambda t:.12+.88*math.sin(math.pi*t)**.72)
        # Tapered directional clumps blend into side of muzzle instead of flat circles.
        for j in range(11):
            t=j/10
            root=Vector((sign*(.094+.024*math.sin(t*math.pi)), -.098+.019*t,1.923-.108*t))
            tip=Vector((sign*(.082+.043*math.sin(t*math.pi)), -.164+.048*t,1.887-.132*t))
            samples=[root.lerp(tip,k/10)+Vector((sign*.014,0,.006))*math.sin(math.pi*k/10) for k in range(11)]
            # v-shaped clump tips follow the cheek into the light.
            s.tube(f'Swept cheek fur {side} {j:02}',samples,.015-.003*t,m['fur'],'head',9,lambda u:.06+.94*(1-u)**.72)
        ear=Vector((sign*.116,-.034,1.862))
        s.ellipsoid('Vanara ear · '+side,ear,(.027,.022,.042),m['fur'],'head',22,16)
        s.ellipsoid('Ear concha · '+side,ear+Vector((sign*.004,-.017,.001)),(.015,.009,.029),m['inner'],'head',18,14)
        rim=[ear+Vector((sign*.019*math.cos(a),-.021,.035*math.sin(a))) for a in [TAU*k/32 for k in range(33)]]
        s.tube('Rounded helix · '+side,rim,.0055,m['fur'],'head',7)
        hoop=[ear+Vector((sign*(.012+.011*math.cos(a)),-.007,-.045+.018*math.sin(a))) for a in [TAU*j/28 for j in range(29)]]
        s.tube('Earring loop · '+side,hoop,.004,m['gold'],'head',8)
        p=skin_contact(s,sign*.015,1.839,.002)
        s.ellipsoid('Nostril · '+side,p,(.0069,.0022,.0028),m['muzzle_crease'],'head',16,10)
    def seam_z(u):
        return 1.791 + .002*math.sin(math.pi*u) - .001*abs(2*u-1)

    # Fitted lip volumes turn the previous black drawn line into a low,
    # closed crease. Curl both ribbons into the muzzle at the corners.
    def lip(u,v,upper):
        x=(u-.5)*.078
        shape=math.sin(math.pi*u)**.83
        extent=(.004 if upper else -.007)*shape
        offset=(.0014+.0033*math.sin(math.pi*v))*shape
        return skin_contact(s,x,seam_z(u)+extent*v,offset)

    for upper in (False,True):
        label='Upper' if upper else 'Lower'
        s.cloth(f'{label} fitted muzzle lip',
                lambda u,v:lip(u,v,upper),m['eyelid'],rows=6,columns=36,bone='head')
    mouth=[skin_contact(s,(j/38-.5)*.075,seam_z(j/38),.0018) for j in range(39)]
    s.tube('Closed mouth corner crease',mouth,.00105,m['muzzle_crease'],'head',8,
           lambda t:.12+.88*math.sin(math.pi*t)**.7)
    for offset, mat in ((-.014,m['ivory']),(.014,m['ivory']),(0,m['red'])):
        track=[skin_contact(s,offset*(.50+.50*j/18),1.927+.041*j/18,.0025) for j in range(19)]
        s.tube('Sacred forehead pigment',track,.0037 if offset else .0046,mat,'head',8, lambda t:.5+.5*math.sin(math.pi*t))
    # Profile-driven swept head shape, not overlapping full spheres.
    def cap(u, v):
        a=TAU*u
        extent=1.74+.24*math.sin(a)+.10*math.cos(2*a)
        p=.016+v*extent
        ripple=1+.024*math.cos(25*a+3*v)+.016*math.cos(13*a-2*v)
        return (.110*ripple*math.sin(p)*math.cos(a),
                -.030+.133*ripple*math.sin(p)*math.sin(a)+.026*(1-v)**2,
                1.955+.123*math.cos(p)+.006*math.cos(a*5)*v**3)
    s.cloth('Swept Vanara mane cap',cap,m['mane'],rows=26,columns=88,wrap=True,bone='head')
    for j in range(34):
        u=j/34
        start=.19+.14*math.cos(TAU*u*7)
        length=.82+.16*math.sin(TAU*u*9)**2
        points=[cap(u+.061*math.sin(math.pi*k/18),mix(start,length,k/18)) for k in range(19)]
        s.tube(f'Mane crest {j:02}',points,.0068,m['fur'],'head',7,lambda t:.16+.84*math.sin(math.pi*t)**.71)
    # Side and back bronze brow band; a flame finial stays below the tuft.
    crown=[(.110*math.cos(a),-.026+.137*math.sin(a),1.962+.015*max(0,-math.sin(a))) for a in [TAU*j/72 for j in range(73)]]
    s.tube('Restrained temple diadem',crown,.0055,m['gold'],'head',11)
    for j in (-2,-1,0,1,2):
        x=j*.021; y=-.163+abs(j)*.004
        s.ellipsoid('Diadem petal',(x,y,1.988+(.014 if j==0 else 0)),(.014,.009,.020-.002*abs(j)),m['bronze'],'head',18,12)
    s.ellipsoid('Diadem carnelian',(0,-.175,1.998),(.009,.006,.013),m['ember'],'head',16,10)


def surface_ring(s, name, center, axis, radii, profiles, mat, bone, columns=48):
    """Lathed cross-sections for cloth, forged trims and weapon pieces."""
    center,axis=Vector(center),Vector(axis).normalized()
    u=axis.cross(Vector((0,1,0)))
    if u.length < 1e-4:
        u=axis.cross(Vector((1,0,0)))
    u.normalize()
    v=axis.cross(u)
    def point(t, row):
        a=TAU*t
        advance,ripple=profiles[min(len(profiles)-1,round(row*(len(profiles)-1)))]
        x,z=radii; ridge=1+ripple+.022*math.cos(12*a)
        return center+axis*advance+ridge*(u*x*math.cos(a)+v*z*math.sin(a))
    s.cloth(name,point,mat,rows=len(profiles)-1,columns=columns,wrap=True,bone=bone)
    return point


def dorsal_armor(s, m):
    """Give the shell and sash one surface and one moving reference frame."""
    def base(x,z):
        hit,point,_,_=s.body.ray_cast((x,.75,z),(0,-1,0))
        return point.y if hit else .125

    def plating(u,v):
        side=2*u-1
        x=side*(.133+.041*math.sin(math.pi*v))
        z=1.392+.183*v+.021*side**2
        return x,base(x,z)+.028+.014*math.sin(math.pi*v),z

    # Every point on the shell, piping, and crossing portion of the strap
    # shares spine01. The sash below the metal returns to the belt weight.
    def lash(obj):
        obj.vertex_groups.clear()
        groups={n:obj.vertex_groups.new(name=n) for n in ('spine01','spine05')}
        for vertex in obj.data.vertices:
            share=smooth(1.172,1.386,vertex.co.z)
            for name,weight in (('spine01',share),('spine05',1-share)):
                if weight>0:
                    groups[name].add([vertex.index],weight,'REPLACE')
        return obj

    def sash(u,v):
        x=mix(-.17,.14,v)+(u-.5)*(.084+.027*math.sin(math.pi*v))
        z=mix(1.623,1.147,v)
        relief=smooth(1.346,1.389,z)*(1-smooth(1.596,1.622,z))
        # Shell max offset 42 mm plus 4.6 mm piping. Across its entire
        # span the textile and dark selvedge are elevated at least 58 mm.
        y=base(x,z)+.015+.046*relief+.003*math.cos(TAU*u*3)
        return x,y,z

    s.cloth('Shaped scapula harness',plating,m['leather'],rows=15,columns=36,bone='spine01')
    for v in (0,1):
        s.tube('Rear harness piping',[plating(j/46,v) for j in range(47)],.0046,m['gold'],'spine01',8)
    lash(s.cloth('Continuous sacred cross-back strap',sash,m['cloth'],rows=38,columns=18,bone='spine01'))
    for u in (0,1):
        lash(s.tube('Strap bound edge',[sash(u,j/52) for j in range(53)],.0031,m['gold'],'spine01',8))
    seal=Vector(sash(.5,.306))
    s.ellipsoid('Lotus escutcheon on back',seal+Vector((0,.013,0)),(.046,.015,.038),m['bronze'],'spine01',24,14,ridge=.10)
    s.ellipsoid('Carmine harness clasp',seal+Vector((0,.026,0)),(.013,.009,.019),m['ember'],'spine01',18,12)
    # Tiny driven rivets carry the plate edge shape around the sash.
    for u in (.135,.865):
        for v in (.22,.78):
            p=Vector(plating(u,v))+Vector((0,.004,0))
            s.ellipsoid('Dorsal plate brass pin',p,(.006,.004,.006),m['gold'],'spine01',12,8)


def bound_calf_cuff(s,m,side):
    bone=s.rig.data.bones['lowerleg01.'+side]
    head,tail=bone.head_local,bone.tail_local
    def profile(u,v):
        theta=TAU*u
        z=.417+.067*v
        center=head.lerp(tail,(z-head.z)/(tail.z-head.z))
        radial=Vector((math.cos(theta),math.sin(theta),0))
        hit,point,_,_=s.body.ray_cast(center+radial*.156,-radial)
        if not hit:
            raise ValueError(f'Calf cuff ray missed {side} at z={z:.3f}')
        return point+radial*(.013+.007*math.sin(math.pi*v))
    s.cloth('Bound greave cuff · '+side,profile,m['leather'],rows=12,columns=42,wrap=True)
    for v in (.13,.91):
        s.tube('Greave bead edge · '+side,[profile(k/52,v) for k in range(53)],.0032,m['gold'],sides=7)


def armor(s, m):
    # The under-wrap uses donor topology and its actual skin, so an animated
    # thigh cannot expose the uncut skin through either decorative fold.
    def split(u,v,sign):
        # Continuous ellipse with free edges away from the knee. Independent
        # thigh attachment keeps the wrap supported through wide stances.
        a=(u-.5)*math.pi*1.68+.07*sign
        fold=(.008+.011*v)*math.sin(8*a+v*.80)
        x=sign*(.133+.040*v + (.127+.022*v+fold)*math.sin(a)*sign)
        y=.025-(.190+.027*v+fold)*math.cos(a)
        z=1.116-.371*v+.065*v*math.sin(a)**2
        return x,y,z
    for side,sign in (('L',1),('R',-1)):
        panel=lambda u,v:split(u,v,sign)
        bone='upperleg01.'+side
        s.cloth('Split pleated battle drape · '+side,panel,m['cloth'],rows=20,columns=44,bone=bone)
        s.tube('Saffron selvedge',[panel(k/60,1) for k in range(61)],.0038,m['gold'],bone,sides=8)
    def tabard(u,v):
        return ((u-.5)*(.174-.038*v),-.214-.064*v-.010*math.cos(3*u*TAU)*(.4+.6*v),1.106-.359*v+.082*v*abs(2*u-1)**4)
    s.cloth('Central red sash end',tabard,m['saffron'],rows=26,columns=32,bone='spine05')
    for border in (0,1):
        s.tube('Central stitched edge',[tabard(border,j/32) for j in range(33)],.0045,m['gold'],'spine05')
    s.tube('Central stitched hem',[tabard(j/45,1) for j in range(46)],.0038,m['gold'],'spine05')
    surface_ring(s,'Layered hide belt',(0,.015,1.114),(0,0,1),(.278,.213),[(-.039,-.02),(-.032,.008),(.030,0),(.038,-.035)],m['leather'],'spine05',64)
    for height in (1.079,1.139):
        s.ring('Cast belt piping',(0,.015,height),(.278,.213),m['gold'],'spine05',.006,segments=64,wave=.003)
    s.ellipsoid('Belt medallion',(0,-.201,1.107),(.063,.022,.050),m['bronze'],'spine05',28,18,ridge=.05)
    s.ellipsoid('Inset lotus seal',(0,-.222,1.107),(.028,.011,.028),m['gold'],'spine05',24,14,ridge=.13)
    # One cast shell bridges the sternum and follows the rib cage.
    def cuirass(u,v):
        t=2*u-1
        width=mix(.149,.267,math.sin(v*math.pi/2)**1.15)
        x=t*width
        z=mix(1.22 + .077*abs(t)**.65,1.628 - .039*abs(t)**1.4 - .047*bell(t,0,.35),v)
        offset=.023 + .031*math.sin(math.pi*v)**.7*(1-abs(t)**2) + .010*(1-abs(t))
        return skin_contact(s,x,z,offset)
    s.cloth('Cuirass · continuous arched temple bronze',cuirass,m['bronze'],rows=26,columns=54)
    for fixed_u in (0,1):
        s.tube('Bound bronze cuirass side',[cuirass(fixed_u,j/38) for j in range(39)],.006,m['gold'],sides=9)
    for fixed_v in (0,1):
        s.tube('Chased chest shell edge',[cuirass(j/64,fixed_v) for j in range(65)],.006,m['gold'],sides=9)
    for j in range(4):
        v=.22+.16*j
        arc=[cuirass(.13+.74*k/54,v+.048*abs(2*k/54-1)**1.7) for k in range(55)]
        s.tube('Shallow cast ribs',arc,.004,m['gold'],sides=8)
    seal=Vector(cuirass(.5,.76))
    s.ellipsoid('Heart seal engraved socket',seal+Vector((0,-.007,0)),(.054,.013,.049),m['gold'],'spine01',22,12,ridge=.13)
    s.ellipsoid('Heart seal carnelian stone',seal+Vector((0,-.020,0)),(.019,.008,.025),m['ember'],'spine01',16,12)
    dorsal_armor(s,m)
    for sign,side in ((-1,'R'),(1,'L')):
        bound_calf_cuff(s,m,side)
        b=s.rig.data.bones['upperarm01.'+side]
        center=b.head_local + Vector((sign*.044,0,-.031))
        def pauldron(u,v):
            a=TAU*u
            angle=.012+v*(1.84+.18*math.cos(a))
            return (center.x+.126*math.sin(angle)*math.cos(a),center.y+.136*math.sin(angle)*math.sin(a),center.z+.104*math.cos(angle)-sign*.028*math.sin(angle)*math.cos(a))
        s.cloth('Layered bronze shoulder · '+side,pauldron,m['bronze'],rows=16,columns=58,wrap=True,bone=b.name)
        for row in (.59,.98):
            s.tube('Shoulder chased lip',[pauldron(j/70,row) for j in range(71)],.0055,m['gold'],b.name,9)
        for index in range(7):
            p=Vector(pauldron(index/7,.83))
            s.ellipsoid('Shoulder brass rivet',p,(.008,.008,.008),m['gold'],b.name,12,8)
        f=s.rig.data.bones['lowerarm02.'+side]
        axis=(f.tail_local-f.head_local).normalized()
        mid=f.head_local.lerp(f.tail_local,.54)
        point=surface_ring(s,'Tapered bracer · '+side,mid,axis,(.062,.061),[(-.086,-.02),(-.077,.02),(-.033,.07),(.029,.02),(.064,-.11),(.078,-.16)],m['bronze'],f.name)
        for row in (0,1):
            s.tube('Bracer rolled rim',[point(j/48,row) for j in range(49)],.0065,m['gold'],f.name,9)
        for i in range(7):
            u=i/7
            s.tube('Wrist chased ornament',[point(u+.019*math.sin(j*math.pi/5),j/5) for j in range(6)],.0031,m['gold'],f.name,6)
        foot=s.rig.data.bones['foot.'+side]
        pos=foot.head_local
        s.ellipsoid('Sandal soles · '+side,(pos.x,pos.y-.061,.012),(.062,.122,.011),m['leather'],foot.name,30,10)
        for y in (-.090,-.031):
            strap=[(pos.x+.107*(j/28-.5),pos.y+y,.035+.026*math.sin(math.pi*j/28)) for j in range(29)]
            s.tube('Sandal leather straps',strap,.007,m['leather'],foot.name,8)
        s.ring('Ankle bronze cording',(pos.x,pos.y,.159),(.054,.052),m['gold'],'lowerleg02.'+side,.006,segments=32)
    chord=[cuirass(.84-.68*j/48,.99-.76*j/48) for j in range(49)]
    s.tube('Sacred braided cord',[Vector(p)+Vector((0,-.011,0)) for p in chord],.007,m['gold'],sides=9)


def tail(s, m):
    controls=[(0,.11,1.10),(.19,.27,.87),(.45,.32,.58),(.67,.34,.72),(.72,.34,1.14),(.68,.31,1.51),(.54,.31,1.68),(.45,.30,1.58)]
    controls=[Vector(p) for p in controls]
    # Hermite interpolation keeps the full-profile tail continuous past each bend.
    def at(t):
        j=min(int(t),len(controls)-2)
        u=t-j
        a,b=controls[j:j+2]
        left=(b-controls[max(0,j-1)])*.5
        right=(controls[min(len(controls)-1,j+2)]-a)*.5
        return (2*u**3-3*u*u+1)*a +(u**3-2*u*u+u)*left+(-2*u**3+3*u*u)*b+(u**3-u*u)*right
    points=[at((len(controls)-1)*k/84) for k in range(85)]
    rig=s.rig
    bpy.context.view_layer.objects.active=rig
    bpy.ops.object.mode_set(mode='EDIT')
    previous=rig.data.edit_bones['spine05']
    joints=(0,25,49,68,84)
    names=[]
    for i,(a,b) in enumerate(zip(joints,joints[1:]),1):
        bone=rig.data.edit_bones.new(f'tail_{i:02}')
        bone.head,bone.tail=points[a],points[b]
        bone.parent=previous
        names.append(bone.name)
        previous=bone
    bpy.ops.object.mode_set(mode='OBJECT')
    sides=16
    obj=s.tube('Curved articulated Vayu tail',points,.041,m['fur'],names[0],sides,
               lambda t:.25+.75*(1-t)**.93)
    obj.vertex_groups.clear()
    for i,n in enumerate(names):
        group=obj.vertex_groups.new(name=n)
        for j in range(len(points)):
            fade_in=smooth(joints[i]-8,joints[i]+8,j) if i else 1.0
            fade_out=1-smooth(joints[i+1]-8,joints[i+1]+8,j) if i+1<len(names) else 1.0
            weight=fade_in*fade_out
            if weight>0:
                group.add(list(range(j*sides,(j+1)*sides)),weight,'REPLACE')
    for t in (12,17,22):
        s.tube('Tail bronze binding',points[t:t+3],.041*(.31+.75*(1-t/84)**.93),m['bronze'],names[0],16)
    for i in range(7):
        p=points[-7]+Vector(((i-3)*.003,0,(i-3)*.003))
        s.tube('Sweep at tail tip',[p.lerp(points[-1],j/12)+Vector((.04,-.012,(i-3)*.005))*math.sin(math.pi*j/12) for j in range(13)],.012,m['mane'],names[-1],8,lambda t:.06+.94*(1-t)**.62)
    return names, points[-1]


def mace(s,m):
    wrist=s.rig.data.bones['wrist.R']
    rotation=wrist.matrix_local.to_3x3()
    scale=HEIGHT/1.85
    def p(x,y,z):
        return wrist.head_local+rotation@(Vector((z,y,-x))+Vector((0,.105,.025)))*scale
    def lathe(name, ranges, mat, facets=52):
        def form(u,v):
            z,r,flute=ranges[min(len(ranges)-1,round(v*(len(ranges)-1)))]
            a=u*TAU
            radius=r*(1+flute*math.cos(a*10))
            return p(radius*math.cos(a),radius*math.sin(a),z)
        s.cloth(name,form,mat,rows=len(ranges)-1,columns=facets,wrap=True,bone=wrist.name)
        return form
    lathe('Vajra Gada · ashwood haft',[(-.35,0,0),(-.35,.019,0),(-.29,.021,.03),(.54,.026,.04),(.65,.030,.03)],m['leather'])
    for start,step,num in ((-.129,.033,13),(.43,.037,4)):
        for j in range(num):
            z=start+step*j
            pts=[p(.024*math.cos(TAU*k/24),.024*math.sin(TAU*k/24),z) for k in range(25)]
            s.tube('Twined grip ring',pts,.0028 if num>6 else .0045,m['bronze'],wrist.name,7)
    for z in (-.34,.54,.61):
        pts=[p(.029*math.cos(TAU*k/40),.029*math.sin(TAU*k/40),z) for k in range(41)]
        s.tube('Haft collars',pts,.006,m['gold'],wrist.name,9)
    sections=[(.55,.028,0),(.565,.045,0),(.59,.057,.04),(.62,.061,.04)]
    for j in range(29):
        t=j/28
        sections.append((.622+.305*t,(.060+.077*math.sin(math.pi*t)**.85)*(1-.23*t),.09*math.sin(math.pi*t)))
    sections.extend([(.929,.042,.02),(.956,.033,0),(.989,0,0)])
    head=lathe('Vajra Gada · bell metal fluted crown',sections,m['bronze'],88)
    for row in (.15,.27,.74,.84):
        s.tube('Repoussé weapon bands',[head(j/91,row) for j in range(92)],.0048,m['gold'],wrist.name,9)
    for j in range(10):
        u=j/10
        ribs=[head(u,v) for v in [.23+.58*k/28 for k in range(29)]]
        s.tube('Crown petals · gilded flutes',ribs,.005,m['gold'],wrist.name,9,lambda t:.21+.79*math.sin(math.pi*t))
        center=head(u+.05,.52)
        s.ellipsoid('Vajra ember rivet',center,(.012,.012,.012),m['ember'],wrist.name,16,10)
    return p(0,0,0), p(0,0,.775)


def landmark(rig, name, bone, world_rest):
    node=bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(node)
    node.parent=rig
    node.parent_type='BONE'
    node.parent_bone=bone
    bpy.context.view_layer.update()
    node.matrix_world=Matrix.Translation(world_rest)
    return node


def special_actions(rig, actions):
    """Reuse original brawler pose/IK; give the planted abilities their own beat."""
    for clip, seconds, release in (('tail_sweep',1.0,.5),('mountain_pulse',1.3,.55)):
        action=bpy.data.actions.new(clip)
        action.use_fake_user=True
        action['yuga_release_ratio']=release
        rig.animation_data.action=action
        action['yuga_root_motion']=False
        previous={}
        phases=sorted({i/24 for i in range(25)}|{release})
        for phase in phases:
            before=phase<=release
            anticipation=smooth(0,release,phase) if before else 1-smooth(release,1,phase)
            punch=math.sin(math.pi*smooth(0,1,phase))**.8
            pose=_sample(rig,'mace','idle',0)
            if clip=='tail_sweep':
                spin=-34*anticipation+46*bell(phase,.63,.19)
                _planted(pose,-.035-.093*anticipation)
                pose.rotate('spine02',z=spin,x=5*punch)
                pose.rotate('head',z=-.32*spin)
                pose.arm('L',(.31+.17*punch,-.14-.14*punch,1.09+.29*punch),(.54,-.04,1.27))
                pose.grip('L',.16)
            else:
                _planted(pose,-.035-.11*anticipation)
                pose.rotate('spine02',x=12*anticipation+9*bell(phase,.65,.10))
                pose.arm('R',(-.28-.02*punch,-.29-.10*anticipation,1.25+.40*punch),(-.47,.04,1.38),(0,-.55,.55))
                pose.arm('L',(.29+.065*punch,-.15-.30*anticipation,1.1+.53*punch),(.56,-.06,1.33),(0,-.8,.5))
                pose.grip('L',.03)
            frame=1+round(seconds*FPS*phase)
            for name in set(pose.rot)|set(pose.loc):
                bone=rig.pose.bones[name]
                bone.rotation_mode='QUATERNION'
                if name in pose.rot:
                    q=pose.rot[name].copy()
                    if name in previous and previous[name].dot(q)<0:
                        q.negate()
                    previous[name]=q
                    bone.rotation_quaternion=q
                    bone.keyframe_insert('rotation_quaternion',frame=frame,group=name)
                if name in pose.loc:
                    bone.location=pose.loc[name]
                    bone.keyframe_insert('location',frame=frame,group=name)
        for fcurve in action.fcurves:
            for key in fcurve.keyframe_points:
                key.interpolation='LINEAR'
        actions[clip]=action


def animated_tail(rig, names, actions):
    # Secondary motion is baked on the four new joints, leaving existing clips intact.
    drives={'idle':3,'run':16,'fire':20,'cast':16,'jump':19,'defeat':9,'cast1':24,'cast2':11,'cast3':27,
            'tail_sweep':31,'mountain_pulse':23}
    for clip,action in actions.items():
        rig.animation_data.action=action
        start,end=map(float,action.frame_range)
        for i,name in enumerate(names):
            joint=rig.pose.bones[name]
            joint.rotation_mode='QUATERNION'
            for j in range(17):
                phase=j/16
                pulse=math.sin(TAU*phase-i*.58)
                if clip not in ('idle','run'):
                    pulse*=math.sin(math.pi*phase)
                if clip=='tail_sweep':
                    pulse=bell(phase,.5+i*.047,.164)-.44*bell(phase,.235+i*.02,.09)
                    pulse*=math.sin(math.pi*phase)**.4
                magnitude=math.radians(drives[clip]*(.48+i*.21))
                joint.rotation_quaternion=Euler((pulse*magnitude*.48,0,pulse*magnitude)).to_quaternion()
                joint.keyframe_insert(data_path='rotation_quaternion',frame=start+(end-start)*phase,group=name)
    rig.animation_data.action=actions['idle']
    bpy.context.scene.frame_set(1)


def studio():
    scene=bpy.context.scene
    graph=bpy.context.evaluated_depsgraph_get()
    soles=[]
    for marker in ('L','R'):
        shoe=bpy.data.objects['Sandal soles · '+marker].evaluated_get(graph)
        soles.append(min((shoe.matrix_world @ v.co).z for v in shoe.data.vertices))
    support=min(soles)
    bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1.2,depth=.10,location=(0,.03,support-.05))
    stand=bpy.context.object
    stand.name='Granite display plinth'
    stand.data.materials.append(texture_material('Display · blue granite',(.079,.095,.107),.09,.81,'bronze'))
    bevel=stand.modifiers.new('Cut pedestal edge','BEVEL')
    bevel.width=.016;bevel.segments=3
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,support-.102))
    bpy.context.object.data.materials.append(material('Display · cool slate',(.024,.034,.044),0,.92))
    for name,position,color,power,size in (
        ('Key · warm softbox',(2.2,-3.9,4.5),(1,.79,.58),550,2.3),
        ('Fill · pale teal',(-3.2,-1.8,2.6),(.49,.72,1),280,3.2),
        ('Rim · sky edge',(.2,2.7,3.7),(.49,.76,1),750,2.2),
        ('Eyes · soft bounce',(.4,-2.0,1.4),(1,.9,.77),48,1.1)):
        lamp=bpy.data.lights.new(name,'AREA')
        lamp.color=color;lamp.energy=power;lamp.shape='DISK';lamp.size=size
        obj=bpy.data.objects.new(name,lamp);scene.collection.objects.link(obj)
        obj.location=position
        obj.rotation_euler=(Vector((0,0,1.18))-obj.location).to_track_quat('-Z','Y').to_euler()
    scene.world=bpy.data.worlds.new('Granite studio ambient')
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.14,.183,.25,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.25
    camera=bpy.data.cameras.new('Asset review camera')
    camera.type='ORTHO'
    obj=bpy.data.objects.new('Asset review camera',camera)
    scene.collection.objects.link(obj)
    scene.camera=obj
    scene.render.engine='CYCLES';scene.cycles.device='CPU'
    scene.cycles.samples=48;scene.cycles.use_denoising=False
    scene.cycles.adaptive_threshold=.065;scene.cycles.max_bounces=5
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    return scene,soles


def set_view(scene,name):
    views={
        'beauty':((2.8,-7.0,2.55),(.04,0,1.14),2.85,800,960),
        'face':((.44,-3.70,2.16),(0,-.12,1.84),.72,640,640),
        'rear':((3.8,6.0,2.8),(.04,0,1.15),3.0,800,960),
        'profile':((6.8,-.5,2.45),(.035,0,1.13),2.95,800,960),
    }
    position,point,scale,width,height=views[name]
    scene.camera.location=position
    scene.camera.rotation_euler=(Vector(point)-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.ortho_scale=scale
    scene.render.resolution_x=width;scene.render.resolution_y=height
    scene.render.resolution_percentage=100


def output_receipt(path, rig, source_files):
    size,tag=struct.unpack_from('<II',path.read_bytes(),12)
    assert tag==0x4E4F534A
    doc=json.loads(path.read_bytes()[20:20+size])
    primitives=[p for mesh in doc['meshes'] for p in mesh['primitives']]
    def count(key):
        return sum(doc['accessors'][p['attributes'][key]]['count'] for p in primitives if key in p['attributes'])
    return {
        'glb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'bytes':path.stat().st_size,'bones':len(rig.data.bones),'vertices':count('POSITION'),
        'colored_vertices':count('COLOR_0'),
        'triangles':sum(doc['accessors'][p['indices']]['count']//3 for p in primitives),
        'materials':len(doc['materials']),'surfaces':len(primitives),
        'verified_reused_sources':{str(p.relative_to(NATIVE.parents[1])):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
        'joints_in_skin':len(doc['skins'][0]['joints']),
        'clips':[a['name'] for a in doc['animations']],
        'body_height_m':HEIGHT,'art_facing':'+Z','art_up':'+Y',
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--render',action='store_true')
    parser.add_argument('--views',nargs='+',default=('beauty','face','rear','profile'))
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source=ART/'sources/makehuman'
    body,rig,weights,_=build_anatomy(source,'male',HEIGHT,REST_WIDTH,FACE_WIDTH)
    mats=palette()
    sculpt=Sculpt(rig,body,weights,sculpt_anatomy(body,mats))
    face(sculpt,mats)
    armor(sculpt,mats)
    tail_names,tail_tip=tail(sculpt,mats)
    grip,head=mace(sculpt,mats)
    markers=[landmark(rig,'gada_grip','wrist.R',grip),
             landmark(rig,'gada_head','wrist.R',head),
             landmark(rig,'tail_tip',tail_names[-1],tail_tip)]
    actions=author_animations(rig,'mace','hanuman')
    special_actions(rig,actions)
    animated_tail(rig,tail_names,actions)
    # Keep the authored surfaces editable. Consolidate only copies for the runtime.
    bpy.ops.object.select_all(action='DESELECT')
    clones=[]
    for surface in sculpt.objects:
        clone=surface.copy();clone.data=surface.data.copy()
        bpy.context.collection.objects.link(clone)
        clone.select_set(True);clones.append(clone)
    bpy.context.view_layer.objects.active=clones[0]
    bpy.ops.object.join()
    game_mesh=bpy.context.object
    game_mesh.name='Hanuman skinned hero'
    # Retain authored originals above and remove surplus game-only edges.
    bm=bmesh.new()
    bm.from_mesh(game_mesh.data)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bm.to_mesh(game_mesh.data)
    bm.free()
    reducer=game_mesh.modifiers.new('Game geometry simplification','DECIMATE')
    reducer.ratio=.68
    reducer.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=reducer.name)
    game_mesh.select_set(True);rig.select_set(True)
    for marker in markers:
        marker.select_set(True)
    path=args.output/'hanuman.glb'
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,
        export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,
        export_frame_range=False,export_skins=True,export_all_influences=False,
        export_yup=True,export_image_format='AUTO',export_tangents=True,
        export_vertex_color='MATERIAL')
    receipt=output_receipt(path,rig,sorted(source.glob('*'))+[ART/'pipeline'/n for n in ('anatomy.py','animations.py','geometry.py','build_heroes.py')])
    print('HANUMAN_ART '+json.dumps(receipt),flush=True)
    (args.output/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
    bpy.data.objects.remove(game_mesh,do_unlink=True)
    scene,soles=studio()
    receipt['posed_sandal_minima_m']=soles
    receipt['plinth_top_m']=min(soles)
    (args.output/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
    set_view(scene,'beauty')
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output/'hanuman.blend'),compress=True)
    if args.render:
        for name in args.views:
            set_view(scene,name)
            scene.render.filepath=str(args.output/f'hanuman-{name}.png')
            bpy.ops.render.render(write_still=True)


if __name__=='__main__':
    main()
