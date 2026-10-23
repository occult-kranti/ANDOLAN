import copy
import http.client
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock
import urllib.error
import urllib.request

import local_swarm


ROOT = Path(__file__).resolve().parent


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT / "plan.example.json").read_text())

    def assertInvalid(self, plan):
        result = local_swarm.validate_plan(plan)
        self.assertEqual(result["status"], "INVALID", result)
        self.assertFalse(result["runnable"])
        return result

    def test_example_is_valid_but_unresolved_and_not_runnable(self):
        result = local_swarm.validate_plan(self.plan)
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertFalse(result["runnable"])
        self.assertFalse(result["runtime_qualified"])
        self.assertEqual(result["unresolved"], ["route local: model_id is null"])

    def test_local_binding_does_not_imply_runtime_qualification(self):
        self.plan["routing"]["routes"]["local"]["model_id"] = "local-model-test-only"
        result = local_swarm.validate_plan(self.plan)
        self.assertEqual(result["status"], "CONFIGURED")
        self.assertTrue(result["runnable"])
        self.assertFalse(result["runtime_qualified"])

    def test_exact_ids_roles_and_worker_count(self):
        for changed in ("duplicate_id", "wrong_id", "duplicate_role", "extra", "missing"):
            with self.subTest(changed=changed):
                plan = copy.deepcopy(self.plan)
                if changed == "duplicate_id":
                    plan["workers"][1]["id"] = "W1"
                elif changed == "wrong_id":
                    plan["workers"][1]["id"] = "W7"
                elif changed == "duplicate_role":
                    plan["workers"][1]["role"] = "QA"
                elif changed == "extra":
                    plan["workers"].append(copy.deepcopy(plan["workers"][0]))
                else:
                    plan["workers"].pop()
                self.assertInvalid(plan)

    def test_rejects_traversal_absolute_and_glob_paths(self):
        invalid = ["../ui", "ui/../hero", "/ui", "ui/", "ui//child", "./ui", "ui/.",
                   "C:/ui", "ui\\child", "ui/*", "ui/?", "ui/[ab]", "ui/{a,b}",
                   "~/ui", "", " ui", "ui\nchild", "ui\x00child", 1, None, ["ui"]]
        for path in invalid:
            with self.subTest(path=repr(path)):
                plan = copy.deepcopy(self.plan)
                plan["workers"][1]["paths"] = [path]
                self.assertInvalid(plan)

    def test_rejects_ancestors_duplicates_and_same_worker_overlap(self):
        for first, second in [("hero", "hero/model"), ("hero/model", "hero"), ("hero", "hero")]:
            with self.subTest(first=first, second=second):
                plan = copy.deepcopy(self.plan)
                plan["workers"][1]["paths"] = [first]
                plan["workers"][2]["paths"] = [second]
                self.assertInvalid(plan)
        self.plan["workers"][1]["paths"] = ["ui", "ui/components"]
        self.assertInvalid(self.plan)

    def test_shared_string_prefix_is_not_path_overlap(self):
        self.plan["workers"][1]["paths"] = ["hero-ui"]
        self.assertTrue(local_swarm.validate_plan(self.plan)["valid"])

    def test_gpu_parallelism_is_exactly_integer_one(self):
        for count in (2, 0, True, 1.0, "1", None):
            with self.subTest(count=count):
                plan = copy.deepcopy(self.plan)
                plan["gpu_parallelism"] = count
                self.assertInvalid(plan)

    def test_cloud_requires_explicit_worker_route_and_binding(self):
        routes = self.plan["routing"]["routes"]
        routes["local"]["model_id"] = "local-test"
        self.plan["workers"][0]["route"] = "cloud"
        result = local_swarm.validate_plan(self.plan)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("route cloud: endpoint is null", result["unresolved"])
        routes["cloud"] = {"endpoint": "https://example.invalid/v1", "model_id": "cloud-test"}
        self.assertEqual(local_swarm.validate_plan(self.plan)["status"], "CONFIGURED")
        del self.plan["workers"][0]["route"]
        self.assertInvalid(self.plan)

    def test_no_cloud_default_or_fallback(self):
        for key, value in [("default", "cloud"), ("fallback", "cloud"), ("fallback", "local")]:
            with self.subTest(key=key, value=value):
                plan = copy.deepcopy(self.plan)
                plan["routing"][key] = value
                self.assertInvalid(plan)

    def test_endpoint_restrictions_and_malformed_shapes(self):
        for endpoint in ([], {}, "http://remote.example/v1", "http://127.0.0.1:11434/v1?x=y"):
            with self.subTest(endpoint=endpoint):
                plan = copy.deepcopy(self.plan)
                plan["routing"]["routes"]["local"]["endpoint"] = endpoint
                self.assertInvalid(plan)
        for endpoint in ("http://example.invalid/v1", "https://user:secret@example.invalid/v1",
                         "https://example.invalid/v1?token=test", "https://example.invalid/v1#x"):
            with self.subTest(endpoint=endpoint):
                plan = copy.deepcopy(self.plan)
                plan["routing"]["routes"]["cloud"]["endpoint"] = endpoint
                self.assertInvalid(plan)
        for value in ([], None, "bad", {"workers": [None]}):
            with self.subTest(value=value):
                self.assertInvalid(value)

    def test_cli_unresolved_exit_is_distinct_from_invalid(self):
        result = subprocess.run([sys.executable, str(ROOT / "local_swarm.py"), "validate",
                                 str(ROOT / "plan.example.json")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "UNRESOLVED")
        result = subprocess.run([sys.executable, str(ROOT / "local_swarm.py"), "validate",
                                 str(ROOT / "missing-plan.json")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "INVALID")


class ProbeTests(unittest.TestCase):
    url = "http://127.0.0.1:11434/v1/models"

    def response(self, body, status=200):
        response = mock.MagicMock()
        response.status = status
        response.read.side_effect = lambda limit: body[:limit]
        response.__enter__.return_value = response
        return response

    def call_with_response(self, body, **kwargs):
        response = self.response(body)
        with mock.patch.object(urllib.request, "build_opener") as build:
            build.return_value.open.return_value = response
            result = local_swarm.probe_models(self.url, **kwargs)
        return result, response, build

    def test_fixed_get_no_proxy_credentials_or_generation(self):
        result, response, build = self.call_with_response(b'{"data":[{"id":"local-test"}]}')
        self.assertEqual(result["models"], ["local-test"])
        self.assertFalse(result["generation_performed"])
        handlers = build.call_args.args
        proxy = next(handler for handler in handlers if isinstance(handler, urllib.request.ProxyHandler))
        self.assertEqual(proxy.proxies, {})
        self.assertTrue(any(isinstance(handler, local_swarm.NoRedirect) for handler in handlers))
        request = build.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, self.url)
        self.assertEqual(request.get_method(), "GET")
        self.assertIsNone(request.data)
        self.assertIsNone(request.get_header("Authorization"))
        self.assertEqual(build.return_value.open.call_args.kwargs["timeout"], 3.0)
        response.read.assert_called_once_with(local_swarm.MAX_RESPONSE_BYTES + 1)

    def test_invalid_urls_never_open(self):
        urls = ["https://127.0.0.1:11434/v1/models", "http://127.0.0.2:11434/v1/models",
                "http://127.1:11434/v1/models", "http://[::1]:11434/v1/models",
                "http://localhost:11435/v1/models", "http://localhost:11434/v1/chat/completions",
                "http://localhost:11434/v1/models/", self.url + "?x=y", self.url + "#x",
                "http://user:pass@localhost:11434/v1/models", "http://example.invalid/v1/models",
                "http://localhost.example.invalid:11434/v1/models", "http://LOCALHOST:11434/v1/models"]
        with mock.patch.object(urllib.request, "build_opener") as build:
            for url in urls:
                with self.subTest(url=url), self.assertRaises(ValueError):
                    local_swarm.probe_models(url)
            build.assert_not_called()

    def test_localhost_uses_literal_loopback_without_dns(self):
        with mock.patch.object(urllib.request, "build_opener") as build:
            build.return_value.open.return_value = self.response(b'{"data":[]}')
            result = local_swarm.probe_models("http://localhost:11434/v1/models")
            request = build.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, self.url)
            self.assertEqual(result["request_url"], self.url)

    def test_redirect_handler_blocks_all_redirect_codes(self):
        handler = local_swarm.NoRedirect()
        request = urllib.request.Request(self.url)
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code):
                self.assertIsNone(handler.redirect_request(request, None, code, "redirect", {},
                                                          "https://example.invalid/"))
        error = urllib.error.HTTPError(self.url, 302, "redirect", {}, BytesIO(b"unused"))
        with mock.patch.object(urllib.request, "build_opener") as build:
            build.return_value.open.side_effect = error
            result = local_swarm.probe_models(self.url)
            self.assertEqual(result["status"], "ERROR")
            self.assertIn("302", result["error"])
            build.return_value.open.assert_called_once()

    def test_network_http_and_timeout_errors(self):
        errors = [urllib.error.URLError("refused"), TimeoutError("timeout"),
                  urllib.error.HTTPError(self.url, 500, "failed", {}, BytesIO()),
                  http.client.RemoteDisconnected("peer closed"),
                  http.client.IncompleteRead(b"partial", 20)]
        for error in errors:
            with self.subTest(error=type(error).__name__), mock.patch.object(urllib.request, "build_opener") as build:
                build.return_value.open.side_effect = error
                self.assertEqual(local_swarm.probe_models(self.url)["status"], "ERROR")

    def test_bounded_response_and_json_schema(self):
        result, response, _ = self.call_with_response(b"x" * 20, max_bytes=10)
        self.assertEqual(result["status"], "ERROR")
        response.read.assert_called_once_with(11)
        for body in (b"not json", b"\xff", b"[]", b'{}', b'{"data":[{}]}', b'{"data":[{"id":null}]}'):
            with self.subTest(body=body):
                result, _, _ = self.call_with_response(body)
                self.assertEqual(result["status"], "ERROR")
        result, _, _ = self.call_with_response(b'{"data":[]}')
        self.assertEqual(result["status"], "NO_MODELS")

    def test_limits_are_bounded_and_finite(self):
        with mock.patch.object(urllib.request, "build_opener") as build:
            for timeout in (0, -1, 11, float("inf"), float("nan"), True):
                with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                    local_swarm.probe_models(self.url, timeout=timeout)
            for max_bytes in (0, -1, local_swarm.MAX_RESPONSE_BYTES + 1, True):
                with self.subTest(max_bytes=max_bytes), self.assertRaises(ValueError):
                    local_swarm.probe_models(self.url, max_bytes=max_bytes)
            build.assert_not_called()


if __name__ == "__main__":
    unittest.main()
