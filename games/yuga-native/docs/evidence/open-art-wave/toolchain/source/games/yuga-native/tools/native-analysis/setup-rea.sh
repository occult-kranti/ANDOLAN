#!/usr/bin/env bash
# Restore the pinned development CLI outside the checkout; no MCP registration.
set -euo pipefail
YUGA_REA_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
exec python3 - "$YUGA_REA_SCRIPT_DIR" "$@" <<'PY'
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time

sys.dont_write_bytecode = True
script_dir = Path(sys.argv.pop(1)).resolve()
source_dir = script_dir / 'rea-runtime'
repository = script_dir.parents[3]
expected_integrity = 'sha512-C6BG7LyrAdR74mSjertM6PrxJkcNZ2bfQNOJornPo9erDEp2tyPRVYPnV5Yodr+1RqewCQla68WulXlVnveD+A=='
expected_lock_hash = '73fa03d670870e8234e7823bca98e8cd846773fb661819ffe48a5bbb6728c7dd'
parser = argparse.ArgumentParser(description='Restore exact REA6.5.0 into a fresh outside-checkout directory. No Ghidra install or persistent agent configuration.')
parser.add_argument('--destination', type=Path, default=Path('/workspace/tooling/rea-runtime'))
parser.add_argument('--dry-run', action='store_true', help='Validate inputs/tools and print the plan; no filesystem writes or network requests.')
parser.add_argument('--timeout', type=int, default=300, help='Per-process deadline,1–600seconds.')
args = parser.parse_args()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

