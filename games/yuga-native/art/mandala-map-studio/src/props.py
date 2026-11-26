"""Editable Mandala civic hardware, wayfinding and carried ritual vessels in metres.

The covers take their exact dimensions from the atlas. The bell comb and ember
pot translate the district-landmarks and objective-concept artboards into mesh.
The turned profiles follow the local world/build-nature.py diya/lantern method.
Blender Z is up. Front faces -Y. A long cover faces -X/+X if its plan runs north.
"""
import math

import bpy
from mathutils import Quaternion, Vector

import artlib as A


TAU = math.tau


def _slab(name, w, d, lo, hi, material, bevel=.02, x=0, y=0):
    return A.box(name, (x,y,(lo+hi)/2), (w,d,hi-lo), material, bevel)


def _profile(name, outline, y0, y1, material):
    """Extrude a closed X/Z elevation between two depth stations."""
    area = sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(outline,outline[1:]+outline[:1]))
    if area < 0:
        outline = list(reversed(outline))
    n = len(outline)
    vertices = [(x,y,z) for y in (y0,y1) for x,z in outline]
    faces = [list(range(n)), list(reversed(range(n,2*n)))]
    faces += [(i,n+i,n+(i+1)%n,(i+1)%n) for i in range(n)]
    return A.mesh(name,vertices,faces,material)


def _turn(name, position, profile, material, sides=40, flutes=0):
    """Spin a hollow or solid contour. Optional third ordinate flutes a ring."""
    x,y,z = position
    verts, rings, faces = [],[],[]
    for index,row in enumerate(profile):
        if index == len(profile)-1 and row == profile[0]:
            rings.append(rings[0])
            continue
        h,r = row[:2]
        if r <= .000001:
            rings.append([len(verts)])
            verts.append((x,y,z+h))
            continue
        ring = []
        for i in range(sides):
            a = TAU*i/sides
            rad = r+(row[2]*math.cos(a*flutes) if len(row)>2 and flutes else 0.)
            ring.append(len(verts))
            verts.append((x+rad*math.cos(a),y+rad*math.sin(a),z+h))
        rings.append(ring)
    for low,high in zip(rings,rings[1:]):
        for i in range(sides):
            j = (i+1)%sides
            if len(low)==1:
                faces.append((low[0],high[j],high[i]))
            elif len(high)==1:
                faces.append((low[i],low[j],high[0]))
            else:
                faces.append((low[i],low[j],high[j],high[i]))
    obj = A.mesh(name,verts,faces,material)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def _sweep(name, path, radii, material, sides=8, bore=0.):
    """Sweep a round handle, chain or open spout along a curve with a stable frame."""
    p = [Vector(point) for point in path]
    if isinstance(radii,(float,int)):
        radii = [radii]*len(p)
    tangent = (p[1]-p[0]).normalized()
    right = min((Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))),key=lambda v:abs(v.dot(tangent)))
    verts,faces = [],[]
    for i,(point,r) in enumerate(zip(p,radii)):
        tangent = (p[min(i+1,len(p)-1)]-p[max(0,i-1)]).normalized()
        right = (right-tangent*right.dot(tangent)).normalized()
        up = tangent.cross(right)
        for radius in ((r,r*bore) if bore else (r,)):
            for j in range(sides):
                a = j*TAU/sides
                verts.append(tuple(point+radius*(math.cos(a)*right+math.sin(a)*up)))
    stride = sides*(2 if bore else 1)
    for i in range(len(p)-1):
        for j in range(sides):
            k = (j+1)%sides
            b,t = i*stride,(i+1)*stride
            faces.append((b+j,b+k,t+k,t+j))
            if bore:
                faces.append((b+sides+j,t+sides+j,t+sides+k,b+sides+k))
    last = (len(p)-1)*stride
    if bore:
        for j in range(sides):
            k=(j+1)%sides
            faces += [(j,sides+j,sides+k,k),(last+j,last+k,last+sides+k,last+sides+j)]
    else:
        faces += [list(reversed(range(sides))), list(range(last,last+sides))]
    obj = A.mesh(name,verts,faces,material)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def _bezier(a,b,c,d,n=18):
    pts=[Vector(v) for v in (a,b,c,d)]
    return [tuple(pts[0]*(1-t)**3+pts[1]*(3*t*(1-t)**2)+pts[2]*(3*t*t*(1-t))+pts[3]*t**3)
            for t in (i/n for i in range(n+1))]


