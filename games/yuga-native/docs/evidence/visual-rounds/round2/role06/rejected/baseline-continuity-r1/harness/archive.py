#!/usr/bin/env python3
"""Verify and preserve a completed raw capture, logs and exact diagnostic tools."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists(), 'Evidence archives are immutable; choose a new path'
    capture=json.loads((a.capture/'capture.json').read_text())
    run=json.loads((a.capture/'run.json').read_text())
    assert capture['complete'] and capture['source_unchanged'] and run['complete']
    assert sha(a.capture/'capture.json')==run['report_sha256']
    assert sha(a.capture.with_suffix('.godot.log'))==run['godot_log_sha256']
    assert sha(a.capture.with_suffix('.xvfb.log'))==run['xvfb_log_sha256']
    for row in capture['shots']: assert sha(a.capture/row['file'])==row['sha256']
    for resource,digest in capture['source_sha256'].items():
        assert sha(a.project/resource.removeprefix('res://'))==digest, resource
    shutil.copytree(a.capture,a.output)
    for suffix in ['.godot.log','.xvfb.log']:
        shutil.copy2(a.capture.with_suffix(suffix),a.output/('producer'+suffix))
    shutil.copy2(a.project/'candidate-origin.json',a.output/'candidate-origin.json')
    for optional in ['candidate-overlay.json','import-receipt.json','import.log']:
        if (a.project/optional).is_file(): shutil.copy2(a.project/optional,a.output/optional)
    target=a.output/'harness';target.mkdir()
    for name in ['capture.gd','run.py']:
        shutil.copy2(a.project/'tools/visual-rounds'/name,target/name)
    print(json.dumps({'complete':True,'raw_pngs':len(capture['shots']),'archive':str(a.output)}))

if __name__=='__main__':main()