created = False
destination = None
receipt = None
try:
    if not 1 <= args.timeout <= 600:
        raise ValueError('Timeout must be between 1 and 600 seconds')
    if not args.destination.is_absolute():
        raise ValueError('Use an absolute destination path')
    if os.path.lexists(args.destination):
        raise ValueError('Destination already exists; use a fresh directory, including for dry-run')
    destination = args.destination.resolve()
    if destination.is_relative_to(repository):
        raise ValueError('Destination must be outside the repository')
    files = {name: source_dir / name for name in ('package.json', 'package-lock.json')}
    if any(path.is_symlink() or not path.is_file() for path in files.values()):
        raise ValueError('Pinned manifest and lockfile must be regular source files')
    package = json.loads(files['package.json'].read_text())
    lock = json.loads(files['package-lock.json'].read_text())
    if package != {'dependencies': {'rea-agents': '6.5.0'}}:
        raise ValueError('Manifest must pin only rea-agents 6.5.0 exactly')
    if digest(files['package-lock.json']) != expected_lock_hash:
        raise ValueError('Lockfile differs from the reviewed exact dependency tree')
    root = lock['packages']['node_modules/rea-agents']
    if lock.get('lockfileVersion') != 3 or root.get('version') != '6.5.0' or root.get('integrity') != expected_integrity:
        raise ValueError('Lockfile does not identify the reviewed REA archive')
    if os.environ.get('NODE_TLS_REJECT_UNAUTHORIZED') == '0':
        raise ValueError('TLS verification must remain enabled')
    node, npm = shutil.which('node'), shutil.which('npm')
    if not node or not npm:
        raise ValueError('Node and npm must already be installed')
    helper = script_dir / 'inspect-component.py'
    if helper.is_symlink() or not helper.is_file():
        raise ValueError('The repository bounded-process helper is missing or unsafe')
    plan = {'schema': 1, 'mode': 'DRY_RUN' if args.dry_run else 'INSTALL',
        'destination': str(destination), 'rea_version': '6.5.0',
        'node_version': None, 'npm_version': None,
        'runtime_probes_executed': False,
        'source_inputs': {name: digest(path) for name, path in files.items()},
        'root_archive_integrity': expected_integrity, 'locked_package_entries': len(lock['packages']),
        'lifecycle_scripts': False, 'tls_verification': True,
        'process_helper_sha256': digest(helper),
        'bootstrap_sha256': digest(script_dir / 'setup-rea.sh'),
        'persistent_agent_configuration': False, 'native_providers_installed': False}
    if args.dry_run:
        print(json.dumps(plan, indent=2))
        raise SystemExit(0)
    spec = importlib.util.spec_from_file_location('yuga_component_process', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    env = dict(os.environ)
    code, version, error = module.run_bounded([node, '--version'], env, 30)
    match = re.fullmatch(rb'v(\d+)\.(\d+)\.(\d+)\s*', version)
    if code or not match:
        raise ValueError('Cannot identify the installed Node version')
    major, minor, patch = map(int, match.groups())
    if not ((major == 22 and minor >= 19) or (major == 24 and minor >= 11) or major >= 26):
        raise ValueError('Use Node 22.19+, 24.11+, or 26+ as required by the pinned package')
    code, npm_version, error = module.run_bounded([npm, '--version'], env, 30)
    if code or not re.fullmatch(rb'\d+\.\d+\.\d+\s*', npm_version):
        raise ValueError('Cannot identify the installed npm version')
    plan.update(node_version=version.decode().strip(),
        npm_version=npm_version.decode().strip(), runtime_probes_executed=True)
    destination.mkdir(parents=True, exist_ok=False)
    created = True
    receipt = {**plan, 'status': 'INSTALLING', 'steps': [],
        'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    write_json(destination / 'setup-receipt.json', receipt)
    for name, path in files.items():
        shutil.copyfile(path, destination / name)
    def run(name, command):
        started = time.monotonic()
        code, stdout, stderr = module.run_bounded(command, env, args.timeout)
        (destination / (name + '.stdout')).write_bytes(stdout)
        (destination / (name + '.stderr')).write_bytes(stderr)
        receipt['steps'].append({'name': name, 'command': command, 'exit_code': code,
            'seconds': round(time.monotonic() - started, 3),
            'stdout_sha256': hashlib.sha256(stdout).hexdigest(),
            'stderr_sha256': hashlib.sha256(stderr).hexdigest()})
        write_json(destination / 'setup-receipt.json', receipt)
        if code:
            raise ValueError(name + ' failed; inspect the retained destination logs')
        return stdout
    run('npm-ci', [npm, '--prefix', str(destination), '--cache', str(destination / '.npm-cache'),
        'ci', '--ignore-scripts', '--no-fund', '--no-audit', '--strict-ssl=true'])
    if any(digest(path) != plan['source_inputs'][name] or
           digest(destination / name) != plan['source_inputs'][name] for name, path in files.items()):
        raise ValueError('Source or copied dependency inputs changed during installation')
    installed = destination / 'node_modules/rea-agents'
    installed_package = json.loads((installed / 'package.json').read_text())
    if installed_package.get('name') != 'rea-agents' or installed_package.get('version') != '6.5.0':
        raise ValueError('Installed package identity differs from the pin')
    if installed_package.get('bin', {}).get('rea') != 'scripts/rea.mjs':
        raise ValueError('Installed CLI entry differs from the reviewed dispatcher')
    scripts = ['scripts/rea.mjs', 'dist/cli-runtime/cli.js', 'dist/cli-runtime/cliOutput.js',
        'dist/cli-runtime/cliResultOutput.js', 'dist/mcp/main.js']
    for relative in scripts:
        path = installed / relative
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(installed):
            raise ValueError('Installed compiled script is missing or unsafe: ' + relative)
    cli = installed / 'scripts/rea.mjs'
    if run('rea-version', [node, str(cli), '--version']).decode().strip() != '6.5.0':
        raise ValueError('CLI version differs from the package pin')
    help_text = run('rea-help', [node, str(cli), '--help']).decode()
    if 'inspect' not in help_text or 'decompile' not in help_text:
        raise ValueError('CLI help does not expose the expected static-analysis commands')
    receipt.update({'status': 'READY', 'cli': str(cli),
        'verified_script_sha256': {relative: digest(installed / relative) for relative in scripts},
        'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'Pinned CLI install and version/help checks. Optional lifecycle-built addons, native providers, target analysis, MCP registration and game reconstruction are not established.'})
    write_json(destination / 'setup-receipt.json', receipt)
    print(json.dumps({'status': 'READY', 'rea_version': '6.5.0', 'cli': str(cli),
        'receipt': str(destination / 'setup-receipt.json')}))
except (OSError, ValueError, KeyError, TypeError, ImportError) as failure:
    if created and receipt is not None:
        receipt.update(status='FAILED', failure=str(failure))
        write_json(destination / 'setup-receipt.json', receipt)
    parser.exit(1, str(failure) + '\n')
PY
