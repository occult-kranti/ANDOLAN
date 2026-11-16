"""Report links must work without accepting lookalike or credential-bearing URLs."""
import unittest

from audit_browser import allowed_output_link


class BrowserAuditLinkTests(unittest.TestCase):
    base = "https://occult-kranti.github.io/ANDOLAN/production/"

    def test_actual_media_and_repository_report(self):
        self.assertTrue(allowed_output_link(self.base + "media/studio.png", self.base))
        self.assertTrue(allowed_output_link(
            "https://github.com/occult-kranti/ANDOLAN/blob/game/yuga-native-production/README.md",
            self.base))

    def test_rejects_lookalikes_credentials_and_unrelated_repositories(self):
        for url in (
            "https://github.com.example.org/occult-kranti/ANDOLAN/blob/main/README.md",
            "https://github.com@evil.example/occult-kranti/ANDOLAN/blob/main/README.md",
            "https://user:secret@github.com/occult-kranti/ANDOLAN/blob/main/README.md",
            "https://github.com/another/ANDOLAN/blob/main/README.md",
            "https://github.com/occult-kranti/ANDOLAN/blob/../../elsewhere",
            "https://github.com/occult-kranti/ANDOLAN/blob/%2e%2e/elsewhere",
            "https://github.com/occult-kranti/ANDOLAN/blob/main/README.md?token=secret",
            "http://github.com/occult-kranti/ANDOLAN/blob/main/README.md",
            "javascript:alert(1)",
        ):
            with self.subTest(url=url):
                self.assertFalse(allowed_output_link(url, self.base))

    def test_loopback_audit_keeps_exact_origin(self):
        base = "http://127.0.0.1:8765/production/"
        self.assertTrue(allowed_output_link(base + "media/test.png", base))
        self.assertFalse(allowed_output_link("http://127.0.0.1:8766/media/test.png", base))
        self.assertFalse(allowed_output_link("http://user@127.0.0.1:8765/test.png", base))


if __name__ == "__main__":
    unittest.main()
