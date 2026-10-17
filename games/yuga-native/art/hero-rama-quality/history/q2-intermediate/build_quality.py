"""Original Rama art quality candidate. Blender 4.3.2, no runtime mutation.
blender -b -t 2 --python build_quality.py -- --output /new/path [--render]
Source: accepted editable R7. Preserves rig/rest/actions/contact conventions.
"""
from pathlib import Path
import sys, math, json, hashlib, time, importlib.util
import bpy
import numpy as np
from mathutils import Vector
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
INPUT=ROOT/'games/yuga-native/art/hero-rama/rama-hero.blend'
BASESCRIPT=ROOT/'games/yuga-native/art/hero-rama/build_hero.py'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=Path(args[args.index('--output')+1]) if '--output' in args else HERE
OUT.mkdir(parents=True,exist_ok=True)
TAU=math.tau
spec=importlib.util.spec_from_file_location('rama_original_generator',BASESCRIPT)
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
h.TEX=OUT/'textures';h.TEX.mkdir(parents=True,exist_ok=True)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def smooth(a,b,v):
 t=max(0.,min(1.,(v-a)/(b-a)));return t*t*(3-2*t)
def activate(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o

def set_mask(o,values):
 old=o.data.color_attributes.get('secondary_motion')
 if old:o.data.color_attributes.remove(old)
 c=o.data.color_attributes.new(name='secondary_motion',type='FLOAT_COLOR',domain='CORNER')
 for loop in o.data.loops:c.data[loop.index].color=(1,1,1,float(values[loop.vertex_index]))
 o.data.color_attributes.active_color=c
 o.data.color_attributes.render_color_index=list(o.data.color_attributes).index(c)

def mask_trailing(o):
 return [smooth(.175,.25,v.co.y)*(1-smooth(1.02,1.36,v.co.z)) for v in o.data.vertices]

def lock(rig,name,points,width,depth,mat,phase=0,root_width=1.0):
 """Sealed tapered lock with deliberately modelled longitudinal subclumps.
 The groove is geometric and follows tangent; not a remeshed sausage volume.
 """
 pts=h.resample(points,41);vs=[];fs=[];uv=[];weights=[];sides=12
 for i,p in enumerate(pts):
  t=i/(len(pts)-1);tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
  # Front-facing cross section kept stable for front crown; gradual side/back turn.
  outward=Vector((p.x*.5,-1 if p.y<.035 else .35,0))
  across=tangent.cross(outward)
  if across.length<.03:across=tangent.cross(Vector((1,0,0)))
  across.normalize();normal=tangent.cross(across).normalized()
  # Broad root overlaps neighbouringlocks; four-filament tips taper continuously.
  envelope=(.92+.08*math.sin(t*math.pi))*(1-smooth(.58,1,t))+.004
  envelope*=smooth(0,.075,t)*(root_width+(1-root_width)*smooth(0,.22,t))
  for j in range(sides):
   angle=j/sides*TAU
   groove=1+.09*math.cos(angle*4+phase+.4*math.sin(t*3))
   pt=p+across*(width*math.cos(angle)*envelope)+normal*(depth*math.sin(angle)*envelope*groove)
   vs.append(pt);uv.append((j/sides,t));weights.append(smooth(.12,.92,t))
 for i in range(len(pts)-1):
  for j in range(sides):
   a=i*sides+j;b=i*sides+(j+1)%sides;fs.append((a,b,b+sides,a+sides))
 fs.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))])
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],fs);mesh.update()
 o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.parent=rig
 mesh.materials.append(mat)
 for f in mesh.polygons:f.use_smooth=True
 layer=mesh.uv_layers.new(name='UVMap')
 for loop in mesh.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
 o.vertex_groups.new(name='head').add(list(range(len(vs))),1,'REPLACE')
 mod=o.modifiers.new('Skin deformation','ARMATURE');mod.object=rig
 set_mask(o,weights)
 o['yuga_semantic']='hair_clump';o['secondary_anchor']='head; rooted first12%'
 return o

