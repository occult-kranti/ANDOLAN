"""Read licensed Blender donor datablocks only; no addon, evaluation, save or render."""
import argparse,hashlib,json,sys,math
from pathlib import Path
import bpy

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bounds(points):
    points=list(points)
    return {'min':[min(p[j] for p in points) for j in range(3)],'max':[max(p[j] for p in points) for j in range(3)]} if points else None

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    expected='93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5';assert sha(args.source)==expected
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(args.source),link=False) as (before,after):
        available={key:list(getattr(before,key)) for key in ['objects','materials','node_groups','meshes','hair_curves','texts'] if hasattr(before,key)}
        after.objects=list(before.objects)
    rows=[]
    for obj in after.objects:
        if obj is None:continue
        row={'name':obj.name,'type':obj.type,'matrix_world':[list(r) for r in obj.matrix_world],'parent':obj.parent.name if obj.parent else None,'custom_properties':{k:str(obj[k])[:300] for k in obj.keys()},'modifiers':[]}
        for modifier in obj.modifiers:
            group=getattr(modifier,'node_group',None)
            row['modifiers'].append({'name':modifier.name,'type':modifier.type,'node_group':group.name if group else None,'show_viewport':modifier.show_viewport,'show_render':modifier.show_render,'inputs':{k:str(modifier[k])[:300] for k in modifier.keys()}})
        if obj.type=='MESH':row.update({'vertices':len(obj.data.vertices),'polygons':len(obj.data.polygons),'local_bounds':bounds(v.co for v in obj.data.vertices),'uv_layers':[u.name for u in obj.data.uv_layers]})
        elif obj.type=='CURVES':
            data=obj.data;position=data.attributes.get('position');points=[tuple(v.vector) for v in position.data] if position else []
            row.update({'curve_count':len(data.curves),'point_count':len(data.points),'local_bounds':bounds(points),'surface':data.surface.name if data.surface else None,'surface_uv_map':data.surface_uv_map,'attributes':[{'name':a.name,'domain':a.domain,'data_type':a.data_type,'count':len(a.data)} for a in data.attributes],'first_curve_properties':list(data.curves[0].bl_rna.properties.keys()) if len(data.curves) else [],'finite_points':all(math.isfinite(x) for pt in points for x in pt)})
        if getattr(obj,'data',None) is not None and hasattr(obj.data,'materials'):row['materials']=[m.name if m else None for m in obj.data.materials]
        rows.append(row)
    groups=[]
    for group in bpy.data.node_groups:
        groups.append({'name':group.name,'node_count':len(group.nodes),'node_types':sorted(set(n.bl_idname for n in group.nodes)),'undefined_nodes':[n.name for n in group.nodes if n.bl_idname=='NodeUndefined'],'inputs':[{'name':item.name,'identifier':item.identifier,'socket_type':getattr(item,'socket_type',None)} for item in group.interface.items_tree if item.item_type=='SOCKET' and item.in_out=='INPUT']})
    materials=[{'name':m.name,'nodes':sorted(set(n.bl_idname for n in m.node_tree.nodes)) if m.use_nodes else [],'custom_properties':{k:str(m[k])[:300] for k in m.keys()}} for m in bpy.data.materials]
    report={'schema_version':1,'scope':'Actual read-only donor datablock inspection, no evaluation, addon installation, render, fit or adoption','reader':bpy.app.version_string,'source_header':args.source.read_bytes()[:12].decode(),'source_sha256':expected,'source_version_newer_than_reader':True,'script_sha256':sha(__file__),'available':available,'objects':rows,'node_groups':groups,'materials':materials,'images':[{'name':im.name,'size':list(im.size),'packed_sha256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None} for im in bpy.data.images],'texts_loaded':list(bpy.data.texts.keys()),'autoexec_enabled':bpy.context.preferences.filepaths.use_scripts_auto_execute,'undefined_node_count':sum(len(g['undefined_nodes']) for g in groups),'source_unchanged':sha(args.source)==expected,'canonical_adopted':False}
    assert not args.output.exists();args.output.write_text(json.dumps(report,indent=2)+'\n');print('HAIR_INTAKE='+json.dumps({'reader':report['reader'],'source_header':report['source_header'],'object_names':[o['name'] for o in rows],'undefined_node_count':report['undefined_node_count'],'autoexec_enabled':report['autoexec_enabled'],'source_unchanged':report['source_unchanged']}))
if __name__=='__main__':main()
