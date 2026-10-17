#!/usr/bin/env python3
"""Validate the review helper's CLI and owned-screen input bounds without X11."""
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest


TOOL = Path(__file__).resolve().parents[1] / 'tools' / 'native-window-review.py'
SPEC = importlib.util.spec_from_file_location('native_window_review', TOOL)
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)
REQUIRED = ['--engine', '/unused/godot', '--pack', '/unused/yuga.pck', '--output', '/unused/review']


class ReviewBounds(unittest.TestCase):
    def parse(self, *options):
        return REVIEW.build_parser().parse_args(REQUIRED + list(options))

    def test_default_window_preserves_existing_review(self):
        args = self.parse()
        self.assertEqual((args.width, args.height), (960, 600))

    def test_supported_review_sizes(self):
        for width, height in [(960, 600), (1280, 720), (1920, 1080)]:
            with self.subTest(size=(width, height)):
                args = self.parse('--width', str(width), '--height', str(height))
                self.assertEqual((args.width, args.height), (width, height))

    def test_out_of_range_dimensions_fail_before_launch(self):
        for option, value in [('--width', '959'), ('--width', '1921'), ('--height', '599'), ('--height', '1081')]:
            with self.subTest(option=option, value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as failure:
                    self.parse(option, value)
                self.assertEqual(failure.exception.code, 2)

    def test_invalid_dimensions_fail_before_launch(self):
        for value in ['960.5', 'nan', 'inf', 'screen']:
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as failure:
                    self.parse('--width', value)
                self.assertEqual(failure.exception.code, 2)

    def test_visible_corner_pixels_are_clickable(self):
        for width, height in [(960, 600), (1280, 720), (1920, 1080)]:
            for point in [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]:
                with self.subTest(size=(width, height), point=point):
                    self.assertEqual(REVIEW.click_position(dict(zip(('x', 'y'), point)), width, height), point)

    def test_clicks_cannot_escape_requested_screen(self):
        for width, height in [(960, 600), (1280, 720), (1920, 1080)]:
            for point in [(-1, 0), (0, -1), (width, 0), (0, height), (width, height)]:
                with self.subTest(size=(width, height), point=point):
                    with self.assertRaisesRegex(ValueError, 'outside owned window'):
                        REVIEW.click_position(dict(zip(('x', 'y'), point)), width, height)

    def test_larger_review_accepts_pixels_beyond_old_960_limit(self):
        self.assertEqual(REVIEW.click_position({'x': 1200, 'y': 700}, 1280, 720), (1200, 700))
        with self.assertRaises(ValueError):
            REVIEW.click_position({'x': 1200, 'y': 700}, 960, 600)

    def test_guardian_and_existing_help_scroll_are_available(self):
        self.assertTrue({'c', 'Page_Up', 'Page_Down', 'Home', 'End'} <= REVIEW.REVIEW_KEYS)
        self.assertNotIn('F12', REVIEW.REVIEW_KEYS)


if __name__ == '__main__':
    unittest.main(verbosity=2)
