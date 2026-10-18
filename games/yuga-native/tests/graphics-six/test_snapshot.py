#!/usr/bin/env python3
"""Synthetic filesystem counterexamples; no Godot, GLB import or render."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[2] / 'tools/graphics-six/snapshot.py'
spec = importlib.util.spec_from_file_location('graphics_snapshot', TOOL)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SnapshotCases(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.project = self.root / 'project'
        self.store = self.root / 'store'
        self.write('project.godot', '[application]\nconfig/name="fixture"\n')
        self.write('scripts/actor.gd', 'extends Node\n')
        self.write('assets/sample.bin', 'raw')
        self.write('assets/sample.bin.import', '[remap]\npath="res://.godot/imported/sample.scn"\n')
        self.write('.godot/imported/sample.scn', 'compiled')
        self.write('.godot/imported/sample.md5', 'source_md5="' + hashlib.md5(b'raw').hexdigest() + '"\n')

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, text):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def create(self, round_id='G1', dry_run=False):
        return module.refresh(self.source, self.project, self.store, round_id,
                              self.root / (round_id + '.json'), dry_run)

    def test_exact_initial_copy(self):
        record = self.create()
        self.assertEqual(module.inventory(self.source), module.inventory(self.project))
        self.assertEqual(module.verify(self.project)['round'], 'G1')
        self.assertEqual(record['validated_imports'][0]['source'], 'assets/sample.bin')

    def test_cache_is_independent_of_canonical_and_shared_only_with_store(self):
        record = self.create()
        name = '.godot/imported/sample.scn'
        cached = self.project / name
        blob = self.store / 'imports' / record['files'][name]['sha256']
        self.assertEqual(cached.stat().st_ino, blob.stat().st_ino)
        self.assertNotEqual(cached.stat().st_ino, (self.source / name).stat().st_ino)
        self.assertEqual(blob.stat().st_mode & 0o222, 0)
        self.write(name, 'later canonical cache')
        self.assertEqual(cached.read_text(), 'compiled')
        module.verify(self.project)

    def test_refresh_retains_displaced_bytes_and_prior_receipt(self):
        old = self.create()
        first = (self.root / 'G1.json').read_bytes()
        self.write('scripts/actor.gd', 'extends Node3D\n')
        new = self.create('G2')
        self.assertEqual(new['changed_paths'], ['scripts/actor.gd'])
        self.assertEqual(Path(new['preserved_old_sources']['scripts/actor.gd']).read_text(), 'extends Node\n')
        self.assertEqual((self.root / 'G1.json').read_bytes(), first)
        self.assertEqual(new['previous_receipt_sha256'], hashlib.sha256(first).hexdigest())
        self.assertNotEqual(old['files']['scripts/actor.gd'], new['files']['scripts/actor.gd'])

    def test_removed_file_preserved_before_removal(self):
        self.create()
        (self.source / 'scripts/actor.gd').unlink()
        record = self.create('G2')
        self.assertFalse((self.project / 'scripts/actor.gd').exists())
        self.assertTrue(Path(record['preserved_old_sources']['scripts/actor.gd']).is_file())

    def test_previous_source_tamper_rejected(self):
        self.create()
        (self.project / 'scripts/actor.gd').write_text('unreviewed change')
        with self.assertRaisesRegex(ValueError, 'Previous snapshot changed'):
            self.create('G2')
        self.assertFalse((self.root / 'G2.json').exists())

    def test_added_runtime_file_detected(self):
        self.create()
        (self.project / 'scripts/extra.gd').write_text('extends Node')
        with self.assertRaisesRegex(ValueError, 'Previous snapshot changed'):
            module.verify(self.project)

    def test_import_store_mutation_detected(self):
        self.create()
        cached = self.project / '.godot/imported/sample.scn'
        cached.chmod(0o644)
        cached.write_text('corruption')
        with self.assertRaisesRegex(ValueError, 'Previous snapshot changed'):
            module.verify(self.project)

    def test_stale_raw_rejected_before_any_write(self):
        self.write('assets/sample.bin', 'different raw')
        with self.assertRaisesRegex(ValueError, 'Stale compiled import'):
            self.create()
        self.assertFalse(self.project.exists())

    def test_missing_compiled_payload_rejected(self):
        (self.source / '.godot/imported/sample.scn').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing compiled import'):
            self.create()

    def test_dry_run_has_no_writes(self):
        record = self.create(dry_run=True)
        self.assertTrue(record['passed'])
        self.assertFalse(self.project.exists())
        self.assertFalse(self.store.exists())
        self.assertFalse((self.root / 'G1.json').exists())

    def test_unmarked_existing_directory_rejected(self):
        self.project.mkdir()
        with self.assertRaisesRegex(ValueError, 'unmarked'):
            self.create()

    def test_nested_project_rejected(self):
        with self.assertRaisesRegex(ValueError, 'separate trees'):
            module.refresh(self.source, self.source / 'snapshot', self.store, 'G1', self.root / 'receipt.json')

    def test_receipt_overwrite_rejected(self):
        self.create()
        with self.assertRaisesRegex(ValueError, 'fresh receipt'):
            self.create()

    def test_symlink_raw_rejected(self):
        (self.source / 'assets/link.bin').symlink_to(self.source / 'assets/sample.bin')
        with self.assertRaisesRegex(ValueError, 'Symlink source'):
            self.create()

    def test_explicit_harness_contract_overlay_recorded_without_source_write(self):
        contract = self.root / 'contract.json'
        contract.write_text('{"camera": "declared"}')
        name = 'tools/visual-rounds/groom_contract.json'
        record = module.refresh(self.source, self.project, self.store, 'G1', self.root / 'G1.json',
                                overlays={name: contract})
        self.assertEqual((self.project / name).read_bytes(), contract.read_bytes())
        self.assertFalse((self.source / name).exists())
        self.assertEqual(record['harness_overlays'][name]['sha256'], module.digest(contract))
        module.verify(self.project)

    def test_runtime_overlay_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Only explicit'):
            module.refresh(self.source, self.project, self.store, 'G1', self.root / 'G1.json',
                           overlays={'scripts/actor.gd': self.source / 'scripts/actor.gd'})

    def test_new_unimported_image_rejected(self):
        self.write('assets/new.png', 'new raw image')
        with self.assertRaisesRegex(ValueError, 'no import descriptor'):
            self.create()

    def test_s3tc_import_receipt_pair_supported(self):
        self.write('assets/sample.bin.import', '[remap]\npath.s3tc="res://.godot/imported/sample.s3tc.ctex"\n')
        self.write('.godot/imported/sample.s3tc.ctex', 'compiled texture')
        self.assertTrue(self.create()['passed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
