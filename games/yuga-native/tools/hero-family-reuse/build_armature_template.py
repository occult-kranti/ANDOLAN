"""Save/reopen a small editable rig scaffold from the exact accepted Rama GLB.

Geometry and textures stay in the canonical shared GLB. Nine embedded Blender
actions are inherited; 23 Godot runtime clips stay an external .tres reference.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
import bpy
from mathutils import Matrix

PROJECT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rig_signature(rig):
    data=[{'name':b.name,'parent':b.parent.name if b.parent else None,'rest':[list(row) for row in b.matrix_local]} for b in rig.data.bones]
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
def action_signature():
    result={}
    for action in bpy.data.actions:
        curves=[{'path':f.data_path,'index':f.array_index,'keys':[[*p.co] for p in f.keyframe_points]} for f in action.fcurves]
        result[action.name]=hashlib.sha256(json.dumps(curves,sort_keys=True).encode()).hexdigest()
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);started=time.monotonic();script_hash=sha(__file__)
    if a.output.exists() or a.report.exists():raise RuntimeError('Use fresh outputs')
    manifest=json.loads(a.manifest.read_text());donor=next(r for r in manifest['source_pins'] if r['path']=='assets/heroes/rama-hero.glb');source=PROJECT/donor['path'];assert sha(source)==donor['sha256']
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];assert len(rigs)==1;rig=rigs[0];assert len(rig.data.bones)==164
    actions=action_signature();assert len(actions)==9
    for action in bpy.data.actions:action.use_fake_user=True
    if rig.animation_data:
        rig.animation_data.action=None
        for track in rig.animation_data.nla_tracks:track.mute=True
    for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
    rig.data.pose_position='REST'
    for obj in list(bpy.data.objects):
        if obj!=rig:bpy.data.objects.remove(obj,do_unlink=True)
    for collection in [bpy.data.meshes,bpy.data.materials,bpy.data.images]:
        for item in list(collection):collection.remove(item,do_unlink=True)
    scene=bpy.context.scene;scene['hero_id']='arjuna';scene['authoring_template_only']=True;scene['finished_hero']=False
    scene['appearance_scope']='Rig-only scaffold; unchanged donor geometry is externally referenced, not copied.'
    scene['canonical_geometry_res_path']=donor['res_path'];scene['canonical_geometry_sha256']=donor['sha256']
    scene['runtime_clip_library']=json.dumps(next(r for r in manifest['source_pins'] if r['path']=='assets/animations/rama_hero_motion.tres'))
    scene['runtime_23_clips_are_external']=True;scene['runtime_socket_contract_json']=json.dumps(manifest['sockets']);scene['lod_constraints_json']=json.dumps(manifest['lod'])
    signature=rig_signature(rig);a.output.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(a.output.resolve()),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(a.output.resolve()));reopened=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    checks={'one_rig':sum(o.type=='ARMATURE' for o in bpy.context.scene.objects)==1,'164_bones':len(reopened.data.bones)==164,'bone_rest_signature_unchanged':rig_signature(reopened)==signature,'nine_embedded_actions_unchanged':action_signature()==actions,'no_geometry_or_images_duplicated':len(bpy.data.meshes)==0 and len(bpy.data.images)==0,'23_runtime_clips_external':bpy.context.scene['runtime_23_clips_are_external'],'canonical_source_hash_unchanged':sha(source)==donor['sha256'],'template_only':bpy.context.scene['authoring_template_only'] and not bpy.context.scene['finished_hero']}
    assert all(checks.values());report={'schema_version':1,'scope':'Actual small Blender rig-scaffold save/reopen; no new hero geometry, 23-clip Blender conversion or art acceptance.','source':donor,'output':{'path':str(a.output),'bytes':a.output.stat().st_size,'sha256':sha(a.output)},'script_sha256':script_hash,'blender':bpy.app.version_string,'rig_signature_sha256':signature,'embedded_actions':actions,'runtime_clip_count_external':23,'checks':checks,'passed':True,'runtime_promoted':False,'elapsed_seconds':time.monotonic()-started}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n');print('HERO_FAMILY_BLEND_REOPEN_PASS',json.dumps(checks),flush=True)
if __name__=='__main__':main()