def _rosette(name,x,y,z,r,material,depth):
    outline=[]
    for i in range(40):
        a=i*TAU/40
        q=r*(.82+.18*math.cos(a*8))
        outline.append((x+q*math.cos(a),z+q*math.sin(a)))
    return _profile(name,outline,y-depth/2,y+depth/2,material)


def _band(name,x,y,z,r,w,material):
    t=min(w*.35,.006)
    return _turn(name,(x,y,z),[(0,r-t),(w*.25,r),(w*.75,r),(w,r-t),
                               (w,r-2*t),(0,r-2*t),(0,r-t)],material)


def _bell_screen(w,d,h):
    _slab('Heel | river granite',w,d,0,h*.105,'granite',.055)
    _slab('Undercut skirt',w*.96,d*.95,h*.105,h*.19,'sandstone',.04)
    _slab('Screen opaque masonry',w*.945,d*.85,h*.17,h*.91,'sandstone',.045)
    _slab('Carved stringcourse',w*.97,d*.93,h*.22,h*.255,'limestone',.018)
    _slab('Capital shadow line',w*.97,d*.94,h*.89,h*.925,'basalt',.014)
    _slab('Drip course',w,d*.99,h*.925,h*.976,'limestone',.034)
    _slab('Ridge coping',w*.95,d*.94,h*.976,h,'sandstone',.015)
    for side in (-1,1):
        y=side*d*.433
        for i in (-1,0,1):
            x=i*w*.29
            span=w*.111
            bottom,shoulder,apex=h*.34,h*.61,h*.81
            arch=[(x-span,bottom),(x+span,bottom),(x+span,shoulder),
                  (x+span*.83,shoulder+h*.059),(x+span*.52,shoulder+h*.082),(x,apex),
                  (x-span*.52,shoulder+h*.082),(x-span*.83,shoulder+h*.059),(x-span,shoulder)]
            _profile(f'Bell niche {side}.{i}',arch,y-.012,y+.012,'basalt')
            dy=side*(abs(y)+.021)
            _rosette(f'Cast sound flower {side}.{i}',x,dy,h*.535,span*.68,'bronze',.025)
            A.ellipsoid(f'Bell eye {side}.{i}',(x,dy+side*.02,h*.535),(span*.17,.035,span*.17),'brass')
        for i in range(4):
            x=(i-1.5)*w*.286
            _slab('Fluted bay jamb',w*.021,d*.038,h*.27,h*.855,'limestone',.012,x,side*d*.443)


