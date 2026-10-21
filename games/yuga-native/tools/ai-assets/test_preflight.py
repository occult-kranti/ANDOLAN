import contextlib
import io
import unittest
from unittest.mock import patch

import preflight


class CapacitySafetyTests(unittest.TestCase):
    def observation(self, devices=(), free_disk=100 * preflight.GIB, gpu_status="observed"):
        return {"disk": {"status": "observed", "free_bytes": free_disk},
                "gpu": {"status": gpu_status, "devices": list(devices)}}

    def requirements(self, vram=24, disk=40, reserve=1, execution="cuda"):
        return {"execution": execution, "vram_bytes": vram * preflight.GIB,
                "new_disk_bytes": disk * preflight.GIB,
                "reserve_disk_bytes": reserve * preflight.GIB}

    def test_no_gpu_is_not_cuda_ready(self):
        result = preflight.assess(self.observation(gpu_status="unavailable"), self.requirements())
        self.assertFalse(result["ready"])
        self.assertIn("nvidia_capacity_unavailable_or_unknown", result["failures"])

    def test_free_not_total_memory_determines_capacity(self):
        devices = preflight.parse_gpus("0, 32768, 15360, GPU A\n1, 32768, 28672, GPU B\n")
        result = preflight.assess(self.observation(devices), self.requirements())
        self.assertTrue(result["ready"])
        self.assertEqual(result["selected_gpu_index"], 1)

    def test_multiple_cards_do_not_implicitly_pool_vram(self):
        devices = preflight.parse_gpus("0, 16384, 16384, GPU A\n1, 16384, 16384, GPU B\n")
        result = preflight.assess(self.observation(devices), self.requirements())
        self.assertFalse(result["ready"])
        self.assertIsNone(result["selected_gpu_index"])

    def test_disk_reserve_cannot_be_spent_on_download(self):
        result = preflight.assess(self.observation(free_disk=40 * preflight.GIB),
                                 self.requirements(execution="cpu"))
        self.assertFalse(result["ready"])
        self.assertEqual(result["failures"], ["insufficient_free_disk_including_reserve"])

    def test_cpu_mode_is_explicit_and_has_no_cuda_selection(self):
        result = preflight.assess(self.observation(gpu_status="unknown"),
                                 self.requirements(execution="cpu"))
        self.assertTrue(result["ready"])
        self.assertIsNone(result["selected_gpu_index"])
        self.assertIn("model_inference", result["not_verified"])

    def test_unknown_disk_never_passes(self):
        observed = self.observation(gpu_status="unavailable")
        observed["disk"] = {"status": "unknown"}
        self.assertFalse(preflight.assess(observed, self.requirements(execution="cpu"))["ready"])

    def test_partial_or_invalid_gpu_inventory_fails_closed(self):
        invalid = ["", "0, 32768, N/A, GPU", "0, 32768, nan, GPU", "0, 1, 2, GPU",
                   "0, 0, 0, GPU", "0, 16, 16, GPU\n0, 16, 16, GPU",
                   "0, 32768, 32000, GPU\nmalformed"]
        for sample in invalid:
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                preflight.parse_gpus(sample)

    def test_probe_error_cannot_become_empty_success(self):
        with patch("preflight.shutil.which", return_value="/test/nvidia-smi"), \
             patch("preflight.subprocess.run", side_effect=OSError("query failed")):
            self.assertEqual(preflight.probe_gpus()["status"], "unknown")

    def test_invalid_numeric_requirements_and_implicit_mode_are_rejected(self):
        for flag in ["--required-vram-gib", "--required-free-disk-gib", "--reserve-disk-gib"]:
            for value in ["nan", "inf", "-inf", "0", "-1", "junk", "1e308"]:
                args = ["--required-vram-gib", "6", "--required-free-disk-gib", "20", flag, value]
                with self.subTest(flag=flag, value=value), contextlib.redirect_stderr(io.StringIO()), \
                     self.assertRaises(SystemExit):
                    preflight.parser().parse_args(args)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            preflight.parser().parse_args(["--required-free-disk-gib", "20"])


if __name__ == "__main__":
    unittest.main()
