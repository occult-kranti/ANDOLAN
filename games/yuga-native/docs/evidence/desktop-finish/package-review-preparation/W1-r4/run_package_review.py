#!/usr/bin/env python3
"""Bounded wrapper for the existing native package runner; no package mutation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
from package_identity import SOURCE as EXPECTED_SOURCE, RUNTIME, EXPORTER, ARCHIVE, PCK, EXPORT_MANIFEST, PACKAGE_MANIFEST, SELECTION, exact_selection, approved_inputs_bound
GDB = Path('/workspace/tooling/native-debug/gdb-local')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def process_table():
    result = {}
    ticks = os.sysconf('SC_CLK_TCK')
    for folder in Path('/proc').iterdir():
        if not folder.name.isdigit():
            continue
        try:
            raw = (folder / 'stat').read_text()
            fields = raw[raw.rfind(')') + 2:].split()
            result[int(folder.name)] = {
                'pid': int(folder.name), 'ppid': int(fields[1]),
                'state': fields[0], 'start_ticks': int(fields[19]),
                'cpu_seconds': (int(fields[11]) + int(fields[12])) / ticks,
                'rss_bytes': int(fields[21]) * os.sysconf('SC_PAGE_SIZE'),
                'exe': os.readlink(folder / 'exe'),
            }
        except (OSError, ValueError, IndexError):
            pass
    return result


def descendants(table, root):
    found = {root} if root in table else set()
    while True:
        more = {pid for pid, row in table.items() if row['ppid'] in found} - found
        if not more:
            return [table[pid] for pid in sorted(found)]
        found.update(more)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['project', 'executable', 'package', 'package-archive', 'export-manifest', 'extraction-report', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--phase', choices=['warm', 'cold'], required=True)
    parser.add_argument('--display', type=int, required=True)
    parser.add_argument('--shader-cache-seed', type=Path)
    parser.add_argument('--godot-shader-cache-seed', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if not approved_inputs_bound(): parser.error('r4 qualified archive identities are not yet bound')
    if args.output.exists() or args.output.with_name(args.output.name + '-watchdog').exists():
        parser.error('Fresh output and watchdog directories are required')
    if args.phase == 'cold' and (args.shader_cache_seed or args.godot_shader_cache_seed):
        parser.error('Cold qualification prohibits both cache seeds')
    if args.phase == 'warm' and not (args.shader_cache_seed and args.godot_shader_cache_seed):
        parser.error('Warm qualification requires both explicitly identified cache seeds')
    for name in ['executable', 'package', 'package_archive', 'export_manifest']:
        if not getattr(args, name).is_file():
            parser.error('Missing actual package input: ' + name)
    if sha(args.executable) != RUNTIME:
        parser.error('This attempt is bound to the exact separately declared patched e69 packaged binary')
    exported = json.loads(args.export_manifest.read_text())
    if exported.get('git', {}).get('head') != EXPECTED_SOURCE or exported.get('git', {}).get('native_worktree_status') != '':
        parser.error('Export must identify the exact clean approved96d5b9cd source checkpoint')
    if not exact_selection(exported.get('engine_selection', {})):
        parser.error('Exporter/runtime/source-build proof selection differs from approved r4')
    if (sha(args.package) != PCK or sha(args.package_archive) != ARCHIVE or
            sha(args.export_manifest) != EXPORT_MANIFEST):
        parser.error('Package/archive/export manifest differs from approved r4')
    extraction = json.loads(args.extraction_report.read_text())
    destination = args.executable.resolve().parent
    if (extraction.get('passed') is not True or extraction.get('script_sha256') != sha(HERE/'verify_extract.py') or
            not extraction.get('checks') or not all(extraction['checks'].values()) or
            set(extraction.get('input_sha256',{}).values()) != {ARCHIVE,EXPORT_MANIFEST,PACKAGE_MANIFEST} or
            Path(extraction.get('destination','')).resolve() != destination or
            args.executable.resolve() != destination/'godot' or args.package.resolve() != destination/'yuga-native.pck' or
            extraction.get('source_commit') != EXPECTED_SOURCE or
            extraction.get('input_sha256',{}).get(str(args.package_archive)) != ARCHIVE):
        parser.error('Require the actual exact verified extraction and its sibling executable/PCK')
    members = extraction.get('members',{})
    if not members or not all((destination/name).is_file() and (destination/name).stat().st_size == row['bytes'] and sha(destination/name) == row['sha256'] for name,row in members.items()):
        parser.error('An extracted archive payload changed before execution')
    command = [sys.executable, str(HERE / 'tools/ui-campaign/run.py'),
               '--mode', 'package', '--project', str(args.project.resolve()),
               '--executable', str(args.executable.resolve()), '--package', str(args.package.resolve()),
               '--package-archive', str(args.package_archive.resolve()),
               '--export-manifest', str(args.export_manifest.resolve()),
               '--output', str(args.output.resolve()), '--plan', str(HERE / ('package-' + args.phase + '-plan.json')),
               '--renderer', 'forward_plus', '--render-threads', '2',
               '--width', '960', '--height', '600', '--display', str(args.display), '--timeout', '600']
    if args.phase == 'warm':
        command += ['--allow-authority-staging', '--shader-cache-seed', str(args.shader_cache_seed.resolve()),
                    '--godot-shader-cache-seed', str(args.godot_shader_cache_seed.resolve())]
    limit = 600 if args.phase == 'cold' else 900
    record = {'expected_source_commit': EXPECTED_SOURCE, 'phase': args.phase, 'command': command, 'overall_limit_seconds': limit,
              'shutdown_grace_seconds': 12,
              'inner_timeout_scope': '600 seconds per readiness condition; outer bound is separate',
              'first_native_observer_after_seconds': 120, 'sample_interval_seconds': 15,
              'engine_selection': exported['engine_selection'],
              'archive_runtime_executed': True, 'diagnostic_runtime_override': False,
              'extraction_report_sha256': sha(args.extraction_report), 'extracted_payloads': members,
              'engine_sha256': sha(args.executable), 'package_sha256': sha(args.package),
              'archive_sha256': sha(args.package_archive), 'export_manifest_sha256': sha(args.export_manifest),
              'tool_sha256': {str(p.relative_to(HERE)): sha(p) for p in [Path(__file__), HERE / 'package_identity.py', SELECTION,
                  HERE / 'tools/ui-campaign/run.py', HERE / 'tools/ui-campaign/observer.gd',
                  HERE / 'tools/ui-campaign/integrated_capture.gd', HERE / 'tools/ui-campaign/authority_stage.gd',
                  HERE / ('package-' + args.phase + '-plan.json')]},
              'scope': 'Actual extracted explicitly selected pipeline-low-priority-v1 e69 Linux executable; official f64 exporter remains distinct; fresh isolated XDG; native XTest. Warm journey includes explicitly labeled actual-rule outcome stages; cold has none. No pose or asset writes.'}
    if args.dry_run:
        print(json.dumps(record, indent=2))
        return 0
    os.sched_setaffinity(0, {0, 1})
    logroot = args.output.with_name(args.output.name + '-watchdog')
    logroot.mkdir(parents=True)
    record['started_unix'] = time.time()
    record['affinity'] = sorted(os.sched_getaffinity(0))
    save(logroot / 'receipt.json', record)
    started = time.monotonic()
    next_sample = 0.0
    observed = False
    terminated = False
    with (logroot / 'driver.log').open('w') as driver:
        proc = subprocess.Popen(command, stdout=driver, stderr=subprocess.STDOUT, start_new_session=True)
        record['owned_runner_pid'] = proc.pid
        try:
            while proc.poll() is None:
                elapsed = time.monotonic() - started
                if elapsed >= next_sample:
                    table = process_table()
                    tree = descendants(table, proc.pid)
                    sample = {'elapsed_seconds': elapsed, 'pngs': len(list(args.output.glob('*.png'))),
                              'processes': tree, 'summed_rss_bytes': sum(p['rss_bytes'] for p in tree),
                              'rss_scope': 'Sampled sum; shared mappings may be counted more than once'}
                    with (logroot / 'process-samples.jsonl').open('a') as f:
                        f.write(json.dumps(sample) + '\n')
                    next_sample = elapsed + 15
                    engines = [p for p in tree if Path(p['exe']).resolve() == args.executable.resolve()]
                    if elapsed >= 120 and not (args.output / ('01-title-after-configured-boot.png' if args.phase == 'warm' else '01-package-title.png')).exists() and engines and not observed:
                        observed = True
                        target = engines[0]
                        current = process_table().get(target['pid'])
                        if current and current['start_ticks'] == target['start_ticks'] and GDB.is_file():
                            argv = [str(GDB), '--batch', '-ex', 'set pagination off', '-ex',
                                    'set print frame-arguments none', '-p', str(target['pid']), '-ex',
                                    'info threads', '-ex', 'thread apply all bt 32', '-ex', 'detach']
                            with (logroot / 'native-gdb.log').open('w') as gl:
                                try:
                                    observer = subprocess.run(argv, stdout=gl, stderr=subprocess.STDOUT, timeout=20)
                                    record['native_observer'] = {'target': target, 'command': argv, 'exit': observer.returncode}
                                except subprocess.TimeoutExpired:
                                    record['native_observer'] = {'target': target, 'command': argv, 'timeout_seconds': 20}
                        else:
                            record['native_observer'] = {'target': target, 'not_run': 'Target changed or verified local debugger unavailable'}
                if elapsed >= limit:
                    terminated = True
                    os.killpg(proc.pid, signal.SIGTERM)
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait()
                    break
                time.sleep(.25)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
            # A failed Python driver can exit before its descendants. Its new
            # session is owned by this invocation; never leave that group live.
            try:
                os.killpg(proc.pid, 0)
            except ProcessLookupError:
                record['remaining_owned_group_cleanup'] = False
            else:
                record['remaining_owned_group_cleanup'] = True
                os.killpg(proc.pid, signal.SIGTERM)
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    try:
                        os.killpg(proc.pid, 0)
                    except ProcessLookupError:
                        break
                    time.sleep(.1)
                else:
                    os.killpg(proc.pid, signal.SIGKILL)
        record.update({'driver_exit': proc.returncode, 'overall_timeout': terminated,
                       'elapsed_seconds': time.monotonic() - started,
                       'png_count': len(list(args.output.glob('*.png'))),
                       'complete': proc.returncode == 0 and not terminated})
    record['extracted_payloads_unchanged'] = all((destination/name).is_file() and (destination/name).stat().st_size == row['bytes'] and sha(destination/name) == row['sha256'] for name,row in members.items())
    record['complete'] = record['complete'] and record['extracted_payloads_unchanged']
    save(logroot / 'receipt.json', record)
    print(json.dumps({k: record[k] for k in ['phase', 'complete', 'driver_exit', 'elapsed_seconds', 'png_count']}))
    return 0 if record['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
