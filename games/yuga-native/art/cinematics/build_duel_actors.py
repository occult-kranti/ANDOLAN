"""Build an original Ravana sentinel costume on existing CC0 production anatomy.
Run Blender --background --threads 1 --python this-file. Writes NEW film asset.
Production Rama and its nine original animation resources are never modified.
"""
from pathlib import Path
import bpy,bmesh,json,hashlib,math,sys
from mathutils import Vector
HERE=Path(__file__).resolve().parent
GAME=HERE.parents[1]
SOURCE=GAME/'assets/heroes/rama-production.glb'
OUT=GAME/'assets/cinematics/ravana-sentinel.glb'
SOURCE_HASH='6657f4bf2fdb41b1f8b1bbd64777b35b5b4acfe00b3e3e22e4bc793fd4df3e8e'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_HASH
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
body=max((o for o in bpy.data.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices))
rig.animation_data_clear()
for bone in rig.pose.bones: bone.matrix_basis.identity()
rig.data.pose_position='REST'
# Remove only separately connected wrist-mounted bow pieces and string.
# The production anatomy/costume is joined, so identify components from topology.
parent=list(range(len(body.data.vertices)))
def find(a):
 while parent[a]!=a: parent[a]=parent[parent[a]];a=parent[a]
 return a
def union(a,b):
 a,b=find(a),find(b)
 if a!=b: parent[b]=a
for edge in body.data.edges: union(*edge.vertices)
components={}
for v in body.data.vertices: components.setdefault(find(v.index),[]).append(v.index)
remove=set(); removed=[]
group_names={g.index:g.name for g in body.vertex_groups}
for indices in components.values():
 weighted={}
 for i in indices:
  for g in body.data.vertices[i].groups: weighted[group_names[g.group]]=weighted.get(group_names[g.group],0)+g.weight
 dominant=max(weighted,key=weighted.get) if weighted else ''
 points=[body.data.vertices[i].co for i in indices]
 ext=[max(v[a] for v in points)-min(v[a] for v in points) for a in range(3)]
 center=sum(points,Vector())/len(points)
 # All original disconnected wrist.R islands are weapon parts: wrist cuffs
 # bind lowerarm02.R, and the connected anatomical body is not wrist-dominant.
 bow_part=dominant in ('bowstring','wrist.R') and len(indices)<2500
 quiver_part=dominant=='spine01' and center.y>.09 and center.x<-.08 and min(v.z for v in points)>1.15
 if bow_part or quiver_part:
  remove.update(indices);removed.append({'vertices':len(indices),'dominant':dominant,'extents':ext})
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[bm.verts[i] for i in remove],context='VERTS');bm.to_mesh(body.data);bm.free()
# Existing original fabric weave/normal maps stay; colour becomes dark crimson.
for mat in body.data.materials:
 shader=mat.node_tree.nodes.get('Principled BSDF')
 if not shader: continue
 n=mat.name
 color=None
 if 'Cobalt' in n: color=(.105,.012,.026,1)
 elif 'Ivory' in n: color=(.075,.064,.068,1)
 elif 'Deep sapphire' in n: color=(.63,.075,.025,1)
 elif 'Warm living skin' in n: color=(.19,.085,.045,1)
 if color:
  for link in list(shader.inputs['Base Color'].links):mat.node_tree.links.remove(link)
  shader.inputs['Base Color'].default_value=color
  mat.name='Sentinel '+n

def material(name,color,metal=.5,rough=.4):
 m=bpy.data.materials.new(name);m.use_nodes=True;s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough;return m
ARMOR=material('Sentinel blackened bronze',(.045,.049,.061),.55,.58)
GOLD=material('Sentinel antique gold',(.52,.285,.065),.78,.33)
GEM=material('Sentinel ember stone',(.42,.025,.009),.45,.2)
parts=[]
def bind(o,name,mat,bone):
 o.name=name;o.data.materials.append(mat);g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE');parts.append(o);return o