def rebuild_hair(rig):
 old=bpy.data.objects.get('Unified swept hair sculpture')
 if not old:raise RuntimeError('Expected exact R7 hair source')
 bpy.data.objects.remove(old,do_unlink=True)
 mat=bpy.data.materials['Swept black hair']
 p=mat.node_tree.nodes.get('Principled BSDF')
 p.inputs['Specular IOR Level'].default_value=.18
 # Existing hairmap remains directional, with less chalky broad normal response.
 for n in mat.node_tree.nodes:
  if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=.24
  if n.type=='TEX_IMAGE' and n.image and 'roughness' in n.image.name:
   n.image=None;mat.node_tree.nodes.remove(n)
 p.inputs['Roughness'].default_value=.49
 objects=[]
 # Asymmetric swept crown fans towards compact half-knot; hairline stays covered.
 for i in range(17):
  u=i/16;x=-.083+.166*u
  points=[(x*.92,-.112+.010*math.sin(u*math.pi),1.778+.010*math.sin(u*math.pi)),(x*.8+.019,-.105,1.824+.010*math.sin(u*math.pi)),(x*.40+.023,-.035,1.860+.007*math.sin(u*math.pi)),(x*.15+.004,.040,1.867-.006*math.cos(u*math.pi))]
  objects.append(lock(rig,'Articulated crown lock %02d'%i,points,.011+.0015*math.sin(i*1.7),.0046,mat,i*.7))
 # Purposeful forelock shapes break the scalp/diadem edge with narrow tapered ends.
 for side in (-1,1):
  for k in range(3):
   q=k/2
   points=[(side*(.010+q*.018),-.103,1.827-q*.006),(side*(.052+q*.016),-.142+q*.006,1.804-q*.008),(side*(.082+q*.010),-.123,1.766-q*.014),(side*(.079+q*.013),-.100,1.712-q*.015)]
   objects.append(lock(rig,'Temple swept forelock %s %s'%(side,k),points,.011-.001*k,.0045,mat,k+side*.4))
  # Wavy side/nape locks with visible negative space, varied lengths and turns.
  for k in range(9):
   u=k/8;phase=k*.87+side*.4;yy=.002+u*.112
   points=[(side*(.068+.012*u),yy-.025,1.806-.014*u),(side*(.103+.006*math.sin(phase)),yy+.006,1.755-.012*u),(side*(.112+.009*math.cos(phase)),yy+.015,1.680-.018*u),(side*(.092+.010*math.sin(phase)),yy+.032,1.600-.016*u),(side*(.112+.013*math.cos(phase)),yy+.020,1.535-.044*u),(side*(.088+.014*math.sin(phase)),yy+.004,1.492-.050*u)]
   objects.append(lock(rig,'Individual cascading side lock %s %02d'%(side,k),points,.014+.0014*math.cos(phase),.0065,mat,phase))
 # Back waves overlap in three irregular tiers rather than a single broad sheet.
 for k in range(15):
  u=k/14;x=(u-.5)*.17;phase=k*.91
  points=[(x*.88,.060+.006*math.cos(phase),1.807),(x+.005*math.sin(phase),.121,1.745),(x+.013*math.sin(phase+1),.143,1.665),(x+.014*math.cos(phase),.151,1.590),(x-.010*math.sin(phase),.140,1.514+.010*(k%3)),(x+.008*math.sin(phase),.118,1.462+.018*(k%4))]
  objects.append(lock(rig,'Layered narrow back curl %02d'%k,points,.014,.006,mat,phase))
 # Smaller bound knot with actual directional crossing and separate tips.
 for k in range(10):
  a=k/10*TAU
  points=[(.025*math.cos(a),.041+.020*math.sin(a),1.857),(.032*math.cos(a+.8),.043+.023*math.sin(a+.8),1.889),(.021*math.cos(a+1.9),.043+.018*math.sin(a+1.9),1.911),(.009*math.cos(a+2.6),.040+.014*math.sin(a+2.6),1.887)]
  objects.append(lock(rig,'Bound knot filament %02d'%k,points,.010,.0052,mat,a))
 # Two restrained flyaways are model geometry; no alpha cards or silhouette noise.
 for side in (-1,1):
  objects.append(lock(rig,'Fine face framing tendril %s'%side,[(side*.075,-.116,1.781),(side*.101,-.126,1.736),(side*.097,-.123,1.697),(side*.084,-.108,1.679)],.0045,.0022,mat,side))
 return objects

def face_refinement():
 body=bpy.data.objects['RamaAnatomy'];count=0;maxdelta=0.
 # Localised, smooth sculpt of bridge, lower cheeks and chin. Eye/socket/ear
 # positions remain unchanged and all original face vertex indices survive.
 for v in body.data.vertices:
  x,y,z=v.co.copy()
  if not (1.61<z<1.76 and y<-.07):continue
  if abs(x)>.016 and z>1.712:continue  # original eyelid/socket surface is unchanged
  dx=dy=dz=0.
  nose=math.exp(-((x/.024)**2+((z-1.695)/.025)**2))
  bridge=math.exp(-((x/.015)**2+((z-1.72)/.025)**2))
  dx-=x*.055*nose;dy-=.0028*bridge
  jaw=math.exp(-((z-1.637)/.020)**2)*smooth(.025,.055,abs(x))
  dx-=x*.045*jaw
  chin=math.exp(-((x/.023)**2+((z-1.619)/.016)**2));dy-=.0025*chin
  cheek=math.exp(-(((abs(x)-.053)/.028)**2+((z-1.683)/.024)**2))
  dy+=.0018*cheek
  delta=Vector((dx,dy,dz));v.co+=delta
  if delta.length>.00001:count+=1;maxdelta=max(maxdelta,delta.length)
 body['yuga_sculpt']='Q1 boundedbridge/jaw/cheek; eye/socket unchanged; no retopology'
 return {'verticesMoved':count,'maximumDisplacementM':maxdelta,'eyeSocketBonesMoved':False,'eyelidSurfaceMoved':False,'shapeKeysAdded':False}

