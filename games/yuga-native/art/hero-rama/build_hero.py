"""Rama hero candidate: original smooth anatomy, garments, swept hair and goldwork.
Blender 4.3+: blender -b -t 2 --python .../build_hero.py -- --output DIR [--preview]
Preserves imported skeleton/action conventions. No commercial assets or image-to-mesh claims.
"""
from pathlib import Path
import sys,math,json,hashlib,struct,time
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PIPE=ROOT/'games/yuga/art/pipeline'
sys.path.insert(0,str(PIPE))
from anatomy import build_anatomy,bind
from geometry import Sculpt
sys.path.insert(0,str(HERE))
from rebind_dhoti import apply_front_drape_binding
TAU=math.tau
ARGS=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=Path(ARGS[ARGS.index('--output')+1]) if '--output' in ARGS else HERE
TEX=HERE/'textures'; TEX.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
BASE=ROOT/'games/yuga-native/art/production/reconstruction-rama.blend'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def activate(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o

def image_file(name,rgb,data=False):
    n=rgb.shape[0];arr=np.ones((n,n,4),dtype=np.float32);arr[:,:,:3]=np.clip(rgb,0,1)
    img=bpy.data.images.new(name,width=n,height=n)
    if data:img.colorspace_settings.name='Non-Color'
    img.pixels.foreach_set(arr.ravel());img.filepath_raw=str(TEX/(name+'.png'));img.file_format='PNG';img.save();img.pack();return img

def material(name,color,rough=.5,metal=0,kind=None):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if kind in ('cloth','ivory'):p.inputs['Sheen Weight'].default_value=.18
    if kind=='hair':p.inputs['Specular IOR Level'].default_value=.25
    if kind=='skin':p.inputs['Subsurface Weight'].default_value=.045;p.inputs['Subsurface Radius'].default_value=(1,.4,.2)
    if not kind:return m
    n=1024 if kind in ('cloth','ivory','brocade') else 512
    y,x=np.mgrid[0:n,0:n]/n
    weave=np.sin(x*TAU*181)*np.cos(y*TAU*173);grain=np.sin((x*131+y*217)*TAU)*np.cos((x*199-y*127)*TAU)
    h=.5+.04*weave+.018*grain;variation=.97+.024*weave+.012*grain
    al=np.stack([variation*c for c in color],axis=2)
    if kind=='brocade':
        # Original continuous lotus/vine jacquard; no sampled external imagery.
        u=(x*5)%1-.5;v=(y*5)%1-.5;r=np.hypot(u,v);a=np.arctan2(v,u)
        line=np.exp(-((r-(.19+.065*np.cos(6*a)))/.012)**2)
        vine=np.exp(-((u-.28*np.sin(v*TAU))/.014)**2)
        diamond=np.exp(-((np.abs(u)+np.abs(v)-.47)/.009)**2)
        mask=np.clip(line+.45*vine+.6*diamond,0,1)
        gold=np.array([.58,.335,.075]);al=al*(1-mask[:,:,None]*.92)+gold[None,None,:]*mask[:,:,None]*.92
        h+=mask*.14
    if kind=='hair':
        strands=np.sin((x*65+.55*np.sin(y*TAU*2))*TAU);h=.5+.15*strands+.02*grain
        al=np.stack([(.85+.1*strands+.03*grain)*c for c in color],axis=2)
    if kind=='gold':h=.5+.035*grain+.07*np.sin((y*25+.18*np.sin(x*TAU*4))*TAU)
    if kind=='skin':h=.5+.015*grain;al=np.stack([(.98+.015*grain)*c for c in color],axis=2)
    gy,gx=np.gradient(h);normal=np.stack([-gx*2,-gy*2,np.ones_like(gx)],axis=2);normal/=np.linalg.norm(normal,axis=2)[:,:,None];normal=normal*.5+.5
    roughmap=np.repeat(np.clip(rough+(h-.5)*.18,0,1)[:,:,None],3,axis=2)
    for suffix,rgb,socket,data in [('basecolor',al,'Base Color',False),('roughness',roughmap,'Roughness',True),('normal',normal,'Normal',True)]:
        im=image_file(name.lower().replace(' ','-')+'-'+suffix,rgb,data)
        node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im
        if socket=='Normal':
            nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.24 if kind=='skin' else .45;m.node_tree.links.new(node.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],p.inputs[socket])
        else:m.node_tree.links.new(node.outputs['Color'],p.inputs[socket])
    return m

def materials():
    return dict(skin=material('Rama warm skin',(.48,.265,.15),.53,kind='skin'),cloth=material('Cobalt handwoven silk',(.018,.085,.29),.44,kind='cloth'),ivory=material('Ivory silk',(.78,.70,.52),.58,kind='ivory'),brocade=material('Cobalt lotus brocade',(.02,.075,.25),.43,kind='brocade'),gold=material('Worked warm gold',(.64,.36,.085),.31,.82,'gold'),darkgold=material('Recessed antique gold',(.24,.115,.025),.42,.8),gem=material('Polished sapphire',(.012,.12,.36),.16,.26),hair=material('Swept black hair',(.010,.006,.004),.62,kind='hair'),hairlight=material('Hair warm ridges',(.026,.016,.01),.42),eye=material('Warm sclera',(.72,.65,.52),.23),iris=material('Deep brown iris',(.055,.025,.01),.27),pupil=material('Pupil',(.003,.002,.001),.18),lips=material('Natural lips',(.16,.040,.027),.56),leather=material('Dark bow leather',(.035,.018,.012),.66))

