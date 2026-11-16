set -euo pipefail
tactical_out="$RUNNER_TEMP/tactical-casual"
mkdir -p "$tactical_out"
for suite in round_rules bot map ui world full_match; do
  timing_args=()
  if [ "$suite" = full_match ]; then
    timing_args=(--disable-render-loop --fixed-fps 60)
  fi
  if XDG_DATA_HOME="$tactical_out/data" XDG_CONFIG_HOME="$tactical_out/config" XDG_CACHE_HOME="$tactical_out/cache" timeout 180s Godot_v4.6.3-stable_linux.x86_64 --headless --audio-driver Dummy "${timing_args[@]}" --path games/yuga-native --script "res://tests/tactical/${suite}_cases.gd" -- --report="$tactical_out/$suite.json" > "$tactical_out/$suite.log" 2>&1; then
    cat "$tactical_out/$suite.log"
  else
    cat "$tactical_out/$suite.log"
    exit 1
  fi
  if grep -Eq '^[[:space:]]*(SCRIPT ERROR|ERROR|WARNING):' "$tactical_out/$suite.log"; then
    exit 1
  fi
done
