#!/usr/bin/env python3
"""Exercise bootstrap guards with controlled npm failures; no package downloads."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
project = Path(__file__).resolve().parents[4]
source = project / 'tools/native-analysis/setup-rea.sh'
helper = source.parent / 'inspect-component.py'
inputs = [source, helper, source.parent/'rea-runtime/package.json',
          source.parent/'rea-runtime/package-lock.json']
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
before = {str(path): digest(path) for path in inputs}
original = Path('/workspace/tooling/rea-runtime')
original_pins = {str(original / name): digest(original / name) for name in
                 ['package.json', 'package-lock.json', 'node_modules/rea-agents/scripts/rea.mjs']}
results = []
reasons = {
    'existing-restored-runtime': 'Destination already exists',
    'existing-directory': 'Destination already exists',
    'inside-repository': 'outside the repository',
    'dangling-symlink': 'Destination already exists',
    'symlink-parent-to-repository': 'outside the repository',
    'relative-path': 'absolute destination',
    'timeout-bounds': 'between 1 and 600',
    'tls-disabled': 'TLS verification must remain enabled',
    'missing-node': 'Node and npm must already be installed',
    'unsupported-node': 'Use Node 22.19+',
    'tampered-lock': 'Lockfile differs',
    'npm-nonzero': 'npm-ci failed',
    'npm-empty-success': 'node_modules/rea-agents/package.json',
    'npm-timeout': 'npm-ci failed',
    'npm-mutates-lock': 'dependency inputs changed',
}

def run(name, argv, *, env=None, expect=1):
    result = subprocess.run(['/usr/bin/bash', str(source), *map(str, argv)],
                            env=env, capture_output=True, timeout=30)
    (out/(name+'.stdout')).write_bytes(result.stdout)
    (out/(name+'.stderr')).write_bytes(result.stderr)
    row = {'name': name, 'exit_code': result.returncode,
           'expected_exit': expect, 'passed': result.returncode == expect}
    if name in reasons:
        row['expected_rejection_observed'] = reasons[name] in result.stderr.decode()
        row['passed'] &= row['expected_rejection_observed']
    results.append(row)
    return result, row

def fake_environment(name, npm_body=None, node_body=None, missing_node=False):
    directory = out/name;directory.mkdir()
    for command in ['python3', 'dirname', 'sleep']:
        (directory/command).symlink_to(shutil.which(command))
    if not missing_node:
        if node_body is None:
            (directory/'node').symlink_to(shutil.which('node'))
        else:
            (directory/'node').write_text('#!/bin/sh\n'+node_body);(directory/'node').chmod(0o755)
    npm_body = npm_body or 'if [ "$1" = --version ]; then printf "11.9.0\\n"; exit 0; fi\nprintf "controlled npm failure\\n" >&2\nexit 19\n'
    (directory/'npm').write_text('#!/bin/sh\n'+npm_body);(directory/'npm').chmod(0o755)
    return {**os.environ, 'PATH': str(directory)}

def fixture(name):
    base = out/name/'repo/games/yuga-native/tools/native-analysis'
    (base/'rea-runtime').mkdir(parents=True)
    for path in inputs:
        relative = path.relative_to(source.parent)
        target = base/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    return base

_, row = run('help', ['--help'], expect=0)
dry_dest = out/'dry-destination'
result, row = run('dry', ['--dry-run','--destination',dry_dest], expect=0)
row['passed'] &= json.loads(result.stdout)['mode']=='DRY_RUN' and not dry_dest.exists()
marker=out/'dry-executable-was-invoked'
dry_env=fake_environment('dry-bin',node_body=f'printf "called" > "{marker}"\nexit 20\n',
                         npm_body=f'printf "called" > "{marker}"\nexit 20\n')
result,row=run('dry-no-executable-probes',['--dry-run','--destination',out/'dry-no-probes'],env=dry_env,expect=0)
row['passed'] &= not marker.exists() and not (out/'dry-no-probes').exists() and not json.loads(result.stdout)['runtime_probes_executed']
_, row = run('existing-restored-runtime',['--destination',original])
row['passed'] &= all(digest(Path(path))==sha for path,sha in original_pins.items())
existing=out/'existing';existing.mkdir();(existing/'sentinel').write_text('retain me')
_, row=run('existing-directory',['--destination',existing]);row['passed'] &= (existing/'sentinel').read_text()=='retain me'
inside=project/'bootstrap-guard-must-not-exist'
assert not inside.exists()
_,row=run('inside-repository',['--destination',inside]);row['passed'] &= not inside.exists()
link=out/'dangling';link.symlink_to(out/'absent-target')
_,row=run('dangling-symlink',['--destination',link]);row['passed'] &= link.is_symlink() and not (out/'absent-target').exists()
parent=out/'repository-link';parent.symlink_to(project,target_is_directory=True)
_,row=run('symlink-parent-to-repository',['--destination',parent/'bootstrap-guard-must-not-exist']);row['passed'] &= not inside.exists()
_,row=run('relative-path',['--destination','relative-bootstrap-must-not-exist'])
_,row=run('timeout-bounds',['--destination',out/'bad-timeout','--timeout','0']);row['passed'] &= not (out/'bad-timeout').exists()
_,row=run('tls-disabled',['--destination',out/'tls-disabled'],env={**os.environ,'NODE_TLS_REJECT_UNAUTHORIZED':'0'});row['passed'] &= not (out/'tls-disabled').exists()
_,row=run('missing-node',['--destination',out/'missing-node-destination'],env=fake_environment('missing-node-bin',missing_node=True));row['passed'] &= not (out/'missing-node-destination').exists()
_,row=run('unsupported-node',['--destination',out/'unsupported-node-destination'],env=fake_environment('unsupported-node-bin',node_body='printf "v25.0.0\\n"\n'));row['passed'] &= not (out/'unsupported-node-destination').exists()

base=fixture('tampered-source')
lock=base/'rea-runtime/package-lock.json';lock.write_bytes(lock.read_bytes()+b'\n')
previous=source;source=base/'setup-rea.sh'
_,row=run('tampered-lock',['--destination',out/'tampered-lock-destination']);row['passed'] &= not (out/'tampered-lock-destination').exists()
source=previous

for name,body,expected_step in [
 ('npm-nonzero',None,19),
 ('npm-empty-success','if [ "$1" = --version ]; then printf "11.9.0\\n"; fi\nexit 0\n',0),
 ('npm-timeout','if [ "$1" = --version ]; then printf "11.9.0\\n"; exit 0; fi\nprintf "partial before timeout\\n"\nsleep 10\n',124),
 ('npm-mutates-lock','if [ "$1" = --version ]; then printf "11.9.0\\n"; exit 0; fi\nprintf "{}\\n" > "$2/package-lock.json"\nexit 0\n',0),
]:
    destination=out/(name+'-destination')
    _,row=run(name,['--destination',destination,'--timeout','1' if name=='npm-timeout' else '10'],env=fake_environment(name+'-bin',npm_body=body))
    receipt=json.loads((destination/'setup-receipt.json').read_text())
    row['passed'] &= receipt['status']=='FAILED' and receipt['steps'][0]['exit_code']==expected_step
    if name=='npm-timeout':row['passed'] &= 'partial before timeout' in (destination/'npm-ci.stdout').read_text()
    command=receipt['steps'][0]['command']
    row['passed'] &= '--ignore-scripts' in command and '--strict-ssl=true' in command

results.append({'name':'original-source-inputs-unchanged','passed':all(digest(Path(path))==sha for path,sha in before.items())})
results.append({'name':'existing-restored-runtime-inputs-unchanged','passed':all(digest(Path(path))==sha for path,sha in original_pins.items())})
report={'passed':all(row['passed'] for row in results),'checks':results,
        'script_sha256':digest(source),'harness_sha256':digest(Path(__file__)),
        'source_before':before,'existing_runtime_pins':original_pins,
        'scope':'Controlled guard/failure tests, real local Node/npm version probes and no package network/install. No Ghidra/game execution or positive install acceptance.'}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks':len(results),'failed':[row for row in results if not row['passed']]}))
raise SystemExit(0 if report['passed'] else 1)