def solid(o,thick=.002):
    activate(o);m=o.modifiers.new('Tailored thickness','SOLIDIFY');m.thickness=thick;m.offset=0;bpy.ops.object.modifier_move_up(modifier=m.name);bpy.ops.object.modifier_apply(modifier=m.name)

def normalize(o):
    for v in o.data.vertices:
        valid=sorted([(w.group,w.weight) for w in v.groups if w.weight>.00001],key=lambda a:-a[1])[:4]
        total=sum(w for _,w in valid)
        for gi in [g.group for g in v.groups]:o.vertex_groups[gi].remove([v.index])
        for g,w in valid:o.vertex_groups[g].add([v.index],w/total,'REPLACE')

def resample(points,n=33):
    pts=[Vector(p) for p in points];out=[]
    for t in np.linspace(0,len(pts)-1,n):
        i=min(int(t),len(pts)-2);f=t-i;p0=pts[max(0,i-1)];p1=pts[i];p2=pts[i+1];p3=pts[min(len(pts)-1,i+2)]
        out.append(.5*((2*p1)+(-p0+p2)*f+(2*p0-5*p1+4*p2-p3)*f*f+(-p0+3*p1-3*p2+p3)*f*f*f))
    return out

def path(s,name,pts,r,mat,bone=None,sides=8,taper=None):return s.tube(name,resample(pts,33),r,mat,bone,sides=sides,taper=taper)

def petal(s,name,center,axis,width,length,mat,bone,depth=.005,normal=(0,-1,0)):
    # Closed convex leaf with an actual raised midrib, not a scaled sphere.
    c=Vector(center);axis=Vector(axis).normalized();normal=Vector(normal);across=axis.cross(normal).normalized()
    verts=[];uv=[];faces=[];rows=12;cols=8
    for i in range(rows+1):
        v=i/rows;span=math.sin(math.pi*v)**.78
        for j in range(cols+1):
            u=j/cols*2-1;pt=c+axis*((v-.5)*length)+across*(u*width*span)+normal*(depth*(1-u*u)*span)
            verts.append(pt);uv.append((j/cols,v))
    for i in range(rows):
        for j in range(cols):
            a=i*(cols+1)+j;faces.append((a,a+1,a+cols+2,a+cols+1))
    o=s.mesh(name,verts,faces,mat,bone,uv);solid(o,.0015);return o

def lotus(s,c,r,bone,m,gem=True):
    c=Vector(c)
    for i in range(7):
        a=TAU*i/7;axis=Vector((math.sin(a),0,math.cos(a)))
        petal(s,'Repousse lotus petal',c+axis*r*.47,axis,r*.24,r*.95,m['gold'],bone,depth=r*.12)
    s.ellipsoid('Lotus raised bezel',c+Vector((0,-.005,0)),(r*.38,.008,r*.47),m['darkgold'],bone,24,16)
    if gem:s.ellipsoid('Sapphire cabochon',c+Vector((0,-.011,0)),(r*.27,.007,r*.35),m['gem'],bone,24,16)

def chain(s,name,pts,mat,bone,r=.002):
    p=resample(pts,48);s.tube(name,p,r,mat,bone,sides=6)
    for i in range(2,46,3):s.ellipsoid('Chain granule',p[i],(r*1.5,)*3,mat,bone,8,6)

def transfer_weights(target,source):
    tree=KDTree(len(source.data.vertices))
    for v in source.data.vertices:tree.insert(v.co,v.index)
    tree.balance();target.vertex_groups.clear();groups={g.index:target.vertex_groups.new(name=g.name) for g in source.vertex_groups}
    for v in target.data.vertices:
        near=source.data.vertices[tree.find(v.co)[1]]
        for w in near.groups:groups[w.group].add([v.index],w.weight,'REPLACE')

def ribbon_trim(s,fn,m,bone=None,edge=.045,source=None):
    start=len(s.objects)
    for side in (0,1):
        def band(u,v,side=side):return fn((u*edge if side==0 else 1-edge+u*edge),v)
        o=s.cloth('Woven floral gold border',band,m['brocade'],rows=36,columns=4,bone=bone);solid(o,.002)
        s.tube('Fine sewn gold edge',[fn(side,v) for v in np.linspace(0,1,49)],.0025,m['gold'],bone,sides=6)
    if source:
        for obj in s.objects[start:]:transfer_weights(obj,source)

def anatomy(rig,m):
    body,newrig,weights,tree=build_anatomy(ROOT/'games/yuga/art/sources/makehuman','male',1.85,1.,.98)
    body.name='RamaAnatomy';body.parent=rig
    for mod in body.modifiers:
        if mod.type=='ARMATURE':mod.object=rig
    bpy.data.objects.remove(newrig,do_unlink=True)
    # Gentle heroic pectoral/shoulder shaping retains the original joints.
    for v in body.data.vertices:
        x,y,z=v.co
        if 1.10<z<1.51 and abs(x)<.25:
            b=math.sin((z-1.10)/.41*math.pi);v.co.x*=1+.065*b
            if y<0:v.co.y-=.012*b
        if 1.62<z<1.80 and y<-.075:
            # More settled cheek/jaw silhouette; face is still authored anatomy.
            cheek=math.exp(-((z-1.70)/.065)**2);v.co.x*=1+.025*cheek
    body.data.materials.append(m['skin']);body.data.materials.append(m['lips'])
    for p in body.data.polygons:p.use_smooth=True
    # True Catmull-Clark quad refinement before deformation avoids faceted shoulders.
    activate(body);sub=body.modifiers.new('Anatomy surface refinement','SUBSURF');sub.levels=1;sub.render_levels=1;bpy.ops.object.modifier_move_up(modifier=sub.name);bpy.ops.object.modifier_apply(modifier=sub.name)
    normalize(body)
    for f in body.data.polygons:
        c=f.center
        if abs(c.x)<.022 and 1.636<c.z<1.651 and c.y<-.153:f.material_index=1
    weights=[[(body.vertex_groups[w.group].name,w.weight) for w in v.groups] for v in body.data.vertices]
    tree=KDTree(len(body.data.vertices))
    for v in body.data.vertices:tree.insert(v.co,v.index)
    tree.balance();return body,weights,tree

