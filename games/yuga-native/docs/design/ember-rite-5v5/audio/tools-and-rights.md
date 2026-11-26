# Ember Rite audio tools and commercial rights

Use the existing browser mixer for the next playtest. The Rust skirmish already decodes original ability cues into Web Audio and runs a stereo limiter in an AudioWorklet, with a compressor fallback. The standalone Ember Rite rehearsal can play authored cues locally. A future networked objective still needs server-authorized events before a listener can hear an opponent or receive a directional caption. The two builds have different audio paths. [Skirmish mixer and measurements](../../../rust-rebuild/deep-search/AUDIO-PORT.md) · [Ember Rite authority contract](../ROUND_AND_TECH.md)

For the listening desk, the score source and stems can travel together. *Ash at the Waterline* is an original 96 BPM piece with a 16-beat, ten-second loop. Its four entries fit the 40-second fire. Keep that timing in the score and music bus, then give ignition, quench and expiry their own event cues. Use Audacity or SoX to inspect edits and render consistently. The EN/HI timing guides use eSpeak NG's built-in voices. Cast performers and review pronunciation before turning those timing reads into character performances. [Score and stem manifest](../../../../art/yagna-audio/manifest.json) · [Guide generator](../../../../art/yagna-audio/voice_reference.py) · [eSpeak NG][esread]

## Authoring, instruments and reference projects

The numbered rows follow the original 21 proposals. Prices are in US dollars. Terms and source revisions were checked on 26 November 2026. The source receipts identify the response examined, including archives of publisher pages and rendered text for sites that require JavaScript. [Source receipts](source-checks.json)

