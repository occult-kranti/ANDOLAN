"""Render the frozen R2 shape-key master; no sculpt edits or source re-save."""
import argparse,hashlib,json,sys,time
from pathlib import Path
import bpy
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--source-receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r=json.loads(a.source_receipt.read_text());source=Path(r['scene']['path']);assert sha(source)==r['scene']['sha256'];a.output.mkdir(parents=True,exist_ok=False);bpy.ops.wm.open_mainfile(filepath=str(source.resolve()));scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2;shape=bpy.data.objects['W3 existing-clump sculpt'].data.shape_keys.key_blocks['W3 two unequal nape flow families'];start=time.monotonic();frames=[]
 for view in ['front','profile','rear','oblique']:
  scene.camera=bpy.data.objects['R2 locked '+view]
  for variant,value in [('baseline',0.),('candidate',1.)]:
   shape.value=value;path=a.output/(view+'-'+variant+'.png');scene.render.filepath=str(path.resolve());begin=time.monotonic();bpy.ops.render.render(write_still=True);frames.append({'path':path.name,'view':view,'variant':variant,'camera_matrix':[list(row) for row in scene.camera.matrix_world],'sha256':sha(path),'bytes':path.stat().st_size,'seconds':time.monotonic()-begin})
 report={'schema_version':1,'scope':'Actual matched four-view R2 clay comparison from exact frozen source; no export or acceptance by renderer.','source_receipt_sha256':sha(a.source_receipt),'scene_sha256':sha(source),'script_sha256':sha(__file__),'source_sha256':r['source_sha256'],'threads':2,'samples':scene.cycles.samples,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'denoising':scene.cycles.use_denoising,'exposure':scene.view_settings.exposure,'frames':frames,'elapsed_seconds':time.monotonic()-start,'positive_completion':len(frames)==8 and sha(source)==r['scene']['sha256'],'runtime_promoted':False}
 (a.output/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print('W3_CLUMP_RENDER='+json.dumps(report,separators=(',',':')))
if __name__=='__main__':main()
