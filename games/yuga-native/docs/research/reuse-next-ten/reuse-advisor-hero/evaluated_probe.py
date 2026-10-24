"""Actual donor modifier evaluation and empty-selection/recovery counterexample. No save/render."""
import argparse,hashlib,json,math,sys,time
from pathlib import Path
import bpy

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);source=json.loads(a.receipt.read_text());master=Path(source['scene']['path']);assert sha(master)==source['scene']['sha256'];start=time.monotonic();bpy.ops.wm.open_mainfile(filepath=str(master));obj=bpy.data.objects['MPFB CC0 fitted rear guides'];selection=obj.data.attributes['YUGA_rear_guides'];states=[x.value for x in selection.data]
 def measure():
  obj.data.update_tag();obj.update_tag(refresh={'DATA'});bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();deps.update();evaluated=obj.evaluated_get(deps);data=evaluated.data
  assert evaluated.type=='CURVES',evaluated.type
  attr=data.attributes.get('position');points=[tuple(evaluated.matrix_world@v.vector) for v in attr.data] if attr else [];finite=all(math.isfinite(x) for p in points for x in p);bounds={'min':[min(p[j] for p in points) for j in range(3)],'max':[max(p[j] for p in points) for j in range(3)]} if points else None
  return {'curves':len(data.curves),'points':len(data.points),'finite':finite,'world_bounds':bounds,'position_digest':hashlib.sha256(json.dumps(points,separators=(',',':'),allow_nan=False).encode()).hexdigest()}
 baseline=measure()
 for item in selection.data:item.value=False
 empty=measure()
 for item,value in zip(selection.data,states):item.value=value
 restored=measure();b=baseline['world_bounds'];within=bool(b) and all(b['min'][i]>=lo and b['max'][i]<=hi for i,(lo,hi) in enumerate([(-.3,.3),(-.3,.4),(1.1,2.0)]));checks={'actual_evaluated_curves_nonempty':baseline['curves']>0 and baseline['points']>0,'actual_evaluated_positions_finite':baseline['finite'],'actual_world_bounds_within_declared_preview_envelope':within,'evaluated_points_under_two_million':baseline['points']<2000000,'all_false_selection_yields_empty_actual_geometry':empty['curves']==0 and empty['points']==0,'restored_selection_recovers_identical_actual_geometry':restored==baseline,'source_master_unchanged':sha(master)==source['scene']['sha256']}
 report={'schema_version':1,'scope':'Actual modifier-stack geometry eligibility only; no render/native skin/LOD or artistic pass','reader':bpy.app.version_string,'script_sha256':sha(__file__),'source_receipt_sha256':sha(a.receipt),'master_sha256':source['scene']['sha256'],'baseline':baseline,'all_false_counterexample':empty,'restored':restored,'checks':checks,'all_passed':all(checks.values()),'elapsed_seconds':time.monotonic()-start,'canonical_promoted':False};assert not a.output.exists();a.output.write_text(json.dumps(report,indent=2)+'\n');print('MPFB_EVALUATED='+json.dumps(report,separators=(',',':')))
 if not report['all_passed']:raise RuntimeError('Evaluated geometry gate failed')
if __name__=='__main__':main()
