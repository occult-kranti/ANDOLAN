#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$project_root"
node -e 'const [major,minor]=process.versions.node.split(".").map(Number);if(major<22||(major===22&&minor<12))throw new Error("YUGA requires Node22.12 or newer")'
engine_version="$(godot --version)"
case "$engine_version" in
  4.6.3.stable.*) ;;
  *) echo 'The prepared native environment requires Godot4.6.3 standard.' >&2; exit 1 ;;
esac
npm ci
godot --headless --path games/yuga-native --editor --import --quit
python3 games/yuga-native/tools/check-roadmap.py
python3 games/yuga-native/art/validate_courtyard.py
python3 games/yuga-native/art/production/validate_rama.py
npm run yuga:typecheck
npm run yuga:test
validation_dir="$(mktemp -d /tmp/yuga-native-setup-XXXXXX)"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/native_acceptance.gd -- --report="$validation_dir/native-acceptance.json"
godot --headless --path games/yuga-native --script res://tests/projectile_cases.gd -- --report="$validation_dir/projectile-cases.json"
python3 games/yuga-native/tools/setup-render-runtime.py
printf 'Native setup checks complete. Reports: %s\n' "$validation_dir"
