#!/usr/bin/env python3
"""One bounded existing-cache helper fixture. Never imports or renders."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools/graphics-six'))
import snapshot


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True)
    before = snapshot.verify(args.base)
    marker = sha(args.base / snapshot.MARKER)
    owned = {p.name: sha(p) for p in [HERE/'shoulder_review.gd', HERE/'helper_cases.gd', Path(__file__)]}
    sources = {name: row for name, row in before['files'].items()
               if name.startswith('scripts/rama_') or name.startswith('assets/heroes/rama-hero.glb')
               or name.startswith('.godot/imported/rama-hero.glb') or name.startswith('assets/hero-finish/')}
    command = ['taskset', '-c', '4', 'timeout', '20s', str(args.engine), '--headless',
               '--path', str(args.base), '--audio-driver', 'Dummy', '--script', str(HERE/'helper_cases.gd'),
               '--log-file', str(args.output/'godot.log')]
    env = dict(os.environ)
    env.update({key: '1' for key in ['LP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']})
    env.update({'YUGA_SHOULDER_SOURCE': str(HERE), 'YUGA_SHOULDER_REPORT': str(args.output/'result.json'),
                'XDG_DATA_HOME': str(args.output/'xdg-data'), 'XDG_CONFIG_HOME': str(args.output/'xdg-config'),
                'XDG_CACHE_HOME': str(args.output/'xdg-cache')})
    record = {'schema': 1, 'command': command, 'engine_sha256': sha(args.engine), 'source_pins': owned,
              'base_marker_before': marker, 'base_files': len(before['files']), 'runtime_sources': sources,
              'scope': 'CPU4 headless helper fixture on existing cached hero. Manual ArrayMesh decoding; no new importer or raster. Affinity/OMP-BLAS1, no worker-pool-cap claim.'}
    (args.output/'command.json').write_text(json.dumps(record, indent=2)+'\n')
    began = time.monotonic()
    with (args.output/'console.log').open('wb') as log:
        run = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    record.update(exit_code=run.returncode, elapsed_s=time.monotonic()-began)
    after = snapshot.verify(args.base)
    record.update(base_marker_after=sha(args.base/snapshot.MARKER), base_and_store_exact=after==before,
                  source_pins_after={p.name: sha(p) for p in [HERE/'shoulder_review.gd', HERE/'helper_cases.gd', Path(__file__)]})
    record['passed'] = run.returncode == 0 and record['base_and_store_exact'] and record['source_pins_after']==owned
    if (args.output/'result.json').exists():
        result = json.loads((args.output/'result.json').read_text())
        record.update(result_sha256=sha(args.output/'result.json'), helper_checks=len(result['checks']))
        record['passed'] = record['passed'] and result['passed']
    else:
        record['passed'] = False
    record['log_sha256'] = sha(args.output/'console.log')
    (args.output/'run.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({k: record.get(k) for k in ['passed', 'exit_code', 'elapsed_s', 'helper_checks', 'base_and_store_exact']}, indent=2))
    sys.exit(0 if record['passed'] else 1)


if __name__ == '__main__':
    main()
