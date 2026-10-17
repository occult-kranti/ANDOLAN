#!/usr/bin/env python3
"""Exercise isolated cloth staging with real source copies and failing CLI cases."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

PROJECT = Path(__file__).resolve().parents[1]
HELPER = PROJECT / "tools/stage-open-cloth.py"
spec = importlib.util.spec_from_file_location("open_cloth_stager", HELPER)
stager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stager)


def digest(data):
    return hashlib.sha256(data).hexdigest()


class OpenClothStageCases(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="yuga-cloth-stage-cases-")
        self.root = Path(self.temporary.name)
        self.checkout = self.root / "checkout"
        self.checkout.mkdir()
        (self.checkout / ".git").mkdir()
        self.project = self.checkout / "games/yuga-native"
        for relative in (*stager.SOURCES, "tools/stage-open-cloth.py", "art/.gdignore"):
            target = self.project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / relative, target)
        self.helper = self.project / "tools/stage-open-cloth.py"
        self.output = self.root / "fixture"

    def tearDown(self):
        self.temporary.cleanup()

    def cli(self, output=None, helper=None, env=None):
        result = subprocess.run(
            [sys.executable, str(helper or self.helper), "--project-output", str(output or self.output)],
            cwd=self.root, capture_output=True, text=True, timeout=10, env=env,
        )
        self.assertEqual(result.stderr, "", result.stderr)
        receipt = json.loads(result.stdout)
        self.assertIs(receipt["passed"], result.returncode == 0)
        return result, receipt

    def rejects(self, error, **kwargs):
        result, receipt = self.cli(**kwargs)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(error, receipt["error"])
        return receipt

    def test_actual_project_cli_preserves_exact_dependencies_and_manifest(self):
        _, receipt = self.cli(helper=HELPER)
        self.assertTrue(receipt["passed"])
        self.assertEqual(receipt["project_output"], str(self.output))
        self.assertEqual(len(receipt["files"]), 9)
        self.assertEqual({row["source"] for row in receipt["files"]}, set(stager.SOURCES))
        self.assertEqual(json.loads((self.output / receipt["manifest"]).read_text()), receipt)
        for row in receipt["files"]:
            source, staged = PROJECT / row["source"], self.output / row["staged"]
            self.assertEqual(row["source_sha256"], digest(source.read_bytes()))
            self.assertEqual(row["sha256"], digest(staged.read_bytes()))
            self.assertFalse(staged.is_symlink())
            if row["source"] != "project.godot":
                self.assertEqual(source.read_bytes(), staged.read_bytes())
                self.assertNotEqual(source.stat().st_ino, staged.stat().st_ino)
        config = self.output / "project.godot"
        self.assertEqual(config.read_bytes(), stager.MINIMAL_PROJECT)
        self.assertEqual(receipt["source_project_sha256"], digest((PROJECT / "project.godot").read_bytes()))
        self.assertEqual({str(path.relative_to(self.output)) for path in self.output.rglob("*") if path.is_file()},
                         set(stager.SOURCES) | {stager.MANIFEST})

    def test_source_files_and_art_ignore_are_unchanged(self):
        before = {str(path.relative_to(self.project)): (path.read_bytes(), path.stat().st_mtime_ns)
                  for path in self.project.rglob("*") if path.is_file()}
        _, receipt = self.cli()
        after = {str(path.relative_to(self.project)): (path.read_bytes(), path.stat().st_mtime_ns)
                 for path in self.project.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.assertTrue(receipt["source_unchanged"])
        self.assertTrue((self.project / "art/.gdignore").is_file())

    def test_no_ignores_full_world_or_cache_are_inherited(self):
        for relative in (".gdignore", "art/open-art-wave/.gdignore", "art/open-art-wave/textures/.gdignore",
                         "assets/world/huge.bin", "scenes/full_world.tscn", ".godot/imported/cached.ctex"):
            extra = self.project / relative
            extra.parent.mkdir(parents=True, exist_ok=True)
            extra.write_text("never stage this")
        _, receipt = self.cli()
        self.assertTrue(receipt["passed"])
        self.assertFalse(any(path.name == ".gdignore" for path in self.output.rglob("*")))
        for relative in ("assets", "scenes", ".godot"):
            self.assertFalse((self.output / relative).exists())

    def test_existing_destination_directory_is_preserved(self):
        self.output.mkdir()
        sentinel = self.output / "preserve"
        sentinel.write_text("original")
        self.rejects("fresh directory")
        self.assertEqual(list(self.output.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_text(), "original")

    def test_existing_destination_file_is_preserved(self):
        self.output.write_text("original")
        self.rejects("fresh directory")
        self.assertEqual(self.output.read_text(), "original")

    def test_relative_destination_is_refused(self):
        self.rejects("absolute path", output=Path("relative-fixture"))
        self.assertFalse((self.root / "relative-fixture").exists())

    def test_checkout_destination_is_refused_even_outside_project(self):
        destination = self.checkout / "scratch-fixture"
        self.rejects("outside the source checkout", output=destination)
        self.assertFalse(destination.exists())

    def test_source_root_alias_is_refused(self):
        self.rejects("outside the source checkout", output=self.project)
        self.assertTrue((self.project / "art/.gdignore").is_file())

    def test_existing_and_dangling_destination_symlinks_are_refused(self):
        for name, target in (("existing-link", self.project), ("dangling-link", self.root / "absent")):
            with self.subTest(name=name):
                destination = self.root / name
                destination.symlink_to(target, target_is_directory=True)
                self.rejects("Symlinks", output=destination)
                self.assertTrue(destination.is_symlink())
        self.assertFalse(self.output.exists())

    def test_symlink_in_destination_parent_is_refused(self):
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        self.rejects("Symlinks", output=alias / "fixture")
        self.assertFalse(self.output.exists())

    def test_missing_destination_parent_is_refused_without_creation(self):
        absent = self.root / "absent"
        self.rejects("parent must be", output=absent / "fixture")
        self.assertFalse(absent.exists())

    def test_missing_required_sources_reject_before_output_creation(self):
        for relative in stager.SOURCES:
            with self.subTest(source=relative):
                source = self.project / relative
                data = source.read_bytes()
                source.unlink()
                try:
                    self.rejects("No such file")
                    self.assertFalse(self.output.exists())
                finally:
                    source.write_bytes(data)

    def test_symlink_source_file_is_refused(self):
        source = self.project / stager.SOURCES[0]
        source.unlink()
        source.symlink_to(PROJECT / stager.SOURCES[0])
        self.rejects("Symlinks")
        self.assertFalse(self.output.exists())

    def test_symlink_source_ancestor_is_refused(self):
        scripts = self.project / "scripts"
        scripts.rename(self.project / "real-scripts")
        scripts.symlink_to(self.project / "real-scripts", target_is_directory=True)
        self.rejects("Symlinks")
        self.assertFalse(self.output.exists())

    def test_symlink_project_alias_is_refused(self):
        alias = self.root / "alias"
        alias.symlink_to(self.project, target_is_directory=True)
        self.rejects("Symlinks", helper=alias / "tools/stage-open-cloth.py")
        self.assertFalse(self.output.exists())

    def test_hardlinked_source_aliases_are_refused(self):
        source = self.project / stager.SOURCES[0]
        second = self.project / stager.SOURCES[1]
        second.unlink()
        os.link(source, second)
        self.rejects("Source aliases")
        self.assertFalse(self.output.exists())

    def test_nonregular_source_is_refused_without_blocking(self):
        source = self.project / stager.SOURCES[0]
        source.unlink()
        os.mkfifo(source)
        self.rejects("not a regular file")
        self.assertFalse(self.output.exists())

    def test_invalid_text_mutations_fail_real_cli_before_creation(self):
        source = self.project / stager.SOURCES[0]
        for name, mutation in (("empty", b""), ("missing envelope", b"broken source"),
                               ("NUL", b"extends Node\n\0"), ("invalid UTF8", b"extends Node\n\xff")):
            with self.subTest(mutation=name):
                source.write_bytes(mutation)
                self.rejects("" if name == "invalid UTF8" else
                             "size" if name == "empty" else "NUL" if name == "NUL" else "envelope")
                self.assertFalse(self.output.exists())

    def test_invalid_png_mutations_fail_real_cli_before_creation(self):
        source = self.project / "art/open-art-wave/textures/indigo-woven-normal.png"
        original = source.read_bytes()
        corrupt = bytearray(original)
        corrupt[40] ^= 1
        for name, mutation in (("signature", b"invalid png"), ("truncated", original[:-3]),
                               ("checksum", bytes(corrupt)), ("trailing bytes", original + b"trailing")):
            with self.subTest(mutation=name):
                source.write_bytes(mutation)
                self.rejects("PNG")
                self.assertFalse(self.output.exists())

    def test_unstaged_resource_dependency_is_refused(self):
        source = self.project / "art/open-art-wave/integration/cloth_candidate.gd"
        source.write_text(source.read_text() + '\nconst BAD = preload("res://assets/full_world.tscn")\n')
        self.rejects("Unstaged dependency")
        self.assertFalse(self.output.exists())

    def test_source_change_after_copy_fails_and_retains_failed_manifest(self):
        original_snapshot = stager.snapshot
        calls = 0
        changed = self.project / stager.SOURCES[0]

        def mutate_after_copy(path):
            nonlocal calls
            calls += 1
            if calls == len(stager.SOURCES) + 1:
                changed.write_bytes(changed.read_bytes() + b"\n# concurrent source mutation\n")
            return original_snapshot(path)

        with mock.patch.object(stager, "PROJECT", self.project), \
                mock.patch.object(stager, "snapshot", side_effect=mutate_after_copy):
            with self.assertRaisesRegex(ValueError, "Source changed during staging"):
                stager.stage(self.output)
        receipt = json.loads((self.output / stager.MANIFEST).read_text())
        self.assertFalse(receipt["passed"])
        self.assertIn("Source changed", receipt["error"])
        self.assertNotEqual((self.output / stager.SOURCES[0]).read_bytes(), changed.read_bytes())

    def test_staging_executes_without_any_engine_on_path(self):
        environment = os.environ.copy()
        environment["PATH"] = str(self.root / "no-executables")
        _, receipt = self.cli(env=environment)
        self.assertTrue(receipt["passed"])
        self.assertFalse(receipt["engine_executed"])
        self.assertTrue(receipt["limitations"])


if __name__ == "__main__":
    unittest.main()
