"""Room-local scenery for the measured Mandala Rift floor, in Blender metres.

Each maker leaves the callout origin open. Named batches separate materials on
one editable prop. Library motifs retain their authored topology and materials.
"""
from collections import defaultdict
from functools import lru_cache
from math import cos, pi, radians, sin, tau
from pathlib import Path

import bpy
from mathutils import Vector

import artlib as A


class Piece:
    """Build a fitted prop in its own right/front/up frame, then batch by finish."""

    def __init__(self, name, x, y, z=0, yaw=0):
        self.name = name
        self.origin = (x, y, z)
        self.c, self.s = cos(radians(yaw)), sin(radians(yaw))
        self.parts = defaultdict(lambda: ([], []))

    def geom(self, material, vertices, faces):
        vx, fs = self.parts[material]
        base = len(vx)
        x, y, z = self.origin
        vx.extend((x+self.c*u-self.s*v, y+self.s*u+self.c*v, z+h) for u,v,h in vertices)
        fs.extend(tuple(base+i for i in face) for face in faces)

    def box(self, material, pos, dims, chamfer=.035, waist=1):
        x,y,z = pos
        w,d,h = (n/2 for n in dims)
        b = min(chamfer, w*.35, d*.35, h*.35)
        levels = [(-h,w-b,d-b), (-h+b,w,d), (h-b,w*waist,d*waist), (h,w*waist-b,d*waist-b)]
        verts = []
        for dz, half_w, half_d in levels:
            r = min(b,half_w*.4,half_d*.4)
            verts.extend((x+u,y+v,z+dz) for u,v in [(-half_w+r,-half_d),(half_w-r,-half_d),
                (half_w,-half_d+r),(half_w,half_d-r),(half_w-r,half_d),(-half_w+r,half_d),
                (-half_w,half_d-r),(-half_w,-half_d+r)])
        self.geom(material,verts,ring_faces(8,4))

    def turned(self, material, base, profile, sides=20):
        """Closed wheel-thrown horizontal courses, profile ordered from foot to top."""
        x,y,z=base
        verts=[(x+r*cos(tau*i/sides),y+r*sin(tau*i/sides),z+up)
               for up,r in profile for i in range(sides)]
        self.geom(material,verts,ring_faces(sides,len(profile)))

    def rod(self, material, start, finish, r, end=None, sides=8):
        a,b=Vector(start),Vector(finish)
        axis=(b-a).normalized()
        ref=Vector((0,0,1)) if abs(axis.z)<.9 else Vector((0,1,0))
        u=axis.cross(ref).normalized()
        v=axis.cross(u)
        verts=[tuple(p+(u*cos(tau*i/sides)+v*sin(tau*i/sides))*radius)
               for p,radius in ((a,r),(b,r if end is None else end)) for i in range(sides)]
        self.geom(material,verts,ring_faces(sides,2))

    def arch(self, material, origin, span, rise, band, depth, scallop=0):
        x,y,z=origin
        verts=[]
        segments=32
        for side in (-1,1):
            for rad in (0,band):
                for i in range(segments+1):
                    t=pi*i/segments
                    cut=1-scallop*sin(5*t)**2 if rad==0 else 1
                    verts.append((x+(span*.5+rad)*cos(t)*cut,y+side*depth/2,
                                  z+(rise+rad)*sin(t)*cut))
        n=segments+1
        faces=[]
        for i in range(segments):
            faces.extend([(i+1,i,n+i,n+i+1),(2*n+i,2*n+i+1,3*n+i+1,3*n+i),
                          (i,i+1,2*n+i+1,2*n+i),(n+i+1,n+i,3*n+i,3*n+i+1)])
        faces.extend([(0,2*n,3*n,n),(n-1,2*n-1,4*n-1,3*n-1)])
        self.geom(material,verts,faces)

    def finish(self):
        for material,(vertices,faces) in self.parts.items():
            A.mesh(f'{self.name} · {material}',vertices,faces,material)


def ring_faces(sides, rows):
    result=[tuple(reversed(range(sides)))]
    for j in range(rows-1):
        for k in range(sides):
            a=j*sides+k
            b=j*sides+(k+1)%sides
            result.append((a,b,b+sides,a+sides))
    result.append(tuple(range((rows-1)*sides,rows*sides)))
    return result


@lru_cache(maxsize=8)
def library_motif(collection_name):
    library=Path(__file__).resolve().parents[2]/'reuse-library'/'yuga-world-elements.blend'
    with bpy.data.libraries.load(str(library),link=False) as (source,selected):
        if collection_name not in source.collections:
            raise KeyError(f'Missing art collection {collection_name} in {library}')
        selected.collections=[collection_name]
    obj,=(o for o in selected.collections[0].all_objects if o.type=='MESH')
    return obj.data.name


