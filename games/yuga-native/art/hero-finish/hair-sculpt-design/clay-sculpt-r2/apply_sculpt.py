"""Apply only the new editable hair cage/depth to the locked authoring scene."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
sys.dont_write_bytecode=True
PROJECT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(PROJECT/'art/hero-finish/hair-sculpt-design/clay-framing-r3'))
from scene_semantics import snapshot,differences
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--cage',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert not a.output.exists();a.output.mkdir()
 parent=Path(bpy.data.filepath);assert sha(parent)=='71763ab25ed84719a8479bcce771732d50db980780b47c7c4b68114bf2bb9c2f'
 data=json.loads(a.cage.read_text());before=snapshot();hair=bpy.data.objects['EDITABLE_WholeHair_CoarseClay'];old=hair.data;name=old.name
 mesh=bpy.data.meshes.new(name+'_new_cage');mesh.from_pydata([(x,-z,y)for x,y,z in data['vertices']],[],data['faces']);mesh.update()
 for poly in mesh.polygons:poly.use_smooth=True
 for material in old.materials:mesh.materials.append(material)
 hair.data=mesh;bpy.data.meshes.remove(old);mesh.name=name
 for group in list(hair.vertex_groups):hair.vertex_groups.remove(group)
 for group_name,ids in data['groups'].items():hair.vertex_groups.new(name=group_name).add(ids,1.,'REPLACE')
 depth=hair.vertex_groups.new(name='Localized coarse volume')
 for i,w in enumerate(data['local_depth_weights']):
  if w>0:depth.add([i],w,'REPLACE')
 solid=next(m for m in hair.modifiers if m.type=='SOLIDIFY');solid.thickness=.016;solid.offset=-1;solid.vertex_group=depth.name;solid.thickness_vertex_group=.125
 after=snapshot();delta=differences(before,after)
 allowed=[f'.meshes.{name}',f'.objects.{hair.name}.vertex_groups',f'.objects.{hair.name}.modifiers']
 assert delta and all(any(row[0]==path or row[0].startswith(path+'.')for path in allowed)for row in delta),[row[0]for row in delta]
 (a.output/'semantic-before.json').write_text(json.dumps(before,sort_keys=True,separators=(',',':'))+'\n')
 (a.output/'semantic-after.json').write_text(json.dumps(after,sort_keys=True,separators=(',',':'))+'\n')
 actual=dict(data);actual['vertices']=[[float(v.co.x),float(v.co.z),float(-v.co.y)]for v in mesh.vertices]
 actual['faces']=[list(p.vertices)for p in mesh.polygons];actual['applier_sha256']=sha(__file__)
 (a.output/'source-cage-actual.json').write_text(json.dumps(actual,separators=(',',':'))+'\n')
 evaluated=hair.evaluated_get(bpy.context.evaluated_depsgraph_get());em=evaluated.to_mesh();derived=dict(actual)
 derived['vertices']=[[float(v.co.x),float(v.co.z),float(-v.co.y)]for v in em.vertices];derived['faces']=[list(p.vertices)for p in em.polygons]
 derived['evaluated_source_cage_sha256']=sha(a.output/'source-cage-actual.json');derived['groups']={}
 (a.output/'evaluated-clay.json').write_text(json.dumps(derived,separators=(',',':'))+'\n');evaluated.to_mesh_clear()
 destination=a.output/'whole-hair-clay-sculpt-r2.blend';bpy.ops.wm.save_as_mainfile(filepath=str(destination))
 (a.output/'hair-only-proof.json').write_text(json.dumps(dict(scope='Only coarse hair cage and localized depth changed; reference meshes, rig source, materials, lights and all four cameras preserved.',parent_scene_sha256=sha(parent),scene_sha256=sha(destination),difference_paths=[row[0]for row in delta],allowed_difference_prefixes=allowed,rendered=False,exported=False,imported=False),indent=2)+'\n')
 print('ONE_EDITABLE_SCULPT_SAVED',sha(destination),'REFS_CAMERAS_LIGHTS_MATERIALS_UNCHANGED',flush=True)
if __name__=='__main__':main()