def cloth(s,m):
    # Full trousers cover concealed anatomy and keep actual anatomical weights.
    trousers=s.fitted('Tailored gathered ivory trousers',m['ivory'],lambda p:.16<p.z<1.035 and abs(p.x)<.29,.018)
    for v in trousers.data.vertices:
        x,y,z=v.co;side=1 if x>0 else -1
        if .2<z<.97:
            bulge=.013*math.sin(math.pi*(z-.2)/.77);v.co.x+=side*bulge
            angle=math.atan2(y,x-side*(.20-.10*(z-.2)/.77));wrinkle=.011*math.sin(z*56+angle*1.7)*(.25+.75*math.sin(math.pi*(z-.2)/.77))*max(0,min(1,(.72-z)/.20));v.co.x+=math.cos(angle)*wrinkle;v.co.y+=math.sin(angle)*wrinkle
    solid(trousers,.002)
    # Ivory front dhoti: broad bowed volume and converging diagonal tension folds.
    def dhoti(u,v):
        w=.305-.175*v+.055*math.sin(v*math.pi);x=(u-.5)*w
        z=1.02-.67*v+.055*v*math.sin(u*math.pi+v)
        y=-.158-.060*math.sin(v*math.pi*.85)-.017*math.sin((u*3.2+.9*v)*TAU)*(.2+.8*math.sin(v*math.pi))+.010*math.sin((v*3+u)*TAU)*math.sin(u*math.pi)*math.sin(v*math.pi)-.060*v-.012*math.sin(v*math.pi)
        return x,y,z
    o=s.cloth('Layered ivory dhoti',dhoti,m['ivory'],rows=46,columns=48);solid(o,.003)
    for u in (0,1):s.tube('Ivory embroidered edge',[dhoti(u,t) for t in np.linspace(0,1,48)],.004,m['gold'])
    apply_front_drape_binding(o,[obj for obj in s.objects if obj.name.startswith('Ivory embroidered edge')])
    # Cobalt wrap side panels: open front, asymmetric fluttered curved hems.
    for side in (-1,1):
        def skirt(u,v,side=side):
            a=side*(.40+u*1.78);radius=.167+.175*v+.025*math.sin(v*math.pi)
            fold=.013*math.sin(u*TAU*3.5+v*2)*math.sin(v*math.pi*.8)
            x=(radius+fold)*math.sin(a);y=-(.155+.135*v+fold)*math.cos(a)
            z=1.07-v*(.77 if side<0 else .67)+.09*v*math.sin(u*math.pi)**2+.025*math.sin(v*math.pi)*math.sin(u*TAU)
            return x,y,z
        o=s.cloth('Flowing cobalt wrapped panel '+str(side),skirt,m['cloth'],rows=44,columns=40);solid(o,.003)
        ribbon_trim(s,skirt,m,edge=.075)
        s.tube('Cobalt scalloped hem',[skirt(u,1) for u in np.linspace(0,1,50)],.004,m['gold'])
        # Sparse woven lotus medallions on lower cloth, with modeled outlines.
        for u in (.22,.55,.84):
            c=Vector(skirt(u,.88));c.y-=.003
            for k in range(5):
                a=TAU*k/5;petal(s,'Woven hem lotus',c+Vector((math.sin(a)*.009,0,math.cos(a)*.009)),(math.sin(a),0,math.cos(a)),.004,.015,m['gold'],None,depth=.001)
    # Draped sash crosses the body, projects outside chest with curved shoulder turn.
    def sash(u,v):
        x=.19-.35*v+(u-.5)*(.118-.020*math.sin(v*math.pi));z=1.535-.49*v
        y=-.153+.08*(1-v)**8-.033*math.sin(v*math.pi)-.005*math.cos(u*TAU*3.2+v*2)
        return x,y,z
    o=s.cloth('Folded cobalt cross sash',sash,m['cloth'],rows=38,columns=24);solid(o,.003);ribbon_trim(s,sash,m,edge=.12)
    # A draped chased shoulder chain replaces the floating secondary cloth strip.
    chain(s,'Shoulder draped gold cord',[(-.15,-.075,1.50),(-.116,-.145,1.405),(-.092,-.16,1.30)],m['gold'],'spine01',.0025)
    # Sweeping mantle originating at shoulders. Upper mesh follows back contour,
    # lateral fall grows away from thighs, without a rectangular cape panel.
    for side in (-1,1):
        def mantle(u,v,side=side):
            x=side*(.155+.15*v+.025*math.sin(v*TAU))+(u-.5)*(.11+.14*v)
            y=.07+.23*v+.025*math.sin(u*TAU*2.5+v*4)*(.3+.7*v)
            z=1.50-(1.12 if side>0 else 1.01)*v+.10*v*math.sin(u*math.pi)+.045*v*math.sin(u*TAU+v*2)
            return x,y,z
        o=s.cloth('Sculpted flowing shoulder mantle '+str(side),mantle,m['cloth'],rows=50,columns=28,bone='spine01');solid(o,.003)
        # Motion-safe broad fall: pelvis plus own-side thigh below waist.
        for v in o.data.vertices:
            t=max(0,min(1,(1.50-v.co.z)/1.12));bone='upperleg01.'+('L' if side>0 else 'R')
            for g in o.vertex_groups:g.remove([v.index])
            for name,w in [('spine01',max(0,1-t*2)),('spine05',min(1,t*2)-max(0,t-.55)*.35),(bone,max(0,t-.55)*.35)]:
                if w>0:
                    g=o.vertex_groups.get(name) or o.vertex_groups.new(name=name);g.add([v.index],w,'REPLACE')
        ribbon_trim(s,mantle,m,bone='spine05',edge=.10,source=o)
        hem=s.tube('Flowing mantle hem',[mantle(u,1) for u in np.linspace(0,1,50)],.004,m['gold'],'spine05');transfer_weights(hem,o)
    def shoulderback(u,v):
        return ((u-.5)*.39,.135+.045*math.sin(v*math.pi)+.010*math.sin(u*TAU*3),1.50-.18*v-.025*math.sin(u*math.pi))
    bridge=s.cloth('Gathered shoulder back drape',shoulderback,m['cloth'],rows=18,columns=40,bone='spine01');solid(bridge,.003)
    s.tube('Back drape shaped gold hem',[shoulderback(u,1) for u in np.linspace(0,1,49)],.003,m['gold'],'spine01')
    # Wide layered waist wrap and chased bands.
    for k in range(3):
        def belt(u,v,k=k):
            a=u*TAU;z=1.035+k*.025+v*.022+.008*math.sin(a*2+k)
            return (.171*math.cos(a),.005+.151*math.sin(a),z)
        o=s.cloth('Layered woven waist sash',belt,m['cloth'] if k%2 else m['brocade'],rows=3,columns=72,wrap=True,bone='spine05');solid(o,.002)
    for z in (1.034,1.107):s.ring('Chased belt rail',(0,.005,z),(.174,.155),m['gold'],'spine05',.004,segments=72,wave=.003)
    lotus(s,(0,-.163,1.074),.052,'spine05',m)
    for side in (-1,1):
        chain(s,'Waist draped chain',[(0,-.165,1.06),(side*.10,-.158,1.005),(side*.17,-.07,1.05)],m['gold'],'spine05')
        for j in range(3):
            x=side*(.047+j*.033);z=1.045-j*.013
            petal(s,'Belt dangling leaf',(x,-.17,z-.03),(side*.15,0,-1),.009,.055,m['gold'],'spine05',.003)

