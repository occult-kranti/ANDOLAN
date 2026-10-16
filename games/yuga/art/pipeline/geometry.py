"""Original mesh construction for Yuga costumes, ornaments, hair and weapons."""
import math
import bpy
from mathutils import Vector
from anatomy import bind

TAU = math.tau


class Sculpt:
    def __init__(self, rig, body, weights, tree):
        self.rig, self.body, self.weights, self.tree = rig, body, weights, tree
        self.objects = [body]

    def mesh(self, name, vertices, faces, material, bone=None, uv=None, weights=None):
        mesh = bpy.data.meshes.new(name); mesh.from_pydata(vertices, [], faces); mesh.update()
        obj = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(obj)
        mesh.materials.append(material)
        layer = mesh.uv_layers.new(name='UVMap')
        for polygon in mesh.polygons:
            polygon.use_smooth = True
            for li in polygon.loop_indices:
                index = mesh.loops[li].vertex_index
                layer.data[li].uv = uv[index] if uv else (vertices[index][0] * 2, vertices[index][2] * 2)
        if weights is None:
            weights = [[(bone, 1)] for _ in vertices] if bone else [self.weights[self.tree.find(Vector(v))[1]] for v in vertices]
        bind(obj, self.rig, weights); self.objects.append(obj)
        return obj

    def tube(self, name, points, radius, material, bone=None, sides=7, taper=None):
        points = [Vector(p) for p in points]; vertices, faces, uv = [], [], []
        for i, p in enumerate(points):
            tangent = points[min(i+1, len(points)-1)] - points[max(0, i-1)]
            tangent.normalize(); a = tangent.cross(Vector((0, 1, 0)))
            if a.length < .01: a = tangent.cross(Vector((1, 0, 0)))
            a.normalize(); b = tangent.cross(a).normalized()
            r = radius * (taper(i / (len(points)-1)) if taper else 1)
            for j in range(sides):
                angle = TAU*j/sides; vertices.append(p + r*(math.cos(angle)*a+math.sin(angle)*b)); uv.append((j/sides, i/(len(points)-1)))
        for i in range(len(points)-1):
            for j in range(sides):
                a=i*sides+j; b=i*sides+(j+1)%sides
                faces.append((a,b,b+sides,a+sides))
        faces.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))])
        return self.mesh(name, vertices, faces, material, bone, uv)

    def ellipsoid(self, name, centre, scale, material, bone='head', segments=18, rings=12, ridge=0):
        vertices, faces, uv = [], [], []
        for i in range(rings+1):
            p = math.pi*i/rings
            for j in range(segments):
                t=TAU*j/segments; r=1+ridge*math.cos(8*t)*math.sin(p)
                vertices.append((centre[0]+scale[0]*math.sin(p)*math.cos(t)*r,centre[1]+scale[1]*math.sin(p)*math.sin(t)*r,centre[2]+scale[2]*math.cos(p)))
                uv.append((j/segments,i/rings))
        for i in range(rings):
            for j in range(segments):
                a=i*segments+j;b=i*segments+(j+1)%segments;faces.append((a,b,b+segments,a+segments))
        return self.mesh(name,vertices,faces,material,bone,uv)

    def ring(self, name, centre, radii, material, bone=None, thickness=.006, segments=40, wave=0):
        pts=[]
        for j in range(segments+1):
            t=TAU*j/segments;pts.append((centre[0]+radii[0]*math.cos(t),centre[1]+radii[1]*math.sin(t),centre[2]+wave*math.cos(6*t)))
        return self.tube(name,pts,thickness,material,bone)

    def fitted(self, name, material, predicate, offset=.012, neckline=None):
        mesh=self.body.data; selected=[p for p in mesh.polygons if predicate(p.center)]
        used=sorted(set(v for p in selected for v in p.vertices)); mapping={old:i for i,old in enumerate(used)}
        vertices=[mesh.vertices[i].co+mesh.vertices[i].normal*offset for i in used]
        faces=[[mapping[i] for i in p.vertices] for p in selected]
        if neckline is not None:
            edges={}
            for face in faces:
                for a,b in zip(face,face[1:]+face[:1]):
                    edge=tuple(sorted((a,b)));edges[edge]=edges.get(edge,0)+1
            boundary={v for edge,count in edges.items() if count==1 for v in edge}
            for i in boundary:
                if vertices[i].z>neckline-.065:vertices[i].z=neckline
        return self.mesh(name,vertices,faces,material,weights=[self.weights[i] for i in used])

    def cloth(self, name, point, material, rows=20, columns=48, wrap=False, bone=None):
        vertices,uv,faces=[],[],[]
        count=columns if wrap else columns+1
        for i in range(rows+1):
            for j in range(count): vertices.append(point(j/columns,i/rows));uv.append((j/columns*2,i/rows*2))
        for i in range(rows):
            for j in range(columns):
                a=i*count+j;b=i*count+(j+1)%count
                faces.append((a,b,b+count,a+count))
        return self.mesh(name,vertices,faces,material,bone,uv)


