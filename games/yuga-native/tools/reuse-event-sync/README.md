# Observed event, socket and receiver inspector

This offline tool extends the existing [Source 2 event-window adapter](../../docs/research/reuse-next-ten/reuse-advisor-world/README.md). It captures the original Rama Kit/Army, routes their real events through the unchanged `RamaHeroRuntime`, observes the existing effect/audio receiver return values, and samples the real 164-bone rig's bow, string, hand and muzzle transforms. It changes no production script, event scheduling, damage, animation, audio cue, or asset.

```sh
python3 games/yuga-native/tools/reuse-event-sync/run.py \
  --output /workspace/scratch/rama-event-sync-fresh
```

Run from the checkout with Godot 4.6.3 and existing imports. Use a fresh absolute output directory. The runner performs five commands: capture, counterexamples, then three reports. Each subprocess has a 180-second bound; capture uses one allowed CPU when `taskset` is available. It preserves logs, source and engine hashes, compressed exact evidence and failures. No installation, download, network access, renderer, credential or deletion is involved. The executed five-command run took about 9.7 seconds; this is a tooling observation on this host, not a game performance benchmark.

Inspect retained evidence directly, including `.json.gz`:

```sh
python3 games/yuga-native/tools/reuse-event-sync/inspect_sidecar.py \
  --trace games/yuga-native/docs/research/reuse-production-continuation/W5/evidence/accepted-r4/actual.json.gz \
  --hz 60 --output /tmp/rama-observed-60-fresh.json
```

The report keeps missing acknowledgements or socket samples as `null`/missing and returns exit 1 with explicit findings. It never supplies an identity transform or an expected success. Event identity is `(generation,event_seq)`; the sampler operates separately within each generation so a reset to simulation time zero cannot merge old and new casts. Every source event, including ordinary ticks, remains in the raw capture. Playback selects lifecycle/contact events and ticks that actually select an audio voice. The existing MIT window algorithm only groups observations; its whole-loop coalescing is unsuitable for combat or repeated audio dispatch.

`observed_effects.gd` and `observed_audio.gd` are instrumentation subclasses. Each calls `super.consume_event` exactly once, records the returned boolean/acknowledgement plus receiver state, and returns it unchanged. Only the fixture replaces its receiver instances. No production script or connection is patched. The inherited effect sequence and audio watermark must match the real event identity. Audio acceptance means consumption, not an audible cue: unchanged tick/terminal events can be accepted with `played_delta:0`.

The fixture excludes unrelated Army units and AI/waves, requests the two abilities directly through the actual Kit, and advances the unchanged Army at 20 Hz. Motion/effect presentation is sampled at 30/60/120 Hz. The three Dawn Volley contacts are actual **range expirations**, not damage hits. Cancellation, reset/recast and stale/duplicate receiver calls are also captured. This is neither ordinary input play nor rendered review.

The actual `RamaActionAudio` implementation uses event simulation time for pulse eligibility and its 70 ms hit-confirmation guard. `AudioServer` voice lifetime has its own clock. The sidecar records monotonic wall time separately and does not reinterpret accelerated capture as real-time playback or listening quality. Missing or suppressed cues remain inspectable.

Current evidence and limitations: [W5 execution packet](../../docs/research/reuse-production-continuation/W5/README.md). Next gate is continuous paired rendering through the same route, followed by genuine unit/wall-contact and listening review; numerical sockets alone cannot close those gates.
