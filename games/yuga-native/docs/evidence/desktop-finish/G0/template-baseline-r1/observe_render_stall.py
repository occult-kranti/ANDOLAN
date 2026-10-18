#!/usr/bin/env python3
"""One owned-process native stack after 45 seconds without log/image progress."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def proc(pid):
    text = Path(f'/proc/{pid}/stat').read_text()
    fields = text[text.rfind(')') + 2:].split()
    return {'starttime': fields[19], 'state': fields[0],
            'user_ticks': int(fields[11]), 'system_ticks': int(fields[12])}


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    engine, project, output = args.engine.resolve(), args.project.resolve(), args.output.resolve()
    logs = output.with_name(output.name + '-logs')
    receipt = logs / 'native-stall-observer.json'
    assert not receipt.exists()
    observed = None
    start = time.monotonic()
    last_progress = start
    previous = None
    record = {'engine': str(engine), 'engine_sha256': sha(engine), 'project': str(project),
              'output': str(output), 'observer_sha256': sha(Path(__file__)),
              'trigger_no_output_progress_seconds': 45, 'overall_observer_limit_seconds': 340,
              'stack_attempted': False, 'samples': [],
              'scope': 'Diagnostic attachment to one exact engine/output process only. No engine source/cache/input modifications; debugger briefly suspends execution.'}
    while time.monotonic() - start < 340:
        if observed is None:
            matches = []
            for path in Path('/proc').iterdir():
                if not path.name.isdigit():
                    continue
                try:
                    argv = (path / 'cmdline').read_bytes().decode().rstrip('\0').split('\0')
                    if argv and argv[0] == str(engine) and str(project) in argv and '--output=' + str(output) in argv:
                        matches.append(int(path.name))
                except (FileNotFoundError, ProcessLookupError, PermissionError, UnicodeDecodeError):
                    pass
            assert len(matches) <= 1, 'Ambiguous owned engine'
            if matches:
                observed = matches[0]
                record['pid'] = observed
                record['starttime'] = proc(observed)['starttime']
                last_progress = time.monotonic()
        if observed is not None:
            try:
                state = proc(observed)
                if state['starttime'] != record['starttime']:
                    record['ended'] = 'Original process identity ended'
                    break
            except (FileNotFoundError, ProcessLookupError):
                record['ended'] = 'Owned engine exited'
                break
            log = logs / 'godot.log'
            progress = (log.stat().st_size if log.exists() else 0, len(list(output.glob('*.png'))))
            now = time.monotonic()
            if progress != previous:
                last_progress = now
                previous = progress
            record['samples'].append({'elapsed_s': now - start, 'no_output_progress_s': now - last_progress,
                                      'log_bytes': progress[0], 'png_count': progress[1], **state})
            if now - last_progress >= 45:
                command = ['/workspace/tooling/native-debug/gdb-local', '--batch',
                           '-ex', 'set pagination off', '-ex', 'set print frame-arguments none',
                           '-p', str(observed), '-ex', 'info threads',
                           '-ex', 'thread apply all bt 32', '-ex', 'info proc mappings', '-ex', 'detach']
                record['stack_attempted'] = True
                record['debugger_command'] = command
                began = time.monotonic()
                with (logs / 'native-gdb-r1.log').open('x') as handle:
                    try:
                        result = subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, timeout=20)
                        record['debugger_exit'] = result.returncode
                    except subprocess.TimeoutExpired:
                        record['debugger_exit'] = None
                        record['debugger_failure'] = '20-second debugger deadline; owned debugger killed by subprocess timeout'
                        try:
                            if proc(observed)['starttime'] == record['starttime']:
                                os.kill(observed, signal.SIGCONT)
                                record['timeout_cleanup'] = 'SIGCONT to the same owned engine after debugger termination'
                        except (FileNotFoundError, ProcessLookupError):
                            record['timeout_cleanup'] = 'Owned engine had already exited'
                record['debugger_elapsed_s'] = time.monotonic() - began
                record['debugger_log_sha256'] = sha(logs / 'native-gdb-r1.log')
                record['ended'] = 'One declared native stack attempt completed'
                break
        time.sleep(1)
    else:
        record['ended'] = 'Observer deadline; no additional attachment'
    record['elapsed_s'] = time.monotonic() - start
    logs.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({key: value for key, value in record.items() if key != 'samples'}, indent=2))


if __name__ == '__main__':
    main()
