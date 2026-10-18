"""Read-only fresh reload protected reference, topology and projection checks."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
import bpy,bmesh,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'clay-framing-r3'))
from scene_semantics import snapshot,differences
from projection_contract import points,census,fits
parser=argparse.ArgumentParser()
parser.add_argument('--build',type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((args.build/'manifest.json').read_text())
assert sha(Path(bpy.data.filepath))==manifest['whole-hair-grouped-r1.blend']['sha256']
before=json.loads(gzip.decompress((args.build/'semantic-before.json.gz').read_bytes()))
after=json.loads(json.dumps(snapshot()))
def clean(v):
 if isinstance(v,dict):return {k:clean(x)for k,x in v.items()if k not in ['session_uid','users']}
 if isinstance(v,list):return [clean(x)for x in v]
 return v
def protected(v):
 result={k:clean(v[k])for k in ['cameras','materials','lights','worlds','scene']}
 result['objects']={k:clean(x)for k,x in v['objects'].items()if k!='EDITABLE_WholeHair_CoarseClay'and not k.startswith('SOURCE_LOFT_')}
 names={x['data']for x in result['objects'].values()if x['type']=='MESH'}
 result['meshes']={k:clean(v['meshes'][k])for k in names}
 return result
delta=differences(protected(before),protected(after))
topology={}
for obj in bpy.data.objects:
 if obj.name!='EDITABLE_WholeHair_CoarseClay'and not obj.name.startswith('SOURCE_LOFT_'):continue
 bm=bmesh.new();bm.from_mesh(obj.data)
 topology[obj.name]=dict(vertices=len(bm.verts),faces=len(bm.faces),boundary_edges=sum(e.is_boundary for e in bm.edges),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges))

 used=set(bm.verts);components=0
 while used:
  components+=1;todo=[used.pop()]
  while todo:
   for edge in todo.pop().link_edges:
    for vertex in edge.verts:
     if vertex in used:used.remove(vertex);todo.append(vertex)
 topology[obj.name]['connected_components']=components
 bm.free()
h,c=points(bpy.context.scene);projection=census(bpy.context.scene,h,c)
report=dict(scope='Fresh reloaded protected rest-space reference and simple source checks; no visible-contact or aesthetic claim',scene_sha256=sha(Path(bpy.data.filepath)),protected_differences=delta,protected_reference_preserved=not delta,process_only_fields_excluded=['session_uid','users'],topology=topology,projection=projection,projection_passed=all(fits(b)for row in projection.values()for b in row.values()),passed=not delta and all(r['nonmanifold_edges']==0 and r['connected_components']==27 for r in topology.values())and all(fits(b)for row in projection.values()for b in row.values()))
(args.build/'fresh-load-checks.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['passed'],report
obj=bpy.data.objects['EDITABLE_WholeHair_CoarseClay']
ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
verts=[Vector((v.co.x,v.co.z,-v.co.y))for v in mesh.vertices]
polys=[list(f.vertices)for f in mesh.polygons]
hair_tree=BVHTree.FromPolygons(verts,polys,all_triangles=False)
contacts={}
for name in ['LOCKED_0_0_Worked warm gold','LOCKED_2_2_Worked warm gold','LOCKED_2_11_Rama warm skin']:
 ref=bpy.data.objects[name]
 world=[ref.matrix_world@v.co for v in ref.data.vertices]
 rv=[Vector((v.x,v.z,-v.y))for v in world]
 tree=BVHTree.FromPolygons(rv,[list(f.vertices)for f in ref.data.polygons],all_triangles=False)
 overlap=hair_tree.overlap(tree)
 selected={a for a,b in overlap};pv=[verts[v]for a in selected for v in polys[a]]
 contacts[name]=dict(intersecting_polygon_pairs=len(overlap),hair_polygons_in_pairs=len(selected),hair_pair_region_gltf_m=dict(minimum=[min(v[k]for v in pv)for k in range(3)],maximum=[max(v[k]for v in pv)for k in range(3)])if pv else None)
band=[v for v in verts if 1.865<=v.y<=1.871]
bun_groups={g.index for g in obj.vertex_groups if g.name.startswith('Filled oblique gather lobe ')}
bun_band=[verts[v.index]for v in mesh.vertices if 1.865<=verts[v.index].y<=1.871 and any(g.group in bun_groups and g.weight>.5 for g in v.groups)]
group_bounds={}
for group in obj.vertex_groups:
 indices=[v.index for v in obj.data.vertices if any(g.group==group.index for g in v.groups)]
 vv=[Vector((obj.data.vertices[i].co.x,obj.data.vertices[i].co.z,-obj.data.vertices[i].co.y))for i in indices]
 group_bounds[group.name]=dict(minimum=[min(v[k]for v in vv)for k in range(3)],maximum=[max(v[k]for v in vv)for k in range(3)])
fit=dict(scope='Source-level rest-space measurements only. Buried seating intersections are allowed; visible scalp/hardware breakthrough and artistic silhouette require the four actual views.',evaluated_vertices=len(verts),evaluated_polygons=len(polys),context_polygon_intersections=contacts,tie_band_y_m=[1.865,1.871],tie_reference_inner_radius_m=.032075216,tie_band_hair_vertices=len(band),tie_band_max_radius_m=max((math.hypot(v.x,v.z+.04)for v in band),default=None),clump_bounds_gltf_m=group_bounds,source_helper_photo_objects_present=any('mh_helper'in o.name.lower()or 'referenceimage'in o.name.lower()for o in bpy.data.objects),materials_exactly_protected=not delta)
fit['tie_band_folded_bun_vertices']=len(bun_band)
fit['tie_band_folded_bun_max_radius_m']=max((math.hypot(v.x,v.z+.04)for v in bun_band),default=None)
fit['tie_band_global_measure_limit']='All-hair band also crosses forward scalp clumps; the global radius is not a tie-aperture fit assertion. Folded-bun subset is separately measured.'
ev.to_mesh_clear()
assert not fit['source_helper_photo_objects_present']
(args.build/'source-fit.json').write_text(json.dumps(fit,indent=2)+'\n')
print('FRESH_PROTECTED_TOPOLOGY_PROJECTION_PASS',len(topology),flush=True)