def _stone_lectern(w,d,h):
    _slab('Square shoe',w,d,0,h*.14,'granite',.07)
    _slab('Ochre plinth',w*.94,d*.93,h*.14,h*.23,'sandstone',.045)
    # Eight clipped corners leave a square plan datum while catching the light.
    chamfer=.16*w
    def ring(width,depth,z):
        a,b=width/2,depth/2
        c=min(chamfer,a*.27,b*.27)
        return [(-a+c,-b,z),(a-c,-b,z),(a,-b+c,z),(a,b-c,z),
                (a-c,b,z),(-a+c,b,z),(-a,b-c,z),(-a,-b+c,z)]
    lower,upper=ring(w*.78,d*.76,h*.23),ring(w*.84,d*.81,h*.72)
    A.mesh('Octagonal reading pedestal',lower+upper,[list(reversed(range(8))),list(range(8,16))]+
           [(i,(i+1)%8,8+(i+1)%8,8+i) for i in range(8)],'sandstone')
    _slab('Desk rim',w*.94,d*.93,h*.70,h*.77,'limestone',.045)
    for i in (-1,1):
        tablet=ring(w*.415,d*.82,h*.77)
        tablet=[(x+i*w*.218,y,z) for x,y,z in tablet]
        upper=[(x,y,h*.84+(y/d+.41)*h*.165) for x,y,z in tablet]
        A.mesh('Sloped ledger leaf',tablet+upper,[list(reversed(range(8))),list(range(8,16))]+
               [(j,(j+1)%8,8+(j+1)%8,8+j) for j in range(8)],'limestone')
        for j in range(4):
            y=(j-1.45)*d*.145
            z=h*.844+(y/d+.41)*h*.165
            length=w*(.126+.016*(j%3))
            A.beam('Survey tally',(i*w*.218-length,y,z),(i*w*.218+length,y,z),.009,'bronze',6)
    _slab('High reading stop',w*.89,d*.052,h*.958,h,'bronze',.009,0,d*.392)
    for side in (-1,1):
        _rosette('Reading seal',0,side*d*.39,h*.48,h*.12,'patina',.034)


def _cloth(name,x,y,top,w,h,mat):
    verts=[]
    cols,rows=12,5
    for j in range(rows+1):
        t=j/rows
        for i in range(cols+1):
            u=i/cols
            wave=math.sin(u*TAU*2.2+.35*t)
            verts.append((x+(u-.5)*w,y-h*(.019+.022*wave)*(.42+t*.58),
                          top-t*h-.035*h*math.sin(math.pi*u)-.03*h*t*t*math.sin(u*TAU*1.7)))
    faces=[]
    for j in range(rows):
        for i in range(cols):
            k=(cols+1)*j+i
            faces.append((k,k+cols+1,k+cols+2,k+1))
    o=A.mesh(name,verts,faces,mat)
    for p in o.data.polygons:
        p.use_smooth=True


def _dye_cabinet(w,d,h):
    _slab('Cabinet stone feet',w,d,0,h*.096,'granite',.045)
    _slab('Painted toe rail',w*.97,d*.92,h*.096,h*.18,'indigo',.022)
    _slab('Shuttered timber case',w*.95,d*.82,h*.16,h*.89,'timber',.045)
    for side in (-1,1):
        for i in range(4):
            x=(i-1.5)*w*.237
            _slab('Joined door',w*.222,d*.055,h*.22,h*.85,'timber',.022,x,side*d*.42)
            for z in (.24,.77):
                _slab('Framed shutter rail',w*.212,d*.036,h*z,h*(z+.048),'bronze',.012,x,side*d*.455)
            if side<0 and i<3:
                _cloth('Dyed sample | '+str(i),x,-d*.456,h*.782,w*.166,h*.40,('indigo','madder','saffron')[i])
                A.beam('Cloth spindle',(x-w*.098,-d*.47,h*.79),(x+w*.098,-d*.47,h*.79),.028,'brass')
            else:
                A.beam('Door brace',(x-w*.091,side*d*.457,h*.295),
                       (x+w*.094,side*d*.457,h*.748),.023,'bronze')
            A.ellipsoid('Turn button',(x+w*.081,side*d*.473,h*.43),(.043,.033,.043),'brass')
    _slab('Shadow under eave',w*.975,d*.92,h*.87,h*.92,'basalt',.019)
    _slab('Capped shutter ridge',w,d,h*.92,h*.975,'timber',.05)
    _slab('Copper flashing',w*.976,d*.962,h*.975,h,'bronze',.022)


