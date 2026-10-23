# Reuse the qualified public Godot runtime

Restored the already qualified Linux runtime from [the 18 October public release](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-desktop-polish-2026-10-18), then executed **one current-source headless fixture: 41/41 checks passed**, exit 0 in 0.281 seconds. This establishes bounded `--path` / `--script` compatibility, not current graphical startup or rendering quality.

Executable: `/workspace/scratch/ten-rounds-oct23/runtime-release/restored/godot`, 85,447,128 bytes, mode 0755, SHA-256 **`e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e`**. It is Godot `4.6.3.stable.custom_build`, `template_debug`, `pipeline-low-priority-v1`; the archived source build records `disable_path_overrides=no`.

[Restoration receipt](restoration-receipt.json) binds the ordinary `gh release download` command, the 4.74-second / 97,919,893-byte download, all three asset hashes, static ELF identity and fifteen selectively extracted executable/license/provenance members. The Linux ZIP matches its public SHA256SUMS, downloaded native package manifest, internal package manifest, [versioned independent public audit](../../../evidence/desktop-finish/continuation-oct18/W3-public-audit-r1/receipt.json) and [publication receipt](../../../evidence/desktop-finish/published/release-polish-r1/publication-receipt.json). All 46 archive paths were inspected as safe regular files. No PCK was extracted. No token was read or copied.

[Current-source compatibility receipt](current-source-compatibility-receipt.json) records the 30-second bound, actual command, unchanged executable and before/after hashes of the project config, fixture, builder, shader, direct resource helper and map. [The complete 41-case report](current-source-headless.json) and [raw log](current-source-headless.log) are retained. Script-reported builder/map hashes match the external pins.

```sh
/workspace/scratch/ten-rounds-oct23/runtime-release/restored/godot --headless --path /workspace/ANDOLAN/games/yuga-native --script res://tools/wind-court-pilot/test_pilot.gd -- --report=/workspace/scratch/ten-rounds-oct23/runtime-release/current-source-headless.json
```

That was the single executed test command; its output is preserved rather than rerun. Future runs need fresh output filenames and source pins. The restoration scripts, full archive inventory and selected original Godot notices/provenance remain alongside the executable in scratch. If scratch is lost, download the three exact named assets again through normal GitHub release transport and verify against these retained pins before extracting or executing anything.

No project source or art was changed by this work. No editor import or renderer was requested. This run does not validate graphical compilation, materials, input/game feel, whole-world physics, hardware FPS, current-source packaging or a new public release. The priority patch changes pipeline task priority; it is not evidence of a universal cold-start fix.
