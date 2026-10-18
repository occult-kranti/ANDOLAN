"""Prepare exactly one editable connected C5 cage in the locked C4 scene.

No render/export/runtime write. Run only after W1 lane admission and >500MiB.
"""
import argparse,gzip,hashlib,json,os,shutil,sys
from pathlib import Path
import bpy,bmesh
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'clay-framing-r3'))
from scene_semantics import snapshot,differences
from projection_contract import points,census,fits
PARENT_SHA='da97ad89b5660eadc688eb58e4c73cad42b7b3f767daefb99c17028758439a88'
CAGE_SHA='c41a4893a76268b82e1312062ac3d28af889119c559e395f5394867d2a5929dd'
HAIR='EDITABLE_WholeHair_CoarseClay'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
def gz(p,value):
 with gzip.GzipFile(filename=str(p),mode='wb',mtime=0)as f:f.write(json.dumps(value,separators=(',',':')).encode())
def gltf(p):return [float(p.x),float(p.z),float(-p.y)]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--cage',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
 assert not a.output.exists(),'Fresh output required'
 assert shutil.disk_usage('/workspace').free>500*1024**2,'500MiB reserve required'
 assert sha(bpy.data.filepath)==PARENT_SHA
 assert sha(a.cage)==CAGE_SHA
 cage=json.loads(gzip.decompress(a.cage.read_bytes()))
 before=snapshot();material=bpy.data.objects[HAIR].data.materials[0]
 allowed=[]
 for old in list(bpy.data.objects):
  if old.name!=HAIR and not old.name.startswith('SOURCE_LOFT_'):continue
  mesh=old.data;allowed+=['.objects.'+old.name,'.meshes.'+mesh.name]
  bpy.data.objects.remove(old,do_unlink=True);bpy.data.meshes.remove(mesh)
 mesh=bpy.data.meshes.new(HAIR)
 mesh.from_pydata([(p[0],-p[2],p[1])for p in cage['vertices']],[],cage['faces']);mesh.update()
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 obj=bpy.data.objects.new(HAIR,mesh);bpy.context.scene.collection.objects.link(obj);mesh.materials.append(material)
 for f in mesh.polygons:f.use_smooth=True
 obj['role']='C5 original sculpt: one connected seated scalp, oblique shared-edge bun and layered asymmetric rear flow cage'
 obj['not_runtime']=True;obj['source_cage_sha256']=CAGE_SHA
 sub=obj.modifiers.new('Editable continuous sculpt smoothing','SUBSURF');sub.levels=1;sub.render_levels=1
 allowed+=['.objects.'+HAIR,'.meshes.'+mesh.name]
 bpy.context.view_layer.update()
 after=snapshot();delta=differences(before,after)
 unexpected=[row[0]for row in delta if not any(row[0]==p or row[0].startswith(p+'.')for p in allowed)and not row[0].endswith('.properties.users')]
 assert not unexpected,unexpected
 h,c=points(bpy.context.scene);projection=census(bpy.context.scene,h,c)
 assert all(fits(b)for row in projection.values()for b in row.values())
 a.output.mkdir(parents=True)
 os.link(a.cage,a.output/'source-cage.json.gz')
 gz(a.output/'semantic-before.json.gz',before);gz(a.output/'semantic-after.json.gz',after)
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());evaluated=ev.to_mesh()
 gz(a.output/'evaluated-clay.json.gz',dict(name=HAIR,vertices=[gltf(v.co)for v in evaluated.vertices],faces=[list(f.vertices)for f in evaluated.polygons]))
 counts=dict(evaluated_vertices=len(evaluated.vertices),evaluated_faces=len(evaluated.polygons));ev.to_mesh_clear()
 js(a.output/'projection.json',dict(views=projection,passed=True))
 js(a.output/'construction-receipt.json',dict(scope='C5 original connected editable major-shape sculpt; source preparation only, inactive',parent_sha256=PARENT_SHA,builder_sha256=sha(__file__),cage_sha256=CAGE_SHA,source_vertices=len(mesh.vertices),source_faces=len(mesh.polygons),source_mesh_count=1,source_connected=True,subdivision_levels=1,voxel_union=False,protected_reference_changes=unexpected,allowed_difference_prefixes=allowed,difference_paths=[row[0]for row in delta],reference_geometry_preserved=True,projection_passed=True,no_render=True,no_export=True,actual_review='pending',**counts))
 assert shutil.disk_usage('/workspace').free>500*1024**2
 destination=a.output/'whole-hair-volume-r5.blend'
 bpy.ops.wm.save_as_mainfile(filepath=str(destination),compress=True)
 js(a.output/'manifest.json',{p.name:dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(a.output.iterdir())if p.is_file()})
 print('C5_CONNECTED_CAGE_SAVED',destination,sha(destination),flush=True)
if __name__=='__main__':main()