def _weigh_counter(w,d,h):
    _slab('Counter sill',w,d,0,h*.14,'granite',.055)
    _slab('Counter carcass',w*.935,d*.87,h*.11,h*.78,'timber',.026)
    for s in (-1,1):
        for i in (-1,0,1):
            x=i*w*.293
            _slab('Ledger drawer',w*.27,d*.044,h*.29,h*.68,'bronze' if i==0 else 'timber',.019,x,s*d*.445)
            _slab('Stamped drawer escutcheon',w*.097,d*.018,h*.42,h*.58,'patina',.007,x,s*d*.473)
            A.beam('Bail pull',(x-w*.044,s*d*.479,h*.51),(x+w*.044,s*d*.479,h*.51),.022,'brass')
    _slab('Hammered rim',w*.982,d*.98,h*.755,h*.821,'bronze',.026)
    _slab('Polished ledger slab',w,d,h*.821,h*.966,'limestone',.045)
    for i in (-1,1):
        _slab('Weighing runner',w*.06,d*.82,h*.958,h,'brass',.012,i*w*.363,0)
    for i in range(7):
        x=(i-3)*w*.079
        _slab('Stamped weight division',.011,d*(.060 if i%3 else .10),h*.966,h*.977,'bronze',.002,x,-d*.34)


def _bank_parapet(w,d,h):
    _slab('Bank footing',w,d,0,h*.16,'basalt',.04)
    _slab('Bank batter',w*.965,d*.92,h*.15,h*.77,'sandstone',.048)
    for row in range(2):
        n=4-row
        stone=w*.95/n
        for i in range(n):
            x=(i-(n-1)/2)*stone
            for s in (-1,1):
                _slab('Bank ashlar',stone-.023,d*.066,h*(.20+row*.25),h*(.44+row*.25),
                      'granite' if (i+row)%4==0 else 'sandstone',.017,x,s*d*.448)
    _slab('Flood line',w*.98,d*.95,h*.748,h*.813,'patina',.012)
    n=4
    for i in range(n):
        x=(i-(n-1)/2)*w/n
        _slab('Split coping',w/n-.015,d,h*.81,h,'limestone',.052,x,0)
    for i in range(4):
        z=h*(.235+i*.095)
        width=w*(.041 if i%2 else .067)
        _slab('Flood staff cut',width,.024,z,z+.017,'limestone',.003,-w*.305,-d*.486)


def _wheel(name,x,y,z,r,depth,teeth,material):
    # Cog and straight-sided handwheel rims have real open space between spokes.
    count=teeth*4 if teeth else 36
    outer=[]
    for i in range(count):
        a=TAU*i/count
        q=r*(1 if not teeth or i%4 in (1,2) else .89)
        outer.append((x+q*math.cos(a),z+q*math.sin(a)))
    inner=[(x+r*.69*math.cos(TAU*i/count),z+r*.69*math.sin(TAU*i/count)) for i in range(count)]
    verts=[(a,dy,b) for dy in (y-depth/2,y+depth/2) for ring in (outer,inner) for a,b in ring]
    faces=[]
    for i in range(count):
        j=(i+1)%count;n=count
        faces += [(i,j,n+j,n+i),(i,2*n+i,2*n+j,j),(2*n+i,3*n+i,3*n+j,2*n+j),
                  (n+i,n+j,3*n+j,3*n+i)]
    A.mesh(name+' open rim',verts,faces,material)
    for i in range(3):
        a=TAU*i/6
        v=Vector((r*.73*math.cos(a),0,r*.73*math.sin(a)))
        p=Vector((x,y,z))
        A.beam(name+' spoke',p-v,p+v,r*.071,material,8)
    A.cyl(name+' keyed axle',(x,y,z),r*.213,depth*1.4,'brass',12,(math.pi/2,0,0))


