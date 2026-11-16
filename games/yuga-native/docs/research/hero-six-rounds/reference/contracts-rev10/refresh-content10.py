#!/usr/bin/env python3
"""Refresh only the two original Sangam pins; retain frozen revision9 authority."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[7]
NATIVE = ROOT / "games/yuga-native"
old = json.loads((NATIVE / "tests/fixtures/contracts/native-content9-catalog.json").read_text())
path = NATIVE / "assets/contracts/native-contracts-v1.json"
data = json.loads(path.read_text())
base = old["profiles"][1]
profile = data["profiles"][1]
assert all(data["profiles"][i] == old["profiles"][i] for i in (0, 2))
assert all(profile[key] == value for key, value in base.items() if key not in ("content_revision", "content_sources", "content_sha256"))
assert all(profile["content_sources"].get(key) == sha for key, sha in base["content_sources"].items())
added = ("scripts/sangam_district.gd", "assets/world/sangam-district.json")
assert set(profile["content_sources"]) <= set(base["content_sources"]) | {"games/yuga-native/" + x for x in added}
profile["content_revision"] = 10
for relative in added:
 profile["content_sources"]["games/yuga-native/" + relative] = hashlib.sha256((NATIVE / relative).read_bytes()).hexdigest()
profile["content_sha256"] = hashlib.sha256(json.dumps(profile["content_sources"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
path.write_text(json.dumps(data, indent=2) + "\n")
print(json.dumps({"content_revision":10,"content_sha256":profile["content_sha256"],"new_sources":{x:profile["content_sources"][x] for x in profile["content_sources"] if x not in base["content_sources"]}}, indent=2))