def motif(collection, name, pos, dimensions, yaw=0):
    """Instance original library geometry by base centre; preserve its UVs and slots."""
    mesh_name=library_motif(collection)
    if mesh_name not in bpy.data.meshes:
        library_motif.cache_clear()
        mesh_name=library_motif(collection)
    obj=bpy.data.objects.new(name,bpy.data.meshes[mesh_name]);bpy.context.collection.objects.link(obj)
    points=[Vector(p) for p in obj.bound_box]
    low=Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in points) for i in range(3)))
    scale=Vector(tuple(span/(high[i]-low[i]) for i,span in enumerate(dimensions)))
    centre=Vector(((low.x+high.x)/2,(low.y+high.y)/2,low.z))
    offset=Vector((centre.x*scale.x,centre.y*scale.y,centre.z*scale.z))
    obj.rotation_euler.z=radians(yaw)
    offset.rotate(obj.rotation_euler)
    obj.scale=scale
    obj.location=Vector(pos)-offset
    obj['donor_collection']=collection
    return obj


def column(p,x,y,h,r,stone='sandstone'):
    p.box('basalt',(x,y,.10),(r*2.35,r*2.35,.20))
    p.turned(stone,(x,y,0),[(.16,r),(.27,r),(.33,r*.85),(.44,r*.67),(.53,r*.74),
             (h*.65,r*.54),(h*.77,r*.52),(h*.83,r*.66),(h*.89,r*.65),(h*.94,r*.92),(h,r)],16)
    for z in (.32,h*.82,h*.91):p.turned('brass',(x,y,z),[(0,r*(.85 if z<.5 else .73)),(.055,r*(.85 if z<.5 else .73))],16)
    p.box('limestone',(x,y,h+.06),(2.36*r,2.36*r,.12))


def vessel(p,x,y,z,r,h,body='terracotta'):
    p.turned(body,(x,y,z),[(0,r*.54),(.07*h,r*.56),(.20*h,r*.82),(.44*h,r),(.61*h,.99*r),
             (.8*h,r*.64),(.84*h,r*.47),(.91*h,r*.48),(.94*h,.62*r),(h,.62*r),(.98*h,.44*r),(.90*h,.39*r)],24)
    p.turned('ink',(x,y,z+h*.907),[(0,r*.385),(.001,r*.385)],16)
    for k in (.23,.25):p.turned('limestone' if body=='terracotta' else 'brass',(x,y,z+h*k),[(0,r*.87),(.018*h,r*.89)],24)


def canopy(p,z,width,depth,colors):
    """Alternating continuous cloth bands, with tension ridges and a scalloped hem."""
    count=7
    def cloth(x,t):
        slouch=.26*(1-(2*x/width)**2)*(1-.3*t)
        return z+.72*t-slouch-.25*sin(pi*t)+.055*sin(x*pi*2.5+.45*t)
    for band in range(count):
        start=-width/2+band*width/count
        verts=[]
        for j in range(7):
            t=j/6
            for i in range(5):
                x=start+i*width/count/4
                verts.append((x,depth*(t-.5),cloth(x,t)))
        faces=[(j*5+i,j*5+i+1,(j+1)*5+i+1,(j+1)*5+i) for j in range(6) for i in range(4)]
        for i in range(5):
            x=start+i*width/count/4
            verts.append((x,-depth/2+.035,cloth(x,0)-.16-.14*sin(pi*i/4)))
        faces.extend((i+1,i,35+i,36+i) for i in range(4))
        p.geom(colors[band%len(colors)],verts,faces)
    for side in (-1,1):
        x=side*width*.48
        for y,h in ((-depth/2,z),(depth/2,z+.72)):
            p.rod('timber',(x,y,0),(x,y,h+.12),.097,.061,10)
            p.turned('brass',(x,y,h+.10),[(0,.088),(.11,.063),(.19,.017)],12)
        p.rod('timber',(x,-depth/2,z),(x,depth/2,z+.72),.062)
    p.rod('timber',(-width*.5,depth/2,z+.71),(width*.5,depth/2,z+.71),.065)


def roof(p,z,w,d,height,base='sandstone'):
    # Deeply shadowed projecting eave, pitched cap and ridge finials.
    p.box('basalt',(0,0,z+.09),(w*.90,d*.94,.18))
    p.box('limestone',(0,0,z+.24),(w,d,.18),.055)
    p.box(base,(0,0,z+.34+height/2),(w*.98,d*.96,height),.08,.57)
    p.box('bronze',(0,0,z+.37+height),(w*.59,d*.59,.12))
    for x in (-.24*w,0,.24*w):
        p.turned('brass',(x,0,z+.40+height),[(0,.17),(.09,.19),(.17,.12),(.21,.16),(.35,.10),(.48,.025)],14)