def _sluice_gearbox(w,d,h):
    _slab('Machine sill',w,d,0,h*.12,'basalt',.052)
    _slab('Bronze mounting bed',w*.94,d*.91,h*.115,h*.22,'bronze',.035)
    _slab('Oil-tight casting',w*.84,d*.65,h*.20,h*.83,'patina',.10)
    _slab('Rear cast plate',w*.83,d*.035,h*.28,h*.82,'bronze',.046,0,d*.334)
    for side in (-1,1):
        for k in range(4):
            x=(k-1.5)*w*.203
            A.cyl('Cast bolt head',(x,side*d*.361,h*.31),.042,.045,'brass',6,(math.pi/2,0,0))
    _wheel('Reduction gear',-w*.137,-d*.369,h*.51,h*.205,.074,15,'bronze')
    _wheel('Driving pinion',w*.164,-d*.369,h*.55,h*.125,.074,9,'brass')
    _wheel('Operator rim',w*.17,-d*.435,h*.562,h*.205,.068,0,'patina')
    _slab('Cover gasket',w*.89,d*.695,h*.827,h*.855,'basalt',.015)
    _slab('Bevel casting lid',w*.92,d*.72,h*.854,h*.915,'bronze',.064)
    A.cyl('Oil filler',(0,.04,h*.94),h*.06,h*.06,'patina',16)
    A.cyl('Filler cap',(0,.04,h*.981),h*.073,h*.038,'brass',12)
    for i in (-1,0,1):
        _slab('Rear heat fin',w*.67,d*.07,h*(.47+i*.092),h*(.50+i*.092),'patina',.013,0,d*.375)


def build_cover(slug, obj):
    """Build on the atlas footprint, with the furnished face along the long side."""
    builders={'bell-screen':_bell_screen,'stone-lectern':_stone_lectern,'dye-cabinet':_dye_cabinet,
              'weigh-counter':_weigh_counter,'bank-parapet':_bank_parapet,'sluice-gearbox':_sluice_gearbox}
    width,depth=obj['size']
    before=set(bpy.context.collection.objects)
    builders[slug](max(width,depth),min(width,depth),obj['height'])
    if depth>width:
        _rotate_ninety(set(bpy.context.collection.objects)-before)


def _temple_bell(name,x,y,z,scale):
    # z is the bottom of the bell mouth. The return profile leaves it hollow.
    profile=[(0,.47),(.04,.48),(.095,.45),(.15,.39),(.30,.34),(.49,.29),(.58,.24),
             (.64,.19),(.70,.18),(.72,.12),(.72,.08),(.66,.08),(.61,.13),(.57,.19),
             (.46,.235),(.27,.295),(.12,.36),(.046,.405),(0,.425),(0,.47)]
    _turn(name+' resonator',(x,y,z),[(h*scale,r*scale) for h,r in profile],'bronze',48)
    for h,r in ((.053,.467),(.14,.393),(.57,.246)):
        _band(name+' cast bead',x,y,z+h*scale,r*scale,.021*scale,'brass')
    A.beam(name+' striker stem',(x,y,z+.44*scale),(x,y,z+.014*scale),.036*scale,'basalt')
    A.ellipsoid(name+' striker',(x,y,z+.006*scale),(.082*scale,.082*scale,.102*scale),'brass')


def _bell_comb():
    # Build three rising fluted blades along the longitudinal bank of the Ghat,
    # with the narrow return against the adjacent Bell Screen.
    _slab('Comb footing',4.72,1.10,0,.18,'granite',.055)
    _slab('Waterline seat',4.52,1.01,.18,.31,'limestone',.036)
    for i,(x,h) in enumerate(((-1.52,3.11),(-.03,3.92),(1.45,3.36))):
        base=.31
        stations=[(0.,-.18,.93),(.10,-.20,.88),(.29,-.24,.67),(.52,-.22,.46),
                  (.70,-.12,.43),(.83,.06,.36),(.93,.30,.25),(1.,.51,.045)]
        left=[(x+c-w/2,base+h*z) for z,c,w in stations]
        right=[(x+c+w/2,base+h*z) for z,c,w in stations]
        _profile(f'Carved ghat rib {i+1}',left+right[::-1],-.29,.29,'sandstone')
        for side in (-1,1):
            for f in (.24,.68):
                line=[(x+c+(f-.50)*w,side*.296,base+h*z) for z,c,w in stations[1:-1]]
                _sweep('Continuous cut moulding',line,.026,'limestone',7)
        _slab('Comb rib foot',1.11,.85,.31,.49,'limestone',.04,x-.15)
        hook_x=x+.42
        high=base+h*.755
        A.beam('Bell timber corbel',(x-.07,0,high-.04),(hook_x+.04,0,high),.077,'timber',10)
        A.beam('Suspension eye',(hook_x,0,high),(hook_x,0,high-.27),.026,'brass',10)
        scale=.97 if i==1 else .79
        _temple_bell('Ghat bell '+str(i+1),hook_x,0,high-.27-.72*scale,scale)