def hair_lock(s,points,width,depth,m,name='Swept sculpted hair lock'):
    pts=resample(points,33);verts=[];faces=[];uv=[];sides=14
    for i,p in enumerate(pts):
        t=i/(len(pts)-1);tangent=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
        front=Vector((0,-1,0));across=tangent.cross(front)
        if across.length<.05:across=tangent.cross(Vector((1,0,0)))
        across.normalize();normal=tangent.cross(across).normalized()
        taper=max(.018,math.sin(math.pi*t)**.48)
        for j in range(sides):
            a=j/sides*TAU;ridge=1+.055*math.cos(a*5+t*4)
            verts.append(p+across*(width*math.cos(a)*taper)+normal*(depth*math.sin(a)*taper*ridge));uv.append((j/sides,t))
    for i in range(len(pts)-1):
        for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;faces.append((a,b,b+sides,a+sides))
    faces.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))]);return s.mesh(name,verts,faces,m,'head',uv)

def unite_hair(s,m):
    # Union overlapping clumps into one sculpted hair surface. This removes
    # visible cut ribbon caps and internal overlap seams while keeping waves.
    pieces=[o for o in s.objects if o.data.materials and o.data.materials[0]==m['hair'] and 'eyebrow' not in o.name.lower() and 'foundation' not in o.name.lower()]
    activate(pieces[0])
    for o in pieces:o.select_set(True)
    bpy.ops.object.join();hair=bpy.context.object;hair.name='Unified swept hair sculpture'
    s.objects=[o for o in s.objects if o not in pieces];s.objects.append(hair)
    for mod in list(hair.modifiers):hair.modifiers.remove(mod)
    rem=hair.modifiers.new('Hair volume union','REMESH');rem.mode='VOXEL';rem.voxel_size=.0024;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
    smooth=hair.modifiers.new('Hair sculpt polish','SMOOTH');smooth.factor=.55;smooth.iterations=4;bpy.ops.object.modifier_apply(modifier=smooth.name)
    reduce=hair.modifiers.new('Hair surface economy','DECIMATE');reduce.ratio=.45;bpy.ops.object.modifier_apply(modifier=reduce.name)
    hair.vertex_groups.clear();g=hair.vertex_groups.new(name='head');g.add(list(range(len(hair.data.vertices))),1,'REPLACE')
    mod=hair.modifiers.new('Skin deformation','ARMATURE');mod.object=s.rig;hair.parent=s.rig
    hair.data.materials.clear();hair.data.materials.append(m['hair']);uv=hair.data.uv_layers.new(name='UVMap')
    for face in hair.data.polygons:
        face.use_smooth=True
        for li in face.loop_indices:
            p=hair.data.vertices[hair.data.loops[li].vertex_index].co
            uv.data[li].uv=(math.atan2(p.y+.02,p.x)/TAU+.5,(p.z-1.45)/.48)