def hanging_lamp(p,x,y,z,drop):
    p.rod('bronze',(x,y,z),(x,y,z-drop),.019,sides=6)
    p.turned('brass',(x,y,z-drop-.12),[(0,.07),(.04,.21),(.12,.31),(.15,.30),(.11,.18)],16)
    p.turned('ember',(x+.11,y,z-drop+.005),[(0,.055),(.06,.07),(.18,.016)],8)


def handloom(p):
    p.box('timber',(0,0,1.03),(3.5,1.1,.18),.06)
    for sx in (-1.40,1.40):
        for sy in (-.42,.42):p.rod('timber',(sx,sy,.03),(sx,sy,1.14),.095,.075)
    for x in (-1.20,1.20):p.rod('brass',(x,-.48,1.18),(x,.48,1.18),.085,sides=12)
    for j in range(17):
        y=(j-8)*.049
        p.rod('linen' if j%4 else 'madder',(-1.21,y,1.19),(1.21,y,1.19),.013,sides=5)
    p.rod('timber',(-.4,-.5,1.18),(-.15,.49,1.23),.048)


def scale_beam(p,z,width):
    column(p,0,.22,z,.30,'granite')
    p.box('bronze',(0,0,z+.24),(width,.22,.23),.045)
    p.turned('brass',(0,0,z+.34),[(0,.14),(.17,.20),(.40,.04)],12)
    for side in (-1,1):
        x=side*width*.39; bottom=z-1.0+side*.12
        for angle in range(3):
            a=angle*tau/3
            p.rod('brass',(x,0,z+.14),(x+.50*cos(a),.50*sin(a),bottom+.14),.019,sides=5)
        p.turned('brass',(x,0,bottom),[(0,.12),(.065,.36),(.13,.52),(.17,.54),(.15,.43)],24)


def spawn(key,node):
    is_spice=key=='atk'; w,d=node['size']
    depth=-1 if is_spice else 1
    p=Piece('Spice gate · traders’ torana' if is_spice else 'Water gate · aqueduct arcade',0,depth*(d/2-1.7),yaw=180 if is_spice else 0)
    span=w*.51
    stone='sandstone' if is_spice else 'granite'
    for x in (-span/2,span/2):
        column(p,x,0,3.7,.59,stone)
        p.box(stone,(x,0,4.04),(1.72,1.57,.58),.11,.78)
        p.turned('brass',(x,0,4.29),[(0,.36),(.22,.37),(.42,.20),(.64,.12),(.88,.055)],16)
    p.arch('limestone',(0,0,3.54),span,1.75,.42,.90,scallop=.10)
    p.arch('brass',(0,-.47,3.58),span+.10,1.77,.07,.09,scallop=.08)
    p.box('teal' if not is_spice else 'madder',(0,0,5.87),(span+1.25,1.24,.40),.07)
    roof(p,5.98,span+1.72,1.75,.59,stone)
    for x in (-span*.22,span*.22):hanging_lamp(p,x,.1,5.26,.49)
    p.finish()
    if is_spice:
        rack=Piece('Spice gate · open spice scales',w*.346,-d*.18)
        for x,y,r,h in [(-.6,-.48,.37,.73),(.06,-.35,.42,.89),(.58,.15,.36,.78),(-.42,.38,.51,1.02)]:
            vessel(rack,x,y,0,r,h,'linen')
            rack.turned('saffron' if y<0 else 'madder',(x,y,h*.91),[(0,r*.43),(.10,r*.35),(.16,.023)],16)
        rack.finish()
    else:
        p=Piece('Water gate · gauge cistern',-w*.35,d*.24)
        for y in (-.62,.62):p.box('granite',(0,y,.35),(2.1,.26,.70))
        for x in (-.92,.92):p.box('granite',(x,0,.35),(.26,1.08,.70))
        p.box('water',(0,0,.39),(1.58,.94,.035),.008)
        for j in range(6):p.box('brass',(-.80,.15,.18+j*.075),(.08,.24 if j%2 else .44,.027),.004)
        vessel(p,.90,1.16,0,.41,.93,'patina');p.finish()


