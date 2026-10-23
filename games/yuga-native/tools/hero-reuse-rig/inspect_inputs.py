"""Read-only Blender inspection of the exact existing rig and generated source."""
import argparse,hashlib,json,sys,math
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
root=Path(__file__).resolve().parents[4]
inputs={'accepted':root/'games/yuga-native/assets/heroes/rama-hero.glb','generated':root/'games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb'}
result={'schema_version':1,'scope':'Input rest/posed data only; no geometry, rig or skin changes','inputs':{}}
for kind,path in inputs.items():
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
 points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
 low=[min(v[i] for v in points) for i in range(3)];high=[max(v[i] for v in points) for i in range(3)]
 result['inputs'][kind]={'path':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bounds':{'low':low,'high':high},'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'groups':len(o.vertex_groups),'armature_modifiers':[m.object.name for m in o.modifiers if m.type=='ARMATURE'],'matrix_world':[list(row) for row in o.matrix_world]} for o in meshes],'actions':[{'name':x.name,'range':list(x.frame_range)} for x in bpy.data.actions],'rigs':[]}
 for rig in rigs:
  result['inputs'][kind]['rigs'].append({'name':rig.name,'matrix_world':[list(row) for row in rig.matrix_world],'pose_position':rig.data.pose_position,'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(rig.matrix_world@b.head_local),'tail':list(rig.matrix_world@b.tail_local),'deform':b.use_deform} for b in rig.data.bones],'pose_matrices':[{'name':b.name,'matrix_basis':[list(row) for row in b.matrix_basis]} for b in rig.pose.bones]})
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('RIG_INPUT_INSPECTION_PASS')