def _label(name,text,side,z,y,height,mat):
    # Bake the built-in Blender font once, keeping the physical signage portable.
    curve=bpy.data.curves.new('Lettering master','FONT')
    curve.body=text
    curve.align_x='CENTER'; curve.align_y='CENTER'
    curve.size=height; curve.extrude=.0025; curve.resolution_u=2
    temp=bpy.data.objects.new('Lettering master',curve)
    bpy.context.collection.objects.link(temp)
    try:
        graph=bpy.context.evaluated_depsgraph_get()
        evaluated=temp.evaluated_get(graph)
        lettering=evaluated.to_mesh()
        # A front observer sees +X right, a back observer sees -X right.
        verts=[(-side*v.co.x,y+side*v.co.z,z+v.co.y) for v in lettering.vertices]
        faces=[p.vertices[:] for p in lettering.polygons]
        A.mesh(name,verts,faces,mat)
        evaluated.to_mesh_clear()
    finally:
        bpy.data.objects.remove(temp,do_unlink=True)
        bpy.data.curves.remove(curve)


def _fold_lintels(variant):
    tokens=variant.lower().replace('_','-').split('-')
    south=tokens[0]=='south'
    if tokens[0] not in ('south','north'):
        raise ValueError('Choose the south or north fold')
    direction='SOUTH' if south else 'NORTH'
    destination=direction+(' TEMPLE' if 'pyramid' in tokens else ' PYRAMID')
    for sign in (-1,1):
        x=sign*2.85
        _slab('Fold post shoe',.70,1.04,0,.20,'granite',.038,x)
        _slab('Fold post lower mould',.66,.98,.20,.38,'limestone',.037,x)
        _slab('Fold post',.58,.87,.36,2.77,'sandstone',.052,x)
        for side in (-1,1):
            _slab('Directional reveal',.067,.041,.49,2.62,'patina',.009,x-sign*.127,side*.444)
            _slab('Jamb reveal',.032,.037,.49,2.62,'limestone',.006,x-sign*.20,side*.443)
        _slab('Corbel capital',.70,1.02,2.77,2.98,'limestone',.033,x)
    _slab('Open passage transom',6.48,1.03,2.98,3.27,'sandstone',.051)
    _slab('Bronze lintel return',6.57,1.08,3.255,3.35,'bronze',.021)
    _slab('Fold sign fascia',6.32,.92,3.35,3.82,'sandstone',.041)
    _slab('Shelter drip mould',6.67,1.12,3.81,3.96,'limestone',.037)
    for side in (-1,1):
        _slab('Destination tablet',3.15,.045,3.39,3.77,'basalt',.021,0,side*.474)
        y=side*.500
        _label('Cast letters | '+destination,destination,side,3.58,y,.205,'limestone')
        x=-side*2.07
        if south:
            _sweep('South V cut',[(x-.25,y,3.70),(x,y,3.46),(x+.25,y,3.70)],.038,'brass',8)
        else:
            for h in (3.505,3.645):
                A.beam('North paired bar',(x-.245,y,h),(x+.245,y,h),.035,'brass',8)


