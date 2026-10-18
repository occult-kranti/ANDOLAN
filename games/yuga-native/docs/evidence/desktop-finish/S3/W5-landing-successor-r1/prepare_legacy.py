#!/usr/bin/env python3
"""Retain original119db in the same private presentation for unchanged strict gates."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[4]
BASE=Path('/tmp/yuga-s3-landing-successor-r1/baseline/project')
OUTPUT=BASE.parents[1]/'legacy/project'


def main():
    assert not OUTPUT.exists()
    def copy(source,target):
        if '/.godot/imported/' in str(source):return os.link(source,target)
        return shutil.copy2(source,target)
    shutil.copytree(BASE,OUTPUT,copy_function=copy)
    old=PROJECT/'docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd'
    assert hashlib.sha256(old.read_bytes()).hexdigest()=='119db2e65a40c148725813137340bc109f057d98ea82ef777ab7735c999c661c'
    shutil.copy2(old,OUTPUT/'scripts/rama_motion.gd')
    spec=importlib.util.spec_from_file_location('snapshot',PROJECT/'tools/graphics-six/snapshot.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    record=json.loads((OUTPUT/module.MARKER).read_text())
    record.update(files=module.inventory(OUTPUT),round='S3-landing-successor-legacy119db-headless',project=str(OUTPUT),source=str(BASE))
    (OUTPUT/module.MARKER).write_text(json.dumps(record,indent=2)+'\n')
    module.verify(BASE);module.verify(OUTPUT)
    (ROOT/'legacy-preparation.json').write_text(json.dumps(record,indent=2)+'\n')
    print(str(OUTPUT))


if __name__=='__main__':main()
