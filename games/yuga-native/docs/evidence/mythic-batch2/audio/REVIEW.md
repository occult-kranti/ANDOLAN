# Original invocation cue verification

`invocation-audio-build.json` reproduces all 16 generated PCM files byte for byte. The final imported-resource `invocation-audio.json` passes 49 owner lifecycle and adversarial checks on the frozen runtime, including every hero release, three-player bounds, epoch/cast/event de-duplication, muted/suspended onset consumption, pause defense, reset and cleanup. The numerical maximum sum of three peaks is 0.5562, below full scale.

The runtime uses three pooled players and no per-tick sound allocation. It loads raw WAVs in an unimported source checkout and Godot remapped resources in a package. Source paths, generator hash and each WAV hash are recorded in [the original synthesis manifest](../../../../assets/audio/invocations/manifest.json); [usage and scope](../../../../assets/audio/invocations/README.md) describe the API.

`history/invocation-audio-final.log.txt` preserves a fast-shutdown ObjectDB warning even though its 48 assertions passed. The final test observes weak references to ten actual stopped playbacks until they retire, bounded to one second; they retired in 75 ms. `invocation-audio.log.txt` is the clean 49-case rerun. The imported-resource fixed-60-ms warning is also preserved under `history/invocation-audio-fixed-wait-warning.*`. The runtime source was unchanged by these test cleanup changes. Earlier 45-case history predates the default-volume and paused-tree probes.

The first post-import run failed 47/48 because Godot's default WAV import used QOA compression. `history/invocation-audio-default-import-failure.*` retains that counterexample. All sixteen versioned `.wav.import` settings now explicitly select `compress/mode=0`. Root performed the serialized reimport, and the final report records actual PCM16 format, 48 kHz, nonlooping state, duration and import-setting hashes for every cue. WAV bytes, generator and runtime were unchanged.

These are deterministic PCM and Dummy-driver lifecycle checks, not a listening review, musical-quality claim, measured hardware latency or final scene/release approval. Root owns actual integrated playback and publication.
