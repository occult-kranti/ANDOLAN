#!/usr/bin/env python3
"""Counterexamples for CI engine acquisition and source closure; no network/engines."""
from contextlib import ExitStack
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import warnings
import zipfile

SPEC = importlib.util.spec_from_file_location('candidate', Path(__file__).resolve().parents[1] / 'tools/ci-native-package.py')
CI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CI)
DATA = b'finite fixture runtime\n'
BINARY = {'bytes': len(DATA), 'sha256': hashlib.sha256(DATA).hexdigest()}


class RuntimeAcquisitionCases(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='yuga-ci-runtime-')
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def archive(self, rows):
        path = self.root / 'input.zip'
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)  # Intentional duplicate-name counterexample.
            with zipfile.ZipFile(path, 'w') as output:
                for name, data, mode in rows:
                    info = zipfile.ZipInfo(name)
                    info.create_system = 3
                    info.external_attr = mode << 16
                    output.writestr(info, data)
        return path, CI.record(path)

    def valid_rows(self):
        return [(CI.RUNTIME_MEMBER, DATA, stat.S_IFREG | 0o755),
                ('yuga-native-linux-x86_64/START-HERE.txt', b'fixture', stat.S_IFREG | 0o644)]

    def test_exact_member_only_and_input_unchanged(self):
        archive, pinned = self.archive(self.valid_rows())
        before = archive.stat()
        destination = self.root / 'runtime'
        CI.extract_runtime(archive, destination, pinned, BINARY)
        self.assertEqual({p.name for p in destination.iterdir()}, {'godot', 'runtime-preparation.json'})
        self.assertEqual((destination / 'godot').read_bytes(), DATA)
        self.assertEqual(stat.S_IMODE((destination / 'godot').stat().st_mode), 0o755)
        self.assertEqual(CI.record(archive), pinned)
        self.assertEqual((before.st_ino, before.st_mtime_ns), (archive.stat().st_ino, archive.stat().st_mtime_ns))

    def test_changed_outer_archive_rejected_before_write(self):
        archive, pinned = self.archive(self.valid_rows())
        with archive.open('ab') as stream:
            stream.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'ZIP identity'):
            CI.extract_runtime(archive, self.root / 'runtime', pinned, BINARY)
        self.assertFalse((self.root / 'runtime').exists())

    def test_duplicate_runtime_rejected(self):
        archive, pinned = self.archive(self.valid_rows() + self.valid_rows()[:1])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            CI.extract_runtime(archive, self.root / 'runtime', pinned, BINARY)

    def test_unsafe_names_and_nonregular_members_rejected(self):
        for name, mode in [('yuga-native-linux-x86_64/../other', stat.S_IFREG | 0o644),
                           ('/outside', stat.S_IFREG | 0o644),
                           ('yuga-native-linux-x86_64\\other', stat.S_IFREG | 0o644),
                           ('yuga-native-linux-x86_64/link', stat.S_IFLNK | 0o777),
                           ('yuga-native-linux-x86_64/fifo', stat.S_IFIFO | 0o644)]:
            with self.subTest(name=name):
                archive, pinned = self.archive(self.valid_rows() + [(name, b'x', mode)])
                with self.assertRaises(ValueError):
                    CI.extract_runtime(archive, self.root / 'runtime', pinned, BINARY)
                self.assertFalse((self.root / 'runtime').exists())

    def test_missing_runtime_rejected(self):
        archive, pinned = self.archive(self.valid_rows()[1:])
        with self.assertRaisesRegex(ValueError, 'member missing'):
            CI.extract_runtime(archive, self.root / 'runtime', pinned, BINARY)

    def test_inner_hash_mismatch_is_never_made_executable(self):
        archive, pinned = self.archive(self.valid_rows())
        wrong = {**BINARY, 'sha256': '0' * 64}
        with self.assertRaisesRegex(ValueError, 'Extracted runtime identity'):
            CI.extract_runtime(archive, self.root / 'runtime', pinned, wrong)
        self.assertEqual((self.root / 'runtime/godot').stat().st_mode & 0o111, 0)

    def test_existing_destination_and_symlink_input_rejected(self):
        archive, pinned = self.archive(self.valid_rows())
        destination = self.root / 'occupied'
        destination.mkdir()
        (destination / 'keep').write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError, 'Fresh runtime destination'):
            CI.extract_runtime(archive, destination, pinned, BINARY)
        self.assertEqual((destination / 'keep').read_bytes(), b'keep')
        link = self.root / 'alias.zip'
        link.symlink_to(archive)
        with self.assertRaisesRegex(ValueError, 'Regular file'):
            CI.extract_runtime(link, self.root / 'runtime', pinned, BINARY)


