"""Matched original/candidate renders reusing the frozen original intake studio."""
import argparse,hashlib,json,sys,time
from pathlib import Path
import bpy
from mathutils import Vector

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def aim(obj,p):obj.rotation_euler=(Vector(p)-obj.location).to_track_quat('-Z','Y').to_euler()
def main():
 p=argparse.ArgumentParser();p.add_argument('--studio',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--candidate-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);start=time.monotonic();assert sha(a.studio)=='9fe7b4115f2680f06a320965afdabcd9c5a2b428372b9166be5ad1be187ec398';candidate_report=json.loads(a.candidate_report.read_text());assert sha(a.candidate)==candidate_report['candidate_sha256']
 a.output.mkdir(parents=True,exist_ok=False);bpy.ops.wm.open_mainfile(filepath=str(a.studio.resolve()));scene=bpy.context.scene;source=bpy.data.objects['geometry_0'];before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(a.candidate.resolve()));candidate=next(o for o in set(bpy.data.objects)-before if o.type=='MESH');source.name='Original source';candidate.name='Masked cleanup candidate';candidate.hide_render=True
 scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=False;scene.cycles.seed=0;scene.cycles.use_animated_seed=False
 center=Vector((.00036856532096862793,-.0015292912721633911,-.0005865693092346191));span=1.0021296739578247;camera=scene.camera;frames=[]
 for view,offset in [('front',(1.1,-3,.75)),('rear',(-1.1,3,.75))]:
  camera.location=center+Vector(offset)*span;aim(camera,center);camera.data.ortho_scale=span*1.25
  for variant in ('original','candidate'):
   source.hide_render=variant!='original';candidate.hide_render=variant!='candidate';path=a.output/(view+'-'+variant+'.png');scene.render.filepath=str(path);begin=time.monotonic();bpy.ops.render.render(write_still=True);frames.append({'path':path.name,'sha256':sha(path),'bytes':path.stat().st_size,'seconds':time.monotonic()-begin,'view':view,'variant':variant,'camera_offset':offset})
 # A diagnostic material shows the exact changed vertices over the original mesh.
 source.hide_render=False;candidate.hide_render=True;mask=source.data.color_attributes.new(name='CleanupMask',type='FLOAT_COLOR',domain='POINT');ids=set(candidate_report['changed_vertex_ids'])
 for i,c in enumerate(mask.data):c.color=(1,0,0,1) if i in ids else (0,0,0,1)
 mat=source.data.materials[0].copy();source.data.materials[0]=mat;nodes=mat.node_tree.nodes;links=mat.node_tree.links;bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');original_socket=bsdf.inputs['Base Color'].links[0].from_socket;attribute=nodes.new('ShaderNodeVertexColor');attribute.layer_name='CleanupMask';mix=nodes.new('ShaderNodeMixRGB');mix.inputs[2].default_value=(1,.015,.015,1);links.new(attribute.outputs['Color'],mix.inputs[0]);links.new(original_socket,mix.inputs[1]);links.new(mix.outputs[0],bsdf.inputs['Base Color']);path=a.output/'rear-diagnostic-mask.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);frames.append({'path':path.name,'sha256':sha(path),'bytes':path.stat().st_size,'view':'rear','variant':'diagnostic changed-vertex mask; not a candidate look'})
 report={'schema_version':1,'scope':'Matched image comparison only; no artistic acceptance by renderer.','studio_sha256':sha(a.studio),'candidate_sha256':sha(a.candidate),'candidate_report_sha256':sha(a.candidate_report),'script_sha256':sha(__file__),'blender':bpy.app.version_string,'renderer':'Cycles CPU','samples':32,'denoising':False,'threads':2,'seed':0,'resolution':[640,800],'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'source_geometry_unchanged':True,'frames':frames,'positive_completion':len(frames)==5 and all((a.output/f['path']).is_file() for f in frames),'elapsed_seconds':time.monotonic()-start}
 (a.output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print('YUGA_CLEANUP_COMPARISON='+json.dumps(report,separators=(',',':')))
if __name__=='__main__':main()
