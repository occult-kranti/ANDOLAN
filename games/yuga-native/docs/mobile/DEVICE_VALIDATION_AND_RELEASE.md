# Mobile device validation and release contract — M0-06

**Requirements proposal, 18 October 2026. No mobile build, physical-device test, hardware benchmark or store submission has passed in this packet.** The new direction is an elevated-camera 5v5 game with all heroes unlocked. Ten simultaneous player heroes and the eventual fourteen-hero roster are different coverage requirements. Existing native offline Confluence, browser protocol 2 3v3 and the older proposed 6v6 profile remain distinct products/contracts until explicitly migrated.

[validation-sources.json](validation-sources.json) records primary source commits, license bytes, retrieval failures and fifteen inspected local source hashes. This Linux environment has no `adb`, `xcodebuild`, `scrcpy` or Perfetto executable, and no physical device/GPU cohort is available. This packet changed documentation only. The [master roadmap](../MOBILE_PRODUCTION_ROADMAP.md) owns M1–M18; its108 planned six-worker packets and the six M0 research packets are plans, not completed implementation or a fixed parity promise.

## What can be reused, and what is missing

| Existing evidence / source | Useful scope | Mobile gap |
|---|---|---|
| [Native workflow](../../../../.github/workflows/yuga-native.yml), [setup](../../../../tools/cloud/setup-native.sh) | Locked dependencies, pinned engine, rules, strict content admission, imported resources, motion/UI contracts, package/source receipts. | Headless/software/desktop checks do not measure a phone GPU, multitouch, thermal behavior or OS lifecycle. |
| [Exports](../../export_presets.cfg), [project](../../project.godot) | Linux/Windows presets only; desktop Forward+, mobile override `gl_compatibility`,60-Hz physics. | No Android/iOS preset, signing configuration or qualified mobile renderer. Desktop S3TC/BPTC imports are not an Android ASTC/ETC2 qualification. |
| [Packager](../../tools/package-native.py), [security fixtures](../../tests/traversal_security_cases.py) | Manifest/hashes, strict PCK paths/remaps, resource presence, corruption and synthetic secret/path rejection. | Not APK/AAB/IPA signing, all SDK dependencies, runtime/network security, privacy or store review. Do not reuse desktop allowlists without a mobile-format review. |
| [Arena adapter](../../scripts/arena_client.gd), browser server/client | Protocol2 validation, bounded input sequences, reconnect identity, stale snapshot handling and server-side rules are useful seams. | Existing server admits six slots, not ten. Native adapter reconnect tokens are memory-only. OS process death therefore needs a new explicit recovery contract; it is not proven by an in-process reconnect test. |

Godot’s pinned 4.6 documentation distinguishes Mobile/Vulkan-or-Metal from Compatibility/OpenGL; moving between them can require scene/lighting changes. M1 must test both candidate Android paths on the selected GPUs, then select the actual shipping renderer(s) and feature tiers. Do not silently fall back to another renderer and keep the original acceptance label. iOS export requires macOS and Xcode; the pinned guide reports simulator export unsupported. Engine minima for a simple project are not this game’s supported-device list. The documentation’s iOS Metal baseline is iOS 16; the oldest supported game device remains an M1 measurement decision.

## M1 cohort and reproducible identity

Root’s provisional Android floor is **4 GB physical RAM**, with a 6–8 GB standard tier and an upper tier. M1 must name exact device model, SoC/GPU, driver, Android version/API, native page size, display/refresh modes and renderer. Include at least Adreno and Mali and more than one Android OS generation. Memory capacity alone does not define a GPU tier. Choose an actual oldest-supported iPhone after the Godot/export spike, plus a newer iPhone; include iPad/foldables only if the supported-device promise includes them. Record small/large landscape screens, notches, cutouts, gesture areas and both handedness layouts. A simulator/emulator is useful for flow testing but cannot qualify physical GPU, temperature, battery or touch latency.

Every evidence directory must contain:

- Git commit plus dirty-file/source hashes; engine/export-template/tool versions and hashes; imported asset/descriptors/compiled caches; renderer/driver, shader/material tier, dynamic-resolution policy and selected texture formats. Mobile hero mesh/bind/library identities are separate from desktop 164-bone contracts.
- APK/AAB or IPA SHA256/size, package/bundle ID, version/build number, signing-certificate fingerprint, ABI, min/target OS and permissions/entitlements. Retain actual installed split-APK identities/device spec, or the Xcode archive/export record and installed iOS build identity. Store signing/encryption can change distributed bytes: document that derivation and runtime content-manifest identity; do not claim byte equality to a differently signed local container.
- Server build, rules/map/content revisions, seed, all ten hero IDs, entity/effect/wave caps, input/event tape, actual camera transform/FOV or projection, resolution, HUD scale, clocks and tool configuration. Record actual live counts throughout each workload.
- Device pseudonym plus public model/OS/GPU details; ambient temperature, initial battery/thermal state, brightness, refresh rate, power mode, charging/case/network state. Keep serials, account tokens and signing keys outside public receipts.
- Raw full-size screenshots, uninterrupted video with timestamps, input/authority event log, OS trace and application log, lifecycle/crash/jetsam/ANR evidence where available, exact analysis queries, pass/fail predicates and source-before/after checks. Preserve failures and incomplete captures.

Freeze one shared capture project per candidate and retain versioned changed bytes/source receipts, as in the graphics-six workflow. Do not copy the full imported project per worker or round. A worker must stop before refreshing shared files during a capture. Any renderer, content, tool or build change creates a new run ID and states which previous gates need rerunning.

## Workload and measurement gates

The following numerical values are **initial engineering targets for M1 to accept or replace with documented measurements**, not measured results or store guarantees. Freeze them before judging a candidate.

| Gate | Proposed procedure and predicate |
|---|---|
| Sustained frame delivery | Baseline tier 30 fps: budget B=33.333ms; qualified standard/upper 60 fps: B=16.667ms. Measure actual presentation intervals and CPU/GPU work separately. Proposed p95≤1.10B, p99≤2B, intervals above 1.5B≤1%, and no unexplained combat stall above 100 ms. Report all intervals, not average FPS alone. Declare cap/refresh/dynamic resolution; never count duplicate screen frames as rendered work. |
| Thermal/battery | Three runs per required device/profile: controlled starting state, ten-minute warmup, then at least 30 continuous minutes or two full matches, whichever is longer. Include late-match crowded combat; compare early/late frame distributions and chosen quality. Unplugged baseline, brightness and ambient recorded. No cooling fan or thermal-throttle override. Record thermal status/frequency/quality changes and battery rate; pause at critical OS thermal state. Charging/high-temperature diagnostics are separate. |
| Memory/lifetime | Freeze numeric CPU/GPU memory and download/install budgets in M1 from the cohort. Ten lobby→match→results cycles after cache warmup: distinguish retained bounded shader/asset caches from monotonically growing live objects/listeners/resources. Proposed retained working-set growth≤5% after warm baseline, plus no OOM/OS kill in the required scenario. OS resident-memory changes alone do not prove a leak, and iOS has no universal safe jetsam limit. |
| Touch response | Physical two-thumb movement+aim+release, target change, cancel, attack and camera pan. Proposed local input-to-visible response p95≤100ms at 60 fps or 150 ms at 30 fps; network damage confirmation measured separately. Use a synchronized external high-speed camera for finger-to-photon measurement, or state that only event-to-render latency is known. OS injection timestamps alone exclude physical touch latency. |
| Startup/streaming | Fresh install/first shader use, warm relaunch, scene entry and first use of every hero/effect. Record click-to-interactive and shader/asset hitches separately; no missing imports, fallback boxes, black textures or invisible effects. A warm seeded capture cannot qualify cold startup. |
| Repetition/reproducibility | Same release settings, seed and workload for at least three comparable runs. Preserve individual runs and variance; no silent removal of the slowest run. Recording and GPU interception alter workload: pair review captures with unrecorded performance runs and quantify the observer overhead. |

The mandatory stress manifest uses **the worst legal ten-hero selection**, maximum legal simultaneous waves/units/summons/projectiles/areas, objectives/buildings and HUD notices at the actual elevated match camera. Those caps are defined by rules owners, not guessed by QA. Exercise overlapping casts, attack/cancel/recovery, deaths/respawns, lane convergence, camera movement, bushes/occlusion and day/night only where those are shipping rules. Retain the greatest recorded counts and explain any cap never reached. Ten repeated copies or an over-cap synthetic scene can be a separate diagnostic; it cannot replace a legal match. Each of the fourteen selectable heroes must pass solo readability and interactions, even when only ten are present in one match. Placeholder characters/effects do not close their eventual art/performance gate.

## Visual and animation rubric at the real camera

Review original device pixels at native playback speed before slow motion or crop inspection. Use two independent reviewers and retain their answers and disagreement. Fixed cameras and source-matched day/night/material ablations supplement actual play; they are labelled separately.

