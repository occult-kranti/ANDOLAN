"""Three diagnostic source-mask views, no deletion or fitted candidate."""
import argparse,hashlib,json,struct,sys,time
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from freeze_mask import digest_faces
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def main():
 p=argparse.ArgumentParser();p.add_argument('--studio',type=Path,required=True);p.add_argument('--mask',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);start=time.monotonic();assert sha(a.studio)=='9fe7b4115f2680f06a320965afdabcd9c5a2b428372b9166be5ad1be187ec398';r=json.loads(a.mask.read_text());a.output.mkdir(parents=True,exist_ok=False);bpy.ops.wm.open_mainfile(filepath=str(a.studio.resolve()));scene=bpy.context.scene;o=bpy.data.objects['geometry_0'];m=o.data
 assert hashlib.sha256(b''.join(struct.pack('<3f',*v.co) for v in m.vertices)).hexdigest()==r['positions_sha256']
 assert digest_faces(m,r['protected_face_ids'])==r['protected_faces_uv_digest'];assert digest_faces(m,r['selected_face_ids'])==r['selected_faces_uv_digest']
 def diagnostic(name,color):
  mat=bpy.data.materials.new(name);mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(*color,1);bsdf.inputs['Roughness'].default_value=.62;m.materials.append(mat);return len(m.materials)-1
 red=diagnostic('RED proposed hair-only omission; UNVALIDATED',(1,.015,.015));amber=diagnostic('AMBER mixed-corner triangles PROTECTED',(1,.45,.015))
 for i in r['selected_face_ids']:m.polygons[i].material_index=red
 for i in r['mixed_corner_faces_explicitly_PROTECTED']:m.polygons[i].material_index=amber
 scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=False;scene.cycles.seed=0;scene.cycles.use_animated_seed=False
 center=Vector((.00036856532096862793,-.0015292912721633911,-.0005865693092346191));span=1.0021296739578247;frames=[]
 for name,offset in [('rear',(-1.1,3,.75)),('rear-left',(-2.4,2.4,.75)),('rear-right',(2.4,2.4,.75))]:
  scene.camera.location=center+Vector(offset)*span;aim(scene.camera,center);scene.camera.data.ortho_scale=span*1.25;scene.render.filepath=str(a.output/(name+'.png'));begin=time.monotonic();bpy.ops.render.render(write_still=True);path=a.output/(name+'.png');frames.append({'path':path.name,'sha256':sha(path),'bytes':path.stat().st_size,'camera_offset_in_source_span':offset,'seconds':time.monotonic()-begin})
 report={'schema_version':1,'scope':'Conservative semantic mask proposal only: RED proposed omission, AMBER mixed triangles protected. No geometry removed/donor fitted.','source_sha256':r['source_sha256'],'studio_sha256':sha(a.studio),'mask_sha256':sha(a.mask),'script_sha256':sha(__file__),'blender':bpy.app.version_string,'threads':2,'renderer':'Cycles CPU','samples':32,'seed':0,'denoising':False,'resolution':[640,800],'frames':frames,'source_positions_unchanged':True,'source_triangles_retained':len(m.polygons),'positive_completion':len(frames)==3,'elapsed_seconds':time.monotonic()-start}
 (a.output/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print('YUGA_DONOR_MASK='+json.dumps(report,separators=(',',':')))
if __name__=='__main__':main()
