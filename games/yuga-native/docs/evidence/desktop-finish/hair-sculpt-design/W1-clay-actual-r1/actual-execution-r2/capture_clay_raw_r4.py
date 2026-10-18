"""W1-only four-view authoring clay capture; never a runtime-quality receipt."""
import argparse, hashlib, json, sys, time
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from projection_contract import points, bounds as context_bounds, fits as context_fits
from bpy_extras.object_utils import world_to_camera_view

BLEND_SHA='71763ab25ed84719a8479bcce771732d50db980780b47c7c4b68114bf2bb9c2f'
CASES=['front','anatomical-left-profile','rear','cast-angle-authoring']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--preflight',action='store_true')
    a=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);assert not a.output.exists()
    scene_path=Path(bpy.data.filepath);assert sha(scene_path)==BLEND_SHA
    scene=bpy.context.scene;scene.cycles.device='CPU';scene.cycles.use_denoising=False;a.output.mkdir(parents=True)
    result=dict(scope='Four real authoring clay views only; not runtime frames, animated cast, material acceptance, or promotion.',
                blend_sha256=BLEND_SHA,helper_sha256=sha(Path(__file__)),blender_version=bpy.app.version_string,
                preflight_only=a.preflight,render_engine=scene.render.engine,samples=scene.cycles.samples,use_denoising=scene.cycles.use_denoising,
                resolution=[scene.render.resolution_x,scene.render.resolution_y],source_glb_sha256=scene['source_glb_sha256'],views=[])
    hair=bpy.data.objects['EDITABLE_WholeHair_CoarseClay']
    _,reference_points=points(scene)
    for case in CASES:
        camera=bpy.data.objects['VIEW_'+case];scene.camera=camera
        evaluated=hair.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
        projected=[world_to_camera_view(scene,camera,evaluated.matrix_world@v.co)for v in mesh.vertices]
        bounds=[[min(p[i]for p in projected)for i in range(3)],[max(p[i]for p in projected)for i in range(3)]]
        evaluated.to_mesh_clear()
        framed=bounds[0][0]>=.015 and bounds[1][0]<=.985 and bounds[0][1]>=.015 and bounds[1][1]<=.985 and bounds[0][2]>camera.data.clip_start
        row=dict(id=case,camera_matrix_world=[list(r)for r in camera.matrix_world],lens_mm=camera.data.lens,
                 hair_normalized_projection_bounds=bounds,full_hair_framed=framed,view_scope=camera['view_scope'])
        reference_bounds=context_bounds(scene,camera,reference_points)
        row.update(head_context_normalized_bounds=reference_bounds,head_context_framed=context_fits(reference_bounds))
        result['views'].append(row)
        assert framed and row['head_context_framed'],('Clay or locked head context outside agreed frame',case,bounds,reference_bounds)
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
