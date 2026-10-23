"""Render actual frozen skinning failures in the reused source-intake studio."""
import argparse, hashlib, json, runpy, sys, time
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[4]
STUDIO=ROOT/'games/yuga-native/tools/production-art-stage/inspect_generated_hero.py'
aim=runpy.run_path(str(STUDIO))['aim']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(parents=True,exist_ok=False)
    script_hash=sha(__file__);started=time.monotonic();bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()))
    scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');target=bpy.data.objects['Rama generated skin-transfer candidate']
    for o in list(scene.objects):o.hide_render=o!=target
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=False
    scene.render.threads_mode='FIXED';scene.render.threads=1;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    scene.world=bpy.data.worlds.new('Reused source intake neutral studio');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.08,.105,.14,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
    # Same light ratios/color/scale contract as the generated source intake.
    center=Vector((0,0,.96));span=1.92
    for name,offset,power,color in [('warm key',(2,-3,4),550,(1,.88,.72)),('cool fill',(-3,-1,2),260,(.65,.8,1)),('ivory rim',(1,3,3),650,(1,.93,.8))]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power*span*span;data.color=color;data.size=span*3;data.shape='DISK'
        light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=center+Vector(offset)*span;aim(light,center)
    data=bpy.data.cameras.new('Frozen transfer diagnosis');camera=bpy.data.objects.new('Frozen transfer diagnosis',data);scene.collection.objects.link(camera);scene.camera=camera;data.type='ORTHO'
    rows=[]
    shots=[('rest','REST',0,(0,-6,.99),(0,0,.96),2.36,480,600),('idle','idle',0,(0,-6,.99),(0,0,.96),2.36,480,600),('fire','fire',8,(0,-6,.99),(0,0,.96),2.36,480,600),('fire-wrist','fire',8,(-2,-5,1.25),(-.24,-.15,1.15),1.25,480,480),('run-cloth','run',5,(0,-6,.8),(0,0,.65),1.43,480,480)]
    for name,action_name,frame,pos,look,scale,width,height in shots:
        rig.animation_data.action=None
        for t in rig.animation_data.nla_tracks:t.mute=True
        for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
        if action_name!='REST':rig.animation_data.action=next(x for x in bpy.data.actions if x.name.startswith(action_name+'_'))
        scene.frame_set(frame);bpy.context.view_layer.update();camera.location=pos;aim(camera,look);data.ortho_scale=scale
        scene.render.resolution_x=width;scene.render.resolution_y=height;scene.render.filepath=str(a.output/(name+'.png'));begin=time.monotonic();bpy.ops.render.render(write_still=True)
        path=Path(scene.render.filepath);rows.append({'file':path.name,'sha256':sha(path),'bytes':path.stat().st_size,'action':action_name,'frame':frame,'camera':{'position':pos,'target':look,'ortho_scale':scale},'seconds':time.monotonic()-begin})
        print('RIG_POSE_VIEW_SAVED',name,flush=True)
    report={'schema_version':1,'scope':'Actual frozen nearest-transfer rest and action views. Defects intentionally visible; not accepted art or gameplay. No bow is present on new generated source.','scene':{'path':str(a.scene),'sha256':sha(a.scene)},'script_sha256':script_hash,'reused_studio_helper':{'path':str(STUDIO.relative_to(ROOT)),'sha256':sha(STUDIO)},'renderer':'Cycles CPU','samples':16,'threads':1,'denoising':False,'images':rows,'runtime_promoted':False,'quality_accepted':False,'elapsed_seconds':time.monotonic()-started}
    (a.output/'views.json').write_text(json.dumps(report,indent=2)+'\n');print('RIG_POSE_VIEWS_PASS',json.dumps({'count':len(rows),'seconds':report['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
