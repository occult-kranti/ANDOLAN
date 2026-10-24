"""Cold-reopen R2 authoring invariants, without rendering or saving either master."""
import argparse, hashlib, json, math, struct, sys
from pathlib import Path
import bpy

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def digest(rows):
    h=hashlib.sha256()
    for row in rows:
        h.update(json.dumps(row,separators=(',',':'),allow_nan=False).encode())
        h.update(b'\n')
    return h.hexdigest()

def snapshot(obj, source_group_count=None):
    mesh=obj.data
    group_count=len(obj.vertex_groups) if source_group_count is None else source_group_count
    rig=next(m.object for m in obj.modifiers if m.type=='ARMATURE')
    return {
        'vertices':len(mesh.vertices), 'polygons':len(mesh.polygons),
        'basis':digest([list(v.co) for v in mesh.vertices]),
        'topology_material_slots':digest([[list(p.vertices),p.material_index,p.use_smooth] for p in mesh.polygons]),
        'uv_layers':{layer.name:digest([list(item.uv) for item in layer.data]) for layer in mesh.uv_layers},
        'color_attributes':{layer.name:{'domain':layer.domain,'data_type':layer.data_type,'values':digest([list(item.color) for item in layer.data])} for layer in mesh.color_attributes},
        'source_group_names':[obj.vertex_groups[i].name for i in range(group_count)],
        'source_skin':digest([[[g.group,g.weight] for g in v.groups if g.group<group_count] for v in mesh.vertices]),
        'material_names':[m.name if m else None for m in mesh.materials],
        'images':{im.name:{'size':list(im.size),'packed_sha256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None,'filepath':im.filepath} for im in bpy.data.images if im.name!='Render Result'},
        'rig_bones':digest([[b.name,b.parent.name if b.parent else None,[list(row) for row in b.matrix_local]] for b in rig.data.bones]),
        'rig_matrix':[list(row) for row in rig.matrix_world],
        'source_group_count':group_count,
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--ancestor-receipt',type=Path,required=True)
    parser.add_argument('--source-receipt',type=Path,required=True)
    parser.add_argument('--source-glb',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    parent=json.loads(args.ancestor_receipt.read_text()); source=json.loads(args.source_receipt.read_text())
    source_path=Path(source['scene']['path']); parent_path=Path(parent['scene']['path'])
    assert sha(source_path)==source['scene']['sha256']
    assert sha(parent_path)==parent['scene']['sha256']
    assert sha(args.source_glb)==source['source_sha256']==parent['source_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(parent_path))
    before=snapshot(bpy.data.objects['APPROVED BASELINE Rama'])
    bpy.ops.wm.open_mainfile(filepath=str(source_path))
    obj=bpy.data.objects['W3 existing-clump sculpt']; after=snapshot(obj,before['source_group_count'])
    basis=obj.data.shape_keys.key_blocks['Basis']; sculpt=obj.data.shape_keys.key_blocks['W3 two unequal nape flow families']
    selected=set(source['selected_vertex_ids']); protected=[i for i in range(len(obj.data.vertices)) if i not in selected]
    deltas=[(sculpt.data[i].co-basis.data[i].co).length for i in range(len(obj.data.vertices))]
    checks={
        'source_mesh_topology_uv_color_skin_material_images_rig_equal':before==after,
        'shape_basis_matches_original_mesh':all(tuple(v.co)==tuple(basis.data[i].co) for i,v in enumerate(obj.data.vertices)),
        'protected_shape_positions_exact':all(tuple(basis.data[i].co)==tuple(sculpt.data[i].co) for i in protected),
        'selected_and_protected_cover_mesh':len(selected)+len(protected)==len(obj.data.vertices),
        'all_candidate_positions_finite':all(math.isfinite(x) for v in sculpt.data for x in v.co),
        'all_four_locked_cameras_present':all(bpy.data.objects.get('R2 locked '+name) is not None for name in ['front','profile','rear','oblique']),
        'no_render_result':bpy.data.images.get('Render Result') is None,
        'canonical_and_masters_hashes_unchanged':sha(args.source_glb)==source['source_sha256'] and sha(source_path)==source['scene']['sha256'] and sha(parent_path)==parent['scene']['sha256'],
    }
    report={'schema_version':1,'scope':'Cold-reopened editable R2 source integrity only; no render, export, artistic or runtime acceptance','script_sha256':sha(__file__),'source_receipt_sha256':sha(args.source_receipt),'ancestor_receipt_sha256':sha(args.ancestor_receipt),'source_sha256':source['source_sha256'],'master_sha256':source['scene']['sha256'],'checks':checks,'all_passed':all(checks.values()),'source_snapshot':before,'reopened_snapshot':after,'selected_vertices':len(selected),'protected_vertices':len(protected),'changed_shape_vertices':sum(d>1e-8 for d in deltas),'maximum_shape_delta_m':max(deltas),'protected_maximum_delta_m':max(deltas[i] for i in protected),'canonical_promoted':False}
    args.output.parent.mkdir(parents=True,exist_ok=True); assert not args.output.exists()
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('W3_R2_SOURCE_VERIFY='+json.dumps({k:report[k] for k in ['all_passed','checks','selected_vertices','protected_vertices','changed_shape_vertices','maximum_shape_delta_m']},separators=(',',':')))
    if not report['all_passed']:raise RuntimeError('R2 source integrity failed')

if __name__=='__main__':main()
