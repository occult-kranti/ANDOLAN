#!/usr/bin/env bash
# Prepare this Ubuntu build host for YUGA desktop authoring and verification.
# Runtime dependencies stay outside the repository; no agent config is changed.
set -euo pipefail
if [[ "${1:-}" == "--help" ]]; then
  cat <<'HELP'
Usage: bash tools/cloud/setup-studio.sh [EXTERNAL_TOOL_ROOT]
Installs Ubuntu authoring/capture packages, the repository-pinned official
Godot 4.6.3 Linux/Windows engines, Blender 4.3.2, Python 3.12 wheels and Playwright
Chromium. Writes versions and download provenance outside the checkout.
Requires sudo on Ubuntu 24.04 x86_64. It does not publish or run a game.
HELP
  exit 0
fi
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
tool_root="${1:-/workspaces/tooling}"
case "$tool_root/" in "$project_root/"*) echo 'Choose a tool root outside the source checkout.' >&2; exit 2;; esac
if [[ "$(uname -m)" != x86_64 ]] || ! grep -q 'VERSION_ID="24.04"' /etc/os-release; then
  echo 'This setup is qualified for Ubuntu 24.04 x86_64; qualify another host separately.' >&2
  exit 2
fi
mkdir -p "$tool_root/studio-receipts"
cd "$project_root"
sudo apt-get update
sudo apt-get install -y --no-install-recommends blender ffmpeg xvfb mesa-vulkan-drivers vulkan-tools libvulkan1 libx11-6 libxtst6 libxi6 libxrandr2 libxinerama1 libxcursor1 libasound2t64 libgl1 libegl1 xauth ripgrep python3.12-venv
python3 games/yuga-native/tools/release-native.py install-engines --destination "$tool_root/native-engine"
sudo ln -sfn "$tool_root/native-engine/Godot_v4.6.3-stable_linux.x86_64" /usr/local/bin/godot
python3 tools/cloud/install-studio-blender.py --destination "$tool_root/blender"
sudo ln -sfn "$tool_root/blender/blender-4.3.2-linux-x64/blender" /usr/local/bin/blender4.3
/usr/bin/python3.12 -m venv "$tool_root/yuga-native-python312"
"$tool_root/yuga-native-python312/bin/python" -m pip install --disable-pip-version-check --only-binary=:all: numpy==2.3.5 scipy==1.15.3 Pillow==12.3.0
npx --no-install playwright install-deps chromium
npx --no-install playwright install chromium
dpkg-query -W blender ffmpeg xvfb mesa-vulkan-drivers vulkan-tools ripgrep python3.12-venv > "$tool_root/studio-receipts/ubuntu-packages.txt"
godot --version > "$tool_root/studio-receipts/godot-version.txt"
blender --background --factory-startup --python-expr 'import bpy; print("STUDIO_BLENDER_READY", bpy.app.version_string)' > "$tool_root/studio-receipts/blender-startup.log" 2>&1
vulkaninfo --summary > "$tool_root/studio-receipts/vulkan-summary.txt" 2>&1
printf 'Tools prepared. Receipts: %s/studio-receipts\n' "$tool_root"
printf 'Import: godot --headless --path games/yuga-native --editor --import --quit\n'
