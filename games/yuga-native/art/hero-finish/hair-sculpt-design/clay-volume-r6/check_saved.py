"""Read-only fresh reload protected reference, topology and projection checks."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
import bpy,bmesh
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'clay-framing-r3'))
from scene_semantics import snapshot,differences
from projection_contract import points,census,fits
parser=argparse.ArgumentParser()
parser.add_argument('--build',type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((args.build/'manifest.json').read_text())
assert sha(Path(bpy.data.filepath))==manifest['whole-hair-sculpt-r6.blend']['sha256']
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
report=dict(scope='Fresh reloaded protected rest-space reference and simple source checks; no visible-contact or aesthetic claim',scene_sha256=sha(Path(bpy.data.filepath)),protected_differences=delta,protected_reference_preserved=not delta,process_only_fields_excluded=['session_uid','users'],topology=topology,projection=projection,projection_passed=all(fits(b)for row in projection.values()for b in row.values()),passed=not delta and all(r['nonmanifold_edges']==0 and r['connected_components']==1 for r in topology.values())and all(fits(b)for row in projection.values()for b in row.values()))
(args.build/'fresh-load-checks.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['passed'],report
print('FRESH_PROTECTED_TOPOLOGY_PROJECTION_PASS',len(topology),flush=True)
