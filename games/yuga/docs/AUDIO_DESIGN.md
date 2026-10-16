# YUGA: Confluence — original audio design

The arena uses browser Web Audio synthesis. The implementation contains no recordings, voice imitation, copied game sounds, third-party songs, or sacred chants. Noise is seeded locally; oscillators and short envelopes generate every cue. Audio requires no download or external service.

## Readable combat

| Authoritative action | Sound | Scope |
| --- | --- | --- |
| Bow shot | Short descending string-like tone and air transient | Own hero and nearby heroes |
| Mace shot | Low pitched body sound and short broad impact texture | Own hero and nearby heroes; confirmed damage has a separate cue |
| Staff shot | Rising soft tone and quiet upper partial | Own hero and nearby heroes |
| Chakram shot | Short paired metallic tones | Own hero and nearby heroes |
| Spear shot | Midrange downward tone and air transient | Own hero and nearby heroes |
| Ability cast | Rising friendly or lower descending opposing cue | Authoritative cast event, once per cast |
| Confirmed hit | Short quiet acknowledgement | Damage dealt by the local player |
| Local player hurt | Low body tone and directional transient | Actual damage received |
| Hero defeat | Short two-note acknowledgement or descending death cue | Local hero kill/death; minion defeats stay quiet |
| Tower/core destroyed | Distinct rising or descending pair | Objective outcome, based on the destroyed structure's team |
| Friendly structure under attack | Restrained descending warning | Core damage, or nearby tower damage; at most once per six seconds |
| Pickup/upgrade | Short two-note confirmation | Accepted local events |
| Gold secured/intercepted | Quiet paired tones; an interception uses a distinct higher interval | Local authoritative `gold` event only; one cue per 0.2 seconds |
| Jungle camp cleared | Restrained rising interval | Local credited hero; paired temporary-power event is coalesced |
| Temporary power granted | Short rising tone with a distinct base pitch | Local standalone `buff` event; no duplicate sound for its camp reward |
| Match finished | Rising win, descending loss, or neutral draw phrase | One authoritative match outcome |

Sound follows successful server/simulation events. A key press, rejected ability, cooldown change, or purchase-button click does not manufacture confirmation. HUD flashes, health bars, objective states, event labels and the match result remain the primary readable feedback; sound provides another channel.

Protocol 2 adds gold and jungle events. Changing credits, spawning a shard, or changing an effect timer does not manufacture a reward sound. Camp and power events from the same guardian share a 1.2-second cooldown even when split across snapshots. Nearby allies' rewards remain silent. Routine neutral shots remain quiet; damage to the local player uses the guardian's authoritative position for its directional transient.

Nearby hero cues use a stereo pan from the listener's facing direction and distance attenuation, with a 42-metre hearing boundary. Friendly/opposing casts and weapons use different pitch contours. This gives orientation assistance without replacing visual team identification. There is no HRTF, occlusion simulation, or claim of precise front/back localization.

Optional rhythm is off by default. It is an original eight-step pattern of quiet pitched drum-like tones, suitable for the game's contemporary Indian setting. It is not presented as a researched historical performance or traditional composition. It stops with local gameplay activity, stays underneath combat, and never schedules a backlog of missed beats.

## Integration and preferences

The root client owns persistence and settings labels:

```ts
const audio = new ArenaAudio();
audio.setVolume(saved.volume);       // 0..1; finite values clamped
audio.setMuted(saved.muted);         // never creates a context
audio.setRhythm(saved.rhythm);       // optional; default false
audio.setActive(inVisibleGameplay);  // false in menus, disconnected/title states
// Call directly from a Play/Enable user gesture:
await audio.unlock();               // preserves the mute preference
// On authoritative snapshots:
audio.update(snapshot, playerId);
// From the explicit settings Test sound button:
await audio.preview();              // isolated sample; preserves mute/activity
// On final teardown:
audio.destroy();
```

Preview works while settings are open or sound is muted. It uses the selected volume, including zero, and an optional quiet percussion sample. Its approximately 0.7-second lifetime restores the prior desired playback state. Overlapping previews, visibility/activity changes and destruction cancel pending work. An older unlock or suspend completion cannot override a newer control action.

Normal pause/mute fades for 60 milliseconds before suspension; resume rises over 140 milliseconds. Hidden tabs suspend immediately. Initial snapshots, changed rooms/player identities, match restarts and menu recovery establish an event baseline, so joining an active battle does not play historical combat. Events older than 0.6 seconds are discarded; repeated IDs never replay.

There are at most 20 transient sources, including preview and optional rhythm. Finished sources disconnect their graph nodes. Local critical outcomes can replace an older lower-priority voice. Each update emits at most five event cues; per-action cooldowns, a bounded 64-key cooldown map and minion-shot suppression keep a busy lane from becoming a stream of notifications. No recurring audio timer runs: two cancellable timers cover short preview and suspension transitions.

## Evidence and limits

`games/yuga/tests/audio.test.ts` checks opt-in, mute preservation, event deduplication/backlog suppression, range/pan, confirmed-action semantics, voice limits/priority, structure-warning rate, preview restoration/overlap/zero volume, stale async transitions, optional rhythm and complete shutdown. Its Web Audio mock verifies lifecycle and resource ownership; it does not establish the perceived sound of a weapon or musical quality.

Read-only diagnostics include context state, preferences, preview state, active voice count and on-demand native RMS/peak measurements. A 256-sample analyser observes game and preview output after gain/compression. A suspended context may retain its last buffer: diagnostics do not substitute a zero based on mute labels. To verify native attenuation, set volume zero while running, then separately verify suspension.

The prior native browser baseline verified original synthesis, muted preview, zero-volume attenuation, suspension and preference persistence (`docs/evidence/baseline-browser-check.json`). The new protocol 2 reward routes have 16 passing mocked lifecycle/routing tests; those constructed snapshots are not evidence of earned gameplay rewards or native acoustic output. Native earned-reward acceptance remains with the integrated QA pass. No subjective headphone or loudspeaker listening pass has been performed by this implementation agent. Balance across hardware, spatial usability, cultural interpretation and mobile audio behavior require real playtesting. Production must not expose a development audio control global.
