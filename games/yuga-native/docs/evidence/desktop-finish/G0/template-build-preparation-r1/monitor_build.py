#!/usr/bin/env python3
"""Own one bounded unmodified template build; keep logs outside ephemeral /tmp."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time

PERSISTENT = Path('/workspace/tooling/godot-public-4.6.3')
RECEIPTS = PERSISTENT / 'template-baseline-r1'
SOURCE = Path('/tmp/yuga-engine-template-baseline-r1/godot-35e80b3a8822a9df9be390814b62f44c0a9c69e8')
FLOOR = 3 * 1024 ** 3
MEMORY_GUARD = 24 * 1024 ** 3
DEADLINE = 7200
COMMAND = ['python3', '-m', 'SCons', '-j4', 'platform=linuxbsd',
           'target=template_debug', 'dev_build=no', 'debug_symbols=no',
           'lto=none', 'use_sowrap=yes', 'disable_path_overrides=no']


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def proc_stat(pid):
    text = Path(f'/proc/{pid}/stat').read_text()
    values = text[text.rfind(')') + 2:].split()
    return {'ppid': int(values[1]), 'starttime': values[19]}


def owned_tree(root_pid, starttime):
    graph = {}
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            graph[int(path.name)] = proc_stat(path.name)
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    if graph.get(root_pid, {}).get('starttime') != starttime:
        return []
    owned = {root_pid}
    while True:
        additional = {pid for pid, row in graph.items() if row['ppid'] in owned} - owned
        if not additional:
            return sorted(owned)
        owned.update(additional)


def rss(pid):
    try:
        return int(Path(f'/proc/{pid}/statm').read_text().split()[1]) * os.sysconf('SC_PAGE_SIZE')
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return 0


def cgroup():
    base = Path('/sys/fs/cgroup')
    current = int((base / 'memory.current').read_text())
    events = dict(line.split() for line in (base / 'memory.events').read_text().splitlines())
    return {'memory_current_bytes': current, 'memory_events': {key: int(value) for key, value in events.items()}}


def write_json(name, value):
    target = RECEIPTS / name
    temporary = target.with_suffix(target.suffix + '.partial')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temporary, target)


def main():
    assert sorted(os.sched_getaffinity(0)) == [0, 1, 2, 3]
    assert not (RECEIPTS / 'build.log').exists()
    assert shutil.disk_usage('/tmp').free > FLOOR
    assert json.loads((RECEIPTS / 'configure-receipt.json').read_text())['passed'] is True
    pristine = json.loads((RECEIPTS / 'pristine-source-files.json').read_text())
    changed = [name for name, pin in pristine.items()
               if not (SOURCE / name).is_file() or (SOURCE / name).stat().st_size != pin['bytes']
               or sha(SOURCE / name) != pin['sha256']]
    assert not changed, changed
    env = os.environ.copy()
    env['PYTHONPATH'] = str(PERSISTENT / 'scons')
    env['PATH'] = '/workspace/tooling/wayland-scanner-local/root/usr/bin:' + env['PATH']
    env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    record = {'source': str(SOURCE), 'command': COMMAND, 'source_patches': 0,
              'original_source_files_verified': len(pristine), 'affinity': [0, 1, 2, 3],
              'compiler_jobs': 4, 'scratch_floor_bytes': FLOOR,
              'cgroup_memory_stop_bytes': MEMORY_GUARD, 'overall_deadline_seconds': DEADLINE,
              'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'samples': [], 'completed': False,
              'memory_scope': 'Five-second sampled sum of owned process RSS, not unique physical memory or exact peak. Cgroup current/events cover the whole container, not only this build.',
              'process_tree_method': 'All readable /proc/PID/stat PPID graph, recursive/de-duplicated, exact root PID and starttime pinned.',
              'monitor_sha256': sha(Path(__file__))}
    start = time.monotonic()
    failure = None
    last_print = -60
    with (RECEIPTS / 'build.log').open('x') as log:
        process = subprocess.Popen(COMMAND, cwd=SOURCE, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        record['pid'] = process.pid
        record['starttime_ticks'] = proc_stat(process.pid)['starttime']
        try:
            while process.poll() is None:
                elapsed = time.monotonic() - start
                pids = owned_tree(process.pid, record['starttime_ticks'])
                sample = {'elapsed_s': elapsed, 'pids': pids, 'process_count': len(pids),
                          'sampled_process_RSS_sum_bytes': sum(rss(pid) for pid in pids),
                          'free_tmp_bytes': shutil.disk_usage('/tmp').free,
                          'free_workspace_bytes': shutil.disk_usage('/workspace').free,
                          'log_bytes': (RECEIPTS / 'build.log').stat().st_size, **cgroup()}
                record['samples'].append(sample)
                if sample['free_tmp_bytes'] < FLOOR:
                    failure = 'Scratch free space below declared 3 GiB floor'
                elif sample['memory_current_bytes'] >= MEMORY_GUARD:
                    failure = 'Whole-container current memory reached declared 24 GiB safety stop'
                elif elapsed >= DEADLINE:
                    failure = 'Declared two-hour build deadline reached'
                record['status'] = 'building' if failure is None else 'stopping'
                write_json('build-progress.json', record)
                if elapsed - last_print >= 60:
                    print(json.dumps(sample), flush=True)
                    last_print = elapsed
                if failure:
                    break
                time.sleep(5)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
    record.update(completed=process.returncode == 0 and failure is None,
                  status='complete' if process.returncode == 0 and failure is None else 'stopped',
                  exit_code=process.returncode, failure=failure,
                  elapsed_s=time.monotonic() - start,
                  ended_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    record['maximum_sampled_process_RSS_sum_bytes'] = max((row['sampled_process_RSS_sum_bytes'] for row in record['samples']), default=0)
    record['maximum_sampled_cgroup_memory_bytes'] = max((row['memory_current_bytes'] for row in record['samples']), default=0)
    record['minimum_sampled_free_tmp_bytes'] = min((row['free_tmp_bytes'] for row in record['samples']), default=0)
    write_json('build-progress.json', record)
    write_json('build-result.json', record)
    print(json.dumps({key: value for key, value in record.items() if key != 'samples'}), flush=True)
    return 0 if record['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
