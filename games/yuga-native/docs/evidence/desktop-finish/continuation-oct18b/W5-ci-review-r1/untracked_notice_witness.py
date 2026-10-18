#!/usr/bin/env python3
"""Isolated source-census counterexample; all Git/process/network calls blocked."""
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
from unittest import mock
import zipfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def main():
    ci = load('reviewed_ci_candidate', HERE / 'ci-native-package.py.reviewed.txt')
    packaging = load('reviewed_existing_packager', PROJECT / 'tools/package-native.py')
    with tempfile.TemporaryDirectory(prefix='w5-ci-notice-') as temporary:
        repo = Path(temporary)
        project = repo / 'games/yuga-native'
        (project / 'scripts').mkdir(parents=True)
        (project / 'scripts/a.gd').write_text('extends Node\n')
        for name in ('shaders', 'scenes', 'assets'):
            (project / name).mkdir()
        (project / 'project.godot').write_text('config_version=5\n')
        (project / 'export_presets.cfg').write_text('[preset.0]\n')
        (project / 'tools').mkdir()
        (project / 'tools/package-native.py').write_bytes((PROJECT / 'tools/package-native.py').read_bytes())
        (repo / '.github/workflows').mkdir(parents=True)
        (repo / '.github/workflows/yuga-native-package.yml').write_bytes((HERE / 'yuga-native-package.yml.reviewed.txt').read_bytes())
        notices = project / 'NOTICE'
        notices.mkdir()
        required = ['GODOT-LICENSE.txt', 'GODOT-COPYRIGHT.txt', 'MAKEHUMAN-ASSET-LICENSE.md',
                    'HERO-PROVENANCE.json', 'RAMA-PRODUCTION-PROVENANCE.json', 'RAMA-HERO-PROVENANCE.json',
                    'CONFLUENCE-WORLD-PROVENANCE.json', 'CONFLUENCE-DUEL-PROVENANCE.json',
                    'TPS-MOTION-NOTICE.txt', 'GODOT-TPS-UPSTREAM-LICENSE.md',
                    'TRAVERSAL-AUDIO-PROVENANCE.json', 'TRAVERSAL-ARMIES.txt', 'SIEGE-VEHICLES.txt', 'MYTHIC-INVOCATIONS.txt']
        for name in required:
            (notices / name).write_text('{}\n' if name.endswith('.json') else 'finite fixture notice\n')
        for name in packaging.BUNDLED_FONT_NOTICES:
            target = project / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / name, target)
        commit = '1' * 40
        runtime_paths = ['games/yuga-native/scripts/a.gd', 'games/yuga-native/project.godot', 'games/yuga-native/export_presets.cfg']
        calls = []

        def git_output(command, **kwargs):
            calls.append(command)
            if command == ['git', 'rev-parse', 'HEAD']:
                return commit + '\n'
            if command[:4] == ['git', 'ls-files', '-z', '--']:
                return ('\0'.join(runtime_paths) + '\0').encode()
            raise AssertionError('Unexpected subprocess: ' + repr(command))

        def git_diff(command, **kwargs):
            calls.append(command)
            assert command == ['git', 'diff', '--exit-code', 'HEAD', '--']
            return subprocess.CompletedProcess(command, 0)

        with mock.patch.object(ci, 'PROJECT', project), mock.patch.object(ci, 'REPOSITORY', repo), \
             mock.patch.object(packaging, 'PROJECT', project), mock.patch.object(ci, 'package_module', return_value=packaging), \
             mock.patch.object(subprocess, 'check_output', side_effect=git_output), \
             mock.patch.object(subprocess, 'run', side_effect=git_diff), \
             mock.patch.object(subprocess, 'Popen', side_effect=AssertionError('No process allowed')), \
             mock.patch.object(socket, 'socket', side_effect=AssertionError('No network allowed')):
            before = ci.source_snapshot(commit)
            extra = notices / 'extra-generated-at-build.txt'
            extra.write_text('not part of the declared source commit\n')
            after = ci.source_snapshot(commit)
            stage = repo / 'staging'
            stage.mkdir()
            packaging.safe_notice_copy(stage)
            archive = repo / 'witness.zip'
            packaging.zip_directory(stage, archive)
            with zipfile.ZipFile(archive) as bundle:
                member = 'staging/NOTICE/extra-generated-at-build.txt'
                copied = bundle.read(member)
            result = {
                'counterexample_reproduced': before == after and copied == extra.read_bytes(),
                'snapshot_unchanged': before == after,
                'untracked_notice_copied_and_zipped_by_real_packager': copied == extra.read_bytes(),
                'extra_member': member,
                'extra_sha256': hashlib.sha256(copied).hexdigest(),
                'git_calls_mocked': calls,
                'scope': 'Synthetic tracked census models a clean checkout plus an untracked NOTICE file. Actual source_snapshot, safe_notice_copy and zip_directory execute; no Git, network, engine or PCK export executes. This demonstrates the snapshot boundary, not a qualified package.',
                'helper_sha256': hashlib.sha256((HERE / 'ci-native-package.py.reviewed.txt').read_bytes()).hexdigest(),
                'packager_sha256': hashlib.sha256((PROJECT / 'tools/package-native.py').read_bytes()).hexdigest(),
            }
            assert result['counterexample_reproduced']
            output = HERE / 'untracked-notice-witness.json'
            with output.open('x') as stream:
                json.dump(result, stream, indent=2)
                stream.write('\n')
            print(json.dumps({k: result[k] for k in ('counterexample_reproduced', 'snapshot_unchanged', 'untracked_notice_copied_and_zipped_by_real_packager')}))


if __name__ == '__main__':
    main()