class SourceClosureCases(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='yuga-ci-source-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / 'games/yuga-native'
        (self.project / 'NOTICE/nested').mkdir(parents=True)
        self.notice = self.project / 'NOTICE/nested/license.txt'
        self.notice.write_bytes(b'tracked notice\n')
        (self.project / 'tools').mkdir()
        (self.project / 'tools/package-native.py').write_text('# finite fixture\n')
        (self.root / '.github/workflows').mkdir(parents=True)
        (self.root / '.github/workflows/yuga-native-package.yml').write_text('name: fixture\n')
        self.commit = '1' * 40
        self.runtime = {'sha256': 'fixture runtime digest', 'files': {'scripts/example.gd': {'bytes': 0, 'sha256': 'fixture'}}}
        self.tracked_notices = ['games/yuga-native/NOTICE/nested/license.txt']
        self.calls = []
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(mock.patch.object(CI, 'PROJECT', self.project))
        self.stack.enter_context(mock.patch.object(CI, 'REPOSITORY', self.root))
        self.stack.enter_context(mock.patch.object(CI, 'package_module', return_value=SimpleNamespace(source_state=lambda: self.runtime)))
        self.stack.enter_context(mock.patch.object(subprocess, 'check_output', side_effect=self.git_output))
        self.stack.enter_context(mock.patch.object(subprocess, 'run', side_effect=self.git_diff))
        self.stack.enter_context(mock.patch.object(subprocess, 'Popen', side_effect=AssertionError('No process permitted')))
        self.stack.enter_context(mock.patch.object(socket, 'socket', side_effect=AssertionError('No network permitted')))

    def git_output(self, command, **kwargs):
        self.calls.append(command)
        if command == ['git', 'rev-parse', 'HEAD']:
            return self.commit + '\n'
        if command == ['git', 'ls-files', '-z', '--', 'games/yuga-native/NOTICE']:
            return ('\0'.join(self.tracked_notices) + '\0').encode()
        expected = ['games/yuga-native/' + part for part in ('scripts', 'shaders', 'scenes', 'assets', 'project.godot', 'export_presets.cfg')]
        self.assertEqual(command, ['git', 'ls-files', '-z', '--', *expected])
        return b'games/yuga-native/scripts/example.gd\0'

    def git_diff(self, command, **kwargs):
        self.calls.append(command)
        self.assertEqual(command, ['git', 'diff', '--quiet', 'HEAD', '--'])
        self.assertTrue(kwargs['check'])
        return subprocess.CompletedProcess(command, 0)

    def test_tracked_notice_bytes_bound_and_generated_tool_uid_allowed(self):
        before = CI.source_snapshot(self.commit)
        self.assertEqual(before['notices'], {'NOTICE/nested/license.txt': CI.record(self.notice)})
        (self.project / 'tools/generated.gd.uid').write_text('uid://abc123\n')
        self.assertEqual(CI.source_snapshot(self.commit), before)

    def test_untracked_notice_rejected(self):
        CI.source_snapshot(self.commit)
        (self.project / 'NOTICE/extra-generated-at-build.txt').write_text('not committed\n')
        with self.assertRaisesRegex(ValueError, 'NOTICE file census'):
            CI.source_snapshot(self.commit)

    def test_changed_notice_bytes_stop_finalize_before_manifests(self):
        before = CI.source_snapshot(self.commit)
        path = self.root / 'before.json'
        path.write_text(json.dumps(before))
        self.notice.write_bytes(b'changed notice\n')
        with self.assertRaisesRegex(ValueError, 'Source changed during'):
            CI.finalize(path, self.root / 'absent-build', self.commit, 'fixture')
        self.assertFalse((self.root / 'absent-build').exists())

    def test_missing_tracked_notice_rejected(self):
        self.notice.unlink()
        with self.assertRaisesRegex(ValueError, 'NOTICE file census'):
            CI.source_snapshot(self.commit)

    def test_notice_root_symlink_rejected(self):
        outside = self.root / 'outside-notices'
        (self.project / 'NOTICE').rename(outside)
        (self.project / 'NOTICE').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Regular NOTICE directory'):
            CI.source_snapshot(self.commit)

    def test_notice_file_and_directory_symlinks_rejected(self):
        for target in (self.notice, self.notice.parent, self.root / 'outside'):
            with self.subTest(target=target):
                link = self.project / 'NOTICE/link'
                link.symlink_to(target, target_is_directory=target.is_dir())
                try:
                    with self.assertRaisesRegex(ValueError, 'NOTICE symlink'):
                        CI.source_snapshot(self.commit)
                finally:
                    link.unlink()


if __name__ == '__main__':
    unittest.main(verbosity=2)
