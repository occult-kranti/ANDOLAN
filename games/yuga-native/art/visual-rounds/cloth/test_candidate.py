#!/usr/bin/env python3
"""CPU contract/counterexample tests; actual engine mip receipt is a separate gate."""
import hashlib
import json
from pathlib import Path
import unittest
import numpy as np
from PIL import Image
import build_candidate as bake


def validate(a):
    if a.shape != (1024, 1024) or a.dtype != np.uint8:
        raise ValueError('expected one 1024x1024 uint8 scalar channel')
    q = a.astype(float) / 255
    if q.min() < .76 or q.max() > .82 or not (.785 < q.mean() < .795):
        raise ValueError('roughness bounds or linear-data mean wrong')
    if not (.003 < q.std() < .012):
        raise ValueError('weave missing or amplitude excessive')


class ClothCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = np.asarray(Image.open(bake.OUTPUT))
        cls.baseline = np.asarray(Image.open(bake.PROJECT / 'assets/materials/rama-finish/woven-roughness.png'))

    def test_actual_png_encoding_and_reproducibility(self):
        data = bake.OUTPUT.read_bytes()
        self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(data[24:26], bytes([8, 0]), 'PNG must be 8-bit grayscale')
        self.assertEqual(data, bake.encode(bake.pixels()))
        validate(self.a)

    def test_counterexamples_reject_flat_gamma_and_packed_maps(self):
        bad = [np.full_like(self.a, 201),
               np.rint((self.a / 255.) ** 2.2 * 255).astype(np.uint8),
               np.repeat(self.a[:, :, None], 3, axis=2)]
        for image in bad:
            with self.assertRaises(ValueError):
                validate(image)

    def test_periodic_value_and_gradient_at_both_seams(self):
        t = np.linspace(0, 1, 3001)
        e = 1e-6
        for axis in (0, 1):
            f = (lambda u: bake.field(u, t)) if axis == 0 else (lambda u: bake.field(t, u))
            np.testing.assert_allclose(f(0.), f(1.), atol=1e-12)
            np.testing.assert_allclose((f(e)-f(-e))/(2*e), (f(1+e)-f(1-e))/(2*e), atol=1e-7)
        # Quantized edge adjacency cannot exceed the strongest interior transition.
        for axis in (0, 1):
            interior = np.abs(np.diff(self.a.astype(float), axis=axis))
            seam = np.abs(np.take(self.a.astype(float), 0, axis=axis) - np.take(self.a.astype(float), -1, axis=axis))
            self.assertLessEqual(float(seam.max()), float(interior.max()))

    def test_cpu_mip_reduction_retains_mean_and_removes_fiber_alias(self):
        current = Image.fromarray(self.a.astype(np.float32) / 255.)
        rows = []
        for level in range(11):
            a = np.asarray(current).astype(float)
            rows.append({'level': level, 'size': current.width, 'mean': float(a.mean()), 'std': float(a.std())})
            self.assertLess(abs(a.mean() - self.a.mean()/255), 1e-6)
            if current.width <= 64:
                self.assertLess(a.std(), .003)
            if current.width > 1:
                current = current.resize((current.width//2, current.height//2), Image.Resampling.BOX)
        self.assertEqual(rows[-1]['size'], 1)
        self.__class__.mips = rows

    def test_material_contract_and_distinct_channel_counterexample(self):
        p = json.loads((bake.HERE / 'material-profile.json').read_text())
        self.assertEqual(p, bake.PROFILE)
        packed_probe = np.array([.79, .08, .02, 1.])
        self.assertAlmostEqual(float(np.dot(packed_probe, p['rough_channel'])), .79)
        self.assertNotAlmostEqual(float(np.dot(packed_probe, [0,1,0,0])), .79)
        self.assertTrue(p['mipmaps_generate'])
        self.assertEqual(set(p['allowed_surface_names']), {'Cobalt handwoven silk', 'Cobalt lotus brocade'})
        self.assertEqual(p['roughness_multiplier'], 1.)
        self.assertIn('linear', p['color_space'])

    def test_source_ownership_and_all_lod_bytes_unchanged(self):
        manifest = json.loads((bake.HERE / 'source-manifest.json').read_text())
        for rel, expected in manifest['source_inputs'].items():
            self.assertEqual(hashlib.sha256((bake.PROJECT/rel).read_bytes()).hexdigest(), expected['sha256'], rel)
        self.assertEqual(len([x for x in manifest['source_inputs'] if x.endswith('.glb')]), 3)

    def test_candidate_changes_response_without_low_frequency_diamonds(self):
        a, b = self.a.astype(float)/255, self.baseline.astype(float)/255
        self.assertGreater(a.mean()-b.mean(), .05)
        self.assertLess(a.std(), b.std()*.30)
        small = np.asarray(Image.fromarray(self.a).resize((32,32), Image.Resampling.BOX)).astype(float)/255
        self.assertLess(small.std(), .002)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ClothCandidateTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    root = bake.PROJECT/'docs/evidence/visual-rounds/round3/role01'
    report = {'task': 'R3-01', 'tests_run': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'passed': result.wasSuccessful(),
              'candidate_sha256': hashlib.sha256(bake.OUTPUT.read_bytes()).hexdigest(),
              'candidate_texels': {'min': int(ClothCandidateTests.a.min()), 'max': int(ClothCandidateTests.a.max()),
                  'mean': float(ClothCandidateTests.a.mean()/255), 'std': float(ClothCandidateTests.a.std()/255)},
              'cpu_box_filter_mip_reference': getattr(ClothCandidateTests, 'mips', []),
              'actual_godot_import_mips': 'PENDING serialized capture owner; CPU reference is not an imported mip claim',
              'actual_pixels': 'PENDING matched capture review'}
    (root/'cpu-tests.json').write_text(json.dumps(report, indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