def texture_pass():
 # Deterministic original fine brocade. Materialnames/UVmaps remain stable.
 # Contrasting roughness carries weave; measured gold density avoidssolidnoise.
 n=1024;y,x=np.mgrid[0:n,0:n]/n
 weave=np.sin(x*TAU*197)*np.cos(y*TAU*181)
 grain=np.sin((x*113+y*211)*TAU)*np.cos((x*223-y*127)*TAU)
 al=np.ones((n,n,3))*np.array([.024,.085,.285])[None,None,:]
 al*= (.97+.025*weave+.008*grain)[:,:,None]
 u=(x*3)%1-.5;v=(y*4)%1-.5;r=np.hypot(u,v);a=np.arctan2(v,u)
 petals=np.exp(-((r-(.16+.064*np.cos(5*a)))/.016)**2)
 vine=np.exp(-((u-.27*np.sin(v*TAU*1.3))/.013)**2)*(.3+.7*np.cos(v*math.pi)**2)
 leaves=np.exp(-(((u-.20*np.sin(v*TAU*1.3))/.045)**2+((np.abs(v)-.28)/.08)**2))
 mask=np.clip(petals*.98+vine*.76+leaves*.48,0,.98)
 gold=np.array([.78,.52,.17]);al=al*(1-mask[:,:,None])+gold[None,None,:]*mask[:,:,None]
 height=.5+.018*weave+.008*grain+.055*mask
 gy,gx=np.gradient(height);norm=np.stack([-gx*2,-gy*2,np.ones_like(x)],axis=2);norm/=np.linalg.norm(norm,axis=2)[:,:,None];norm=norm*.5+.5
 rough=np.repeat((.42+.025*weave-.045*mask)[:,:,None],3,axis=2)
 mat=bpy.data.materials['Cobalt handwoven silk'];nodes=mat.node_tree.nodes
 maps={}
 for label,data,color in [('basecolor',al,False),('normal',norm,True),('roughness',rough,True)]:
  image=h.image_file('q1-cobalt-ornamental-weave-'+label,data,color);maps[label]=image
  for node in nodes:
   if node.type=='TEX_IMAGE' and node.image and label in node.image.name:node.image=image
 # Maintain goldmetallic=.82. Controlled handworked roughness avoidsuniformfoil.
 goldmat=bpy.data.materials['Worked warm gold']
 for node in goldmat.node_tree.nodes:
  if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.24
 return {'originalProceduralMaps':[p.name for p in sorted((OUT/'textures').glob('*.png'))],'blueGoldCoverageFraction':float(np.mean(mask>.1))}

def preserve_signature(rig):
 return {'rig':h.rig_signature(rig),'actions':{a.name:len(a.fcurves) for a in bpy.data.actions}}

def exported_doc(p):
 import struct
 data=Path(p).read_bytes();n,kind=struct.unpack_from('<II',data,12);return json.loads(data[20:20+n])