def face_hair(s,m):
    tree=BVHTree.FromObject(s.body,bpy.context.evaluated_depsgraph_get())
    def facepoint(x,z):
        co,normal,index,dist=tree.ray_cast(Vector((x,-.7,z)),Vector((0,1,0)),1.0)
        return Vector((x,(co.y if co is not None else -.16)-.0015,z))
    # Eyeballs are recessed within the native eyelid aperture and use small irises.
    for side in ('L','R'):
        c=s.rig.data.bones['eye.'+side].head_local.copy();c.y-=.003
        s.ellipsoid('Seated sclera '+side,c,(.0153,.0153,.0153),m['eye'],'eye.'+side,40,24)
        s.ellipsoid('Brown iris '+side,c+Vector((0,-.0150,0)),(.0055,.0010,.0055),m['iris'],'eye.'+side,32,18)
        s.ellipsoid('Dark pupil '+side,c+Vector((0,-.0158,0)),(.0027,.0005,.0027),m['pupil'],'eye.'+side,24,12)
        # Continuous almond rims bridge the seated globes to the sculpted face.
        for top in (True,False):
            pts=[]
            for j in range(33):
                t=j/32;dx=(t-.5)*.032;dz=(.0065 if top else -.0047)*math.sin(t*math.pi)
                pts.append(c+Vector((dx,-math.sqrt(max(.00002,.0158**2-dx*dx-dz*dz))-.0005,dz)))
            s.tube('Integrated upper eyelid' if top else 'Integrated lower eyelid',pts,.0018 if top else .0015,m['skin'],'head',sides=10,taper=lambda t:.35+.65*math.sin(t*math.pi))
        sign=1 if side=='L' else -1
        brow=[facepoint(c.x+sign*(t-.5)*.049,c.z+.018+.005*math.sin(t*math.pi)-.003*t) for t in np.linspace(0,1,33)]
        s.tube('Surface seated natural eyebrow',brow,.0026,m['hair'],'head',sides=10,taper=lambda t:.15+.85*math.sin(math.pi*t)**.6)
    # Scalp follows the actual refined skull, avoiding approximate helmet gaps.
    scalp=s.fitted('Anatomical fitted hair foundation',m['hair'],lambda p:p.z>1.78 and (p.y>-.10 or p.z>1.812),.004)
    solid(scalp,.001)
    # Asymmetric swept masses have tapered ends, with no flat cut ribbon caps.
    for i in range(7):
        t=i/6;x=-.079+.158*t
        hair_lock(s,[(x,-.124+.013*math.sin(t*math.pi),1.785+.015*math.sin(t*math.pi)),(x*.72+.020,-.100,1.828+.013*math.sin(t*math.pi)),(x*.50+.029,-.038,1.864+.008*math.sin(t*math.pi)),(x*.22+.005,.043,1.857)],.023,.0068,m['hair'],'Overlapping swept crown lock')
    # Broad wavy side groups vary their turning points and taper into curls.
    for side in (-1,1):
        for i in range(5):
            yy=.005+i*.024;phase=i*.9
            hair_lock(s,[(side*(.065+.006*i),yy-.02,1.815),(side*(.103+.013*math.sin(phase)),yy+.008,1.743),(side*(.116+.017*math.cos(phase)),yy+.03,1.661),(side*(.082+.022*math.sin(phase)),yy+.052,1.575-.018*i),(side*(.106+.024*math.cos(phase)),yy+.025,1.515-.016*i)],.024-.0018*i,.009,m['hair'],'Wavy overlapping nape lock')
        hair_lock(s,[(side*.018,-.122,1.826),(side*.068,-.137,1.793),(side*.092,-.108,1.738),(side*.073,-.10,1.697)],.019,.007,m['hair'],'Swept temple fringe')
    for i in range(5):
        x=(i-2)*.029;phase=i*.8
        hair_lock(s,[(x,.102,1.811),(x+.010*math.sin(phase),.126,1.72),(x+.017*math.cos(phase),.144,1.64),(x-.014,.153,1.55),(x+.013,.132,1.49+.012*(i%3))],.024,.009,m['hair'],'Layered back hair wave')
    # Compact tied half-knot uses flattened overlapping masses with small flyaway ends.
    for i in range(5):
        a=i/5*TAU
        hair_lock(s,[(.032*math.cos(a),.04+.022*math.sin(a),1.859),(.038*math.cos(a+.7),.045+.025*math.sin(a+.7),1.891),(.025*math.cos(a+1.8),.044+.021*math.sin(a+1.8),1.908),(.01*math.cos(a+2.4),.038+.015*math.sin(a+2.4),1.878)],.017,.009,m['hair'],'Compact swept topknot')
    unite_hair(s,m)
    s.ring('Fine knot gold tie',(0,.04,1.868),(.037,.035),m['gold'],'head',.003,segments=56)
    # Worked diadem and crest uses real petals and fine articulated scrolls.
    s.ring('Diadem lower chased rail',(0,-.029,1.792),(.105,.137),m['gold'],'head',.0035,segments=80,wave=.003)
    lotus(s,(0,-.167,1.802),.025,'head',m)
    for side in (-1,1):
        for k in range(3):
            x=side*(.025+k*.019);y=-.164+.60*x*x
            petal(s,'Diadem chased leaf',(x,y,1.806+.007*k),(side*.8,0,.55),.007,.027,m['gold'],'head',.003)
        chain(s,'Diadem filigree',[(side*.016,-.17,1.794),(side*.045,-.16,1.82),(side*.082,-.13,1.803)],m['gold'],'head',.0015)
    path(s,'Ivory tilaka',[(0,-.164,1.755),(0,-.166,1.777)],.0018,m['ivory'],'head',8)
    # Hanging earrings have open hoops, lotus studs and drops.
    for side in (-1,1):
        c=Vector((side*.089,-.052,1.672));s.ellipsoid('Earring stud',c,(.006,.004,.006),m['gem'],'head',16,10)
        pts=[c+Vector((.009*math.cos(a),-.002,.013*math.sin(a)-.018)) for a in np.linspace(0,TAU,41)];s.tube('Fine earring hoop',pts,.0022,m['gold'],'head',sides=8)
        petal(s,'Earring pendant',c+Vector((0,-.002,-.04)),(0,0,-1),.006,.020,m['gold'],'head',.003)

