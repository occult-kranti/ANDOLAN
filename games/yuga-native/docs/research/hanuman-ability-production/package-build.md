# Build and play the portable Hanuman Trial

Extract the entire platform ZIP and open its `yuga-native-<platform>-x86_64` folder. On Linux run `./launch.sh`. On Windows open `launch.bat`. Choose **Hanuman → Begin Hanuman Trial → Begin practice**. Move with WASD or arrows and aim with the mouse. The default ability controls are LMB for Vajra Gada, Q for Vajra Kavacha, E for Maruti Udayana, C for Lanka Dahan and X for Mountain Pulse. Escape pauses, and F5 resets practice. [Playable kit and timing](../../HANUMAN_GAME_DESIGN.md)

The ZIP keeps the launcher, an x86_64 Godot runtime and its PCK together. Forward+ needs a Vulkan-capable driver. If Vulkan fails to start, append `--rendering-method gl_compatibility` to the launcher command. If a Linux extraction utility drops execute permissions, run `chmod +x launch.sh godot`. Use an ordinary desktop session. Notices and exact release payload hashes ship inside each archive.

Run `sha256sum -c package-SHA256SUMS.txt` with both downloaded ZIPs and the checksum file in the same directory. Both packages include the same 628-entry PCK and a Vajra Kavacha impact frame from the native trial, composed with the ability preview camera. [Exact ZIP checksums](package-SHA256SUMS.txt)

The extracted Linux package opened the normal title, entered Hanuman’s court, loaded all five revised clips, and ran every ability through X11 keyboard and mouse events before returning to title and exiting normally. The full routes passed under both Forward+ and Compatibility software rendering. The five impact or movement records matched exactly across the two runs. The Windows ZIP passed archive, executable format, and PCK inspection. Windows gameplay execution remains open. [Package receipt](package-verification.json) · [Forward+ Mountain Pulse from the extracted Linux package](package-linux-mountain.png)

## Rebuild from the reviewed source

Use a frozen checkout and a fresh working directory. The official Godot 4.6.3 Linux engine exports both presets. The Linux package uses the verified `pipeline-low-priority` runtime whose patch, binary identity and licensing are pinned by the existing packager. The Windows package uses the official Windows executable. [Build handbook](../../BUILD_HANDBOOK.md#8-package-and-release) · [Existing export presets](../../../export_presets.cfg) · [Engine acquisition](../../../tools/release-native.py)

```sh
native=games/yuga-native
build_root=/absolute/new/hanuman-package
engine_dir=/absolute/verified/godot-4.6.3-engines
linux_runtime=/absolute/verified/patched-linux/godot

python3 "$native/tools/release-native.py" install-engines --destination "$engine_dir"
"$engine_dir/Godot_v4.6.3-stable_linux.x86_64" --headless --path "$native" --editor --import --quit
python3 "$native/tools/package-native.py" \
  --linux-engine "$engine_dir/Godot_v4.6.3-stable_linux.x86_64" \
  --windows-engine "$engine_dir/Godot_v4.6.3-stable_win64.exe" \
  --linux-runtime "$linux_runtime" \
  --linux-runtime-variant pipeline-low-priority \
  --linux-runtime-provenance "$native/docs/evidence/desktop-finish/G0/template-priority-build-r1/finished-build-verification.json" \
  --build-dir "$build_root" --stream-large-payloads --hanuman-trial
```

For an optional ability frame, append `--hanuman-sample /absolute/path/to/the-reviewed-frame.png`. Exporting with `--export-only` and subsequently packaging with `--package-only` lets the final frame come from the same frozen runtime. Keep the source unchanged between these phases. Each platform ZIP contains a file inventory, source and runtime identities, and engine and asset notices. For Linux, qualify an extracted ZIP through the actual launcher and trial. On Windows, track native execution separately from successful PCK and archive inspection. [Hanuman provenance](../../../art/hanuman/NOTICE.md) · [Ability sound source](../../../NOTICE/HANUMAN-ABILITY-AUDIO.json)