def ghat(node):
    p=Piece('Ghat · open-sided audience mandapa',7.8,-6.2)
    for x in (-1.68,1.68):
        for y in (-1.34,1.34):column(p,x,y,3.55,.30)
    roof(p,3.6,4.35,3.55,.95,'terracotta')
    p.arch('sandstone',(0,-1.34,3.30),3.35,.53,.16,.30,.08)
    hanging_lamp(p,.75,.18,3.67,.69);p.finish()


def bazaar(node):
    p=Piece('Bazaar · indigo dye stall',8.05,-5.55,yaw=90)
    canopy(p,3.18,6.0,3.06,('indigo','linen','teal','linen'))
    for j in range(5):
        x=(j-2)*.83
        vessel(p,x,.58,0,.35+.07*(j%2),.76+.18*(j%3),'terracotta' if j%2 else 'patina')
    p.box('timber',(0,-.63,1.06),(3.68,.75,.14))
    for x in (-1.56,1.56):
        for y in (-.87,-.38):p.rod('timber',(x,y,0),(x,y,1.06),.073)
    for j,mat in enumerate(('indigo','linen','madder','teal')):
        x=(j-1.5)*.80
        p.box(mat,(x,-.63,1.20),(.74,.62,.14),.052)
        p.box(mat,(x+.02,-.64,1.32),(.65,.57,.107),.045)
    p.finish()


def sluice(node):
    p=Piece('Sluice · suspended water-lift wheel',-2.5,3.6,0,90)
    z=3.65;rad=1.38
    for i in range(24):
        t,u=tau*i/24,tau*(i+1)/24
        for y in (-.38,.38):p.rod('timber',(rad*cos(t),y,z+rad*sin(t)),(rad*cos(u),y,z+rad*sin(u)),.085,sides=8)
        if i%2==0:
            p.rod('brass',(0,-.37,z),(rad*cos(t),-.37,z+rad*sin(t)),.048,.068)
            p.rod('timber',(0,.37,z),(rad*cos(t),.37,z+rad*sin(t)),.067)
            p.rod('bronze',(rad*cos(t),-.41,z+rad*sin(t)),(rad*cos(t),.41,z+rad*sin(t)),.065)
            p.turned('terracotta',(1.22*cos(t),0,z+1.22*sin(t)-.14),[(0,.13),(.10,.19),(.25,.18),(.31,.14)],12)
    for y in (-.58,.58):
        p.rod('patina',(-.71,y,2.08),(0,y,z+.10),.105)
        p.rod('patina',(.71,y,2.08),(0,y,z+.10),.105)
    p.rod('brass',(0,-.78,z),(0,.78,z),.22,sides=18)
    p.finish()


def waterfront(key,node):
    w,d=node['size']
    if key=='steps_s':
        p=Piece('Reed Steps · ghat stair and mooring pins',-w*.33,-d*.01,0,90)
        for j in range(4):p.box('limestone' if j<3 else 'sandstone',(0,.57*j,.075+j*.09),(4.6,.64,.15+j*.18),.045)
        for x in (-1.80,1.80):p.turned('timber',(x,1.65,.67),[(0,.15),(.38,.14),(.43,.22),(.50,.18)],14)
        p.finish();motif('Reed Cluster','Ghat · living reeds',(-w*.33,-d*.30,.035),(1.66,1.48,1.53),32)
    elif key=='steps_n':
        p=Piece('Jar Steps · throwing terrace',-w*.30,d*.19,0,90)
        for j in range(3):p.box('terracotta',(0,j*.74,.075+j*.14),(4.15,.79,.15+j*.28),.045)
        for row in range(2):
            for j in range(4):
                x=(j-1.5)*.96+.17*row
                vessel(p,x,.73+row*.75,.43+.28*row,.32+.055*(j%2),.75+.12*((j+row)%3),'teal' if j==1 and row else 'terracotta')
        p.finish()
    elif key=='bank':
        p=Piece('Dry Bank · ringed mooring winch',-4.6,4,1.19)
        for x in (-.86,.86):p.box('timber',(x,0,.42),(.31,1.0,.84),.04,.70)
        p.rod('brass',(-1.05,0,.75),(1.20,0,.75),.13,sides=16)
        for i in range(11):p.rod('timber',(-.65+i*.12,0,.75),(-.56+i*.12,0,.75),.26,sides=16)
        p.rod('brass',(1.12,0,.75),(1.12,.04,1.17),.053);p.finish()
        motif('Mangrove Roots','Dry Bank · pollarded mangrove',(-3.7,-4.38,0),(3.35,2.75,3.38),14)
    else:
        motif('Mangrove Roots','Reed Ford · overhanging roots',(-3.55,1.70,0),(3.15,4.1,2.93),-12)
        motif('Reed Cluster','Reed Ford · bronze reed heads',(-3.55,-4.68,0),(1.46,1.64,1.35),48)
        motif('Lotus Cluster','Reed Ford · cupped lotus leaves',(3.15,4.03,.035),(2.05,1.56,.48),12)


