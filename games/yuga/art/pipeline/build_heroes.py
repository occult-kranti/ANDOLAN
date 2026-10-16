"""Reproducible authored Yuga heroes. Blender 4.3+, no downloaded executable code.

blender -b --factory-startup -t 2 --python games/yuga/art/pipeline/build_heroes.py -- rama --preview
Omit hero IDs to build the whole roster. All source data is pinned and bundled.
"""
import sys, json, math, hashlib, struct
from array import array
from pathlib import Path
import bpy, bmesh
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from anatomy import build_anatomy
from geometry import Sculpt, costume, face_and_hair, weapon
from animations import author_animations

ART=HERE.parent; GAME=ART.parent; SOURCE=ART/'sources/makehuman'; OUT=GAME/'client/assets/heroes'
COMMIT='a8bc2d54ff0ac92e78ff71431b1023eda42bf482'
PIPELINE_HASHES={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))}
HEROES=[
 dict(id='rama',sex='male',height=1.85,width=1.,face_width=.98,weapon='bow',cloth=(.025,.055,.22),gem=(.025,.18,.45),skin=(.34,.17,.085),hair='knot',crown=.05,brocade=True),
 dict(id='hanuman',sex='male',height=2.02,width=1.25,face_width=1.2,weapon='mace',cloth=(.38,.018,.025),gem=(.8,.18,.025),skin=(.33,.17,.07),hair='knot',crown=.10,beard=False),
 dict(id='sita',sex='female',height=1.75,width=1.,face_width=.97,weapon='staff',cloth=(.018,.20,.075),gem=(.018,.55,.24),skin=(.37,.20,.11),hair='braid',crown=.065),
 dict(id='ravana',sex='male',height=1.97,width=1.18,face_width=1.15,weapon='chakram',cloth=(.16,.015,.20),gem=(.7,.02,.08),skin=(.24,.105,.05),hair='long',crown=.14,beard=True,ivory_skirt=False),
 dict(id='arjuna',sex='male',height=1.86,width=1.02,face_width=.94,weapon='bow',cloth=(.025,.12,.33),gem=(.12,.5,.75),skin=(.38,.205,.105),hair='long',crown=.075,brocade=True),
 dict(id='duryodhana',sex='male',height=1.91,width=1.22,face_width=1.12,weapon='mace',cloth=(.29,.07,.015),gem=(.75,.22,.025),skin=(.32,.15,.065),hair='knot',crown=.09,beard=True,ivory_skirt=False),
 dict(id='karna',sex='male',height=1.90,width=1.08,face_width=.99,weapon='bow',cloth=(.46,.18,.025),gem=(.95,.38,.025),skin=(.40,.22,.11),hair='knot',crown=.10),
 dict(id='bhima',sex='male',height=2.08,width=1.28,face_width=1.18,weapon='mace',cloth=(.08,.15,.035),gem=(.3,.55,.08),skin=(.29,.125,.05),hair='knot',crown=.04,beard=True),
 dict(id='meghnad',sex='male',height=1.87,width=.98,face_width=.96,weapon='bow',cloth=(.12,.025,.24),gem=(.5,.08,.75),skin=(.25,.13,.07),hair='long',crown=.12,brocade=True,ivory_skirt=False),
 dict(id='draupadi',sex='female',height=1.78,width=1.04,face_width=1.03,weapon='staff',cloth=(.36,.018,.11),gem=(.75,.08,.20),skin=(.28,.12,.065),hair='braid',crown=.09),
 dict(id='subhadra',sex='female',height=1.73,width=1.02,face_width=.96,weapon='spear',cloth=(.018,.20,.25),gem=(.1,.65,.7),skin=(.42,.245,.14),hair='braid',crown=.045),
 dict(id='hidimbi',sex='female',height=1.94,width=1.18,face_width=1.08,weapon='spear',cloth=(.035,.13,.04),gem=(.25,.65,.12),skin=(.22,.11,.055),hair='long',crown=.075,ivory_skirt=False),
 dict(id='chitrangada',sex='female',height=1.80,width=1.06,face_width=1.,weapon='spear',cloth=(.28,.035,.055),gem=(.55,.14,.055),skin=(.34,.175,.09),hair='knot',crown=.055),
 dict(id='ulupi',sex='female',height=1.82,width=.98,face_width=.93,weapon='staff',cloth=(.015,.19,.21),gem=(.05,.7,.58),skin=(.29,.19,.13),hair='braid',crown=.105,ivory_skirt=False),
]


def material(name,color,metal=0,rough=.5,texture=None):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    node=m.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Metallic'].default_value=metal;node.inputs['Roughness'].default_value=rough
    if texture and texture.exists():
        image=bpy.data.images.load(str(texture),check_existing=True)
        if max(image.size)>1024:image.scale(1024,1024)
        image.pack()
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
        m.node_tree.links.new(tex.outputs['Color'],node.inputs['Base Color'])
    return m


