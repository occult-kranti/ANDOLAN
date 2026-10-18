#!/usr/bin/env python3
"""Derive only a successor render child; reuse the exact archived8c377 take."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[4]
ACTUAL=ROOT.parent/'W5-actual-motion-r1'
BASE=Path('/tmp/yuga-s3-motion-pair-r1/candidate/project')
OUT=Path('/tmp/yuga-s3-landing-successor-render-r1')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not OUT.exists()
    spec=importlib.util.spec_from_file_location('snapshot',BASE/'tools/graphics-six/snapshot.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    baseline=module.verify(BASE)
    baseline_marker=sha(BASE/module.MARKER)
    assert baseline_marker=='3e12066815237a7409c4e285c511a361ee74daa1caa9b77e6afdcbc612b65506'
    assert sha(BASE/'scripts/rama_motion.gd')=='8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8'
    prior={}
    for case in ('landing120','full'):
        capture=ACTUAL/case/'candidate/capture.json.gz'
        report=json.loads(gzip.decompress(capture.read_bytes()))
        assert report['complete'] and report['source_unchanged']
        assert report['source_sha256']==report['source_after_sha256']
        assert all(sha(BASE/name.removeprefix('res://'))==pin for name,pin in report['source_sha256'].items())
        prior[case]={'capture':str(capture.relative_to(PROJECT)),'sha256':sha(capture),
                     'run':str((ACTUAL/case/'candidate/run.json').relative_to(PROJECT)),
                     'run_sha256':sha(ACTUAL/case/'candidate/run.json'),
                     'originals':str((ACTUAL/case/'candidate/originals').relative_to(PROJECT))}
    child=OUT/'candidate/project';child.mkdir(parents=True)
    for name in baseline['files']:
        target=child/name;target.parent.mkdir(parents=True,exist_ok=True)
        if name.startswith('.godot/imported/'):os.link(BASE/name,target)
        else:shutil.copy2(BASE/name,target)
    shutil.copy2(ROOT/'candidate/rama_motion.gd',child/'scripts/rama_motion.gd')
    record=dict(baseline);record.update(files=module.inventory(child),source=str(BASE),project=str(child),round='S3-landing-successor-render')
    record['source_bytes']=sum(v['bytes'] for k,v in record['files'].items() if not k.startswith('.godot/'))
    record['compiled_bytes']=sum(v['bytes'] for k,v in record['files'].items() if k.startswith('.godot/imported/'))
    (child/module.MARKER).write_text(json.dumps(record,indent=2)+'\n');module.verify(child)
    differences=[name for name in baseline['files'].keys()|record['files'].keys() if baseline['files'].get(name)!=record['files'].get(name)]
    assert differences==['scripts/rama_motion.gd']
    pair={'complete':True,'stages':{'baseline':{'project':str(BASE),'seal_sha256':baseline_marker,'motion_sha256':sha(BASE/'scripts/rama_motion.gd')},
          'candidate':{'project':str(child),'seal_sha256':sha(child/module.MARKER),'motion_sha256':sha(child/'scripts/rama_motion.gd')}},
          'pair_differences':differences,'required_free_floor_bytes':3*1024**3,'prior_actual_baseline':prior,
          'capture_status':'Successor not rendered. Baseline is the prior exact8c377 actual take; no rerender or retag.',
          'scope':'One new private source child with readonly linked imports. Same helper, controls, camera, old common FX, hero and presentation. Only motion and snapshot marker differ; runtime canonical is untouched.'}
    pairpath=OUT/'pair.json';pairpath.write_text(json.dumps(pair,indent=2)+'\n')
    inputs=json.loads((ACTUAL/'render-inputs.json').read_text())
    inputs.update(pair=str(pairpath),pair_sha256=sha(pairpath),scope=pair['scope'])
    (ROOT/'render-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    shutil.copy2(pairpath,ROOT/'render-pair.json')
    (ROOT/'render-source-snapshot.json').write_text(json.dumps(record,indent=2)+'\n')
    assert sha(BASE/module.MARKER)==baseline_marker;module.verify(BASE)
    result={'passed':True,'pair_sha256':sha(pairpath),'render_inputs_sha256':sha(ROOT/'render-inputs.json'),
            'source_snapshot_sha256':sha(ROOT/'render-source-snapshot.json'),'motion_sha256':sha(ROOT/'candidate/rama_motion.gd'),
            'baseline_reuse':prior,'only_source_difference':differences,'source_file_count':len(record['files']),
            'runtime_unchanged':sha(PROJECT/'scripts/rama_motion.gd')==pair['stages']['baseline']['motion_sha256'],
            'disk_free_bytes':shutil.disk_usage('/tmp').free,'scope':pair['scope']}
    (ROOT/'render-preparation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','motion_sha256','pair_sha256','source_file_count','runtime_unchanged')}))


if __name__=='__main__':main()
