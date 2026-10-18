#!/usr/bin/env python3
"""Supplement the existing raw-frame validator with this take's import/owner pins."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    run = json.loads((args.capture / 'run.json').read_text())
    inventory = json.loads(args.inventory.read_text())
    frozen = json.loads((args.freeze / 'ui-source-freeze.json').read_text())
    checks = []

    def check(name, passed, detail=None):
        checks.append(dict(name=name, passed=bool(passed), detail=detail))

    check('Native process reached Quit and clean cleanup', run.get('complete') is True and
          run.get('verified_exit_code') == 0 and run.get('cleanup_exit') == 0)
    check('Successor freeze is the declared immutable child',
          sha(args.freeze / 'ui-source-freeze.json') ==
          '5a6fb07e1055d112fb7516ae9e42bda9ca85d4f230ca47ba50bf57ebb9f40337')
    pins = {**inventory['files'], **inventory['existing_cache_files']}
    wrong = [name for name, row in pins.items() if not (args.freeze / name).is_file() or
             (args.freeze / name).stat().st_size != row['bytes'] or sha(args.freeze / name) != row['sha256']]
    check('All declared source and cache/support inputs remain exact', not wrong,
          dict(files=len(pins), differences=wrong))
    imports = {str(p.relative_to(args.freeze)): sha(p) for p in
               (args.freeze / '.godot/imported').rglob('*') if p.is_file()}
    check('Recorded import closure equals freeze and actual payloads',
          imports == run['import_cache_sha256'] == frozen['existing_import_sha256'], len(imports))
    check('Runner guarded source, imports and frozen receipt through completion',
          all(run.get(key) is True for key in ['source_unchanged', 'import_cache_unchanged',
                                               'import_freeze_manifest_unchanged']) and
          run['import_freeze_manifest_sha256'] == sha(args.freeze / 'ui-source-freeze.json'))
    seed_differences = []
    seed_counts = {}
    for key in ['shader_cache_seed', 'godot_shader_cache_seed']:
        seed = run[key]
        root = Path(seed['path'])
        seed_counts[key] = len(seed['files_sha256'])
        for name, checksum in seed['files_sha256'].items():
            path = root / name
            if not path.is_file() or sha(path) != checksum:
                seed_differences.append(str(path))
    check('Both copied warm shader seeds remain exact', not seed_differences and
          run.get('shader_cache_seed_unchanged') is True and
          run.get('godot_shader_cache_seed_unchanged') is True,
          dict(counts=seed_counts, differences=seed_differences))
    engine = Path(run['command'][0])
    check('Executed engine remains the unmodified public template',
          sha(engine) == run['engine_sha256'] ==
          'dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f')
    shots = run['shots'] + run['automatic_shots']
    check('Captured routes retain one persistent transition layer',
          all(s.get('transition_layer_count') == 1 for s in shots), len(shots))
    check('Every captured loading modal owns input and focuses its Cancel control',
          all(s.get('transition_owner_present') is True and
              s.get('focus', '').endswith('/TransitionBack') and
              any(c.get('name') == 'TransitionBack' and c.get('interactive') is True and
                  c.get('focus') is True for c in s['controls']) for s in run['automatic_shots']))
    diagnostics = re.findall(r'^.*(?:WARNING:|ERROR:|ObjectDB instances leaked).*$',
                             (args.capture / 'godot.log').read_text(), re.M)
    check('Full engine log has no warnings, errors or leak diagnostics', not diagnostics, diagnostics)
    report = dict(passed=all(c['passed'] for c in checks), count=len(checks), checks=checks,
                  scope='Supplemental source/import/cache/owner evidence. Original pixels are reviewed separately. '
                        'Warm-cache software rendering; no cold-start, hardware FPS, in-flight cancel or packaging claim.',
                  run_sha256=sha(args.capture / 'run.json'), inventory_sha256=sha(args.inventory),
                  script_sha256=sha(Path(__file__)),
                  actual_automatic_phases={s['file']: s['transition']['phase'] for s in run['automatic_shots']})
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], count=report['count'])))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
