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
native_python_root="/workspace/tooling/yuga-native-python"
if [[ ! -x "$native_python_root/bin/python" ]]; then
  python3 -m venv "$native_python_root"
fi
"$native_python_root/bin/python" -m pip install --disable-pip-version-check numpy==2.3.5 scipy==1.15.3
python3 games/yuga-native/tools/stage-world.py --check
godot --headless --path games/yuga-native --editor --import --quit
python3 games/yuga-native/tools/check-roadmap.py
python3 games/yuga-native/art/validate_courtyard.py
python3 games/yuga-native/art/production/validate_rama.py
npm run yuga:typecheck
npm run yuga:test
validation_dir="$(mktemp -d /tmp/yuga-native-setup-XXXXXX)"
python3 games/yuga-native/tools/check-hero-codex.py --report="$validation_dir/hero-codex.json"
python3 games/yuga-native/tests/hero_codex_cases.py --report="$validation_dir/hero-codex-cases.json"
python3 games/yuga-native/tests/hero_reconstruction_cases.py --report="$validation_dir/hero-reconstruction.json"
python3 games/yuga-native/tools/check-native-contracts.py --report="$validation_dir/native-contract-pins.json"
godot --headless --path games/yuga-native --script res://tests/native_contract_cases.gd -- --report="$validation_dir/native-contracts.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/hero_pose_cases.gd -- --report="$validation_dir/hero-pose.json"
godot --headless --path games/yuga-native --script res://tests/world_presentation_cases.gd -- --report="$validation_dir/world-presentation.json"
python3 games/yuga-native/tests/world_map_cases.py --report="$validation_dir/world-map-cases.json"
python3 games/yuga-native/tests/world_plan_cases.py --report="$validation_dir/world-plan-cases.json"
python3 games/yuga-native/tests/combat_script_cases.py --report="$validation_dir/combat-script-cases.json"
python3 -S games/yuga-native/tools/cinematics/build-duel-audio.py --check
python3 -S games/yuga-native/tools/cinematics/build-duel-audio.py --check-fixtures
python3 games/yuga-native/tools/cinematics/stage-duel-notice.py --check
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/combat_film_cases.gd -- --report="$validation_dir/combat-film-cases.json"
godot --headless --path games/yuga-native --script res://tests/combat_film_audio_cases.gd -- --report="$validation_dir/combat-film-audio-cases.json"
godot --headless --path games/yuga-native --script res://tests/combat_motion_continuity.gd -- --report="$validation_dir/combat-motion-continuity.json"
godot --headless --path games/yuga-native --script res://tests/duel_effects_cases.gd -- --report="$validation_dir/duel-effects-cases.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/world_scene_cases.gd -- --report="$validation_dir/world-scene-cases.json"
godot --headless --path games/yuga-native --script res://tests/world_lighting_cases.gd -- --report="$validation_dir/world-lighting-cases.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/world_flow_cases.gd -- --report="$validation_dir/world-flow-cases.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/native_acceptance.gd -- --report="$validation_dir/native-acceptance.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/rama_ability_cases.gd -- --report="$validation_dir/rama-ability.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/rama_motion_cases.gd -- --asset=res://assets/heroes/rama-hero.glb --report="$validation_dir/rama-motion.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/rama_screen_cases.gd -- --report="$validation_dir/rama-screen.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/rama_hero_integration_cases.gd -- --report="$validation_dir/rama-integration.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/rama_practice_cases.gd -- --report="$validation_dir/rama-practice.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/rama_hud_layout_cases.gd -- --report="$validation_dir/rama-hud-layout.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/rama_hud_expiry_cases.gd -- --report="$validation_dir/rama-hud-expiry.json"
python3 games/yuga-native/tests/rama_package_cases.py --report="$validation_dir/rama-package.json"
godot --headless --path games/yuga-native --script res://tests/projectile_cases.gd -- --report="$validation_dir/projectile-cases.json"
"$native_python_root/bin/python" games/yuga-native/tools/audio/build-traversal-audio.py --check
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/traversal_cases.gd -- --report="$validation_dir/traversal.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/traversal_pose_cases.gd -- --report="$validation_dir/traversal-pose.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/lane_army_cases.gd -- --report="$validation_dir/army.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/input_binding_cases.gd -- --report="$validation_dir/controls.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/traversal_audio_cases.gd -- --report="$validation_dir/traversal-audio.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/traversal_army_stress.gd -- --report="$validation_dir/stress.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/siege_army_cases.gd -- --report="$validation_dir/siege-army.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/lane_vehicle_art_cases.gd -- --report="$validation_dir/vehicle-art.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/siege_effects_cases.gd -- --report="$validation_dir/siege-effects.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/siege_ui_cases.gd -- --report="$validation_dir/siege-ui.json"
python3 games/yuga-native/tests/release_siege_cases.py --report="$validation_dir/siege-release-gates.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/siege_pose_cases.gd -- --report="$validation_dir/siege-pose.json"
python3 games/yuga-native/tools/audio/build-siege-audio.py --check --report="$validation_dir/siege-audio.json"
python3 games/yuga-native/tests/traversal_security_cases.py --report="$validation_dir/security.json"
python3 games/yuga-native/tests/release_traversal_cases.py --report="$validation_dir/release-gates.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tools/test-relay-control.gd -- --report="$validation_dir/relay-control.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tools/test-relay-art.gd -- --report="$validation_dir/relay-art.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tools/test-relay-integration.gd -- --report="$validation_dir/relay-integration.json"
python3 games/yuga-native/tests/release_triad_cases.py --report="$validation_dir/triad-release-gates.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/entity_bridge_cases.gd -- --report="$validation_dir/entity-bridge.json"
python3 games/yuga-native/tools/physics/run.py --godot godot --output "$validation_dir/physics-run"
cp "$validation_dir/physics-run/comparison.json" "$validation_dir/physics.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/ultimate_cases.gd -- --report="$validation_dir/ultimate.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/ultimate_effects_cases.gd -- --report="$validation_dir/ultimate-effects.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/invocation_ui_cases.gd -- --report="$validation_dir/invocation-ui.json"
python3 games/yuga-native/tools/audio/build-invocation-audio.py --check --report="$validation_dir/invocation-audio-build.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/invocation_audio_cases.gd -- --report="$validation_dir/invocation-audio.json"
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/mythic_integration_cases.gd -- --report="$validation_dir/mythic-integration.json"
python3 games/yuga-native/tests/release_mythic_cases.py --report="$validation_dir/mythic-release-gates.json"
python3 games/yuga-native/tools/setup-render-runtime.py
printf 'Native setup checks complete. Reports: %s\n' "$validation_dir"