def costume(s, h, c, materials):
    cloth, light, gold, gem = [materials[k] for k in ('cloth','ivory','gold','gem')]
    width=c.get('width',1); female=c['sex']=='female'
    long_robe=c['id'] in ('sita','draupadi','ulupi')
    # Fitted panels retain the anatomical topology and native skin weights.
    s.fitted('Tailored woven bodice',cloth,lambda p:h*.54<p.z<h*.82 and abs(p.x)<h*.135, .013,neckline=h*.82)
    s.fitted('Gathered loose trousers',light,lambda p:h*.09<p.z<h*.52,.028)
    # Continuous circular pleating: varying fold amplitude and asymmetrical hem.
    def skirt(u,v):
        a=TAU*u; r=(.155+.12*v)*width
        fold=(.009+.016*v)*math.cos(a*18+v*.45)
        x=(r+fold)*math.cos(a); y=(.127+.065*v+fold)*math.sin(a)+.015
        z=h*(.565-(.43 if long_robe else .30)*v)+.065*v*abs(math.cos(a))+.008*math.cos(a*9)*v
        return (x,y,z)
    s.cloth('Sculpted pleated dhoti',skirt,light if c.get('ivory_skirt',True) else cloth,wrap=True,columns=72,rows=18)
    for v in (0,.93,1):
        s.tube('Dhoti embroidered border',[skirt(j/96,v) for j in range(97)],.0045 if v<1 else .006,gold)
    # Layered front tabard with actual vertical folds, separate from trousers.
    def panel(u,v):
        return ((u-.5)*(.24-.055*v)*width,-.18-.11*v-.012*math.cos(u*TAU*5),h*(.56-(.40 if long_robe else .27)*v)+.025*math.cos(u*TAU))
    s.cloth('Brocade overfold',panel,cloth,rows=18,columns=24)
    for u in (0,1):s.tube('Tabard gold piping',[panel(u,j/20) for j in range(21)],.005,gold)
    # Woven diagonal sash follows the front torso; a broad shoulder drape sits behind it.
    def sash(u,v):
        x=(.14-.28*v)*width+(u-.5)*.115
        return (x,-.185-.025*math.sin(math.pi*v)-.006*math.cos(u*TAU*4),h*(.81-.26*v))
    s.cloth('Folded diagonal silk sash',sash,cloth,rows=24,columns=12)
    for u in (0,1):s.tube('Sash woven gold edge',[sash(u,j/24) for j in range(25)],.004,gold)
    def mantle(u,v):
        x=(u-.5)*(.38+.14*v)*width
        return (x,.09+.13*v+.018*math.cos(u*TAU*8)*(v+.3),h*(.805-.47*v)+.035*math.cos(u*TAU))
    s.cloth('Layered silk mantle',mantle,cloth,rows=24,columns=32,bone='spine02')
    for u in (0,1):s.tube('Mantle gold border',[mantle(u,j/24) for j in range(25)],.007,gold,'spine02')
    s.tube('Mantle scalloped hem',[mantle(j/48,1) for j in range(49)],.006,gold,'spine02')
    for z,r in ((h*.555,.151),(h*.577,.146)):
        s.ring('Chased gold belt',(0,.012,z),(r*width,.165),gold,'spine05',.009)
    s.ellipsoid('Belt lotus buckle',(0,-.16,h*.566),(.037,.018,.035),gold,'spine05',20,12,ridge=.12)
    s.ellipsoid('Belt cut gemstone',(0,-.179,h*.568),(.014,.007,.019),gem,'spine05',10,8)
    # Shoulder plates are curved shells following the clavicle, not boxes.
    for side in ('L','R'):
        b=s.rig.data.bones['upperarm01.'+side];pos=b.head_local
        sign=1 if side=='L' else -1
        centre=pos+Vector((sign*.01,0,.015))
        s.ellipsoid('Repousse shoulder petal '+side,centre,(.088,.088,.043),gold,'upperarm01.'+side,24,12,ridge=.08)
        for k in range(3):
            s.tube('Shoulder engraved arc',[(centre.x+sign*(j/20-.5)*.13,centre.y-.079+.02*math.sin(j/20*math.pi),centre.z+.015+k*.009+.014*math.sin(j/20*math.pi)) for j in range(21)],.0025,light,'upperarm01.'+side,sides=5)
        # Cuffs use actual bone axes, and keep the bend unobstructed.
        fore=s.rig.data.bones['lowerarm02.'+side];axis=(fore.tail_local-fore.head_local).normalized()
        a=axis.cross(Vector((0,1,0))).normalized();d=axis.cross(a).normalized();mid=fore.head_local.lerp(fore.tail_local,.5)
        for end in (-.038,.038):
            pts=[mid+axis*end+.046*(a*math.cos(TAU*j/32)+d*math.sin(TAU*j/32)) for j in range(33)]
            s.tube('Ornate wrist cuff',pts,.008,gold,'lowerarm02.'+side)
        for j in range(8):
            theta=TAU*j/8;start=mid-axis*.038+.045*(a*math.cos(theta)+d*math.sin(theta));end=start+axis*.076
            s.tube('Cuff filigree ribs',[start,start.lerp(end,.5)+a*.004,end],.004,gold,'lowerarm02.'+side)
        foot=s.rig.data.bones['foot.'+side];fp=foot.head_local
        s.ellipsoid('Layered leather sandal '+side,(fp.x,fp.y-.045,.026),(.058,.112,.015),materials['hair'],'foot.'+side,24,8)
        s.ellipsoid('Gold-edged sandal sole '+side,(fp.x,fp.y-.045,.016),(.061,.114,.008),gold,'foot.'+side,24,6)
        for y in (-.075,-.025):
            s.tube('Arched sandal strap',[(fp.x+(j/16-.5)*.105,fp.y+y,.045+.035*math.sin(math.pi*j/16)) for j in range(17)],.009,gold,'foot.'+side,sides=6)
        s.ring('Ankle silk gather',(fp.x,fp.y+.008,h*.105),(.058,.055),gold,'lowerleg02.'+side,.008,segments=24)
    # Collar, earrings and chest ornament provide detail readable at portrait range.
    s.ring('Collar torc',(0,-.025,h*.831),(.070,.095),gold,'neck01',.006)
    for length in (.035,.06):
        s.tube('Gold chest chain',[(.10*math.cos(math.pi*j/32),-.19-.018*math.sin(math.pi*j/32),h*.81-length*math.sin(math.pi*j/32)) for j in range(33)],.0035,gold)
    for side in (-1,1):
        s.ellipsoid('Earring',(side*.078,-.061,h*.89),(.012,.009,.024),gold,'head',12,10)
        s.ellipsoid('Earring stone',(side*.078,-.07,h*.89),(.005,.003,.011),gem,'head',10,8)
    # Hero-specific silhouettes and surfaces, beyond recolouring a common outfit.
    if c['id'] in ('chitrangada','duryodhana','karna','subhadra'):
        s.fitted('Curved chased chest cuirass',gold,lambda p:h*.62<p.z<h*.79 and abs(p.x)<h*.12 and p.y<-.015,.025)
        for i in range(3):
            z=h*(.63+.045*i)
            s.tube('Cuirass sculpted chevron',[(-.13,-.18,z+.025),(0,-.22,z),(.13,-.18,z+.025)],.006,materials['ivory'])
    if c['id']=='ulupi':
        # Original overlapping river-scale trim and serpent shoulder curves.
        for i in range(6):
            for j in range(5):
                x=(j-2)*.034+(i%2)*.016;z=h*.72-i*.031
                s.tube('Naga scale embroidery',[(x+.018*math.cos(math.pi*k/10),-.225,z-.015*math.sin(math.pi*k/10)) for k in range(11)],.0028,gold)
        for sign in (-1,1):
            pts=[(sign*(.14+.035*math.sin(j/24*math.pi)), -.08-.05*math.sin(j/24*math.pi),h*.78+j/24*.15) for j in range(25)]
            s.tube('Serpentine shoulder crest',pts,.009,gold,'spine01',sides=8)
    if c['id']=='hidimbi':
        for sign in (-1,1):
            for i in range(5):
                x=sign*(.10+.025*i);z=h*.79-.035*i
                s.ellipsoid('Layered forest mantle leaf',(x,.045,z),(.045,.014,.105),cloth,'spine01',10,10,ridge=.12)


