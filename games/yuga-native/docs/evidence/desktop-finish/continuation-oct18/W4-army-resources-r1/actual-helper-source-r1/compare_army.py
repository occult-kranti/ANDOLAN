#!/usr/bin/env python3
"""Exact tiny source-created army review; only two declared source changes."""
import json,sys
from pathlib import Path

def compare(a,b):
    errors=[]
    for label,r in [('baseline',a),('candidate',b)]:
        if not r.get('complete') or not r.get('checks') or not all(x.get('passed') for x in r['checks']):errors.append(label+': incomplete/failed checks')
        if len(r.get('shots',[]))!=1:errors.append(label+': expected exactly one held view')
    if errors:return {'passed':False,'errors':errors}
    if a.get('preflight')!=b.get('preflight'):errors.append('headless/actual mode mismatch')
    sa,sb=a['shots'][0],b['shots'][0]
    if sa.get('controls_sha256')!=sb.get('controls_sha256') or sa.get('controls')!=sb.get('controls'):errors.append('full node/mesh/material/pose/camera/light/semantic clock controls differ')
    if sa.get('status_unique_meshes')!=7 or sb.get('status_unique_meshes')!=4:errors.append('expected real two-unit status geometry identity7->4')
    allowed={
      'res://scripts/lane_army.gd':('f6a56f3e7b4144a26caaed31eb3e64cfd1594de2847627de43af09961a37fb0c','10dc1372ac2580b5ca20573a6a28f5a01e7973c731965c87a2473d7859eb032e'),
      'res://scripts/lane_minion.gd':('90fe2d84f5c408b4b99779b00c11e59e850c1bb4f88dafb42a8a5aba74cc119c','39e9dd57dc229bb6d99dcf84a42b5e6ef5919d203dfc2092d5f8dae7aa6dc387')}
    left,right=a['source_sha256'],b['source_sha256']
    if left.keys()!=right.keys():errors.append('source closure keys differ')
    for key in set(left)|set(right):
        if key in allowed:
            if (left.get(key),right.get(key))!=allowed[key]:errors.append('unadmitted source identity: '+key)
        elif left.get(key)!=right.get(key):errors.append('undeclared source difference: '+key)
    shared={
      'res://scripts/lane_infantry_art.gd':'a64b4cc283dc7b5c4eb28391ec362928a9fb3126e2a1d41ae5cc27e0a67ae6f2',
      'res://scripts/lane_vehicle_art.gd':'ac78ef11354adecb60fabf0b7e9b060585be42168eac184cc67c09b9b36e0fb1',
      'res://scripts/world_render_resources.gd':'9c05d06cd78fd8e9326ac55f89939038ffd08fa69d1f5cdac00dc8a5a1b93472',
      'res://tools/graphics-six/capture_scene_anchors.gd':'eced4bde40c64e24712718b0e60c1ea46458c4bb3bef1da9789626ad4755ebb1'}
    if set(left)!=set(allowed)|set(shared):errors.append('incomplete exact five-script plus common-helper closure')
    for key,value in shared.items():
        if left.get(key)!=value or right.get(key)!=value:errors.append('unpinned shared source: '+key)
    return {'passed':not errors,'errors':errors,'scope':'Exact full source-created two-unit controls equality, two hard-pinned constructor source deltas, geometry alias count7->4. Pixels require independent original inspection; no tolerance or geometry/material exception.'}

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('usage: compare_army.py baseline.json candidate.json output.json')
    result=compare(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path(sys.argv[2]).read_text()))
    Path(sys.argv[3]).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));raise SystemExit(0 if result['passed'] else 1)
