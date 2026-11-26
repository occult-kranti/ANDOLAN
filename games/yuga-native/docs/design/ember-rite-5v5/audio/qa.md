# Ember Rite audio verification

The browser rehearsal gives one player control of the listener, the vessel and a manually placed practice source. The tests below follow movements, holds and outcomes in that drill. The Rust series has its own ten-seat tests. The live private room still plays Confluence knockouts. A networked Ember Rite needs its own audience and reconnect checks. [Rehearsal](../atlas/rehearsal.html) · [Rust round and series](../../../../../yuga-rust/src/ritual.rs) · [Room adapter](../../../../../yuga-rust/src/bin/room.rs)

## Who hears a cue

| Event | Verified behavior in the solo drill | Multiplayer acceptance case |
| --- | --- | --- |
| Footstep | Accepted movement produces one contact per 1.65 m. The last eligible listener distance is 18 m. A runner pushing an obstacle stops generating steps. Water and stone have different captions and sounds. | Give both teams the same mix. Move a hidden runner on either side of 18 m. An eligible listener gets a coarse direction and surface. Everyone else receives no contact in their event stream, captions or map. |
| Hanuman leap and Kali Tandava | The Explore source plays either tell on demand. The limits are 20 m for Hanuman and 25 m for Kali. Turning in place reverses a side bearing while the source stays put. | Drive the tell from an accepted cast. Check a rival at the same position, an out-of-radius rival and a spectator. Hero position, health and targeting data stay behind the server's visibility rules. |
| Kindle and quench | A legal held interaction starts the windup. The limits are 30 m for kindle and 18 m for quench. Only the acting listener gets the interruption receipt. A released or simulated-hit hold can be retried. | Put one ally and two enemies on opposite sides of each threshold. A defender can feint a quench. A remote listener may hear the onset and the later public result if there is one. The damage source and reason for releasing stay private. |
| Dropped vessel and fold | The runner gets the drop, recovery, departure and successful-arrival cues. A blocked exit and an early release produce zero arrivals. Keeping Interact held through a crossing produces one arrival. | Test both mouths and their ordinary walking routes. Evaluate any future remote windup at the entrance and any confirmed arrival at the exit. Count one arrival per accepted crossing. A fold cannot carry other sounds across the map. |
| Public objective | Ignition announces the confirmed site. Quench, expiry and completion use centered public feedback. The bearing and level of these receipts are independent of supplied world coordinates. | Only allies receive a hidden carrier's identity. Compare redacted player streams before ignition, after ignition, on duty swap and on reconnect. A returning player gets the current public clock and eligible music phase. Past starts, interrupts and result stings must stay silent. |

The radius tests use legal positions along the Spice Gate to South Temple route, with a listener on the boundary, 1 cm inside it and 1 cm outside it. A diagonal offset of 10.8 by 14.4 m also qualifies at 18 m despite floating-point rounding. For a 6 m dry footstep, the open path gave a gain of 0.628 and a 9.83 kHz filter cutoff. The low Stone lectern reduced these to 0.537 and 7.57 kHz. The tall Bell screen reduced them to 0.345 and 2.75 kHz. A ray tangent to the screen retained the open-path values. The South Pyramid masonry test crosses a pavilion wing. A separate pair inside the Quarter-turn Pavilion qualifies for a short reflection. Both Measure Well basins produce water footsteps, while the central sill produces stone. Horizontal rays and the authored cover heights define this test. Floor stacking, head elevation and acoustic diffraction require a 3D integration. [Measured map geometry](../atlas/maps/) · [Executable cases](../atlas/rehearsal/audio.test.mjs)

## Match length and repetition

Regulation lasts 13 to 24 rounds. Duties swap after 12. At 12–12, overtime alternates duties on every round and evaluates the winner after each two-round pair. Three tied pairs end a 15–15 draw after 30 rounds. The Rust tests exercise an overtime lead of 13–12, a pair winner, a 15–15 draw and rejection of new results after settlement. In the separate audio test, a muted listener runs 30 consecutive resets with reused receipt IDs. Each round produces exactly one authorized kindle caption. Duplicate and ineligible receipts add zero. [Series tests](../../../../../yuga-rust/tests/ritual.rs) · [Listener lifecycle test](../atlas/rehearsal/audio.test.mjs)

The 4-second kindle occupies time on the 100-second approach clock. A full 40-second burn on the final approach tick therefore gives at most 140 seconds of active time per round. Twenty-four such rounds take 56 minutes, including 16 minutes of score. Thirty take 70 minutes, including 20 minutes of score. Adding the proposed 20-second preparation to every round raises those upper bounds to 64 and 80 minutes, before intermissions. Early eliminations, incomplete holds and quenches shorten the session. A match with no ignition has no burn music. [Round timing](../ROUND_AND_TECH.md)

