"""Independent first-load path/parser boundary checks. Structural PCKs only."""
from pathlib import Path
import argparse, hashlib, importlib.util, json

PROJECT = Path('/workspace/ANDOLAN/games/yuga-native')
OUT = Path(__file__).parent
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
parser = argparse.ArgumentParser()
parser.add_argument('--result', required=True)
args = parser.parse_args()
packager = module('independent_first_load_package', PROJECT/'tools/package-native.py')
writer = module('shared_binary_fixture_encoder', PROJECT/'tests/traversal_security_cases.py')
base = [(name, ('fixture '+name).encode()) for name in writer.NAMES]
checks = []
def inspect(label, entries, expected):
    data = writer.pack(entries)[0]
    target = OUT/'probe.pck'
    target.write_bytes(data)
    try:
        report = packager.inspect_pack(target)
        accepted = True
        detail = report['first_load_resources']
    except (ValueError, UnicodeDecodeError) as error:
        accepted = False
        detail = str(error)
    checks.append({'name':label, 'passed':accepted == expected,
                   'expected_accept':expected, 'accepted':accepted, 'detail':detail,
                   'fixture_sha256':hashlib.sha256(data).hexdigest()})
inspect('exact canonical source fixture',base,True)
for suffix, name in [('dot source','scripts/./boot.gd'),('double slash source','scripts//boot.gd'),
                     ('trailing slash source','scripts/boot.gd/'),('dot remap','scripts/./boot.gd.remap')]:
    inspect('reject shadow spelling '+suffix,base+[(name,b'alias fixture')],False)
boot = 'scripts/boot.gd'
remap = b'[remap]\npath="res://scripts/boot.gdc"\n'
compiled = [(n,p) for n,p in base if n != boot]+[(boot+'.remap',remap),('scripts/boot.gdc',b'compiled fixture')]
inspect('exact compiled first-load binding',compiled,True)
inspect('reject raw and remap source ambiguity',base+[(boot+'.remap',remap),('scripts/boot.gdc',b'compiled fixture')],False)
inspect('reject required target missing',[(n,p) for n,p in compiled if n != 'scripts/boot.gdc'],False)
for label, payload in [
    ('wrong section',b'[dependencies]\npath="res://scripts/boot.gdc"\n'),
    ('default fallback',b'[DEFAULT]\npath="res://scripts/boot.gdc"\n[remap]\n'),
    ('duplicate section',remap+remap),
    ('duplicate key',remap+b'path="res://scripts/other.gdc"\n'),
    ('target dot alias',b'[remap]\npath="res://scripts/./boot.gdc"\n'),
    ('target wrong script',b'[remap]\npath="res://scripts/launch_shell.gdc"\n')]:
    inspect('reject '+label,[(n,payload if n == boot+'.remap' else p) for n,p in compiled],False)
for source in packager.FIRST_LOAD_RESOURCES:
    inspect('reject exact required source missing '+source,[(n,p) for n,p in base if n != source],False)
result = {'passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,
          'package_sha256':hashlib.sha256((PROJECT/'tools/package-native.py').read_bytes()).hexdigest(),
          'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'scope':'Independent mutations and expectations using the existing binary fixture encoder. No Godot import/export, fixture execution, source-PCK equality or full dependency closure claim.'}
(OUT/args.result).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'count':len(checks),'failed':[c['name'] for c in checks if not c['passed']]}))
