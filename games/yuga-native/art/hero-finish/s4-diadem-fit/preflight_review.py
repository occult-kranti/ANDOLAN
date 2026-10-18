#!/usr/bin/env python3
"""One serial, read-only headless projection preflight for each frozen branch."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/graphics-six'))
import snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prep = json.loads(args.preparation.read_text())
    out = args.output.resolve()
    assert not out.exists()
    out.mkdir(parents=True)
    engine = Path('/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64')
    assert snapshot.digest(engine) == 'f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3'
    result = {'schema': 1, 'preparation_sha256': snapshot.digest(args.preparation), 'engine_sha256': snapshot.digest(engine),
              'scope': 'Headless actual scene/cast/final-pose projection only; no pixels, import, art or general motion acceptance.', 'runs': []}
    for branch in ('baseline', 'candidate'):
        project = Path(prep['branches'][branch]['project'])
        snapshot.verify(project)
        assert snapshot.digest(project / snapshot.MARKER) == prep['branches'][branch]['marker_sha256']
        env = os.environ.copy()
        env.update(LP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', YUGA_DIADEM_REVIEW=branch)
        for key, suffix in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
            env[key] = str(out / (branch + '-user') / suffix)
        command = ['taskset', '-c', '4', 'timeout', '60s', str(engine), '--headless', '--path', str(project),
                   '--audio-driver', 'Dummy', '--fixed-fps', '30', '--script', 'res://' + prep['helper_runtime_path'], '--',
                   '--mode=groom-stills', '--preflight', '--output=' + str(out / branch)]
        began = time.monotonic()
        with (out / (branch + '.log')).open('w') as log:
            run = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
        row = {'branch': branch, 'command': command, 'exit': run.returncode, 'elapsed_s': time.monotonic() - began,
               'log_sha256': snapshot.digest(out / (branch + '.log')), 'PNG_count': len(list((out / branch).glob('*.png')))}
        snapshot.verify(project)
        row['sealed_project_unchanged'] = True
        report = out / branch / 'preflight.json'
        row['complete'] = report.exists() and json.loads(report.read_text())['complete']
        if report.exists(): row['report_sha256'] = snapshot.digest(report)
        result['runs'].append(row)
        result['passed'] = all(x['exit'] == 0 and x['complete'] and x['PNG_count'] == 0 for x in result['runs'])
        (out / 'run.json').write_text(json.dumps(result, indent=2) + '\n')
        if not result['passed']:
            raise SystemExit('Preflight failed; retain this output and diagnose before any retry.')
    snapshot.verify(Path(prep['base']))
    result['base_and_shared_store_unchanged'] = True
    (out / 'run.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Both branches: 4 source-bound headless views, no PNGs; source/store unchanged.')


if __name__ == '__main__':
    main()
