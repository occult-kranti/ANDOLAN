#!/usr/bin/env bash
# Run the source game or separate original map-design prototype.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
engine="${GODOT_BIN:-godot}"
map_study=false
district=false
args=(--path "$project_root/games/yuga-native")
for option in "$@"; do
  case "$option" in
    --map) map_study=true ;;
    --district) district=true ;;
    --compatibility) args+=(--rendering-method gl_compatibility) ;;
    --help)
      printf '%s\n' 'Usage: bash tools/studio/launch-native.sh [--district | --map] [--compatibility]' \
        'Default: native YUGA practice. --map: separate Blender map-study scene.' \
        '--district: enter the integrated Sangam/Confluence world directly.' \
        'Requires Godot 4.6.3; GODOT_BIN can select an installed executable.'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$option" >&2; exit 2 ;;
  esac
done
if ! command -v "$engine" >/dev/null 2>&1; then
  printf '%s\n' 'Godot missing. See docs/research/STUDIO_TOOLCHAIN.md.' >&2
  exit 1
fi
if "$map_study" && "$district"; then printf '%s\n' 'Choose --district or --map.' >&2; exit 2; fi
if "$map_study"; then args+=(res://scenes/studio_map_study.tscn); fi
if "$district"; then args+=(res://scenes/confluence_world.tscn); fi
exec "$engine" "${args[@]}"
