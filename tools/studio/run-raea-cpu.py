#!/usr/bin/env python3
"""Render an owned Raea composition on Mesa's CPU Vulkan adapter, keeping a receipt."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--composition', default='compositions/surya.tsx')
    parser.add_argument('--output', required=True, help='New relative MP4 path under project/out.')
    args = parser.parse_args()
    project, engine = args.project.resolve(), args.engine.resolve()
    output = (project / args.output).resolve()
    if not output.is_relative_to(project / 'out') or output.suffix != '.mp4':
        parser.error('Choose a relative MP4 path below the owned project/out directory.')
    log_path, receipt_path = output.with_suffix('.log'), output.with_suffix('.receipt.json')
    manifest_path = output.with_suffix('.json')
    for path in [output, log_path, receipt_path, manifest_path]:
        if path.exists(): parser.error(f'Preserve existing output: {path}')
    composition = (project / args.composition).resolve()
    if not composition.is_relative_to(project) or not composition.is_file():
        parser.error('Composition must be an existing file in this project.')
    output.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(RAEA_OFFLINE='1', VK_ICD_FILENAMES='/usr/share/vulkan/icd.d/lvp_icd.json',
               WGPU_BACKEND='vulkan', LP_NUM_THREADS='8', RAYON_NUM_THREADS='8')
    command = [str(engine), 'render', args.composition, '-o', str(output), '--manifest', str(manifest_path)]
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    before = digest(composition)
    start = time.monotonic()
    driver_seen = False
    with log_path.open('x') as log:
        process = subprocess.Popen(command, cwd=project, env=env, stdout=log, stderr=subprocess.STDOUT)
        print(json.dumps({'pid': process.pid, 'output': str(output)}), flush=True)
        for _ in range(20):
            if process.poll() is not None: break
            try:
                driver_seen |= 'libvulkan_lvp.so' in Path(f'/proc/{process.pid}/maps').read_text()
            except (FileNotFoundError, PermissionError): pass
            if driver_seen: break
            time.sleep(.5)
        code = process.wait()
    receipt = {'command': command, 'cwd': str(project), 'exit': code,
               'wall_seconds': round(time.monotonic()-start, 3),
               'max_rss_kib': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
               'cpu_driver_observed_in_process': driver_seen,
               'icd': env['VK_ICD_FILENAMES'], 'threads': 8, 'offline': True,
               'engine_sha256': digest(engine), 'composition_sha256': before,
               'composition_unchanged': before == digest(composition),
               'output_sha256': digest(output) if output.is_file() else None,
               'scope': 'Original-asset presentation render, separate from native game. CPU rendering time is not game FPS.'}
    receipt_path.write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt), flush=True)
    raise SystemExit(code)


if __name__ == '__main__':
    main()