## Browser and listening checks

The browser suite operates the generated HTML through its normal controls. It advances the 20 Hz rehearsal clock for the scripted routes and uses real time for Web Audio. A stereo analyser samples the same output sent to Chromium’s destination. An independent observer identifies decoded FLAC stems by their STREAMINFO and records when Chromium starts each source. [Browser test](../atlas/rehearsal/audio.browser.test.mjs) · [Score assets](../../../../art/yagna-audio/)

On 26 November 2026, Chromium 154.0.8037.57 exercised the 1,150,469-byte page built from the working branch based on `2acb45b3d61973a924fe5518c617e4fd2afb02d7`. Its SHA-256 is `ffd7760b0c8d1fe66288425aecedeba24df7c9a4fbe208fef7fdebd1348f5447`. The portable build matched its sources. Sixteen JavaScript cases passed across audio and movement, alongside ten independent Rust round tests.

| Browser observation | Result |
| --- | --- |
| Fixed listening source | At 22.5 m with sound disabled, Kali and kindle still produced directional captions. The Hanuman and footstep auditions produced zero new captions. The marker stayed where the player placed it. |
| Stereo and mono | The same Kali cue peaked at 0.3122 left and 0.0246 right. Turning 180 degrees swapped the two values. Both channels peaked at 0.2215 in mono, with a maximum left-minus-right sample difference of zero. Peaks are normalized digital amplitudes. |
| Interrupted hold | Releasing a real kindle scheduled the active windup to stop with a 12 ms fade. An idle interruption control was disabled. Only a completed four-second hold produced the public site receipt. |
| Gesture, mute and captions | The desktop began with zero output graphs and zero voices. Enter enabled sound. Master mute and zero effects volume silenced an eligible cue while its caption remained available. Turning captions off allowed the signal to play. Switching tabs during a burn paused the drill. After returning and before manual resume, the measured peak was zero. |
| Touch and settings | At 375 px the caption appeared beside the Play cue button without horizontal overflow. A browser with its audio API disabled still ran the text exercise via touch. A scripts-only frame restored mono and 37% music from its parent with zero voices. A fresh tap enabled real playback. The 1280 px desktop layout also kept the cue and controls visible. |
| Objective outcomes | A simulated 100-second approach expired with the clock at zero. The retake ran for forty real seconds and played the expiry sting once. A separate accepted 3.5-second quench played its own sting. The browser recorded all fifteen receipt types across the drills. |

The accepted layer starts arrived at 0.000, 9.969, 19.975 and 29.966 seconds of wall time. The expiry sting arrived at 39.973 s. The displayed fire clock read 40, 30, 20, 10 and 0 seconds at those events. Re-enabling music with 7.2 s displayed brought all four stems back at the same 2.750 s position in their ten-second loops. This exercises an individual listener restoring music during a live solo burn. The multiplayer rejoin case still needs an authoritative snapshot. [Chromium measurements](qa-receipt.json)

Chromium’s audio rendering clock advanced 39.355 s during that 39.973 s wall interval. Another run on this shared host advanced 37.634 s between the same first and last events. The simulation clock governs the stage changes, and the mixer corrects its playback position when the two clocks diverge. The sample output and wall timing establish behavior on this headless host. Headset latency and underruns on player devices still need measurement.

Run from the repository root.

```sh
cd games/yuga-native/docs/design/ember-rite-5v5/atlas/rehearsal
python3 build.py --check
node --test audio.test.mjs simulation.test.mjs
node audio.browser.test.mjs
node browser.test.mjs
```

The independent round checks run from the repository root with `cargo test --locked --manifest-path games/yuga-rust/Cargo.toml --test ritual`.

## Human playtest still needed

Use ten consenting players across the two duties. Place an observer just inside and outside each radius and assign a third observer to the neighboring floor or other fold mouth. Rotate which team approaches. First hide captions and ask players to identify the event, its side and whether a hold finished. Repeat in mono and with the score at its last layer, then with effects muted and captions enabled. Record misses and false alarms by event, distance, device and setting. Ask again after regulation and after each overtime pair whether the score masked a footstep, carried through a handoff, or made a warning tiring to repeat. Physical headphones, speakers, assistive technology and ten-person matches need listening sessions to establish intelligibility and fatigue. [Ten-player encounters](../atlas/ENCOUNTERS.md)