def ornaments(s,m):
    # Collar and fitted layered chains on chest.
    s.ring('Chased collar',(0,-.017,1.543),(.066,.079),m['gold'],'neck01',.004,segments=64)
    for depth in (.025,.073):
        chain(s,'Articulated chest chain',[(-.068,-.07,1.54),(-.07,-.137,1.49),(0,-.169,1.49-depth),(.07,-.137,1.49),(.068,-.07,1.54)],m['gold'],'spine01',.0026)
    lotus(s,(0,-.177,1.438),.027,'spine01',m)
    for side in ('L','R'):
        sign=1 if side=='L' else -1
        upper=s.rig.data.bones['upperarm01.'+side];c=upper.head_local+Vector((sign*.015,-.014,.025))
        # Layered petal pauldron is curved around shoulder, with recessed lining.
        s.ellipsoid('Shoulder blue lining '+side,c,(.079,.077,.033),m['gold'],'upperarm01.'+side,40,22)
        for k in range(5):
            axis=Vector((sign*(.5+k*.15),0,.4-k*.13));cc=c+Vector((sign*(k-2)*.015,-.059,-k*.006))
            petal(s,'Pauldron overlapping gold leaf',cc,axis,.025,.105,m['gold'],'upperarm01.'+side,.010)
            path(s,'Pauldron leaf vein',[cc-axis.normalized()*.035+Vector((0,-.01,0)),cc+Vector((0,-.015,0)),cc+axis.normalized()*.035+Vector((0,-.01,0))],.0018,m['darkgold'],'upperarm01.'+side,6)
        lotus(s,c+Vector((0,-.075,.005)),.022,'upperarm01.'+side,m)
        # Raised rosette and curled relief lie on the pauldron's top surface.
        top=c+Vector((0,-.008,.033))
        for k in range(6):
            angle=TAU*k/6;direction=Vector((math.cos(angle),math.sin(angle),0))
            petal(s,'Pauldron top repousse petal',top+direction*.023,direction,.010,.046,m['gold'],'upperarm01.'+side,.003,normal=(0,0,1))
        s.ellipsoid('Pauldron rosette sapphire',top+Vector((0,0,.006)),(.009,.009,.004),m['gem'],'upperarm01.'+side,20,12)
        for sg in (-1,1):
            points=[]
            for t in np.linspace(0,1,41):
                a0=t*TAU*1.3;rr=.006+.020*t;dx=sg*(.025+rr*math.cos(a0));dy=rr*math.sin(a0)
                zz=.033*math.sqrt(max(.05,1-(dx/.079)**2-(dy/.077)**2))+.002
                points.append(c+Vector((dx,dy,zz)))
            s.tube('Pauldron raised chased scroll',points,.0018,m['darkgold'],'upperarm01.'+side,sides=7)
        # Proper solid cuff shells follow the lower-arm axis and taper at wrist.
        b=s.rig.data.bones['lowerarm02.'+side];axis=(b.tail_local-b.head_local).normalized();a=axis.cross(Vector((0,1,0))).normalized();d=axis.cross(a).normalized();mid=b.head_local.lerp(b.tail_local,.62)
        def cuff(u,v):
            t=TAU*u;r=float(.040+.006*(1-v));return mid+axis*((v-.5)*.105)+r*(a*math.cos(t)+d*math.sin(t))
        o=s.cloth('Fitted cobalt vambrace '+side,cuff,m['cloth'],rows=12,columns=48,wrap=True,bone='lowerarm02.'+side);solid(o,.003)
        for v in (0,.12,.88,1):s.tube('Vambrace chased gold rim',[cuff(u,v) for u in np.linspace(0,1,49)],.003,m['gold'],'lowerarm02.'+side,sides=8)
        for j in range(9):
            u=j/9;s.tube('Vambrace curling leafwork',[cuff(u+.02*math.sin(t*TAU),t) for t in np.linspace(.12,.88,25)],.0022,m['gold'],'lowerarm02.'+side,sides=7)
        # Broad shin leaf over blue fitted shell, leaving knee bend clear.
        b=s.rig.data.bones['lowerleg02.'+side];c=b.head_local.lerp(b.tail_local,.55)+Vector((0,-.048,0))
        petal(s,'Cobalt shin shield '+side,c,(0,0,1),.052,.235,m['cloth'],'lowerleg02.'+side,.017)
        for sg in (-1,1):
            path(s,'Greave chased edge',[(c.x,c.y-.006,c.z-.117),(c.x+sg*.049,c.y-.012,c.z-.015),(c.x+sg*.027,c.y-.012,c.z+.073),(c.x,c.y-.004,c.z+.117)],.004,m['gold'],'lowerleg02.'+side,8)
            for k in range(3):petal(s,'Greave leaf relief',c+Vector((sg*.018,c.y*0-.023,(k-1)*.048)),(sg*.6,0,1),.012,.065,m['gold'],'lowerleg02.'+side,.004)
        foot=s.rig.data.bones['foot.'+side];fp=foot.head_local
        s.ellipsoid('Layered leather sandal '+side,(fp.x,fp.y-.043,.022),(.058,.108,.012),m['leather'],'foot.'+side,40,12)
        s.ellipsoid('Gold sandal welt '+side,(fp.x,fp.y-.043,.015),(.060,.11,.006),m['gold'],'foot.'+side,40,10)
        for yy in (-.08,-.025):path(s,'Crossing leather sandal strap',[(fp.x-.052,fp.y+yy,.03),(fp.x,fp.y+yy-.008,.071),(fp.x+.052,fp.y+yy,.03)],.006,m['leather'],'foot.'+side,10)
        s.ring('Sandal ankle gold binding',(fp.x,fp.y+.002,.108),(.053,.048),m['gold'],'foot.'+side,.0035,segments=48)

