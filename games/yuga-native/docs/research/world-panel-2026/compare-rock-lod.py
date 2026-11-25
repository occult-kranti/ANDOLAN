"""Render and measure the original and compact CC0 rock at identical cameras."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
NATIVE=HERE.parents[2]
SOURCE=NATIVE/'art/world-landmark-study/sources/rock_face_01/rock_face_01_1k.gltf'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def points(obj):
    graph=bpy.context.evaluated_depsgraph_get()
    obj=obj.evaluated_get(graph)
    mesh=obj.to_mesh()
    try:
        vertices=[obj.matrix_world @ v.co for v in mesh.vertices]
        faces=[tuple(p.vertices) for p in mesh.polygons]
    finally:
        obj.to_mesh_clear()
    return vertices,faces

def percentile(samples,p):
    sample=sorted(samples)
    return round(sample[min(len(sample)-1,round((len(sample)-1)*p))],6)

def import_mesh(filename,name,normalize):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(filename))
    added=set(bpy.data.objects)-before
    meshes=[o for o in added if o.type=='MESH']
    if len(meshes)!=1:
        raise RuntimeError(f'{name}: unexpected meshes {len(meshes)}')
    mesh=meshes[0]
    if normalize:
        vertices,_=points(mesh)
        lo=[min(v[i] for v in vertices) for i in range(3)]
        hi=[max(v[i] for v in vertices) for i in range(3)]
        midpoint=[(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]]
        widths=[hi[i]-lo[i] for i in range(3)]
        parent=bpy.data.objects.new(name+' Preview',None)
        bpy.context.scene.collection.objects.link(parent)
        before_matrix=mesh.matrix_world.copy()
        mesh.parent=parent
        mesh.matrix_world=before_matrix
        parent.matrix_world=Matrix.Diagonal(Vector([1/widths[0],1/widths[1],1/widths[2],1])) @ Matrix.Translation(Vector([-v for v in midpoint]))
    mesh.name=name
    bpy.context.view_layer.update()
    return mesh

def camera_at(camera,position,target):
    camera.location=position
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()

def main():
    args=argparse.ArgumentParser()
    args.add_argument('--lod',type=Path,default=Path('/tmp/yuga-ghat-lod/rock-projectile.glb'))
    args.add_argument('--output',type=Path,default=Path('/tmp/yuga-ghat-lod'))
    args=args.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    args.output.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=16
    scene.cycles.use_denoising=bool(getattr(bpy.app.build_options,'openimagedenoise',False))
    scene.render.threads_mode='FIXED'
    scene.render.threads=2
    scene.render.resolution_x=512
    scene.render.resolution_y=512
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.world=bpy.data.worlds.new('Neutral studio')
    scene.world.color=(0.17,0.17,0.17)
    scene.view_settings.view_transform='AgX'
    full=import_mesh(SOURCE,'Full rock',True)
    # The candidate already carries the original source's normalized parent.
    compact=import_mesh(args.lod,'Compact rock',False)
    full_vertices,full_faces=points(full)
    small_vertices,small_faces=points(compact)
    full_bvh=BVHTree.FromPolygons(full_vertices,full_faces)
    small_bvh=BVHTree.FromPolygons(small_vertices,small_faces)
    full_to_small=[small_bvh.find_nearest(v)[3] for v in full_vertices]
    small_to_full=[full_bvh.find_nearest(v)[3] for v in small_vertices]

    bpy.ops.object.light_add(type='AREA',location=(-2,-3,4))
    key=bpy.context.object; key.data.energy=450; key.data.shape='DISK';key.data.size=4
    key.rotation_euler=(Vector((0,0,.5))-key.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='AREA',location=(3,1,2))
    fill=bpy.context.object;fill.data.energy=180;fill.data.size=3
    fill.rotation_euler=(Vector((0,0,.5))-fill.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add()
    camera=bpy.context.object;scene.camera=camera
    camera.data.type='ORTHO';camera.data.ortho_scale=1.75
    images=[]
    for label,position in [('front',(2,-5,2.8)),('side',(-5,-2,2.8))]:
        camera_at(camera,position,(0,0,.5))
        for edition,show,hide in [('full',full,compact),('compact',compact,full)]:
            show.hide_render=False
            hide.hide_render=True
            image=args.output/f'rock-{label}-{edition}.png'
            scene.render.filepath=str(image)
            bpy.ops.render.render(write_still=True)
            images.append({'view':label,'edition':edition,'file':image.name,'sha256':sha(image)})
    def stats(distances):
        return {'vertices':len(distances),'median':percentile(distances,.5),
                'p95':percentile(distances,.95),'max':round(max(distances),6)}
    report={
        'source_gltf_sha256':sha(SOURCE),'candidate_sha256':sha(args.lod),
        'method':'Nearest triangle distance at each vertex with both assets using the same original-source AABB normalization, unit dimensions. This is a sampled metric, not a continuous Hausdorff bound.',
        'full_vertices_to_compact_surface_unit':stats(full_to_small),
        'compact_vertices_to_full_surface_unit':stats(small_to_full),
        'render':{'blender':bpy.app.version_string,'engine':'Cycles CPU','samples':16,
                  'resolution':[512,512],'camera':'orthographic, same lights and framing per pair','images':images}
    }
    (args.output/'lod-visual-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
