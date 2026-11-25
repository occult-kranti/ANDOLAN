#!/usr/bin/env bash
# Prepare the independently published Sirio camera pipeline in a new directory.
set -eu

if [ "$#" -ne 1 ]; then
  printf 'Usage: %s /path/to/new-checkout\n' "$0" >&2
  exit 2
fi
packet=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
destination=$1
revision=602aa2348b0ae67589ce533fff571adced724811

if [ -e "$destination" ]; then
  printf 'Refusing to overwrite existing path: %s\n' "$destination" >&2
  exit 1
fi
git clone --filter=blob:none --sparse --depth 1 \
  https://github.com/sirioberati/ai-filmmaking-camera-control-seedance-2-5.git "$destination"
git -C "$destination" fetch --depth 1 origin "$revision"
git -C "$destination" checkout --detach "$revision"
git -C "$destination" sparse-checkout set engine/cinematic
git -C "$destination" apply --unidiff-zero --check "$packet/compatibility.patch"
git -C "$destination" apply --unidiff-zero "$packet/compatibility.patch"
cp "$packet/yuga-mountain.ts" "$destination/engine/cinematic/src/templates/yuga-mountain.ts"
cp "$packet/package-lock.json" "$destination/engine/cinematic/package-lock.json"
(
  cd "$destination/engine/cinematic"
  npm ci --ignore-scripts --no-audit --no-fund
  npm run check
)
printf 'Prepared %s at %s\n' "$destination" "$revision"
