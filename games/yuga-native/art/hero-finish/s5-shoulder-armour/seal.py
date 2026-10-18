#!/usr/bin/env python3
"""Seal original candidate and its explicit rejection; no promotion."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def pin(path):
    data = Path(path).read_bytes()
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def main():
    manifest = json.loads((HERE/'candidate-r4/source-manifest.json').read_text())
    assert pin(HERE/'build_armour.py')['sha256'] == manifest['generator_sha256']
    assert (HERE/'build_armour.py').read_bytes() == (HERE/'candidate-r4/generator.py').read_bytes()
    assert pin(ROOT/'assets/heroes/rama-hero.glb')['sha256'] == manifest['source_hero_sha256']
    for level, row in manifest['levels'].items():
        assert pin(HERE/'candidate-r4'/('shoulder-armour-'+level+'.glb')) == {key: row[key] for key in ['sha256', 'bytes']}
    history = [('representative-r4.json', 'check-source-single50.py', 6),
               ('split-representative-r4.json', 'check-source-split49.py', 8),
               ('clavicle-representative-r4.json', 'check-source-split48.py', 8)]
    for report, checker, failures in history:
        data = json.loads((HERE/report).read_text())
        assert pin(HERE/'candidate-r4'/checker)['sha256'] == data['checker_sha256']
        assert data['source_unchanged'] and not data['body_crossing_free']
        assert all(item['crossings'] == 0 for row in data['levels'].values() for item in row['contacts'].values())
        assert sum(row['contacts']['Rama warm skin']['crossings'] > 0 for row in data['pose_replay']['rows']) == failures
    khronos = json.loads((HERE/'khronos-r4.json').read_text())
    assert khronos['passed'] and all(row['report']['issues']['numErrors'] == 0 and row['report']['issues']['numWarnings'] == 0 for row in khronos['levels'].values())
    native_runs = sorted(HERE.glob('native-r*/run.json'))
    assert native_runs, 'Retain actual helper fixture before sealing'
    final_run = json.loads(native_runs[-1].read_text())
    assert final_run['passed'] and final_run['source_pins']['shoulder_review.gd'] == pin(HERE/'shoulder_review.gd')['sha256']
    excluded = {'receipt.json'}
    files = {path.relative_to(HERE).as_posix(): pin(path) for path in sorted(HERE.rglob('*'))
             if path.is_file() and path.name not in excluded and not any(part.startswith(('__pycache__', 'xdg-')) for part in path.parts) and path.suffix not in ['.pyc', '.uid']}
    dependencies = ['assets/heroes/rama-hero.glb', 'assets/heroes/rama-hero.glb.import',
                    'art/hero-rama/build_hero.py', 'art/hero-rama-lod/glb_lod.py',
                    'docs/evidence/visual-rounds/round3/role10/geometry_probe.py',
                    'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz',
                    'docs/evidence/desktop-finish/S4/W5/rail-mapping-review.json',
                    'docs/evidence/desktop-finish/G0/template-priority-cold-600-r1/00-title-100.png',
                    'docs/evidence/graphics-six/G1/hero-render/light-front.png']
    result = {'schema': 1, 'task': 'S5-W3 original left shoulder armour',
              'source_commit_at_seal': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'disposition': 'Source artifact sealed; rest contact and helper tests pass; action clearance failed. No activation or visual acceptance.',
              'candidate': 'candidate-r4', 'default_activation': False, 'canonical_asset_changes': False,
              'art_imported': False, 'art_rendered': False, 'action_clearance_accepted': False,
              'native_helper_run': native_runs[-1].relative_to(HERE).as_posix(),
              'files': files, 'dependencies': {path: pin(ROOT/path) for path in dependencies},
              'reference': {str(ROOT/'../yuga/art/references/rama-hanuman-sita.png'): pin(ROOT/'../yuga/art/references/rama-hanuman-sita.png')},
              'remaining': ['Articulated body/sash clearance', 'New GLB isolated import and exact semantics', 'Matched native title/front, cast and rear form/material review', 'LOD pixels and continuous animation/secondary contact']}
    output = HERE/'receipt.json'
    assert not output.exists(), 'Do not overwrite a sealed receipt'
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'receipt': pin(output), 'files': len(files), 'disposition': result['disposition']}, indent=2))


if __name__ == '__main__':
    main()