| Question | Observable acceptance evidence |
|---|---|
| Who and which team? | A twenty-item randomized one-second recognition set at the normal camera includes crowding, both sides and each hero. Proposed≥90% correct hero/team classification per reviewer, no systematic ally/enemy inversion. Team/target state uses silhouette/icon/outline as well as hue. No “all heroes recognizable” claim from portraits. |
| What can hurt me, and when? | Every damaging effect has readable anticipation, boundary/direction and impact timing aligned to the authoritative event. In a crowded cast tape, each reviewer identifies the relevant threat/target before impact. No reduced-effects tier may hide the only gameplay cue. Missed ambiguous threats block that effect’s acceptance. |
| Does motion stay coherent? | Continuous start/stop/turn/attack/cancel/retrigger/death/respawn/LOD transitions at native speed; record callback pose, root/support and authoritative release where available. Reject visible one-frame body snaps, skating during an advertised fixed lock, contact gaps at the play camera, bow/string/hand separation, penetration or duplicated release arrows. Numerical solver locks alone are insufficient. |
| Does the world support play? | Lane/objective/height/bush boundaries remain readable with ten heroes and legal effects; characters separate from light/shadowed backgrounds. No flickering joints, moiré, excessive particles or haze hiding a threat. No foreground object or HUD masks a mandatory cue without an intentional occlusion treatment. |
| Does the UI survive real use? | Critical health, cooldown, selected target, cast state and connection status readable at minimum supported size; notch/safe-area and thumb occlusion tested. Screenshot bounds, large text/localization, enabled/disabled/focus/pressed states and touch hit regions agree. Proposed contrast targets 4.5:1 normal text,3:1 large text/essential control boundaries; UI owner sets and tests exact size rules. |
| Does quality survive reduction? | Compare lowest/highest shipping tier at the same camera/seed. Essential silhouettes, target indicators, authoritative timing and accessibility information remain. A beautiful hero closeup or desktop render cannot compensate for an unreadable phone match. |

## Touch, interruption and online recovery matrix

Use actual fingers in addition to automation. Record touch IDs and transitions without biometric/personal data. Challenge two-finger move+aim, third-finger utility, edge drags, finger crossing/reassignment, release outside button, cancel into safe region, rapid tap/hold, palm/gesture interruption and OS navigation. Rotation policy, fold/resize policy, hand dominance, control scale/position and safe-area handling must be explicit. Releasing a finger, losing focus or resuming must never leave an attack, aim or movement input latched. Device accessibility settings must be tested, not merely drawn as toggles.

| Scenario | Required assertion |
|---|---|
| Notification, app switch, Home, lock/unlock, audio interruption | All local touches released; audio/focus/graphics resources recover without a duplicate scene/listener. Online authority continues according to server policy; opening a client menu must not pause the shared match. Offline pause has its separate contract. |
| Background 5/30/120 seconds | UI truthfully shows reconnect/resync/expired result; no stale target or queued cast fires on return. Server death/economy/cooldowns continue. Rejoin policy/timeouts are visible and tested at the exact boundary. |
| OS process death and explicit force-stop | Separate from backgrounding. Test cold relaunch and identity recovery/reauthentication. Memory-only reconnect credentials cannot survive it. No account/player duplication or result duplication; permanent expired session routes safely. |
| Wi-Fi↔cellular, captive portal, radio off/on, transport loss | Isolated lab profiles: RTT 50/100/200 ms, jitter 20 ms, loss 1%/3%, disconnect 3/10/30 seconds; retain both-direction configuration and actual measured network conditions. Restore only after current authoritative snapshot and generation. Real radio switching remains separate from a simulated network profile. |
| Reordered/duplicated commands, stale snapshot, late ack, full room | Authority admits no extra damage/economy/action from retransmission. Input generations/sequence numbers and reconnect identity are checked. Acks after cancellation or reconnect cannot resurrect prior presentation. Client prediction reconciles visibly without fabricating a successful action. |
| Ten-client match | At M6, ten independently connected **rendered** clients plus the real server exercise admission, all simultaneous inputs and shared outcome. Record the physical-device versus emulator/desktop mix; headless bot load is additional and does not replace a rendered client. Representative physical phones must render the complete crowd; ten logical connections alone do not prove ten-device rendering or touch quality. iOS online claims require an actual iOS participant. |

## Primary tooling and honest limits