def temple(key,node):
    north=key=='temple_n';w,d=node['size']
    # East-edge sign frames the folded threshold. All four floor runs stay usable.
    p=Piece('North Temple · double-bar lintel' if north else 'South Temple · notched lintel',w*.365,0,0,90)
    span=4.52;h=2.89
    for x in (-span/2,span/2):column(p,x,0,h,.28,'granite' if north else 'sandstone')
    p.arch('brass' if north else 'limestone',(0,0,h-.03),span,.71,.18,.41,.055)
    roof(p,h+.71,5.50,1.70,.61,'granite' if north else 'terracotta')
    p.box('teal' if north else 'madder',(0,-.58,h+.86),(1.27,.14,.55),.044)
    if north:
        for z in (h+.77,h+.96):p.box('brass',(0,-.67,z),(.85,.065,.075),.012)
    else:
        for x in (-.42,.42):p.rod('brass',(x,-.67,h+1.04),(0,-.67,h+.70),.047,sides=6)
    for x in (-1.75,1.75):hanging_lamp(p,x,.04,h+.20,.47)
    p.finish()


def pyramids(key,node):
    w,d=node['size']
    if key=='pyramid_s':
        # The axial atlas pavilion is placed by the scene assembler. Fit its outer terraces.
        for s in (-1,1):
            p=Piece('Pavilion · lotus lamp '+str(s),s*(w/2-.80),s*(d/2-1.30))
            p.turned('sandstone',(0,0,0),[(0,.54),(.20,.54),(.27,.40),(.87,.33),(.98,.41)],16)
            vessel(p,0,0,.97,.35,.63,'brass')
            p.turned('ember',(0,0,1.53),[(0,.105),(.15,.13),(.38,.020)],8);p.finish()
    else:
        p=Piece('North Pyramid · twin-bar keeper tower',-w*.29,0,0,90)
        for x in (-1.42,1.42):
            for y in (-.74,.74):column(p,x,y,2.63,.25,'granite')
        p.arch('limestone',(0,-.73,2.58),2.76,.48,.15,.34,.055)
        p.box('sandstone',(0,0,3.02),(3.59,2.19,.44),.05)
        for j in range(4):
            level=3.21+.55*j;ww=3.80-.47*j;dd=2.43-.27*j
            p.box('limestone',(0,0,level+.07),(ww,dd,.14),.034)
            p.box('terracotta',(0,0,level+.32),(ww*.97,dd*.94,.39),.062,.86)
        for zz in (3.00,3.15):p.box('brass',(0,-1.13,zz),(1.02,.07,.064),.012)
        p.finish();motif('Temple Crown','North Pyramid · copper ridge crown',(-w*.29,0,5.31),(1.52,2.32,.72),0)


def yard(key,node):
    w,d=node['size']; cloth=key=='yard_s'
    if cloth:
        p=Piece('Cloth Yard · block printers’ arcade',-w*.32,0,0,90)
        canopy(p,3.18,d*.65,3.31,('madder','saffron','linen','saffron','madder','indigo','linen'))
        handloom(p)
        for i in range(4):
            loc=(2.41+i*.43,.71,.29)
            p.rod(('madder','saffron','teal','indigo')[i],loc,(loc[0],-.12,loc[2]),.24,sides=16)
        p.finish()
    else:
        p=Piece('Scale Yard · weigh-house',w*.31,0,0,90)
        canopy(p,3.60,d*.62,3.42,('teal','linen','indigo','linen'))
        scale_beam(p,2.38,4.33)
        for i in range(6):
            x=-3.76+.36*(i%3);y=-.52+.58*(i//3)
            p.turned('reed',(x,y,.015),[(0,.20),(.12,.29),(.34,.33),(.37,.34),(.33,.29)],14)
        p.finish()


def build_room(key,node):
    if key in ('atk','def'):spawn(key,node)
    elif key=='a':ghat(node)
    elif key=='b':bazaar(node)
    elif key=='mid':sluice(node)
    elif key in ('steps_s','steps_n','bank','ford'):waterfront(key,node)
    elif key in ('temple_s','temple_n'):temple(key,node)
    elif key in ('pyramid_s','pyramid_n'):pyramids(key,node)
    elif key in ('yard_s','yard_n'):yard(key,node)
    else:raise KeyError(f'Unrecognised Mandala district room {key!r}')
