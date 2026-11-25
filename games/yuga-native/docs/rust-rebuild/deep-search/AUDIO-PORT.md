# Battlefront limiter in YUGA’s audio renderer

The browser uses the MIT-licensed stereo limiter from the openbf Battlefront engine reconstruction to control peaks when players trigger overlapping abilities. The unchanged upstream file and copyright notice live together. YUGA supplies the original sounds, block adapter and browser audio routing. The packager includes the MIT text in the downloadable notices. [Upstream implementation](https://github.com/sprucey149/openbf/blob/5015e39c74361efc9e2576fea5b8346361b926de/engine/crates/audio/src/limiter.rs) · [Vendored source](../../../../yuga-rust/src/vendor/openbf/limiter.rs) · [MIT notice](../../../../yuga-rust/src/vendor/openbf/LICENSE)

## Signal path

An ability cue feeds the shared stereo bus. In a supported browser, an AudioWorklet owns a separate instance of the compiled YUGA Wasm module and calls the limiter on short audio blocks. The player’s master gain applies mute and pause after the limiter. A Web Audio dynamics compressor serves as the initial and fallback processor. The switch waits for a readiness message from the worklet. The 2 ms lookahead allows a peak to attenuate both channels together. Quiet samples pass through with the same delay. [Audio routing](../../../../yuga-rust/web/main.ts) · [Worklet](../../../../yuga-rust/web/mix-worklet.js)

The wrapper allocates two fixed 256-sample buffers and preallocates the limiter’s delay on initialization. `mix_init` accepts 8,000–192,000 Hz and returns the block capacity. `mix_left_ptr` and `mix_right_ptr` expose independent aligned buffers, `mix_process` processes a bounded length in place, and `mix_delay_frames` reports the delay from the donor algorithm. Larger browser quanta are chunked. A single input channel is copied into both lanes. The worklet sanitizes nonfinite input in Rust. The optional upstream Kira backend stays out of the YUGA dependency graph. [Rust adapter and tests](../../../../yuga-rust/src/mix.rs)

## What ran

Chromium 154 rendered all six original Hanuman ability cues, with two copies of each, through a real stereo AudioWorklet in an OfflineAudioContext. The left channel started at a peak of 1.193176, and the right channel was half its level with opposite polarity. Peak output was exactly 1.0 for the bus, and every sample kept that channel relationship. At 24 kHz the first 48 frames were silent. After reducing source amplitude to 8%, every left output sample matched the delayed input bit for bit. The underlying donor unit test and two Rust adapter tests also passed. [Browser and Wasm receipt](audio-mixer-qa.json) · [Initial native module probe](catalog/limiter-receipt.json)

The following measurements are for the exact release Wasm recorded in the receipt, in Node 24 on the cloud CPU. Each sample rate used 128-frame stereo blocks, one warm-up pass and three measured passes of roughly two audio seconds. Each block includes copying input into the Wasm buffers. CPU is process user plus system CPU time divided by audio duration. Elapsed time also includes scheduler contention. Neither measure includes device output latency or predicts performance on a specific laptop.

| Device sample rate | Median CPU time relative to audio duration | Median elapsed time relative to audio duration |
| --- | --- | --- |
| 24 kHz | 0.245% | 0.295% |
| 44.1 kHz | 0.717% | 0.739% |
| 48 kHz | 0.836% | 1.008% |
| 96 kHz | 3.181% | 4.799% |
| 192 kHz | 13.107% | 19.235% |

The limiter scans a sample-rate-dependent lookahead window for each output sample. The 192 kHz result makes that cost visible. Before changing the algorithm, measure device callback deadlines during representative team fights at the target headset’s actual sample rate. The receipt covers sample correctness and throughput. Long-session underruns and perceived loudness still require a physical device. [Probe code](../../../../yuga-rust/tools/test_mixer.mjs)

## Reproduce

From the repository root, install the project’s locked Node dependencies and Rust’s `wasm32-unknown-unknown` target. Run these commands with a local Chromium installation or Playwright’s Chromium available. `PLAYWRIGHT_CHROMIUM_EXECUTABLE` can select a browser binary.

```sh
cargo test --locked --manifest-path games/yuga-rust/Cargo.toml --lib mix::
cargo build --locked --release --target wasm32-unknown-unknown --manifest-path games/yuga-rust/Cargo.toml --lib
node games/yuga-rust/tools/test_mixer.mjs
```

For an alternate Cargo target directory pass `--wasm PATH` to the Node test. Use `--report PATH` to save a fresh measurement. [User-facing package](../../../../yuga-rust/README.md)
