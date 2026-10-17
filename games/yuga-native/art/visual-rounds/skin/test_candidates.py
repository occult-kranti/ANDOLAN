#!/usr/bin/env python3
"""Guard the actual one-variable overlays and input/output safety contract."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import stage_candidate as candidate


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r2-skin-test-")
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def test_real_inputs_and_exact_single_variable(self):
        manifest = json.loads((candidate.HERE / "source-manifest.json").read_text())
        before = {p: hashlib.sha256((candidate.PROJECT / p).read_bytes()).hexdigest()
                  for p in manifest["runtime_inputs"]}
        for name, edit in candidate.VARIANTS.items():
            out = self.root / name
            receipt = candidate.stage(candidate.PROJECT, out, name)
            files = [p for p in (out / "overlay").rglob("*") if p.is_file()]
            self.assertEqual(receipt["changed_variable_count"], int(edit is not None))
            self.assertEqual(len(files), int(edit is not None))
            self.assertEqual(receipt["new_maps"], 0)
            if edit:
                relative, old, new = edit
                original = (candidate.PROJECT / relative).read_bytes()
                actual = (out / "overlay" / relative).read_bytes()
                self.assertEqual(actual, original.replace(old.encode(), new.encode(), 1))
                self.assertEqual(actual.replace(new.encode(), old.encode(), 1), original)
        after = {p: hashlib.sha256((candidate.PROJECT / p).read_bytes()).hexdigest()
                 for p in manifest["runtime_inputs"]}
        self.assertEqual(before, after)

    def test_reused_output_refused(self):
        out = self.root / "existing"
        out.mkdir()
        (out / "keep.txt").write_text("retained evidence")
        with self.assertRaisesRegex(ValueError, "must not exist"):
            candidate.stage(candidate.PROJECT, out, "control")
        self.assertEqual((out / "keep.txt").read_text(), "retained evidence")

    def test_repository_and_symlink_output_refused(self):
        for name in [candidate.REPOSITORY / "forbidden-skin-output", candidate.PROJECT / "forbidden-skin-output"]:
            with self.assertRaisesRegex(ValueError, "outside"):
                candidate.stage(candidate.PROJECT, name, "control")
            self.assertFalse(name.exists())
        (self.root / "link").symlink_to(candidate.PROJECT, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "outside"):
            candidate.stage(candidate.PROJECT, self.root / "link" / "forbidden-skin-output", "control")

    def test_drifted_input_refused_before_output(self):
        project = self.root / "drifted-project"
        target = project / "assets/heroes/rama-hero.glb"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"unaccepted hero")
        out = self.root / "not-created"
        with self.assertRaisesRegex(ValueError, "Pinned source mismatch"):
            candidate.stage(project, out, "roughness-mips")
        self.assertFalse(out.exists())

    def test_symlink_input_escape_refused(self):
        project = self.root / "escaped-project"
        target = project / "assets/heroes/rama-hero.glb"
        target.parent.mkdir(parents=True)
        target.symlink_to(candidate.PROJECT / "assets/heroes/rama-hero.glb")
        out = self.root / "not-created"
        with self.assertRaisesRegex(ValueError, "escapes source"):
            candidate.stage(project, out, "control")
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
