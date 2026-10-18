import math
import struct
import unittest
from secondary_frame_probe import accessor, angle, cross, displaced, dot, face_normal, uv_frame


class SecondaryFrameCases(unittest.TestCase):
    points = [(0., 0., 0.), (1., 0., 0.), (0., 1., 0.)]
    uvs = [(0., 0.), (1., 0.), (0., 1.)]

    def test_uniform_translation_preserves_normal(self):
        p = displaced(self.points, [.6]*3, (.03, -.07, .02))
        self.assertLess(angle(face_normal(p), face_normal(self.points)), 1e-6)

    def test_known_differential_exposes_stale_normal(self):
        p = displaced(self.points, [0, 1, 0], (0, 0, .075))
        # The exact triangle is z=.075*x, with normal (-.075,0,1).
        self.assertAlmostEqual(angle(face_normal(p), (0, 0, 1)), math.degrees(math.atan(.075)), places=10)
        self.assertEqual(p[0], self.points[0])
        self.assertEqual(p[2], self.points[2])
        # Anchors do not imply unchanged normals on incident triangles.
        self.assertNotEqual(face_normal(p), face_normal(self.points))

    def test_mirrored_uv_preserves_handedness(self):
        p = displaced(self.points, [0, .4, 1], (.02, .01, .075))
        for uv, sign in [(self.uvs, 1), ([(0, 0), (-1, 0), (0, 1)], -1)]:
            n, t, b, h = uv_frame(p, uv)
            self.assertEqual(h, sign)
            self.assertAlmostEqual(dot(n, t), 0, places=12)
            self.assertAlmostEqual(dot(n, b), 0, places=12)
            self.assertAlmostEqual(dot(t, b), 0, places=12)
            self.assertAlmostEqual(dot(cross(n, t), b), sign, places=12)

    def test_degenerate_and_nonfinite_inputs_refused(self):
        with self.assertRaises(ValueError):
            face_normal([(0, 0, 0)]*3)
        with self.assertRaises(ValueError):
            uv_frame(self.points, [(0, 0)]*3)
        for mask in [float('nan'), -1, 2]:
            with self.assertRaises(ValueError):
                displaced(self.points, [0, mask, 1], (0, 0, .075))

    def test_displacement_bound_and_anchor(self):
        for mask in [0, .1, .5, 1]:
            p = displaced(self.points, [mask]*3, (.045, 0, .06))
            length = math.sqrt(sum(x*x for x in p[0]))
            self.assertLessEqual(length, .075+1e-12)
            self.assertAlmostEqual(length, .075*mask*mask)

    def test_strided_normalized_accessor_and_bounds(self):
        blob = struct.pack('<4B4x4B4x', 255, 255, 255, 0, 255, 255, 255, 255)
        doc = {'accessors': [{'bufferView': 0, 'componentType': 5121, 'type': 'VEC4', 'count': 2, 'normalized': True}],
               'bufferViews': [{'byteLength': 16, 'byteStride': 8}]}
        self.assertEqual(accessor(doc, blob, 0), [(1., 1., 1., 0.), (1., 1., 1., 1.)])
        doc['bufferViews'][0]['byteLength'] = 10
        with self.assertRaises(ValueError):
            accessor(doc, blob, 0)


if __name__ == '__main__':
    unittest.main()
