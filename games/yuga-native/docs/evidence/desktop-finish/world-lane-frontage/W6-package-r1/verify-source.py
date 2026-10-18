#!/usr/bin/env python3
"""Repeat the six bounded source checks; no engine or exported PCK involved."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
PINS = {
    'scripts/world_lane_frontage.gd': 'dcd0c73d8a12fc32e2fc32fa69ccc3466c3835ab0f4c15b8f18b72e8990dda72',
    'scripts/world_lane_frontage.gd.uid': '7506c2840a369ff018ccd966ad054f9eb01ec9b365236548e1a655949bceb8de',
    'assets/world/block2-frontage.json': '67950a68d7b6384b8b114987a27efff1f113d44f8fb1b7df8632f3e9217406a2',
    'scripts/confluence_world.gd': '1301701f7f8b6a711de7a36a6d283d88f1240708a7186053fa51bfc572ca8c76',
}


def record(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise SystemExit('Use a fresh report path')
    package = load('frontage_package', ROOT / 'tools/package-native.py')
    fixture = load('frontage_fixture', ROOT / 'tests/traversal_security_cases.py')
    before = {p: record(ROOT / p) for p in PINS}
    uids = package.validate_runtime_script_uids(ROOT)
    uid = uids['sidecars']['scripts/world_lane_frontage.gd.uid']
    source = 'assets/world/block2-frontage.json'
    data = (ROOT / source).read_bytes()
    json.loads(data)
    entries = [(name, data if name == source else ('benign fixture for ' + name).encode()) for name in fixture.NAMES]
    for raw, target in fixture.GRAPHICS_TEXTURE_FIXTURES.items():
        entries.extend([(raw + '.import', f'[remap]\npath="res://{target}"\n'.encode()),
                        (target, b'benign structural texture fixture; not engine-decodable')])
    rejection = None
    with tempfile.TemporaryDirectory(prefix='frontage-source-', dir=args.report.parent) as folder:
        pck = Path(folder) / 'fixture.pck'
        pck.write_bytes(fixture.pack(entries)[0])
        binding = package.qualify_world_frontage_package(package.inspect_pack(pck), {source: before[source]})
        altered = data[:-1] + (b' ' if data[-1:] != b' ' else b'\n')
        pck.write_bytes(fixture.pack([(name, altered if name == source else value) for name, value in entries])[0])
        try:
            package.qualify_world_frontage_package(package.inspect_pack(pck), {source: before[source]})
        except ValueError as error:
            rejection = str(error)
    after = {p: record(ROOT / p) for p in PINS}
    checks = [
        {'name': 'all runtime UID sidecars remain canonical and numerically unique', 'passed': uids['scripts'] == 73},
        {'name': 'engine-generated frontage UID admitted by unchanged automatic guard', 'passed': uid['uid'] == 'uid://dujcxub60rkud'},
        {'name': 'production frontage JSON syntax and declared owner SHA match', 'passed': before[source]['sha256'] == PINS[source]},
        {'name': 'actual JSON bytes qualify against runtime source record', 'passed': binding['exact_source_payload']},
        {'name': 'same-sized actual JSON substitution rejects', 'passed': bool(rejection and 'Frontage PCK data differs' in rejection)},
        {'name': 'four owner source pins unchanged', 'passed': before == after and all(before[p]['sha256'] == sha for p, sha in PINS.items())},
    ]
    result = {'passed': all(c['passed'] for c in checks), 'checks': checks,
              'scope': 'Python-only runtime UID census and actual JSON in a synthetic structural PCK; no import/export/engine or shipped package qualification.',
              'runtime_scripts': uids['scripts'], 'new_uid': uid, 'binding': binding,
              'same_size_replacement_rejection': rejection, 'sources_before': before, 'sources_after': after,
              'packager': record(ROOT / 'tools/package-native.py'),
              'test_fixture': record(ROOT / 'tests/traversal_security_cases.py'),
              'verifier': record(Path(__file__))}
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(checks)}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