def _weighbeam():
    # Legs straddle the measured 3.2 m market counter. The longer left arm faces the Sluice.
    for side in (-1,1):
        x=side*1.80
        _slab('Scale pier foot',.32,.55,0,.20,'granite',.04,x)
        _slab('Scale pier shoe',.27,.43,.18,.42,'bronze',.022,x)
        _slab('Balance post',.21,.32,.36,2.87,'timber',.028,x)
        _slab('Pier copper binding',.245,.365,2.55,2.66,'patina',.012,x)
        A.beam('Scale knee brace',(x,0,2.31),(side*1.25,0,2.86),.075,'timber',6)
    _slab('Market beam',4.06,.48,2.82,3.04,'timber',.045)
    _slab('Lintel flashing',4.14,.52,3.03,3.10,'bronze',.018)
    _slab('Balance compression block',.38,.40,2.67,2.85,'brass',.018)
    A.cyl('Weighbeam fulcrum',(0,0,2.57),.155,.32,'patina',20,(math.pi/2,0,0))
    outline=[(-1.63,2.53),(0,2.62),(1.32,2.60),(1.34,2.53),(0,2.48),(-1.57,2.46)]
    _profile('Steelyard arm',outline,-.10,.10,'bronze')
    for x,bottom,r in ((-1.29,1.38,.315),(1.16,1.43,.285)):
        _turn('Beaten scale pan',(x,0,bottom),[(0,0),(.012,r*.26),(.055,r*.72),(.106,r),(.124,r),
              (.128,r*.97),(.101,r*.91),(.051,r*.60),(.030,0)],'brass',40)
        for i in range(3):
            a=TAU*i/3-math.pi/2
            A.beam('Pan suspension',(x+r*.94*math.cos(a),r*.94*math.sin(a),bottom+.107),
                   (x,0,2.34),.012,'bronze',8)
        A.beam('Pan suspension eye',(x,0,2.34),(x,0,2.54),.023,'brass',10)
    for x in (-.68,-.52,-.36,-.20,.24,.40,.56,.72):
        A.beam('Steelyard measure',(x,-.108,2.509),(x,-.108,2.587),.009,'limestone',6)
    _profile('Sliding poise',[(.53,2.45),(.73,2.45),(.70,2.63),(.56,2.63)],-.147,.147,'patina')


def _rotate_ninety(items):
    turn=Quaternion((0,0,1),math.pi/2)
    for item in items:
        rot=item.rotation_quaternion.copy() if item.rotation_mode=='QUATERNION' else item.rotation_euler.to_quaternion()
        item.rotation_mode='QUATERNION'
        item.rotation_quaternion=turn @ rot
        item.location=turn @ item.location


def build_artifact(slug, variant='south'):
    if slug=='bell-comb':
        before=set(bpy.context.collection.objects)
        _bell_comb()
        _rotate_ninety(set(bpy.context.collection.objects)-before)
    elif slug=='fold-lintels':
        _fold_lintels(variant)
    elif slug=='weighbeam':
        _weighbeam()
    else:
        raise KeyError(slug)


def _flame(name,x,y,z,r,h,lean,material):
    verts=[]
    rows=[(0.,.46),(.13,.92),(.30,1.),(.52,.64),(.72,.46),(.88,.20),(1.,.015)]
    n=12
    for t,v in rows:
        for i in range(n):
            a=TAU*i/n+t*.80
            q=r*v*(1+.10*math.sin(3*a+t*5))
            verts.append((x+q*math.cos(a)+lean*t*t,y+q*math.sin(a),z+h*t))
    faces=[list(reversed(range(n))),list(range(n*(len(rows)-1),n*len(rows)))]
    for j in range(len(rows)-1):
        for i in range(n):
            k=(i+1)%n
            faces.append((j*n+i,j*n+k,(j+1)*n+k,(j+1)*n+i))
    mesh=A.mesh(name,verts,faces,material)
    for face in mesh.data.polygons:
        face.use_smooth=True