def weapon(s,m):
    before=len(s.objects);b=s.rig.data.bones['wrist.R'];origin=b.head_local;rot=b.matrix_local.to_3x3()
    def p(x,y,z):return origin+rot@(Vector((z,y,-x))+Vector((0,.105,.025)))
    # Retains the original grip and string anchors; adds expressive forged limbs.
    def limb(z):
        t=z/.575;return p(.026*math.sin(abs(t)*math.pi)*(-1 if z<0 else 1),-.1*(1-math.cos(math.pi*t)),z)
    s.tube('Forged recurved bow limbs',[limb(z) for z in np.linspace(-.575,.575,113)],.018,m['gold'],'wrist.R',sides=16,taper=lambda t:.38+.62*math.sin(math.pi*t)**.55)
    s.tube('Cobalt bow inset',[limb(z)+rot@Vector((0,-.014,0)) for z in np.linspace(-.56,.56,97)],.005,m['gem'],'wrist.R',sides=8)
    # Leaf scrolls follow each limb within its front plane.
    for side in (-1,1):
        for k in range(5):
            z=side*(.14+k*.076);c=limb(z)
            pts=[]
            for t in np.linspace(0,1,29):
                zz=z+side*(t-.5)*.12;off=.040*math.sin(t*math.pi);pt=limb(zz)+rot@Vector((0,-off,off*.2));pts.append(pt)
            s.tube('Bow pierced leaf scroll',pts,.0048,m['gold'],'wrist.R',sides=9)
            s.ellipsoid('Bow sapphire setting',c+rot@Vector((0,-.018,0)),(.009,.009,.012),m['gem'],'wrist.R',20,12)
        path(s,'Swept bow tip flourish',[limb(side*.45),p(side*.025,-.245,side*.55),p(0,-.2,side*.575)],.005,m['gold'],'wrist.R',9,lambda t:.7-.4*t)
    s.tube('Leather bound grip',[p(0,0,z) for z in np.linspace(-.046,.046,14)],.022,m['leather'],'wrist.R',sides=20)
    for z in np.linspace(-.042,.042,11):s.tube('Grip chased wire',[p(.0226*math.cos(a),.0226*math.sin(a),z) for a in np.linspace(0,TAU,33)],.0012,m['gold'],'wrist.R',sides=6)
    string=s.tube('Skinned bowstring',[p(0,-.2,-.575),p(0,-.205,0),p(0,-.2,.575)],.0012,m['ivory'],'wrist.R',sides=8)
    string.vertex_groups['wrist.R'].remove(list(range(8,16)));string.vertex_groups.new(name='bowstring').add(list(range(8,16)),1,'REPLACE')
    bow=s.objects[before:]
    # Shoulder-carried quiver, with solid leather body and embossed bands.
    base=Vector((-.145,.145,1.15));top=Vector((-.215,.16,1.64));axis=(top-base).normalized();a=axis.cross(Vector((0,1,0))).normalized();d=axis.cross(a).normalized()
    s.tube('Cobalt leather quiver',[base.lerp(top,t) for t in np.linspace(0,1,18)],.048,m['cloth'],'spine01',sides=32)
    for t in (.04,.14,.86,.96,1):
        c=base.lerp(top,t);s.tube('Quiver chased rim',[c+.050*(a*math.cos(q)+d*math.sin(q)) for q in np.linspace(0,TAU,49)],.0035,m['gold'],'spine01',sides=8)
    for k in range(7):
        end=top+axis*(.16+.018*(k%3))+a*((k-3)*.010)+d*((k%2-.5)*.016)
        s.tube('Quiver arrow shaft',[end-axis*.32,end],.0019,m['gold'],'spine01',sides=8)
        for sign in (-1,1):
            def feather(u,v,end=end,sign=sign):return end-axis*(.014+.075*v)+a*(sign*.012*math.sin(v*math.pi)*u)+d*.002
            o=s.cloth('Curved ivory fletching',feather,m['ivory'],rows=12,columns=3,bone='spine01');solid(o,.0005)
    return bow

