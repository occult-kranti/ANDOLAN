"""Save one editable authoring .blend from the cage. Never renders or exports."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy
from mathutils import Vector

def main():
    p=argparse.ArgumentParser();p.add_argument('--cage',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert not a.output.exists()
    data=json.loads(a.cage.read_text())
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    scene['evidence_scope']='Original authoring clay only. Not a game capture, runtime material, cast clearance, or promoted asset.'
    scene['source_glb_sha256']=data['source_glb_sha256'];scene['cage_sha256']=hashlib.sha256(a.cage.read_bytes()).hexdigest()
    scene['coordinates']='Rigid glTF (x,y,z) -> Blender (x,-z,y); no scaling.'
    def transform(v):return(v[0],-v[2],v[1])
    def material(name,color):
        mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(*color,1);bsdf.inputs['Roughness'].default_value=.75
        return mat
    clay=material('Neutral warm clay — design only',(.38,.30,.24))
    anatomy=material('Locked source anatomy — neutral reference',(.28,.31,.34))
    hardware=material('Locked source crown/tie — neutral reference',(.50,.52,.56))
    other=material('Locked source garment/prop — neutral reference',(.18,.21,.25))
    def mesh(name,vertices,faces):
        m=bpy.data.meshes.new(name);m.from_pydata([transform(v)for v in vertices],[],faces);m.update()
        obj=bpy.data.objects.new(name,m);scene.collection.objects.link(obj)
        for poly in m.polygons:poly.use_smooth=True
        return obj
    hair=mesh('EDITABLE_WholeHair_CoarseClay',data['vertices'],data['faces']);hair.data.materials.append(clay)
    for name,indices in data['groups'].items():
        group=hair.vertex_groups.new(name=name);group.add(indices,1.,'REPLACE')
    sub=hair.modifiers.new('Editable coarse subdivision — not applied','SUBSURF');sub.levels=1;sub.render_levels=1
    solid=hair.modifiers.new('Hidden shell thickness — not applied','SOLIDIFY');solid.thickness=.002;solid.offset=-1
    hair['status']='Single connected author cage. No fine strands, UV, skin weights, LODs or GLB. Await four-view clay review.'
    for row in data['reference_meshes']:
        obj=mesh(row['name'],row['vertices'],row['faces']);obj.hide_select=True
        obj['locked_source']='Exact source rest positions/triangles extracted for authoring reference; not a reexported rig.'
        obj['source_primitive']=f"{row['mesh']}:{row['primitive']}";obj['source_material_name']=row['material']
        mat=hardware if 'gold'in row['material'].lower()or'sapphire'in row['material'].lower()else anatomy if row['material']in ['Rama warm skin','Natural lips','Warm sclera','Deep brown iris','Pupil']else other
        obj.data.materials.append(mat)
    target=Vector(transform([0,1.755,-.010]))
    cameras={'front':[0,1.79,.73],'anatomical-left-profile':[.73,1.79,-.010],
             'rear':[0,1.79,-.75],'cast-angle-authoring':[.48,1.85,.56]}
    for name,pos in cameras.items():
        cam=bpy.data.cameras.new(name);cam.lens=55;cam.clip_start=.01;cam.clip_end=10
        obj=bpy.data.objects.new('VIEW_'+name,cam);scene.collection.objects.link(obj);obj.location=transform(pos)
        obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
        obj['view_scope']='Rest-space authoring silhouette; cast-angle is a three-quarter design view, not the actual animated cast.'
    scene.camera=bpy.data.objects['VIEW_front']
    for name,pos,energy,size in [('Key',[.55,2.25,.65],70,.65),('Fill',[-.55,1.95,.3],35,.60),('Rim',[.1,2.1,-.5],50,.45)]:
        light=bpy.data.lights.new(name,'AREA');light.energy=energy;light.shape='DISK';light.size=size
        obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj);obj.location=transform(pos);obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
    scene.world.color=(.20,.20,.20);scene.render.engine='CYCLES';scene.cycles.samples=32
    scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
    bpy.ops.object.select_all(action='DESELECT');hair.select_set(True);bpy.context.view_layer.objects.active=hair
    a.output.parent.mkdir(parents=True,exist_ok=True)
    # Persist actual evaluated clay surfaces for a bounded rest-space check.
    # This is geometry evaluation during source save, never a framebuffer.
    evaluated=hair.evaluated_get(bpy.context.evaluated_depsgraph_get());evaluated_mesh=evaluated.to_mesh()
    derived=dict(data);derived['vertices']=[[float(v.co.x),float(v.co.z),float(-v.co.y)]for v in evaluated_mesh.vertices]
    derived['faces']=[list(poly.vertices)for poly in evaluated_mesh.polygons]
    derived['kind']='Actual evaluated authoring clay subdivision1 + inward2mm thickness; not runtime evidence'
    derived['groups']={};derived['evaluated_source_cage_sha256']=scene['cage_sha256']
    derived['modifiers']=dict(subdivision_levels=1,render_levels=1,solidify_thickness_m=.002,solidify_offset=-1)
    a.output.with_name('clay-evaluated.json').write_text(json.dumps(derived,separators=(',',':'))+'\n')
    evaluated.to_mesh_clear()
    bpy.ops.wm.save_as_mainfile(filepath=str(a.output))
    print('SAVED_EDITABLE_CLAY_ONLY',str(a.output),'NO_RENDER_NO_EXPORT')
if __name__=='__main__':main()
