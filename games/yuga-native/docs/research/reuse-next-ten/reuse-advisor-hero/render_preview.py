"""Frozen donor preview with a mandatory actual geometry gate; no save/export."""
import argparse,hashlib,json,sys,time
from pathlib import Path
import bpy

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--eligibility',type=Path,required=True)
    parser.add_argument('--comparison-receipt',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    source=json.loads(args.receipt.read_text())
    gate=json.loads(args.eligibility.read_text())
    master=Path(source['scene']['path'])
    assert gate['all_passed'] and gate['master_sha256']==source['scene']['sha256']
    assert gate['source_receipt_sha256']==sha(args.receipt)
    assert 0<gate['baseline']['curves']<=20000 and 0<gate['baseline']['points']<=1300000
    assert gate['baseline']['finite'] and gate['checks']['actual_world_bounds_within_declared_preview_envelope']
    assert sha(master)==source['scene']['sha256']
    args.output.mkdir(parents=True,exist_ok=False)
    bpy.ops.wm.open_mainfile(filepath=str(master))
    scene=bpy.context.scene
    scene.render.threads_mode='FIXED';scene.render.threads=2
    baseline=bpy.data.objects['APPROVED BASELINE Rama']
    candidate=bpy.data.objects['MPFB nape preview Rama']
    donor=bpy.data.objects['MPFB CC0 fitted rear guides']
    start=time.monotonic();frames=[]
    views=source['render']['views'];variants=source['render']['variants']
    for view in views:
        scene.camera=bpy.data.objects['MPFB locked '+view]
        for variant in variants:
            baseline.hide_render=variant!='baseline'
            candidate.hide_render=variant!='candidate'
            donor.hide_render=variant!='candidate'
            frame=args.output/(view+'-'+variant+'.png')
            scene.render.filepath=str(frame)
            begin=time.monotonic();bpy.ops.render.render(write_still=True)
            frames.append({'path':frame.name,'view':view,'variant':variant,'sha256':sha(frame),'bytes':frame.stat().st_size,'elapsed_seconds':time.monotonic()-begin,'camera_matrix':[list(row) for row in scene.camera.matrix_world]})
    report={'schema_version':2,'scope':'Actual frozen textured donor preview only; no native skin/pose/LOD or final art acceptance','source_receipt_sha256':sha(args.receipt),'master_sha256':sha(master),'eligibility_sha256':sha(args.eligibility),'evaluated_curves':gate['baseline']['curves'],'evaluated_points':gate['baseline']['points'],'donor_sha256':source['donor_sha256'],'canonical_source_sha256':source['source_sha256'],'script_sha256':sha(__file__),'reader':bpy.app.version_string,'renderer':'Cycles CPU','threads':2,'samples':scene.cycles.samples,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'exposure':scene.view_settings.exposure,'material_override':str(scene.view_layers[0].material_override),'frames':frames,'positive_completion':len(frames)==len(views)*len(variants) and sha(master)==source['scene']['sha256'],'elapsed_seconds':time.monotonic()-start,'canonical_promoted':False,'runtime_promoted':False}
    if args.comparison_receipt:
        comparison=json.loads(args.comparison_receipt.read_text())
        report['comparison_baseline']={'receipt':str(args.comparison_receipt),'sha256':sha(args.comparison_receipt),'samples':comparison['samples'],'camera_and_light_source':'Same frozen source studio inherited; sample count differs explicitly','baseline_frames':[f for f in comparison['frames'] if f['variant']=='baseline']}
        for frame in frames:
            ancestor=next(f for f in comparison['frames'] if f['view']==frame['view'] and f['variant']=='baseline')
            assert frame['camera_matrix']==ancestor['camera_matrix']
    (args.output/'render-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print('MPFB_RENDER='+json.dumps(report,separators=(',',':')))
if __name__=='__main__':main()
