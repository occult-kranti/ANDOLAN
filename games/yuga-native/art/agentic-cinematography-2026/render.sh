#!/usr/bin/env bash
# Render the original placeholder previs, without contacting a video service.
set -eu
if [ "$#" -ne 3 ] || { [ "$3" != stills ] && [ "$3" != video ]; }; then
  printf 'Usage: %s /path/to/prepared-checkout /path/to/output stills|video\n' "$0" >&2
  exit 2
fi
checkout=$(CDPATH= cd -- "$1" && pwd)
mkdir -p "$2"
out=$(CDPATH= cd -- "$2" && pwd)
cd "$checkout/engine/cinematic"
export CAMERA_CONTROL_OUT="$out"
if [ "$3" = stills ]; then
  node render.mjs --id YUGA01-MountainPulse --stills 0,2,3.9 \
    --scale 0.25 --boxes --clean --no-blur
else
  node render.mjs --videos YUGA01-MountainPulse --boxes --clean --no-blur \
    --scale 0.25 --concurrency 2 --out "$out/video"
fi