def materials(c):
    texture=ART/'textures/indigo-brocade.png' if c.get('brocade') else None
    goldtexture=ART/'textures/engraved-gold.png'
    result=dict(skin=material('Warm skin',c['skin'],rough=.58),cloth=material('Woven hero cloth',c['cloth'],rough=.72,texture=texture),
        ivory=material('Ivory woven silk',(.62,.52,.33),rough=.8),gold=material('Chased antique gold',(.65,.36,.075),metal=.8,rough=.31,texture=goldtexture),
        gem=material('Cut hero gemstone',c['gem'],metal=.3,rough=.19),hair=material('Sculpted dark hair',(.015,.009,.006),rough=.72),fur=material('Warm simian fur',(.12,.055,.021),rough=.9),eyes=material('Eye whites',(.55,.45,.32),rough=.28),iris=material('Natural amber iris',(.12,.042,.013),rough=.4),lips=material('Natural lip contour',(.22,.055,.035),rough=.6))
    if not texture:
        # Original mathematical jacquard, authored for these 3D materials.
        # It is not a recoloured commercial texture or inferred normal map.
        size=512;pixels=array('f');gold=(.52,.31,.075)
        for y in range(size):
            for x in range(size):
                u=(x/size*8)%1-.5;v=(y/size*8)%1-.5;r=math.hypot(u,v);a=math.atan2(v,u)
                thread=abs(r-(.16+.045*math.cos(6*a)))<.012 or abs(abs(u)+abs(v)-.46)<.009
                shade=.92+.08*((x+y)%2)
                color=gold if thread else c['cloth'];pixels.extend((color[0]*shade,color[1]*shade,color[2]*shade,1))
        image=bpy.data.images.new(c['id']+' original woven jacquard',width=size,height=size);image.pixels.foreach_set(pixels);image.pack()
        node=result['cloth'].node_tree.nodes.new('ShaderNodeTexImage');node.image=image
        result['cloth'].node_tree.links.new(node.outputs['Color'],result['cloth'].node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    return result


def preview(rig,actions,hero):
    scene=bpy.context.scene;rig.animation_data.action=actions['idle'];scene.frame_set(1)
    # Real authored, skinned asset in a neutral presentation scene, not generated key art.
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=False
    scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.world.color=(.025,.03,.05)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.02));ground=bpy.context.object
    ground.data.materials.append(material('Preview ground',(.025,.032,.048),rough=.8))
    for pos,power,size in [((2,-4,5),500,4),((-3,-1,3),260,3),((0,3,4),650,3)]:
        data=bpy.data.lights.new('Studio area','AREA');data.energy=power;data.shape='DISK';data.size=size
        light=bpy.data.objects.new('Studio area',data);scene.collection.objects.link(light);light.location=pos;light.rotation_euler=(Vector((0,0,1.1))-light.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('Actual model preview');camera=bpy.data.objects.new('Actual model preview',data);scene.collection.objects.link(camera)
    camera.location=(2.9,-5.4,2.75);target=Vector((0,0,hero['height']*.53));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=2.75;scene.camera=camera
    scene.view_settings.view_transform='AgX';scene.render.filepath=str(ART/'previews'/f"{hero['id']}-actual-model.png")
    bpy.ops.render.render(write_still=True)
    camera.location=(.7,-3,hero['height']*.96);target=Vector((0,-.05,hero['height']*.915));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();data.ortho_scale=.56
    scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.filepath=str(ART/'previews'/f"{hero['id']}-actual-face.png")
    bpy.ops.render.render(write_still=True)


def build(c,render=False):
    # Hidden validation copies are intentionally not operator-selectable.
    # Remove data objects explicitly so each hero gets exactly its current rig.
    for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
    for action in list(bpy.data.actions):bpy.data.actions.remove(action)
    body,rig,weights,tree=build_anatomy(SOURCE,c['sex'],c['height'],c['width'],c['face_width'])
    # Full continuous anatomy remains in the local .blend for independent motion
    # tests, excluded from selected export and from every presentation render.
    validation=body.copy();validation.data=body.data.copy();validation.name='ValidationAnatomy'
    bpy.context.collection.objects.link(validation);validation.hide_render=True;validation.hide_set(True);validation.select_set(False)
    if c['weapon']=='bow':
        # Original helper deforms only the string midpoint; anatomy stays native.
        bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
        wrist=rig.data.edit_bones['wrist.R'];bone=rig.data.edit_bones.new('bowstring')
        bone.head=wrist.head+wrist.matrix.to_3x3()@Vector((0,-.100,.025))*(c['height']/1.85)
        bone.tail=bone.head+wrist.matrix.to_3x3()@Vector((0,.02,0));bone.parent=wrist
        bpy.ops.object.mode_set(mode='OBJECT')
    m=materials(c)
    for key in ('skin','cloth','ivory'):body.data.materials.append(m[key])
    for polygon in body.data.polygons:
        p=polygon.center
        # Opaque fitted clothing stays beneath all separately modeled drapery.
        polygon.material_index=2 if p.z<c['height']*.54 else (1 if p.z<c['height']*.825 and abs(p.x)<c['height']*.14 else 0)
    sculpt=Sculpt(rig,body,weights,tree)
    costume(sculpt,c['height'],c,m);face_and_hair(sculpt,c['height'],c,m);weapon(sculpt,c['height'],c,m)
    # Delete fully occluded source anatomy, retaining face, arms, hands and feet.
    edit=bmesh.new();edit.from_mesh(body.data)
    hidden=[]
    for face in edit.faces:
        p=face.calc_center_median()
        if c['height']*.09<p.z<c['height']*.52 or c['height']*.54<p.z<c['height']*.82 and abs(p.x)<c['height']*.135:hidden.append(face)
    bmesh.ops.delete(edit,geom=hidden,context='FACES')
    loose=[v for v in edit.verts if not v.link_faces]
    bmesh.ops.delete(edit,geom=loose,context='VERTS');edit.to_mesh(body.data);edit.free();body.data.update()
    # Join weighted surfaces to one mesh; materials and native joint groups survive.
    bpy.ops.object.select_all(action='DESELECT')
    for obj in sculpt.objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=c['id']+'_skinned_hero'
    # Joined objects share one armature; avoid repeated deformation modifiers.
    for modifier in list(body.modifiers)[1:]:body.modifiers.remove(modifier)
    # Bounded topology reduction; facial anatomy remains far denser than the old primitives.
    reduce=body.modifiers.new('Game mesh reduction','DECIMATE');reduce.ratio=.72
    bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=reduce.name)
    actions=author_animations(rig,c['weapon'],c['id']);rig.animation_data.action=actions['idle']
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
    OUT.mkdir(parents=True,exist_ok=True);path=OUT/f"{c['id']}.glb"
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_skins=True,export_all_influences=False,export_yup=True,export_image_format='JPEG',export_jpeg_quality=85)
    binary=path.read_bytes();length,kind=struct.unpack_from('<II',binary,12);doc=json.loads(binary[20:20+length])
    primitives=[p for mesh in doc.get('meshes',[]) for p in mesh['primitives']]
    result=dict(id=c['id'],file=str(path.relative_to(GAME)),bytes=len(binary),sha256=hashlib.sha256(binary).hexdigest(),
        triangles=sum(doc['accessors'][p['indices']]['count']//3 for p in primitives),vertices=sum(doc['accessors'][p['attributes']['POSITION']]['count'] for p in primitives),
        bones=len(rig.data.bones),materials=len(doc.get('materials',[])),clips=[a['name'] for a in doc.get('animations',[])],heightMetres=c['height'],weapon=c['weapon'],
        pipelineHashes=PIPELINE_HASHES)
    print('YUGA_HERO '+json.dumps(result),flush=True)
    output=Path('/workspace/tooling/yuga-art/output');output.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output/f"{c['id']}-authored.blend"))
    if render:preview(rig,actions,c)
    return result


def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    requested=[a for a in args if not a.startswith('--')];selected=[c for c in HEROES if not requested or c['id'] in requested]
    unknown=set(requested)-{c['id'] for c in HEROES};assert not unknown,unknown
    manifest_path=ART/'hero-assets.json';manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    models={m['id']:m for m in manifest.get('models',[])}
    for config in selected:
        models[config['id']]=build(config,'--preview' in args)
        manifest=dict(schema=1,sourceCommitMakeHuman=COMMIT,sourceLicense='CC0-1.0 data; original costume/weapon/hair/animation code',
            sourceManifestSha256=hashlib.sha256((SOURCE/'manifest.json').read_bytes()).hexdigest(),
            sourceFiles=[dict(file=str(p.relative_to(ART)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(SOURCE.iterdir()) if p.is_file()],
            pipelineFiles=[dict(file=str(p.relative_to(ART)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(HERE.glob('*.py'))],
            textureSources=[dict(file=str(p.relative_to(ART)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((ART/'textures').glob('*.png'))],
            models=list(models.values()),front='+Z',up='+Y',units='metres',limitations=['First authored browser art pass, not commercial key-art fidelity.','No LODs, Draco compression, facial blendshape system or cloth simulation.','Rig weights are normalized to four influences.'])
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