All below are **researched candidates**, not installed/qualified toolchain versions. Exact commits/readmes/licenses are pinned in the source ledger; dependencies and binary artifacts need their own SBOM/hash review before use.

| Tool / primary source | Verified terms | Intended use and boundary |
|---|---|---|
| [Perfetto](https://github.com/google/perfetto/tree/26db72a4662467e74f557283d41779c89953274e) | Apache 2.0 root license | Android system traces and SQL analysis. FrameTimeline requires Android 12+; qualify the actual Godot surface/layer and trace availability first. Older devices need a validated alternative. CPU slices, GPU work, presented frames and input latency are different metrics. |
| [scrcpy](https://github.com/Genymobile/scrcpy/tree/a60891aea193d92e7e5c3942700eca63f9d19a5f) | Apache 2.0 | Device-timestamped Android review recording. Device-side encoding has overhead; mirrored/encoded frame count is not a GPU benchmark or proof of physical multitouch. |
| [bundletool](https://github.com/google/bundletool/tree/586a43a450712a1067f3d92cf7574dee68226302) | Apache 2.0 | Device specs and device-specific APK sets. Verify actual installed splits and signing separately; code transparency is not a full security audit. |
| [RenderDoc](https://github.com/baldurk/renderdoc/tree/45e91661ee457e64279ff86265abdbe214aa6be0) | MIT; third-party credits separate | Android Vulkan/OpenGL ES diagnostic frame capture requires debuggable build. Keep that build separate from release performance measurements. No iOS Metal support is claimed. |
| [Appium](https://github.com/appium/appium/tree/241d2b29aab7402621de482b4a93f5298fc09c8d) | Apache 2.0 core | OS/dialog automation; core alone automates nothing. Pin/audit Android/iOS drivers separately. A Godot canvas may lack semantic nodes; require a tested accessibility bridge and manual multitouch coverage. |
| [OWASP MASVS](https://github.com/OWASP/masvs/tree/bbe226fd17e6dab51927f392936deef31c816423) | CC BY-SA 4.0 documentation | Organize storage/auth/network/platform/privacy review. It is a requirements document, not game code or automatic certification. Preserve attribution/share-alike when adapting its text. |

Apple Xcode, Instruments/Metal diagnostics, XCTest and distribution/signing services are separate platform tooling with Apple terms; this packet does not call them open source. Their current official documentation was blocked here. Pin the installed Xcode/SDK on the Mac host, then verify the exact device trace/test workflow before scheduling iOS acceptance. Android SDK components likewise have their own terms despite open-source companion tools.

These are **future device-lab command templates**, not executed evidence. Fill the declared variables from a reviewed lab manifest and run on an authorized test device; do not publish device serials or keys:

```sh
sha256sum "$MOBILE_APK" "$MOBILE_CONTENT_MANIFEST" > "$MOBILE_RUN/artifacts.sha256"
adb -s "$MOBILE_SERIAL" shell getprop ro.build.version.sdk > "$MOBILE_RUN/android-api.txt"
adb -s "$MOBILE_SERIAL" shell dumpsys meminfo "$MOBILE_PACKAGE" > "$MOBILE_RUN/memory-start.txt"
adb -s "$MOBILE_SERIAL" exec-out screencap -p > "$MOBILE_RUN/original.png"
scrcpy --serial="$MOBILE_SERIAL" --no-playback --no-control --no-audio \
  --record="$MOBILE_RUN/review.mkv" --time-limit=90
```

The first M1 trace fixture must retain a device-verified Perfetto configuration including `android.surfaceflinger.frametimeline` where supported, selected CPU/scheduler/GPU sources and application markers, plus exact `adb perfetto`/trace-processor commands. Validate layer tokens and sample completeness before calculating percentiles. Do not substitute Android view-only `gfxinfo` averages for a Vulkan/OpenGL game’s presented frames. On iOS retain the real device run destination, Xcode archive/test invocation, trace template and device log; simulator success is separate. No ready-made mobile exporter or trace runner is claimed to exist today.

## Security, privacy, accessibility and store gates

Before external alpha, audit both client and authority against the actual threat model: TLS/certificate failure behavior, production cleartext disabled, token expiry/revocation/secure storage, reconnect identity binding, malformed/rate-limited inputs, server-side range/cooldown/currency checks, replay/duplicate events, dependency/plugin inventory, signed content/update policy and account deletion where accounts exist. Do not trust client-unlocked heroes, clocks or damage as authority. Existing PCK secret/path tests remain useful but cannot certify this list. Use isolated synthetic accounts and networks; never log production credentials.

Inventory every SDK and data flow: account/profile, diagnostics, IP/device data, matchmaking, chat/voice, crash analytics and optional purchases. Decide purpose, minimization, retention/deletion, processor/region and consent before adding SDKs. Request only required permissions; deny/withdraw them in tests. Check backups, crash logs and shared files for tokens/personal data. If chat/UGC or purchases are introduced, moderation/report/block, age-rating and purchase/restore requirements become explicit gates. All-heroes-unlocked is not a privacy or monetization exemption.

Accessibility acceptance includes scalable readable text, reduced effects/motion that preserve combat cues, independent audio channels and visual equivalents, color-independent team/status cues, adjustable control placement/size, safe areas and reachable cancel actions. Test TalkBack/VoiceOver focus and labels on noncombat menus, account/privacy/error flows and custom canvas controls where supported; record unsupported combat interaction honestly. Test localization expansion and reconnect/error announcements. Proposed 48 dp Android /44 pt iOS touch targets and WCAG contrast ratios are project design targets until validated against the current platform guidance and UI owner’s geometry; raw physical pixels are not dp/pt.

Before a store candidate, require signed Android AAB/device-specific install and a signed iOS archive/TestFlight install from the exact candidate, clean install and upgrade/save migration, native ABI/page-size compatibility, correct symbols/crash reporting, no debug/inspection capability in the shipping package, privacy manifests/data declarations/permission purpose strings, age rating, attribution/SBOM and accurate screenshots. Test asset delivery/offline launch/update interruption and last-known-good rollback where supported. Store-delivered bytes/build identity must link back to the reviewed source and qualification receipts. Publishing requires the designated release owner’s concrete candidate review; passing a local archive parser is not store approval.

**Policy access remains open:** official Android thermal/frame-pacing/accessibility/target-API/Data Safety, Apple Metal/MetricKit/accessibility/review/submission and W3C pages returned proxy403 during this research. Their URLs/errors are retained. Before M17/M18, retrieve and date the actual targetAPI/Xcode/SDK, privacy/deletion, child-safety, native-library/page-size and store submission requirements from the platform owners. No current deadline or store readiness is certified here.

## Six-worker gates and release progression

Use the master's stable six packet identities: **W1 rules/authority, W2 touch/screens, W3 hero/motion, W4 world/units, W5 rendering/build/tools, W6 independent QA/security**. Each M1–M18 round assigns exclusive files within those responsibilities. Root may redistribute workers, but the evidence obligations remain. Every packet returns exact source identity, implemented behavior, tests actually run, original pixels/input if relevant, a meaningful adversarial challenge and its observed result, open limits and next owner. A research packet may reject a hypothesis without manufacturing a failed test. A source-only or unavailable-device result can complete a research packet; it cannot close the corresponding runtime/device gate. Shared integration is frozen and reviewed after the six packets, with failed evidence retained.

| Roadmap milestone | Evidence gate owned jointly; reviewer must refuse overclaim |
|---|---|
| M1 | Named device/renderer/authority spikes, toolchain/signing feasibility, numeric budgets and one real-device trace. No selected cohort means no mobile support promise. |
| M2–M3 | Physical touch/camera slice and separately identified mobile Rama at real match scale; real support/cast/cancel motion plus cold/warm device capture. |
| M4–M6 | Frozen lane/economy/load caps, server validation, ten actual rendered client admissions and mixed physical-device crowded combat. Existing six-slot protocol is insufficient. |
| M7–M10 | Match loop/results, bots/services/rejoin, screens and map with the interruption/network/accessibility matrix; full legal workload at fixed camera. |
| M11–M13 | Hero batches2–5,6–10,11–14 each repeat asset/motion/input/effect/network/performance gates. Earlier Rama or placeholder passes never transfer automatically. |
| M14–M16 | Balance, final art and sustained performance/security at worst legal load on every required tier; content/replay versioning and provenance updated. |
| M17 | External alpha only after scoped privacy/security, crash recovery, signed installs, issue severity and cohort coverage are reviewable. Publish known gaps and supported devices. |
| M18 | Beta/store candidate: exact signed build, device/upgrade matrix, dated current platform policy review, store metadata/privacy, staged rollout/monitoring/rollback and release owner approval. Store approval remains external. |

Mobile parity is earned by repeated device and visual gates, not by counting packets or promising a fixed number of asset batches. Current disposition: **M0 research complete within source-review scope; device, mobile-build, online 10-client and store acceptance all open.**
