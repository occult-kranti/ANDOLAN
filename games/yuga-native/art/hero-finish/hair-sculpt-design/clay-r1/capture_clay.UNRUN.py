"""W1-only four-view authoring clay capture; never a runtime-quality receipt."""
import argparse, hashlib, json, sys, time
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view

BLEND_SHA='b2bcea87e5aacf7ec49dae44df915063223bfa4b990ccb448457385008470475'
CASES=['front','anatomical-left-profile','rear','cast-angle-authoring']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--preflight',action='store_true')
    a=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);assert not a.output.exists()
    scene_path=Path(bpy.data.filepath);assert sha(scene_path)==BLEND_SHA
    scene=bpy.context.scene;scene.cycles.device='CPU';a.output.mkdir(parents=True)
    result=dict(scope='Four real authoring clay views only; not runtime frames, animated cast, material acceptance, or promotion.',
                blend_sha256=BLEND_SHA,helper_sha256=sha(Path(__file__)),blender_version=bpy.app.version_string,
                preflight_only=a.preflight,render_engine=scene.render.engine,samples=scene.cycles.samples,
                resolution=[scene.render.resolution_x,scene.render.resolution_y],source_glb_sha256=scene['source_glb_sha256'],views=[])
    hair=bpy.data.objects['EDITABLE_WholeHair_CoarseClay']
    for case in CASES:
        camera=bpy.data.objects['VIEW_'+case];scene.camera=camera
        evaluated=hair.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
        projected=[world_to_camera_view(scene,camera,evaluated.matrix_world@v.co)for v in mesh.vertices]
        bounds=[[min(p[i]for p in projected)for i in range(3)],[max(p[i]for p in projected)for i in range(3)]]
        evaluated.to_mesh_clear()
        framed=bounds[0][0]>=.015 and bounds[1][0]<=.985 and bounds[0][1]>=.015 and bounds[1][1]<=.985 and bounds[0][2]>camera.data.clip_start
        row=dict(id=case,camera_matrix_world=[list(r)for r in camera.matrix_world],lens_mm=camera.data.lens,
                 hair_normalized_projection_bounds=bounds,full_hair_framed=framed,view_scope=camera['view_scope'])
        result['views'].append(row)
        assert framed,('Clay projection outside agreed frame',case,bounds)
        if not a.preflight:
            started=time.monotonic();scene.render.filepath=str(a.output/(case+'.png'))
            bpy.ops.render.render(write_still=True)
            png=a.output/(case+'.png');assert png.is_file()
            row.update(png_sha256=sha(png),png_bytes=png.stat().st_size,render_seconds=time.monotonic()-started)
        (a.output/'capture.json').write_text(json.dumps(result,indent=2)+'\n')
        print('AUTHORING_CLAY_VIEW',case,'PREFLIGHT'if a.preflight else'RENDERED',flush=True)
    result['complete']=len(result['views'])==4;result['scene_unchanged_after']=sha(scene_path)==BLEND_SHA
    (a.output/'capture.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['complete']and result['scene_unchanged_after']
if __name__=='__main__':main()