def join_group(objects,name):
    activate(objects[0])
    for o in objects:o.select_set(True)
    bpy.ops.object.join();o=bpy.context.object;o.name=name
    for mod in list(o.modifiers)[1:]:o.modifiers.remove(mod)
    tri=o.modifiers.new('Runtime triangulation','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name)
    return o

def preview(rig):
    scene=bpy.context.scene;rig.animation_data_clear();rig.data.pose_position='REST'
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=False
    scene.render.resolution_x=720;scene.render.resolution_y=960;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX';scene.world=scene.world or bpy.data.worlds.new('Rama Review World');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.085,.105,.15,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.022));bpy.context.object.name='ReviewGround';bpy.context.object.data.materials.append(material('Review ground',(.045,.055,.07),.85))
    for pos,power,size in [((3,-4,4),520,4),((-3,-1,2.5),230,3),((0,3,3.5),650,3)]:
        d=bpy.data.lights.new('ReviewSoftbox','AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new('ReviewSoftbox',d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
    d=bpy.data.cameras.new('Actual mesh review');cam=bpy.data.objects.new('Actual mesh review',d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO'
    for name,pos,target,scale in [('front',(2.0,-6,2.05),(0,0,1.02),2.32),('face',(.36,-3,1.83),(0,-.025,1.735),.48),('rear',(-2.6,5.5,2.2),(0,.05,1.0),2.3)]:
        if '--front-face' in ARGS and name=='rear':continue
        d.ortho_scale=scale;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/('review-'+name+'.png'));bpy.ops.render.render(write_still=True)

def rig_signature(rig):
    return {b.name:dict(parent=b.parent.name if b.parent else None,matrix=[list(row) for row in b.matrix_local]) for b in rig.data.bones}

def main():
    if '--preview-only' in ARGS:
        bpy.ops.wm.open_mainfile(filepath=str(OUT/'rama-hero.blend'));preview(next(o for o in bpy.data.objects if o.type=='ARMATURE'));return
    started=time.monotonic();bpy.ops.wm.open_mainfile(filepath=str(BASE));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    for o in list(bpy.data.objects):
        if o!=rig:bpy.data.objects.remove(o,do_unlink=True)
    baseline_rig=rig_signature(rig)
    rig.data.pose_position='REST'
    for b in rig.pose.bones:b.matrix_basis.identity()
    for a in bpy.data.actions:a.name=a.name.removesuffix('_YugaHeroRig');a.use_fake_user=True
    rig.animation_data.action=None
    m=materials();body,weights,tree=anatomy(rig,m);s=Sculpt(rig,body,weights,tree)
    cloth(s,m);face_hair(s,m);ornaments(s,m);bows=weapon(s,m)
    # Remove only covered pelvis and leg anatomy; preserve toes, hands and torso.
    bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if .17<f.calc_center_median().z<1.025 and abs(f.calc_center_median().x)<.29],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(body.data);bm.free()
    for o in s.objects:normalize(o)
    for mat in list(bpy.data.materials):
        if mat.users==0:bpy.data.materials.remove(mat)
    for image in list(bpy.data.images):
        if image.users==0:bpy.data.images.remove(image)
    # Save modeling source as separate editable pieces before runtime merge.
    assert rig_signature(rig)==baseline_rig,'Rig rest convention changed'
    source_objects=len(s.objects);rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions.get('idle');bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'rama-hero.blend'),compress=True)
    # Export staged clone, retaining separate bow node for runtime integration.
    hero=join_group([o for o in s.objects if o not in bows],'RamaHero');bow=join_group(bows,'RamaBow')
    activate(rig);hero.select_set(True);bow.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/'rama-hero.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_skins=True,export_all_influences=False,export_yup=True,export_tangents=True,export_image_format='AUTO')
    data=(OUT/'rama-hero.glb').read_bytes();n,kind=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+n]);prims=[p for mesh in doc['meshes'] for p in mesh['primitives']]
    meta=dict(schema=1,asset='Rama smooth hero candidate',generatorSha256=sha(__file__),inputBlendSha256=sha(BASE),outputSha256=sha(OUT/'rama-hero.glb'),editableSha256=sha(OUT/'rama-hero.blend'),bytes=len(data),bones=len(rig.data.bones),clips=[a['name'] for a in doc.get('animations',[])],vertices=sum(doc['accessors'][p['attributes']['POSITION']]['count'] for p in prims),triangles=sum(doc['accessors'][p['indices']]['count']//3 for p in prims),materials=len(doc['materials']),editableMeshPieces=source_objects,rigRestPreserved=True,rigRestSha256=hashlib.sha256(json.dumps(baseline_rig,sort_keys=True).encode()).hexdigest(),buildSeconds=round(time.monotonic()-started,2),textures=[dict(file=p.name,sha256=sha(p)) for p in sorted(TEX.glob('*.png'))],license='CC0 MakeHuman anatomy data; original generated costume/hair/goldwork/textures; retained original project animations',limitations=['No facial blendshapes, cloth physics, hair strand simulation or LODs.','Static studio review does not establish gameplay acceptance or commercial parity.'])
    (OUT/'candidate.json').write_text(json.dumps(meta,indent=2)+'\n');print('RAMA_CANDIDATE '+json.dumps(meta),flush=True)
    if '--preview' in ARGS:preview(rig)

if __name__=='__main__':main()