| # | Proposal | Finding and decision | Primary source |
| --- | --- | --- | --- |
| 1 | Audiokinetic Wwise | Events, mixing and adaptive music make Wwise a candidate if a production team needs an authoring environment. The noncommercial **trial** caps SoundBanks at **200 media assets**. The free **Indie commercial license** allows **unlimited media** for an approved title with a total production budget **below $250,000**. Register the project and its platforms, obtain its key and check premium plug-ins separately. The detailed regional pricing page says “up to” at the boundary, while the comparison and Indie guide say “less than” or “under”. At exactly $250,000, obtain the applicable written tier. | [Pricing and trial FAQ, archived 9 Nov][wwarchive] · [Indie eligibility and registration][wwindie] · [Detailed game pricing][wwdetail] |
| 2 | Mridangam, tabla, shehnai, shankh and tanpura | Use their distinct functions to brief performers; the five directions below are original arrangements for a fictional contest. Commission and credit the actual instrumentalists when a performance is needed. | [Met instrument curator's guide][met] · [Met conch trumpet][conch] |
| 3 | Claude, Ghidra and morluto/REA | Claude is an assistant under the applicable Anthropic terms. Ghidra is an Apache-2.0 analysis framework. REA is an independent MIT-licensed project that can work with coding agents. YUGA's prior case used an original fixture. For audio QA, trace YUGA's own event-to-cue path or inspect an expressly licensed example. Commercial sound recordings and banks have their own owners. | [Anthropic commercial terms][claude] · [Ghidra license][ghid] · [REA at YUGA's revision][rearead] · [REA license][reapil] · [Prior fixture](../../../research/RESEARCH_BRIEF.md) |
| 4 | Rehan Sheikh's Universal Modder | The creator's launch post and the repository agree on the project. The plug-in credits “Rehan”, and its code is MIT. The README describes agent workflows and audio generation through fal. Each external model, generated asset and target game's content has separate terms. This research needs only the public case notes. | [Creator's announcement][rehan] · [Versioned project][umread] · [Plug-in credit][umpl] · [MIT notice][umlic] |
| 5 | awesome-gamedev-agent-skills | At the inspected revision there are **79** skill files under `skills/` plus a router. The NOTICE credits Abhishek Barali and contributors. The proposed attribution to Dr. Álvaro Cintas remains unverified. The two relevant entries are engine-neutral audio design and Godot audio. The former covers buses, ducking and variation, with a separate adaptive-music note on layering and bar boundaries. The skill pack is Apache-2.0. Retain the Apache license and NOTICE if redistributing upstream files. | [Countable tree][skillstree] · [NOTICE][skillsn] · [Audio skill][skillsr] · [Adaptive music][skillsar] |
| 6 | FMOD Studio and Engine | The registered Free Indie game requires **both** a project development budget **below $600,000** and developer annual **gross revenue/funding below $200,000**, before expenses. The EULA limits eligible distribution to the integrated game and lists conditions on third-party commercial exploitation and redistribution of example media. Studio's content authoring grant is for the FMOD Engine. Follow the credit line and startup-logo terms. HTML5 is documented, so a browser middleware comparison is technically meaningful if authoring needs justify it. | [EULA §§1.1–1.4][fmlegal] · [Pricing][fmpricing] · [Attribution][fmat] · [HTML5 API][fmweb] |
| 7 | Unreal Engine MetaSounds | Epic's in-engine graph can synthesize layers and vary footsteps procedurally. YUGA can implement the same design idea with original signals. Distributing Unreal Engine code invokes Epic's EULA and royalty rules. An independently rendered audio asset using original, cleared inputs can qualify as a non-engine product under §4(a)(i). Porting the graph/runtime into the browser would be a separate engineering and licensing decision. | [Epic MetaSounds][ue] · [Engine EULA §4][uel] |
| 8 | Google Resonance Audio | The Apache-2.0 Web SDK renders binaural Ambisonic audio through Web Audio. The core repository was archived in November 2023 and the Web SDK in April 2026. Useful spatial reference for a headphone comparison. A small team can start with a browser PannerNode and a mono-compatible output without adopting an archived SDK. | [Web audio example][googleweb] · [Web repository][reswebg] · [Core repository][resg] · [Web Audio PannerNode][w3pan] |
| 9 | Valve Steam Audio | The Apache-2.0 SDK documents HRTF binaural rendering, occlusion, reflections and reverb. Valve lists native platforms and engine/middleware integrations. A future native geometry test should compare equal-length open and obstructed paths and measure callback cost. A browser port and specific *Deadlock* or *Counter-Strike 2* middleware credits remain unverified here. | [Valve features and platforms][steamp] · [SDK license][steamlic] |

Riot's archived *VALORANT* role explicitly calls for implementing game audio and fixing bugs in Unreal and Wwise. Riot's player-facing patch also describes headphone HRTF and mono behavior. The original *Overwatch* sound team demonstrated Wwise events and REAPER post-processing. For Ember Rite, test whether a listener identifies whose warning matters in a ten-player mix. [Riot implementation role][riotproof] · [Riot audio settings][riotpatch] · [Blizzard team presentation, as documented by Audiokinetic][ow]

### What the instruments can say

| Sound | Musical reference | Proposed place in Ember Rite |
| --- | --- | --- |
| Mridangam | South Indian barrel drum and rhythmic accompaniment in Karnatak music. | A low, answered stroke anchors a cycle after a site is publicly lit. Leave space between strokes for footsteps. |
| Tabla | A drum pair. The larger bayan supports pitch inflection and the smaller drum carries a higher voice. | Short answers to the low drum can mark rising intensity. A pressure bend by a player is a separate recording choice. |
| Shehnai | North Indian double-reed wind with a penetrating upper voice. | Reserve a short melodic entrance for the last musical layer. Keep its register and onset clear of spoken countdowns. |
| Shankh or shankha | Conch trumpet with documented religious associations. | Consider a single breath-led ceremonial call at a public resolution. Have a cultural reviewer assess its setting before recording. |
| Tanpura or tambura | Plucked drone instrument that sustains a tonal foundation. | Give the center of the pitch field to a softly cycling drone. Keep mobile-speaker audibility and the mute control in the listening test. |

The current stem names describe the synthesis. A membrane-like transient or reed-like partial can stand in during rehearsal. Names of performance traditions, ragas, talas or devotional texts need a specific musical or textual basis and a musician who can evaluate the rendition. The museum pages document instruments and their contexts. Any recorded performance needs its own source and release. [Curatorial notes][met] · [Collection's shankh][conch] · [Project score](../../../../art/yagna-audio/score.json)

## Generated sound and speech

| # | Proposal | Finding and decision | Primary source |
| --- | --- | --- | --- |
| 10 | Stability AI Stable Audio Open | The public model card is **stabilityai/stable-audio-open-1.0**. Weights are access-gated. It generates up to 47 seconds of stereo 44.1 kHz audio from text. The separate **stable-audio-tools** code is MIT. Open 1.0 weights use the **Stability AI Community License**. Commercial use requires registration. §III counts annual revenue of the user and affiliates in aggregate and terminates the grant above $1M. Stability advertises the free tier below $1M. Resolve the exact boundary with Stability if it applies. §IV distinguishes model distribution and attribution obligations from rendered outputs and assigns output ownership as between the parties to the extent the law permits. Record model revision, applicable registration and rights to prompt/reference material before selecting a generated effect for release. | [Model card][stmodel] · [Tools license][stools] · [Weight license §§III–IV][stweights] · [Current agreement][stabl] · [Covered models][stlist] |
| 11 | Meta MusicGen / AudioCraft | AudioCraft code is MIT. MusicGen's published weights are **CC BY-NC 4.0**. Keep use of those weights within their noncommercial grant. A commercial team's unreleased mock-up can still have a commercial purpose. For a 120 BPM proposal, an original stem at that tempo has an exact clock and an auditable source. Measure generated tempo and loop joins independently of the text prompt. The current desk score uses 96 BPM. | [AudioCraft licenses][audioc] · [MusicGen card and limitations][mg] · [NC license][nc] |
| 12 | Suno Bark | The upstream project and released pretrained model advertise commercial use under MIT and list both Hindi and English. The project says English quality is strongest and describes unpredictable output. Audition a short, generic read for timing if useful. Before shipping any synthetic line, check the actual words, pronunciation, speaker rights and intelligibility under the mix. A community speaker preset needs its own provenance. | [Suno Bark release, languages and limitations][bark] · [Suno model card][barkhf] |
| 13 | RVC voice conversion | The project code is MIT. The linked distribution has separately downloaded base encoders and checkpoints, and its linked model hub has an empty model card. A tool license establishes only one link in that chain. For a performer covering ten hero roles, record a range of directed performances or negotiate explicit synthetic-voice permission specifying roles, languages, media, term, compensation and reuse. Keep any training recordings and weights within that agreement. | [Project and dependency list][rvc] · [Code license][rvlic] · [Linked model distribution][rvcstage] |
| 14 | Coqui TTS / XTTS-v2 | The original TTS toolkit is **MPL-2.0**. XTTS-v2 supports Hindi and English and has its own **Coqui Public Model License**, explicitly covering both the model and its outputs. It permits qualifying evaluation by a for-profit entity and limits use to noncommercial purposes. For public game lines such as “Yagna Ignited”, “Fire Extinguished” and “Agni Blessing”, record a performer or use a specifically cleared model. An alternate checkpoint in the toolkit requires its own license check. Speak “Agni Blessing” only for a game state that actually grants the blessing. | [Toolkit license][coquit] · [Model card][xttscard] · [CPML 1.0][xttsl] |

## Libraries, editing and distribution

| # | Proposal | Finding and decision | Primary source |
| --- | --- | --- | --- |
| 15 | Freesound | Uploaders select **CC0, CC BY or CC BY-NC**. Legacy Sampling+ files also exist. For commercial assets, keep the exact sound ID, uploader, original URL, license version and source file hash. CC BY requires creator and license credit, a source link where practicable, and an indication of edits. CC0 can simplify use of an uploader's own recording. Voice, recorded music or other embedded material can require separate rights. Set aside NC and legacy files unless equivalent permission is documented. | [Freesound FAQ and credit examples][fs] · [CC BY][ccby] · [CC0][cc0] |
| 16 | BBC Sound Effects | The BBC describes **over 33,000 clips**. RemArc covers specified personal, educational, research or other permitted noncommercial use, with credit under its terms. The commercial route for a specific sound runs through Pro Sound Effects. A public promotional cut, paid game or sponsored release needs terms covering that use. | [BBC archive][bbc] · [RemArc][bbcl] · [BBC commercial FAQ][bbcf] |
| 17 | Sonniss GDC | Bundle size varies. The publisher lists **23.5 GB** for 2024, **38.7 GB** for 2021–23 and **7.47 GB+** for 2026. The GDC agreement permits synchronization in commercial games and films without attribution. Version 2.0, effective 27 August 2026, bars supplying SFX as assets, including redesigned cuts and sample packs, and developing or training AI with them. Keep the terms in force on the download date. Use eligible cuts within the finished work. Reserve the public source repository, stem downloads and reusable audio kit for material with standalone redistribution rights. | [Bundle sizes][sonlist] · [2026 collection][son26] · [Rights granted, restrictions and version history][son] |
| 18 | JUCE | JUCE 9 is a C++ audio framework. Its framework modules offer **AGPLv3 or the commercial JUCE license**. A custom filter integrated into a distributed proprietary binary needs a compatible licensing route. A browser BiquadFilterNode can implement an occlusion low-pass within the existing mixer. Offline authoring and distributing a linked binary raise different questions. | [JUCE license and dependencies][juce] · [Web Audio filters][w3filter] |
| 19 | SoX | Use the CLI offline to resample, trim and inspect predictable batches of original recordings. Upstream licenses the executable under the GPL and libSoX under the LGPL, with a GPL build possible when certain optional libraries are linked. Distributing the program or a linked library triggers its applicable obligations. An original input keeps its rights when exported. | [SourceForge COPYING][soxc] · [SoX manual][soxdoc] · [GNU on program output][gplout] |
| 20 | Audacity | An offline editor for cutting takes, adding fades, listening to joins and exporting clean WAVs. Its application license is GPLv3. An original recording edited with it can be commercially released. Check third-party sample packs and plug-ins on their own terms. | [Audacity FAQ][aud] · [Application license][audl] · [GNU on program output][gplout] |
| 21 | REAPER / ReaScript | REAPER offers a **60-day evaluation**. Afterward the discounted license is **$60** for eligible users, including commercial use at yearly gross revenue **up to $20,000**. The standard commercial license is **$225**. ReaScript supports EEL2, Lua and Python. Automate stem naming and equal-length renders with an authored script; inspect each downloaded script's permissions before copying it into the repo. Session files, samples and the license for the DAW are separate. | [Cockos pricing][reaper] · [ReaScript SDK][reas] · [ReaTeam community scripts][reaprea] |

## Release record for each sound

Record the asset ID, event, writer or recordist, exact source URL/revision, license or signed grant, original hash, edits, exported hash, intended output and credit text. For recorded or generated voices, include performer permission and approved locales where applicable. A game, trailer, public listening desk, downloadable stem and public repository are separate outputs. A license for synchronized playback can cover the game and trailer while requiring separate permission for isolated stems, previews or redistributable source. A desk that serves an isolated downloadable cue is distributing that file. Check the selected asset against the actual delivery format. [Sonniss synchronization and redistribution terms][son] · [Freesound's per-file policy][fs]

The audio lead can release the original score, rebuild sources and eligible takes when their records cover the named output. Assign final character reads to the casting and localization leads. For an external bank, generated asset or middleware release, the producer should verify the actual file, title, platform, budget and credited use against the source receipt. The published source checks cover documentation and metadata. The score and timing guides carry separate generation records.

[esread]: https://github.com/espeak-ng/espeak-ng/blob/master/README.md
[wwarchive]: https://web.archive.org/web/20261109225518/https://www.audiokinetic.com/en/wwise/pricing/
[wwindie]: https://www.audiokinetic.com/en/community/blog/free-wwise-indie-license/
[wwdetail]: https://www.audiokinetic.com/en/wwise/pricing/for-games/
[met]: https://www.metmuseum.org/essays/musical-instruments-of-the-indian-subcontinent
[conch]: https://www.metmuseum.org/art/collection/search/503672
[claude]: https://www.anthropic.com/legal/commercial-terms
[ghid]: https://github.com/NationalSecurityAgency/ghidra/blob/50b78476df100fd360f6623223c5e4510c569c5c/LICENSE
[rearead]: https://github.com/morluto/rea/blob/0c7b6d834af2d044b23196e0e522cc2468327a1e/README.md
[reapil]: https://github.com/morluto/rea/blob/0c7b6d834af2d044b23196e0e522cc2468327a1e/LICENSE
[rehan]: https://x.com/rehan_shei/status/2105161487509852622
[umread]: https://github.com/rehan-remade/universal-modder/blob/a34eae75732d7fd5e7810abde188063e72829525/README.md
[umpl]: https://github.com/rehan-remade/universal-modder/blob/a34eae75732d7fd5e7810abde188063e72829525/plugin.json
[umlic]: https://github.com/rehan-remade/universal-modder/blob/a34eae75732d7fd5e7810abde188063e72829525/LICENSE
[skillstree]: https://github.com/gamedev-skills/awesome-gamedev-agent-skills/tree/c6ca6c41c839b68319ffc08430b99ab768debc32
[skillsn]: https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/c6ca6c41c839b68319ffc08430b99ab768debc32/NOTICE
[skillsr]: https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/c6ca6c41c839b68319ffc08430b99ab768debc32/skills/disciplines/audio-design/SKILL.md
[skillsar]: https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/c6ca6c41c839b68319ffc08430b99ab768debc32/skills/disciplines/audio-design/references/adaptive-music.md
[fmlegal]: https://www.fmod.com/legal
[fmpricing]: https://www.fmod.com/licensing
[fmat]: https://www.fmod.com/attribution
[fmweb]: https://www.fmod.com/docs/2.03/api/platforms-html5.html
[ue]: https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-the-next-generation-sound-sources-in-unreal-engine
[uel]: https://www.unrealengine.com/eula/unreal
[googleweb]: https://resonance-audio.github.io/resonance-audio/develop/web/getting-started.html
[reswebg]: https://github.com/resonance-audio/resonance-audio-web-sdk
[resg]: https://github.com/resonance-audio/resonance-audio
[w3pan]: https://www.w3.org/TR/webaudio-1.1/#PannerNode
[steamp]: https://valvesoftware.github.io/steam-audio/
[steamlic]: https://github.com/ValveSoftware/steam-audio/blob/f943b4204b876bc3096b1c3d308784536d461876/LICENSE.md
[riotproof]: https://web.archive.org/web/20220925090056/https://www.riotgames.com/en/work-with-us/job/4566156/associate-sound-designer-premium-content-valorant-los-angeles-usa
[riotpatch]: https://playvalorant.com/en-us/news/game-updates/valorant-patch-notes-8-0/
[ow]: https://www.audiokinetic.com/en/community/blog/overwatch-game-audio-using-wwise-1/
[stmodel]: https://huggingface.co/stabilityai/stable-audio-open-1.0/blob/f21265c1e2710b3bd2386596943f0007f55f802e/README.md
[stweights]: https://huggingface.co/stabilityai/stable-audio-open-1.0/blob/f21265c1e2710b3bd2386596943f0007f55f802e/LICENSE.md
[stools]: https://github.com/Stability-AI/stable-audio-tools/blob/3241adba4fc2a85cf5b29d9eb68d42f40a28e820/LICENSE
[stabl]: https://stability.ai/community-license-agreement
[stlist]: https://stability.ai/core-models
[audioc]: https://github.com/facebookresearch/audiocraft/blob/896ec7c47f5e5d1e5aa1e4b260c4405328bf009d/README.md
[mg]: https://huggingface.co/facebook/musicgen-small/blob/4c8334b02c6ec4e8664a91979669a501ec497792/README.md
[nc]: https://creativecommons.org/licenses/by-nc/4.0/
[bark]: https://github.com/suno-ai/bark/blob/f4f32d4cd480dfec1c245d258174bc9bde3c2148/README.md
[barkhf]: https://huggingface.co/suno/bark/blob/70a8a7d34168586dc5d028fa9666aceade177992/README.md
[rvc]: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/81eed5e8f68b6bed1789f682fe78cdd324495afc/docs/en/README.en.md
[rvlic]: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/81eed5e8f68b6bed1789f682fe78cdd324495afc/LICENSE
[rvcstage]: https://huggingface.co/lj1995/VoiceConversionWebUI
[coquit]: https://github.com/coqui-ai/TTS/blob/dbf1a08a0d4e47fdad6172e433eeb34bc6b13b4e/LICENSE.txt
[xttscard]: https://huggingface.co/coqui/XTTS-v2/blob/6c2b0d75eae4b7047358e3b6bd9325f857d43f77/README.md
[xttsl]: https://huggingface.co/coqui/XTTS-v2/blob/6c2b0d75eae4b7047358e3b6bd9325f857d43f77/LICENSE.txt
[fs]: https://freesound.org/help/faq/
[ccby]: https://creativecommons.org/licenses/by/4.0/
[cc0]: https://creativecommons.org/publicdomain/zero/1.0/
[bbc]: https://sound-effects.bbcrewind.co.uk/about
[bbcl]: https://sound-effects.bbcrewind.co.uk/licensing
[bbcf]: https://sound-effects.bbcrewind.co.uk/faqs
[sonlist]: https://sonniss.com/gameaudiogdc/
[son26]: https://gdc.sonniss.com/
[son]: https://sonniss.com/gdc-bundle-license/
[juce]: https://github.com/juce-framework/JUCE/blob/654bdbc7a9db0dae90849b44abe91f339e9f0768/LICENSE.md
[w3filter]: https://www.w3.org/TR/webaudio-1.1/#BiquadFilterNode
[soxc]: https://sourceforge.net/p/sox/code/ci/master/tree/COPYING
[soxdoc]: https://sourceforge.net/p/sox/code/ci/master/tree/sox.1
[gplout]: https://www.gnu.org/licenses/gpl-faq.html#GPLOutput
[aud]: https://www.audacityteam.org/faq/
[audl]: https://github.com/audacity/audacity/blob/Audacity-4.0.2/LICENSE.txt
[reaper]: https://www.reaper.fm/purchase.php
[reas]: https://www.reaper.fm/sdk/reascript/reascript.php
[reaprea]: https://github.com/ReaTeam/ReaScripts/blob/master/README.md
