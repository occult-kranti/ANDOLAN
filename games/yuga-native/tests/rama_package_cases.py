#!/usr/bin/env python3
"""Counterexamples for Rama's package provenance gate; no real art is mutated."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_packaging', PROJECT / 'tools/package-native.py')
packaging = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(packaging)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    checks = []
    with tempfile.TemporaryDirectory(prefix='rama-package-cases-') as folder:
        root = Path(folder) / 'project'
        files = {
            'assets/heroes/rama-hero.glb': b'original asset fixture',
            'art/hero-rama/rama-hero.blend': b'editable authoring fixture',
            'art/hero-rama/build_hero.py': b'# generator fixture\n',
            'art/hero-rama/rebind_dhoti.py': b'# weight correction generator fixture\n',
            'art/hero-rama/weight-correction.json': b'{"fixture": true}\n',
        }
        for path, content in files.items():
            destination = root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        notice_path = root / 'NOTICE/RAMA-HERO-PROVENANCE.json'
        notice_path.parent.mkdir()
        original = {
            'schema': 1,
            'asset': 'assets/heroes/rama-hero.glb',
            'sha256': packaging.digest(root / 'assets/heroes/rama-hero.glb'),
            'editableSource': 'art/hero-rama/rama-hero.blend',
            'editableSha256': packaging.digest(root / 'art/hero-rama/rama-hero.blend'),
            'generator': 'art/hero-rama/build_hero.py',
            'generatorSha256': packaging.digest(root / 'art/hero-rama/build_hero.py'),
            'weightCorrectionGenerator': 'art/hero-rama/rebind_dhoti.py',
            'weightCorrectionGeneratorSha256': packaging.digest(root / 'art/hero-rama/rebind_dhoti.py'),
            'weightCorrection': 'art/hero-rama/weight-correction.json',
            'weightCorrectionSha256': packaging.digest(root / 'art/hero-rama/weight-correction.json'),
            'generatedDependencies': [{'path': 'art/hero-rama/rebind_dhoti.py',
                                       'sha256': packaging.digest(root / 'art/hero-rama/rebind_dhoti.py')}],
            'limitations': ['Synthetic identity fixture, not a valid GLB or art acceptance.'],
        }

        def run(name, mutate=None, valid=False):
            value = copy.deepcopy(original)
            if mutate:
                mutate(value)
            notice_path.write_text(json.dumps(value))
            error = None
            try:
                packaging.validate_rama_hero_notice(root)
            except (ValueError, OSError) as exc:
                error = str(exc)
            checks.append({'name': name, 'passed': (error is None) == valid, 'rejection': error})

        run('matching asset editable and generator hashes accepted', valid=True)
        run('boolean schema rejected', lambda value: value.update(schema=True))
        run('unknown schema rejected', lambda value: value.update(schema=2))
        run('path traversal rejected before reading outside', lambda value: value.update(asset='../outside.glb'))
        run('absolute editable path rejected', lambda value: value.update(editableSource='/tmp/other.blend'))
        run('missing digest rejected', lambda value: value.pop('sha256'))
        run('nonhex digest rejected', lambda value: value.update(sha256='z' * 64))
        run('omitted weight correction dependency rejected', lambda value: value.pop('weightCorrectionGenerator'))
        run('weight correction dependency traversal rejected', lambda value: value.update(weightCorrectionGenerator='../rebind_dhoti.py'))
        run('omitted weight correction evidence hash rejected', lambda value: value.pop('weightCorrectionSha256'))
        run('generated dependency ledger mismatch rejected', lambda value: value.update(generatedDependencies=[]))
        for relative in files:
            path = root / relative
            path.write_bytes(files[relative] + b' changed')
            run('changed source rejects: ' + relative)
            path.write_bytes(files[relative])
        asset = root / original['asset']
        asset.unlink()
        run('missing asset rejects')
        outside = Path(folder) / 'outside.glb'
        outside.write_bytes(files[original['asset']])
        asset.symlink_to(outside)
        run('matching external symlink still rejects')
        asset.unlink()
        asset.write_bytes(files[original['asset']])
        run('restored source passes', valid=True)
    passed = all(check['passed'] for check in checks)
    report = {'suite': 'rama_package_cases', 'passed': passed, 'checks': checks,
              'source_sha256': {'tools/package-native.py': packaging.digest(PROJECT / 'tools/package-native.py'),
                                'tests/rama_package_cases.py': packaging.digest(Path(__file__))},
              'scope': 'Provenance schema, exact source identity, and safe-path counterexamples; not GLB format or art quality.'}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': passed, 'checks': len(checks), 'failures': [check for check in checks if not check['passed']]}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
