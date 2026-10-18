# Public Linux runtime: notice and build-record review

**The existing Godot license notices need no text changes for this exact runtime.** Both files match the public source archive byte for byte. The remaining packaging work is to identify the custom Linux runtime accurately, bind it separately from the official exporter, and verify these notices in the final ZIP. No engine was downloaded, built or executed; no shared notice or packaging code was changed.

| Verified input | Identity |
| --- | --- |
| Public source commit | `35e80b3a8822a9df9be390814b62f44c0a9c69e8` |
| Retained source archive | 66,095,747 bytes; SHA-256 `fe5b661d0e7b062201ebffc8740cb309ff96c4f1edca79cdb0ecda50ff2af8d5` |
| Retained Linux runtime | 85,447,128 bytes; SHA-256 `dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f` |
| `NOTICE/GODOT-LICENSE.txt` | 1,149 bytes; SHA-256 `b0435e3b3e4e55238f05f4b306f30524a1b2e20147810d436eaa554fa6855c80` |
| `NOTICE/GODOT-COPYRIGHT.txt` | 99,790 bytes; SHA-256 `b3330849267d56ddd3d62a513817506606c2195034411fe05859f0140bff9d8a` |

[The independent read-only check](checks.json) streamed all **13,847 archived source files**, matching every size/hash to the retained pristine inventory. It also verified the current binary and all **30 artifact pins** in the baseline-build and preparation receipts. The [completed build record](../../G0/template-baseline-r1/build-result.json) and [finished verification](../../G0/template-baseline-r1/finished-build-verification.json) remain exact and bind zero source patches to this retained binary. The recorded version is `4.6.3.stable.custom_build`, target `template_debug`, with `dev_build=no`, `debug_symbols=no`, `lto=none`, `use_sowrap=yes`, and `disable_path_overrides=no`. This verifies the retained build chain; no independent byte-reproducible rebuild is claimed.

**Do not cite the current build directory as pristine.** Its original-source census has one later change: `servers/rendering/renderer_rd/pipeline_hash_map_rd.h` replaces `p_high_priority` with `false` for `PipelineCompilation`. [The exact diff](source-tree-difference.patch) is retained. The archived original is SHA `095dc91c…03e6c5`; the current file is `c4234010…9ac831`. This does not alter the exact retained `dce0422d…` binary or its historical baseline receipt. The proposed shipping record must cite the pristine archive and baseline receipts, rather than infer zero patches from today's mutable source directory.

The [MIT notice](../../../../../NOTICE/GODOT-LICENSE.txt) expressly requires its copyright and permission notice in copies or substantial portions of the software. Retain that full text and the matching [Godot COPYRIGHT file](../../../../../NOTICE/GODOT-COPYRIGHT.txt), including its third-party attribution and license texts, alongside the shipped binary. COPYRIGHT itself describes its third-party summaries; this review compares Godot's supplied notice files and does not claim a separate per-snippet legal audit. No missing or divergent bytes were found in this scope.

W6's proposed Linux-only `GODOT-RUNTIME-PROVENANCE.json` and readable companion should record the identities above, exact build command, baseline receipt hashes, zero patches **at the recorded build**, and official exporter SHA `f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3`. Require the packaged runtime and both notice payloads to match those pins. The current package README's “bundled official” full-engine description must change for this Linux custom template. Keep Windows' separate official-runtime identity intact; the existing notice-copy function copies a common tree to both platforms, so avoid an unqualified Linux descriptor in the Windows package.

This is a bounded source/license/provenance acceptance. Exact successor packaging and native runtime qualification remain with W6/W1 and the lead; the earlier official-runtime failure and cleanup ownership holds remain separate.