def face_and_hair(s,h,c,m):
    skin,hair,gold,gem=[m[k] for k in ('skin','hair','gold','gem')]
    scale=h/1.85; face=c.get('face_width',1)
    # Visible eyeballs sit inside the anatomical eyelids, with small iris and pupil surfaces.
    for side in ('L','R'):
        eye=s.rig.data.bones['eye.'+side].head_local+Vector((0,0,-.001*scale))
        s.ellipsoid('Sclera '+side,eye,(.022*scale,.023*scale,.020*scale),m['eyes'],'eye.'+side,20,14)
        s.ellipsoid('Amber iris '+side,eye+Vector((0,-.022*scale,0)),(.0072*scale,.0016*scale,.0072*scale),m['iris'],'eye.'+side,16,10)
        s.ellipsoid('Pupil '+side,eye+Vector((0,-.0235*scale,0)),(.0033*scale,.0008*scale,.004*scale),hair,'eye.'+side,12,8)
        # Sculpted eyelid surface masks the sphere to an almond-shaped opening.
        # The outer edge sinks into the continuous source face instead of
        # exposing a complete round eyeball on top of it.
        def lid(u,v):
            a=TAU*u;dx=(.017+.010*v)*scale*math.cos(a);dz=(.0065+.019*v)*scale*math.sin(a)
            y=eye.y-math.sqrt(max(.000015*scale*scale,(.024*scale)**2-dx*dx-dz*dz))-.0006*scale
            return (eye.x+dx,y,eye.z+dz)
        s.cloth('Sculpted eyelid '+side,lid,skin,rows=5,columns=32,wrap=True,bone='head')
        sign=1 if side=='L' else -1
        s.tube('Sculpted eyebrow '+side,[(eye.x+sign*(j/12-.5)*.042,eye.y-.030,eye.z+.021+.004*math.sin(j/12*math.pi)) for j in range(13)],.004*scale,hair,'head',sides=6,taper=lambda t:.4+.6*math.sin(math.pi*t))
    # Hair cap with a scalloped irregular hairline and longitudinal sculpted grooves.
    centre=(0,-.034*scale,h*.948);rx=.102*face*scale;ry=.141*scale;rz=.12*scale
    def cap(u,v):
        a=TAU*u;p=.02+v*(1.60+.18*math.sin(a))
        ridge=1+.022*math.cos(a*34+v*4)
        return (rx*math.sin(p)*math.cos(a)*ridge,centre[1]+ry*math.sin(p)*math.sin(a)*ridge,centre[2]+rz*math.cos(p))
    s.cloth('Sculpted swept hair cap',cap,hair,rows=18,columns=64,wrap=True,bone='head')
    for i in range(18):
        u=i/18;s.tube('Swept hair strand',[cap(u+.015*math.sin(v*math.pi),v) for v in [j/20 for j in range(3,21)]],.0025,hair,'head',sides=5)
    style=c.get('hair','knot')
    if style in ('braid','long'):
        for i in range(3):
            pts=[]
            for j in range(37):
                t=j/36;a=t*TAU*4+i*TAU/3
                pts.append((.017*math.cos(a),.065*scale+.026*math.sin(a)+t*.07,h*.93-t*.36))
            s.tube('Interwoven long braid',pts,.021*scale,hair,'head',sides=8,taper=lambda t:1-.65*t)
        for t in (.15,.45,.75):s.ring('Braid binding',(0,.065*scale+t*.07,h*.93-t*.36),(.024,.024),gold,'head',.003,segments=20)
    else:
        for j in range(4):
            pts=[(.032*math.cos(t*TAU),.018+.032*math.sin(t*TAU),h+.015+j*.01+.004*math.sin(t*TAU*3)) for t in [i/32 for i in range(33)]]
            s.tube('Coiled topknot',pts,.018,hair,'head',sides=8)
    # Narrow circlet, asymmetric lotus crest, and small faceted inset jewels.
    s.ring('Embossed crown circlet',(0,-.033*scale,h*.957),(.103*face*scale,.143*scale),gold,'head',.008,segments=56,wave=.004)
    crown=c.get('crown',.065)*scale
    for i in range(-3,4):
        x=i*.020*scale;z=h*.947+(1-abs(i)/4)*crown
        y=-.176*scale+.7*x*x
        s.ellipsoid('Lotus diadem leaf',(x,y,z),(.012*scale,.008*scale,(.024+.008*(3-abs(i)))*scale),gold,'head',10,10,ridge=.08)
        if i%2==0:s.ellipsoid('Crown faceted jewel',(x,y-.008,z),(.006,.004,.012),gem,'head',8,6)
    # Forehead tilaka is modeled above the face surface and stays attached to the head.
    s.tube('Forehead tilaka',[(0,-.167*scale,h*.928),(0,-.168*scale,h*.947)],.003,m['ivory'],'head',sides=6)
    s.tube('Natural upper lip contour',[(j*.0025,-.171*scale+.008*abs(j)/10,h*.891+.0015*math.cos(j*.3)) for j in range(-10,11)],.0018,m['lips'],'head',sides=5,taper=lambda t:.4+.6*math.sin(math.pi*t))
    if c.get('beard'):
        s.ellipsoid('Sculpted jaw beard',(0,-.089*scale,h*.875),(.06*face*scale,.04*scale,.043*scale),hair,'head',24,16,ridge=.07)
        for side in (-1,1):s.tube('Swept moustache',[(side*j*.0025,-.135*scale+.015*(j/16),h*.893-.008*math.sin(j/16*math.pi)) for j in range(17)],.005,hair,'head',sides=6,taper=lambda t:1-.7*t)
    if c['id']=='hanuman':
        # Original stylized simian facial volume, brow ridge and curved tail.
        s.ellipsoid('Simian muzzle',(0,-.175*scale,h*.89),(.060*scale,.065*scale,.040*scale),skin,'head',24,16)
        s.ellipsoid('Simian broad nose',(0,-.229*scale,h*.906),(.025*scale,.011*scale,.012*scale),skin,'head',16,10)
        for sign in (-1,1):
            s.ellipsoid('Nostril',(sign*.011*scale,-.240*scale,h*.904),(.004*scale,.002*scale,.003*scale),hair,'head',10,8)
            s.ellipsoid('Fur cheek ridge',(sign*.070*scale,-.132*scale,h*.907),(.030*scale,.037*scale,.065*scale),m['fur'],'head',16,12,ridge=.12)
            s.ellipsoid('Simian rounded ear',(sign*.095*scale,-.027*scale,h*.92),(.029*scale,.018*scale,.039*scale),m['fur'],'head',16,12)
            s.ellipsoid('Simian inner ear',(sign*.102*scale,-.044*scale,h*.92),(.019*scale,.007*scale,.026*scale),skin,'head',16,10)
        s.tube('Simian mouth line',[(j*.003,-.236*scale+.012*abs(j)/10,h*.883+.002*math.cos(j*.2)) for j in range(-10,11)],.002,m['lips'],'head',sides=6)
        points=[]
        for j in range(65):
            t=j/64;points.append((-.18*math.sin(t*math.pi*1.4),.12+.52*math.sin(t*math.pi*.8),h*.52+.45*t-.16*math.sin(t*TAU)))
        s.tube('Curved simian tail',points,.024,m['fur'],'spine05',sides=10,taper=lambda t:1-.72*t)
    if c['id']=='karna':
        for i in range(12):
            a=TAU*i/12;centre=(.13*math.cos(a),.025,h*.94+.13*math.sin(a))
            s.ellipsoid('Solar crest ray',centre,(.013,.010,.033),gold,'head',10,8)
    if c['id']=='ulupi':
        for sign in (-1,1):
            points=[(sign*(.065+.02*math.sin(j/24*TAU)),-.15,h*.96+j/24*.12) for j in range(25)]
            s.tube('Twin river-serpent diadem',points,.009,gold,'head',sides=8)
            s.ellipsoid('Serpent crown gem',points[-1],(.013,.010,.018),gem,'head',10,8)


