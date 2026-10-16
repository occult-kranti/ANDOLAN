# Portable native packages

`tools/package-native.py` exports the project to a Godot PCK and bundles it with the official Godot 4.6.3 engine. This is a portable native executable package: users extract the entire ZIP and run its launcher. It does not require an editor installation. The full engine is larger than a template-based release export.

The production renderer is Forward+; `--rendering-method gl_compatibility` is the deliberate lower-feature fallback. The fallback omits glow and SSAO. Native desktop libraries and graphics drivers remain operating-system requirements.

## Build

Import final assets before packaging. Use task-local XDG directories in managed cloud sessions:

```sh
export XDG_DATA_HOME=/workspace/tooling/native-render/xdg/data
export XDG_CONFIG_HOME=/workspace/tooling/native-render/xdg/config
export XDG_CACHE_HOME=/workspace/tooling/native-render/xdg/cache
godot --headless --path games/yuga-native --editor --import --quit
python3 games/yuga-native/tools/package-native.py
```

Defaults expect Linux Godot at `/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64` and Windows Godot at `/workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe`. Override using `--linux-engine` and `--windows-engine`. Windows download provenance must accompany that executable as `godot-windows-provenance.json`; its recorded SHA-256 is checked before packaging.

To separate export from archive assembly:

```sh
python3 games/yuga-native/tools/package-native.py --export-only
python3 games/yuga-native/tools/package-native.py --package-only
```

The second command rejects changed runtime source files or changed PCKs. The following package notices must exist before archive assembly: `NOTICE/GODOT-LICENSE.txt`, `NOTICE/GODOT-COPYRIGHT.txt`, `NOTICE/MAKEHUMAN-ASSET-LICENSE.md`, and `NOTICE/HERO-PROVENANCE.json`.

Outputs are under ignored `games/yuga-native/build/`: two PCKs, their exported-directory manifest, Linux and Windows staging folders, two ZIPs, export logs and the aggregate package manifest. The package contains a `PACKAGE-MANIFEST.json` with source and payload hashes. The aggregate manifest records ZIP hashes outside each ZIP, avoiding a circular self-hash.

## Verification boundaries

The tool verifies the PCK magic/version, every packed entry's bounds and stored MD5, SHA-256 of every payload, expected hero/environment resources, runtime-only resource paths, absence of known credential markers, the source Rama model hash, every ZIP entry and every ZIP CRC. It records the Git base, dirty native-tree status and exact runtime source hashes, so a package made from uncommitted work is not mislabeled as the base commit.

PCK parsing follows the official Godot 4.6 `PackedSourcePCK::try_open_pack` layout in `core/io/file_access_pack.cpp`. MD5 verifies Godot's existing pack-integrity field; independent SHA-256 hashes are also retained.

Packaging does not establish gameplay, graphics, frame rate or platform compatibility. Linux packages need a separate extracted-package startup, rendering and input check. Windows packages are marked **packaged and archive-validated; not executed on Windows** until tested on that platform. Headless tests use the dummy renderer and are not screenshot evidence.

## Launch

Linux:

```sh
./launch.sh
./launch.sh --rendering-method gl_compatibility
```

Windows: run `launch.bat`, or `launch.bat --rendering-method gl_compatibility` from Command Prompt. Keep the PCK next to the bundled engine. The launchers resolve paths relative to their own location and forward user arguments.