def _ember_vessel():
    _turn('Ember vessel | repoussé belly',(0,0,0),[(0,0),(0,.089),(.008,.104),(.022,.109),
          (.034,.082),(.051,.091),(.074,.121,.002),(.110,.155,.004),(.158,.173,.005),
          (.193,.174,.005),(.224,.164,.004),(.247,.148,.002),(.266,.128),(.281,.102),
          (.302,.09),(.316,.091),(.329,.110),(.344,.109),(.350,.099),(.336,.091),(.321,.081),
          (.278,.090),(.249,.124),(.210,.151),(.166,.155),(.115,.137),(.081,.101),(.063,0)],'bronze',72,12)
    for z,r,h in ((.010,.105,.016),(.056,.096,.009),(.186,.181,.009),(.197,.178,.008),
                  (.266,.130,.008),(.300,.095,.008),(.333,.114,.010)):
        _band('Turned brass band',0,0,z,r,h,'brass')
    for i in range(12):
        a=TAU*i/12
        A.ellipsoid('Repoussé seed',(.166*math.cos(a),.166*math.sin(a),.225),(.008,.008,.016),'brass')
    for side in (-1,1):
        A.ellipsoid('Handle lug',(side*.159,0,.233),(.025,.030,.032),'patina')
    arch=[(.168*math.cos(a),.012*math.sin(a),.232+.211*math.sin(a)) for a in (math.pi*i/32 for i in range(33))]
    _sweep('Swinging fire bail',arch,.010,'brass',10)
    grip=arch[12:21]
    _sweep('Wound carry grip',grip,.014,'timber',10)
    A.cyl('Hot coal bed',(0,0,.313),.083,.012,'ember',36)
    _flame('Long sheltered ember',-.011,0,.316,.038,.112,.022,'ember')
    _flame('Side flame',.022,.015,.317,.022,.065,-.010,'saffron')


def _water_ewer():
    _turn('Varuna ewer | raised body',(0,0,0),[(0,0),(0,.106),(.009,.116),(.021,.116),(.033,.093),
          (.045,.084),(.064,.099),(.092,.128,.002),(.138,.145,.003),(.176,.147,.003),
          (.211,.137,.002),(.246,.117),(.266,.089),(.276,.072),(.302,.058),(.340,.050),
          (.375,.051),(.404,.062),(.428,.078),(.445,.080),(.448,.069),(.427,.064),(.404,.051),
          (.376,.041),(.339,.040),(.30,.048),(.266,.067),(.240,.104),(.190,.127),(.135,.127),(.075,.085),(.063,0)],'patina',72,12)
    for z,r,h in ((.010,.118,.010),(.037,.093,.009),(.214,.139,.008),(.265,.092,.009),
                  (.335,.053,.013),(.403,.065,.009),(.434,.082,.014)):
        _band('Ewer silvered rim',0,0,z,r,h,'brass' if z<.35 else 'limestone')
    spout=_bezier((.111,0,.147),(.208,0,.165),(.172,0,.348),(.265,0,.392),26)
    radii=[.043-.025*(i/26)+.010*(i/26)**7 for i in range(27)]
    _sweep('Hollow rising spout',spout,radii,'patina',16,.72)
    lip=spout[-3:]
    _sweep('Rolled spout rim',lip,[.027,.029,.030],'brass',16,.72)
    handle=_bezier((-.065,0,.391),(-.218,0,.468),(-.283,0,.183),(-.131,0,.156),30)
    _sweep('Raised loop handle',handle,[.015+.006*math.sin(math.pi*i/30) for i in range(31)],'brass',12)
    for x,z,r in ((-.061,.39,.026),(-.128,.156,.033),(.103,.145,.044)):
        A.ellipsoid('Soldered joint',(x,0,z),(r,r*.90,r*.77),'bronze')
    A.cyl('Water below the lip',(0,0,.430),.064,.003,'water',40)
    for i in range(8):
        a=TAU*i/8
        A.ellipsoid('Hammered water bead',(.135*math.cos(a),.135*math.sin(a),.213),(.008,.008,.012),'brass')


def build_rite(slug):
    {'ember-vessel':_ember_vessel,'water-ewer':_water_ewer}[slug]()
