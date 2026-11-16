# Raea CPU original-asset presentation

Raea0.1.5 is installed at `/workspaces/tooling/raea-0.1.5/raea`, official Linux release digest verified. Its FSL-1.1-ALv2 renderer is used as separate internal tooling; no engine code is embedded in YUGA. The original composition imports the exact shipped SURYA GLB. This is a presentation of actual asset geometry, not Godot gameplay or a new playable engine port.

Owned tool workspace: `/workspaces/tooling/yuga-raea-studio/projects/sanctum`. This folder preserves the source composition, brief and plan. Its `assets/surya-carbine.glb` is a byte-identical input copy from the canonical native path; `compositions/media` links to `../assets` for Raea0.1.5 staticFile resolution. Preserve that relative layout when reproducing.

Run from the ANDOLAN root with a fresh output name:

```sh
python3 tools/studio/run-raea-cpu.py --engine /workspaces/tooling/raea-0.1.5/raea/bin/raea --project /workspaces/tooling/yuga-raea-studio/projects/sanctum --composition compositions/surya-v2.tsx --output out/surya-cpu-orbit-NEW.mp4
```

The wrapper selects Mesa llvmpipe via `VK_ICD_FILENAMES`, eight workerthreads and offline mode, records the loaded CPUdriver, source/output hashes, elapsed render time and process RSS. Actual72-frame6-second960×540orbit completed in13.379seconds using about1.28GiB peakRSS. This is measured renderwork, not nativegameFPS or consumerhardware performance.

[Output and exact receipts](../../../docs/tactical/finish2/raea/). The first assetpath refusal and missing `/usr/bin/time` launcher are preserved, then corrected; no failedimage is presented as delivered. The final renderer reported0errors/warnings/notes, with one OpenH264 encoding configuration warning retained in itslog. Sound is absent intentionally.