def render_reviews(rig,prefix='candidate'):
 rig.animation_data_clear();rig.data.pose_position='REST'
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=False
 scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
 scene.view_settings.view_transform='AgX';scene.world=scene.world or bpy.data.worlds.new('Q1 Review World');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.085,.105,.15,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
 bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.022));floor=bpy.context.object;floor.name='ReviewGround';floor.data.materials.append(h.material('Review ground',(.045,.055,.07),.85))
 for pos,power,size in [((3,-4,4),520,4),((-3,-1,2.5),230,3),((0,3,3.5),650,3)]:
  d=bpy.data.lights.new('ReviewSoftbox','AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new('ReviewSoftbox',d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
 d=bpy.data.cameras.new('Q1ActualMesh');cam=bpy.data.objects.new('Q1ActualMesh',d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO'
 views=[('front',(2,-6,2.05),(0,0,1.02),2.32),('face',(.36,-3,1.83),(0,-.025,1.735),.48),('side',(5,-.1,2.05),(0,0,1.0),2.32),('back',(-2.6,5.5,2.2),(0,.05,1.0),2.3)]
 if '--views' in args:
  requested=args[args.index('--views')+1].split(',');views=[v for v in views if v[0] in requested]
 for name,pos,target,scale in views:
  d.ortho_scale=scale;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(prefix+'-'+name+'.png'));bpy.ops.render.render(write_still=True)

def main():
 started=time.monotonic();bpy.ops.wm.open_mainfile(filepath=str(INPUT));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');before=preserve_signature(rig)
 rig.data.pose_position='REST';rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 if '--baseline-only' in args:
  render_reviews(rig,'baseline');return
 for o in bpy.data.objects:
  if o.type=='MESH':set_mask(o,mask_trailing(o) if any(term in o.name for term in ['Sculpted flowing shoulder mantle','Flowing mantle hem','Woven floral gold border','Fine sewn gold edge']) else [0.]*len(o.data.vertices))
 newhair=rebuild_hair(rig);face=face_refinement();texture=texture_pass()
 assert preserve_signature(rig)==before,'Rig/actions were modified'
 # WhiteRGB alpha masks are semantic only. Allstandardmaterials remainopaque.
 for m in bpy.data.materials:
  m.surface_render_method='DITHERED'
  p=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
  if p:p.inputs['Alpha'].default_value=1.
 rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions.get('idle');bpy.context.scene.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'rama-hero-quality.blend'),compress=True)
 objects=[o for o in bpy.data.objects if o.type=='MESH']
 bows=[o for o in objects if any(g.name=='wrist.R' for g in o.vertex_groups) and all(g.name in ('wrist.R','bowstring') for g in o.vertex_groups)]
 # Bow pieces inheritlargegroups inoriginal? Use exactsource list from geometrynames.
 bowterms=['Forged recurved bow limbs','Cobalt bow inset','Bow pierced leaf scroll','Bow sapphire setting','Swept bow tip flourish','Leather bound grip','Grip chased wire','Skinned bowstring']
 bows=[o for o in objects if any(o.name.startswith(t) for t in bowterms)]
 assert len(bows)>15,(len(bows),[o.name for o in bows])
 hero=h.join_group([o for o in objects if o not in bows],'RamaHero');bow=h.join_group(bows,'RamaBow')
 activate(rig);hero.select_set(True);bow.select_set(True)
 path=OUT/'rama-hero-quality.glb'
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_skins=True,export_all_influences=False,export_yup=True,export_tangents=True,export_image_format='AUTO',export_vertex_color='ACTIVE')
 doc=exported_doc(path);prims=[p for m in doc['meshes'] for p in m['primitives']]
 assert all('COLOR_0' in p['attributes'] for p in prims),'Missingsemanticcolor'
 assert all(m.get('alphaMode','OPAQUE')=='OPAQUE' for m in doc['materials']),'Unexpectedtransparentmaterial'
 meta={'schema':1,'asset':'Rama quality Q2 corrected hair/sculpt/weave candidate','sourceBlend':str(INPUT.relative_to(ROOT)),'inputBlendSha256':sha(INPUT),'inputGlbSha256':sha(ROOT/'games/yuga-native/assets/heroes/rama-hero.glb'),'generatorSha256':sha(__file__),'outputSha256':sha(path),'editableSha256':sha(OUT/'rama-hero-quality.blend'),'bones':len(rig.data.bones),'clips':[a['name'] for a in doc.get('animations',[])],'materials':[m['name'] for m in doc['materials']],'vertices':sum(doc['accessors'][p['attributes']['POSITION']]['count'] for p in prims),'triangles':sum(doc['accessors'][p['indices']]['count']//3 for p in prims),'newHairObjects':len(newhair),'faceRefinement':face,'texturePass':texture,'semanticMask':{'attribute':'COLOR_0','rgb':[1,1,1],'alpha':'head-rooted hair tip or continuousbacktrailingfabricweight','alphaMode':'OPAQUE','anchors':'allothervertices0, scalpandeyebrows0'},'rigRestAndActionCountsPreserved':True,'buildSeconds':round(time.monotonic()-started,2),'license':'CC0MakeHuman anatomy; originalcostume/hairtextures/animations. No commercialgameassets.','limitations':['Candidate pending runtimecontinuousmotion/contact/renderreview','No facialblendshapes or strand/cardhairphysics','Actualstaticrender isnot commercialparity or performanceacceptance']}
 (OUT/'candidate.json').write_text(json.dumps(meta,indent=2)+'\n');print('QUALITY_CANDIDATE '+json.dumps(meta),flush=True)
 if '--render' in args:render_reviews(rig)

if __name__=='__main__':main()
