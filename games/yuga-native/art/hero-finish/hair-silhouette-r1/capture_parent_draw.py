"""Read-only existing native component fixture against a sealed imported parent.

No editor/import, scene mutation, helper overlay, or snapshot rewrite is run.
The fixture itself stages its explicit direct-API draw evaluations.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from build_candidate import PROJECT, sha
sys.path.insert(0, str(PROJECT / 'tools/graphics-six'))
import snapshot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    a = ap.parse_args()
    out = a.output_dir
    out.mkdir(parents=True, exist_ok=True)
    report = out / 'smooth-parent-draw-r3.json'
    log = out / 'smooth-parent-draw-r3.log'
    record = out / 'smooth-parent-draw-r3-command.json'
    assert not any(p.exists() for p in [report, log, record])
    fixture = Path(__file__).with_name('capture_draw_parent.gd')
    marker = sha(a.project / snapshot.MARKER)
    snapshot.verify(a.project)
    env = {**os.environ, 'OMP_NUM_THREADS':'1', 'OPENBLAS_NUM_THREADS':'1', 'MKL_NUM_THREADS':'1',
        'XDG_DATA_HOME':'/tmp/yuga-hair-smooth-draw-r3/data', 'XDG_CONFIG_HOME':'/tmp/yuga-hair-smooth-draw-r3/config'}
    assert not Path(env['XDG_DATA_HOME']).exists() and not Path(env['XDG_CONFIG_HOME']).exists()
    cmd = ['taskset', '-c', '4', 'godot', '--headless', '--path', str(a.project), '--script', str(fixture), '--', '--report='+str(report)]
    started = time.monotonic()
    with log.open('w') as stream:
        try:
            code = subprocess.run(cmd, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=55).returncode
        except subprocess.TimeoutExpired:
            code = 124
    snapshot.verify(a.project)
    assert sha(a.project / snapshot.MARKER) == marker
    record.write_text(json.dumps({'command':cmd, 'exit_code':code, 'elapsed_s':time.monotonic()-started,
        'external_script_sha256':sha(fixture), 'capture_wrapper_sha256':sha(__file__),
        'project_marker_before_and_after':marker, 'project_and_import_store_verified_before_and_after':True,
        'canonical_import_run':False}, indent=2)+'\n')
    print(record.read_text())
    if report.exists():
        data = json.loads(report.read_text())
        print('fixture_passed', data['passed'], 'checks', len(data['checks']), 'samples', len(data['samples']))
    raise SystemExit(code)

if __name__ == '__main__':
    main()