def cube(name,pos,size,mat,bone,bevel=.01):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('Forged chamfer','BEVEL');mod.width=bevel;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name)
 return bind(o,name,mat,bone)
def sphere(name,pos,size,mat,bone):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=pos);o=bpy.context.object;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for p in o.data.polygons:p.use_smooth=True
 return bind(o,name,mat,bone)
def cone(name,pos,radius,height,mat,bone):
 bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=radius,radius2=.001,depth=height,location=pos);return bind(bpy.context.object,name,mat,bone)
def torus(name,pos,radius,minor,mat,bone):
 bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=minor,major_segments=40,minor_segments=8,location=pos);return bind(bpy.context.object,name,mat,bone)
# Layered cuirass and scale-like shoulder caps follow real torso/arm bones.
for sx in [-1,1]:
 sphere('Forged breastplate',(.087*sx,-.131,1.38),(.109,.043,.137),ARMOR,'spine03')
 cube('Gold breastplate rim',(.087*sx,-.17,1.29),(.19,.015,.012),GOLD,'spine03',.003)
 sphere('Segmented shoulder cap',(.223*sx,-.004,1.462),(.108,.112,.056),ARMOR,'upperarm01.'+('L' if sx>0 else 'R'))
 for j in range(3):
  cone('Shoulder crest',((.19+j*.037)*sx,-.012,1.51),.019,.045+j*.011,GOLD,'upperarm01.'+('L' if sx>0 else 'R'))
for z,width in [(1.21,.255),(1.16,.245),(1.11,.235)]:cube('Articulated abdominal plate',(0,-.143,z),(width,.032,.043),ARMOR,'spine04',.008)
sphere('Cuirass ember medallion',(0,-.183,1.38),(.035,.017,.041),GEM,'spine03')
# Ten crown points refer to the tenfold motif; this is a single-headed sentinel
# costume, not a claim to have produced a ten-headed mythological model.
torus('Tenfold crown base',(0,-.026,1.791),.125,.015,GOLD,'head')
for i in range(10):
 a=math.tau*i/10;x=.119*math.cos(a);y=-.026+.119*math.sin(a)
 cone('Tenfold crown point',(x,y,1.873),.025,.158 if i%2==0 else .126,GOLD,'head')
 sphere('Crown ember setting',(x*.98,y,1.796),(.011,.011,.014),GEM,'head')
# Join ornaments while preserving anatomy and skin weights by bone name.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for p in parts:p.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name='Ravana_sentinel_original_costume'
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
rig.data.pose_position='POSE'
for bone in rig.pose.bones:bone.matrix_basis.identity()
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True)
OUT.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_animations=False,export_skins=True,export_tangents=True,export_materials='EXPORT',export_extras=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_HASH
p=HERE/'actor-manifest.json';m=json.loads(p.read_text());m['actors']['ravana'].update({'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'bytes':OUT.stat().st_size,'bones':len(rig.data.bones),'source_sha256':SOURCE_HASH,'removed_bow_components':removed,'render_revision':'ActualR2 poses rejected: disconnected bow jewels and floating crown. Removed all disconnected wrist-bound weapon islands and back quiver; lowered crown85mm; abdominal plates fitted21mmcloser/narrower; armor roughness.58 andskinbasefactor recalibrated.', 'new_costume':'Original articulated blackened-bronze cuirass, crimson woven mantle, dark trousers, ten-point gold/ember crown and shoulder crest. Single-headed sentinel interpretation.','source_license':'CC0 MakeHuman anatomy and existing original YUGA costume/materials; see NOTICE/MAKEHUMAN-ASSET-LICENSE.md andNOTICE/ASSET-NOTICE.md.'});m['costume_generator_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();p.write_text(json.dumps(m,indent=2)+'\n')
print('RAVANA_FILM',json.dumps(m['actors']['ravana']),flush=True)
