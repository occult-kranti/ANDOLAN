# Independent interop, skills and roadmap review

Reviewed 2026-10-23: `games/yuga-native/docs/LOCAL_MODEL_SWARM.md` and all six `.agents/skills/*/SKILL.md`; compared with source artifacts in `interop/`, `runtimes/`, `videos/video-ledger.json` and exact repository documents at `eb0ecc7937ecc600b42588ca448cd87a87206422`. Read-only review; no shared draft edits or inference executed. Retrieval URLs, revision, byte counts and SHA-256 values are preserved in [pinned/sources.json](pinned/sources.json).

## Resolved finding

**RESOLVED: preserve the intermediate full 3v3 gate between P2 and P3.** The earlier central table correctly named P1–P6, but its P2 two-client slice → P3 six-hero/6v6 sequence omitted the mandatory intermediate FG06 integration gate. The source `DEADLOCK_QUALITY_TARGET.md` lines 115–120 explicitly says the existing three-hero 3v3 FG06 is intermediate before P3's FG07/FG08/FG09. `FULL_GAME_PRODUCTION_ROADMAP.md` lines 109 and 121 independently state the same order and the FG06 acceptance behavior. That omission let a reader advance from a two-client fixture directly into six-hero team production without proving a complete match.

The root has now added direct links to the quality target and full production roadmap, plus the following explicit intermediate row after P2 (verified against the revised draft):

> Intermediate FG06: complete 3v3 native slice | Rama/Hanuman/Sita, all three lanes, private rooms/bots and complete start→result→rematch flow, integrated by the same owners | Uncut rendered full match; authority agrees on outcome, tower/core progression, rewards, death/rejoin and rematch; no essential step requires developer intervention.

Source mapping for reference (no additional correction required): P0/P1 → FG01–FG03, FG05 and FG13; P2 → FG04; intermediate FG06; P3 → FG07/FG08/FG09; P4 → FG10/FG11; P5 → FG12/FG13; P6 → FG14/FG15. Keep the source wording that these mappings change neither task status nor dependencies, and that intermediate 3v3 does not replace the final 6v6 design.

## Verified boundaries and source fidelity

No substantive defect found in hardware, model-routing/MoE, protocol, permissions, source-access or licensing boundaries. The drafts distinguish 8 GB dedicated VRAM from shared system RAM; one queued inference backend from six roles; downloadable client source from hosted model weights; document/schema research from actual inference; and unread video claims from verified independent sources. Current Codex Responses, Claude Anthropic-compatible routing and modern-versus-archived Kimi configuration are represented accurately. Existing interop examples make Kimi `-p` automatic-permission behavior explicit. No successful laptop/GPU inference is implied.

- **Phase names:** P1–P6 in the central draft match `DEADLOCK_QUALITY_TARGET.md` lines 104–109. The FG mapping above preserves the authoritative backlog semantics.
- **Desktop counts:** `DESKTOP_FINISH_CAMPAIGN.json` declares 78 planned packets, 17 completed packets, 0 completed rounds. Independent counting of its 13 rounds yields 78 packets: 17 completed, 13 in progress, 48 planned; no round is complete.
- **Android counts:** `MOBILE_PRODUCTION_BACKLOG.json` declares 18 rounds / 108 implementation packets / 0 implementation completions. Independent counting confirms all 108 packets and all 18 rounds planned. Six completed research packets are a distinct field and are not counted as implementation.
- **Hunyuan lineage:** the recovered old model-study README points to official Hunyuan3D-2.1 revision `82920d643c0dc2f7bfd7255f45f62d386edfe60c`. Its historical cached primary README and LICENSE were retrieved from the recovered repository revision, and their bytes match the old source-manifest SHA-256 values. This revalidates the archived source evidence; it is not a fresh upstream Tencent retrieval. README line 81 says 10 GB shape, 21 GB texture, 29 GB combined. License includes separate territory/output conditions. Central wording is accurate and does not claim an 8 GB fit.
- **New Qwen candidate:** current runtime README claims are supported by local pinned upstream README SHA-256 `a71ec46607f81d6056336fb0a8431a26a1c7d8db6ac568a0c021c36f1ed3c92e`: Qwen3.5-4B appears at line 52; family llama.cpp text/vision support at lines 132–136; artifact-specific weight-license requirement at line 197. Exact GGUF/tool behavior/fit remain explicitly unverified. Qwen3-4B-Instruct-2507 alternative is named in its source at line 68. Neither is presented as a measured ranking.
- **Windows/WSL:** revised central guidance correctly requires reaching the actual server, keeps the first pilot's client/server in the same environment, distinguishes server-process settings from client-only variables, and labels the lock Linux/WSL-only. No cross-boundary localhost access is assumed.

## Final integration verification

**PASS against repository HEAD `eb0ecc7937ecc600b42588ca448cd87a87206422` on `game/yuga-native-production`.** The resolved guide and six skills are now integrated in the recovered checkout. [Machine-readable results](final-review.json) bind the reviewed file hashes and checks.

- All 264 local Markdown target paths across 22 authored/updated documents resolve. This includes the six skills, guide, reports, toolkit README and changed navigation/roadmap documents; copied upstream evidence documents were excluded. URL availability and fragment-anchor spelling were not retested.
- All three roadmap JSON files equal their baseline JSON after removing only the new `ai_authoring_evaluation.local_squad_support` subtree. Therefore existing tasks, statuses, dependencies, acceptance rules and completion counts are unchanged. Desktop remains 17/78 packets and 0/13 completed rounds; Android remains 0/108 across 18 planned rounds.
- All 190 source-hash references across 135 unique source/evidence files match; declared byte counts also match where present. This includes retained video failure receipts and the historical model-study evidence. All 22 runtime source entries correctly use portable basenames and retain original scratch capture paths; three recorded 404 source requests remain explicit failures.
- Both Kimi TOML templates parse and retain distinct local/cloud providers with a manual interactive default. Parsing is not a CLI compatibility test; non-interactive Kimi prompt mode still uses its documented automatic permission behavior.

No substantive finding remains open. This review verifies documentation/configuration integration, source integrity and roadmap preservation. It does not establish laptop inference, CUDA/model loading, real client compatibility, the unread video contents or physical-game performance. No game/runtime test, model call, download or new external source retrieval was performed in this final integration pass.
