#!/usr/bin/env python3
"""Derive private headless test children from the sealed rendered8c377 branch."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[4]
BASE = Path('/tmp/yuga-s3-motion-pair-r1/candidate/project')
OUTPUT = Path('/tmp/yuga-s3-landing-successor-r1')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not OUTPUT.exists()
    spec = importlib.util.spec_from_file_location('snapshot', PROJECT/'tools/graphics-six/snapshot.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    source = module.verify(BASE)
    assert sha(BASE/'scripts/rama_motion.gd') == '8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8'
    before = sha(BASE/module.MARKER)
    result = {'base': str(BASE), 'base_marker_sha256': before, 'stages': {}}
    for role in ('baseline', 'candidate'):
        project = OUTPUT/role/'project';project.mkdir(parents=True)
        for name in source['files']:
            target = project/name;target.parent.mkdir(parents=True, exist_ok=True)
            if name.startswith('.godot/imported/'):
                os.link(BASE/name, target)
            else:
                shutil.copy2(BASE/name, target)
        shutil.copy2(ROOT/role/'rama_motion.gd', project/'scripts/rama_motion.gd')
        for name in ('graphics_g2_support_cases.gd', 'desktop_s3_transition_scene_cases.gd', 'desktop_s3_transition_guard_cases.gd'):
            shutil.copy2(PROJECT/'tests'/name, project/'tests'/name)
        legacy = project/'docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd'
        legacy.parent.mkdir(parents=True)
        shutil.copy2(PROJECT/'docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd', legacy)
        witness=project/'docs/evidence/desktop-finish/S3/W5/guard-witness.json'
        shutil.copy2(PROJECT/'docs/evidence/desktop-finish/S3/W5/guard-witness.json',witness)
        record = dict(source)
        record.update(files=module.inventory(project), source=str(BASE), project=str(project),
                      round='S3-landing-successor-headless-'+role)
        (project/module.MARKER).write_text(json.dumps(record, indent=2)+'\n')
        module.verify(project)
        result['stages'][role]={'project':str(project), 'motion_sha256':sha(project/'scripts/rama_motion.gd'),
                               'marker_sha256':sha(project/module.MARKER), 'files':record['files']}
    assert sha(BASE/module.MARKER) == before
    module.verify(BASE)
    result['scope']='Private copied sources; imported resources share sealed readonly bytes. No import/render. Common old FX and presentation deliberately retained.'
    (ROOT/'probe-preparation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'stages':{r:p['project'] for r,p in result['stages'].items()}}))


if __name__=='__main__':main()