def weapon(s,h,c,m):
    bone=s.rig.data.bones['wrist.R']; origin=bone.head_local
    # A declared rest-space frame is shared with animation authoring.
    rotation=bone.matrix_local.to_3x3()
    scale=h/1.85
    def p(x,y,z):return origin+rotation@(Vector((z,y,-x))+Vector((0,.105,.025)))*scale
    gold,wood,gem=m['gold'],m['hair'],m['gem'];kind=c['weapon']
    if kind=='bow':
        pts=[p(0,-.10*(math.cos(TAU*j/40)+1),(j/40-.5)*1.15) for j in range(41)]
        s.tube('Sculpted recurved bow',pts,.021,gold,'wrist.R',sides=10,taper=lambda t:.5+.5*math.sin(math.pi*t))
        s.tube('Bow dark inlay',[p(.012,-.10*(math.cos(TAU*j/40)+1),(j/40-.5)*1.15) for j in range(41)],.005,wood,'wrist.R')
        string=s.tube('Skinned bow string',[pts[0],p(0,-.205,0),pts[-1]],.0017,m['ivory'],'wrist.R',sides=5)
        string.vertex_groups['wrist.R'].remove(list(range(5,10)))
        string.vertex_groups.new(name='bowstring').add(list(range(5,10)),1,'REPLACE')
        for z in (-.47,-.32,.32,.47):s.ellipsoid('Bow gemstone',p(.014,-.10*(math.cos(TAU*(z/1.15+.5))+1),z),(.014,.012,.025),gem,'wrist.R',10,8)
    elif kind=='chakram':
        s.tube('Chakram central hand grip',[p(0,0,-.22),p(0,0,.22)],.024,wood,'wrist.R',sides=10)
        for z in (-.08,-.04,0,.04,.08):
            s.tube('Chakram grip gold binding',[p(.027*math.cos(TAU*j/20),.027*math.sin(TAU*j/20),z) for j in range(21)],.004,gold,'wrist.R',sides=5)
        for radius in (.25,.22):s.tube('Engraved chakram',[p(radius*math.cos(TAU*j/64),0,radius*math.sin(TAU*j/64)) for j in range(65)],.018,gold,'wrist.R',sides=8)
        for j in range(12):
            a=TAU*j/12;s.tube('Chakram radial filigree',[p(.21*math.cos(a),0,.21*math.sin(a)),p(.27*math.cos(a+.07),0,.27*math.sin(a+.07))],.008,gem,'wrist.R')
    else:
        length=.98 if kind=='mace' else 1.5
        s.tube('Carved weapon haft',[p(0,0,-length*.35),p(0,0,length*.65)],.019,wood,'wrist.R',sides=10)
        for z in (-.30,-.1,.12,.33,.50):
            s.tube('Haft gold grip rings',[p(.024*math.cos(TAU*j/20),.024*math.sin(TAU*j/20),z) for j in range(21)],.004,gold,'wrist.R',sides=5)
        end=length*.65
        if kind=='mace':
            s.ellipsoid('Fluted sculpted mace head',p(0,0,end),(.115,.115,.145),gold,'wrist.R',32,20,ridge=.09)
            for j in range(8):
                a=TAU*j/8;s.ellipsoid('Mace inset stone',p(.106*math.cos(a),.106*math.sin(a),end),(.017,.017,.031),gem,'wrist.R',10,8)
        else:
            vertices=[p(0,0,end+.29),p(-.072,0,end+.07),p(0,-.018,end),p(.072,0,end+.07),p(0,.018,end)]
            s.mesh('Faceted lotus spear blade',vertices,[(0,1,2),(0,2,3),(0,3,4),(0,4,1),(1,4,2),(2,4,3)],gem,'wrist.R')
            s.tube('Leaf-shaped golden blade frame',[vertices[i] for i in (2,1,0,3,2)],.009,gold,'wrist.R')
            if kind=='staff':
                s.tube('Lotus staff halo',[p(.14*math.cos(TAU*j/48),0,end+.1+.18*math.sin(TAU*j/48)) for j in range(49)],.012,gold,'wrist.R',sides=8)
