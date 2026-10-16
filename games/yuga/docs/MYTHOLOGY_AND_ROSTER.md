# YUGA: Confluence — mythology and roster

This is an original competitive arena interpretation of characters associated with the Ramayana and Mahabharata. Its combat kits, cooldowns, teams, dialogue and fictional Sangam City are game inventions. The roster is not a claim about canonical powers, historical events or a single authoritative version of these traditions. All fourteen heroes and all three abilities are available from the first match; there is no paid power. Sun and Moon are match teams, independent of the characters' epic allegiances.

The expanded release uses fourteen short, readable kits: five Vanguards, four Strikers and five Keepers. Every character can damage opponents; the role describes an emphasis rather than an exclusive class. The source material below informed selected motifs and relationships. Research consisted of the specified passages, not whole-book reading or a survey of Indian traditions.

## Playable roster

`shared/heroes.ts` is the numerical source of truth. Q/E/R name the default keyboard slots; R is a longer-cooldown ability available at match start, without an unlock or charge requirement. Counterplay in this table is a design hypothesis to test, not a measured result.

| ID / hero | Role; health / speed | Q → E → R | Intended opportunity and constraint |
| --- | --- | --- | --- |
| `rama` / Rama | Striker; 300 / 7.2 | Steady Arrow → Measured Step → Dawn Volley | Accurate projectiles with a short reposition. His three-arrow R locks aim during a one-second preparation; cover and lateral movement interrupt the firing lane. |
| `ravana` / Ravana | Vanguard; 390 / 6.4 | Tenfold Guard → Commanding Circle → Crownfire | Pull a group toward a chosen point, then close for a self-centred blast. His slower movement makes that approach a commitment. |
| `arjuna` / Arjuna | Striker; 275 / 7.7 | Converging Volley → New Angle → One Clear Line | Fast aim and angle changes; the smallest health reserve makes an exposed flank costly. |
| `duryodhana` / Duryodhana | Vanguard; 410 / 6.2 | Mace Shock → Hold the Ground → Iron Crescent | Highest health and short forward attacks. Back away or change angle when his guard is spent. |
| `hanuman` / Hanuman | Keeper; 350 / 7.6 | Windward Leap → Bring Them Home → Mountain Pulse | Leap between allied groups and heal nearby allies. R commits to a marked leap whose damage/heal arrives on landing. |
| `karna` / Karna | Striker; 315 / 6.8 | Sunshaft → Borrowed Dawn → Solar Reprisal | Heavy aimed shots and a brief defensive shield; a close blast discourages pursuit. Missed slow shots leave an opening. |
| `bhima` / Bhima | Vanguard; 400 / 6.4 | Heavy Sweep → Closing Stride → Thunder at Your Feet | Leap into close pressure. Spacing and cover limit his forward sweep and self-centred blast. |
| `meghnad` / Meghnad | Striker; 285 / 7.8 | Cloud Snare → Storm Step → Gathered Squall | Use a visible slowing zone to shape a flank, then strike a forward fan. Low health makes a failed approach risky. |
| `sita` / Sita | Keeper; 330 / 6.8 | Grove Renewal → Rooted Path → Shelter of Mithila | Sustain a gathered team and obstruct an approach. R creates a fixed sanctuary after preparation; ongoing recovery requires remaining inside. |
| `draupadi` / Draupadi | Keeper; 340 / 6.5 | Circle of Resolve → Stand Accountable → Unbroken Assembly | Shield a group, pull approaching opponents and recover a nearby team. No movement ability; keep a route back to allies. |
| `subhadra` / Subhadra | Keeper; 315 / 7.2 | Signal Lance → Rally Close → Twin Standards | Support a moving group and briefly add two allied sentinels. The summons expire and the heal has a small radius. |
| `hidimbi` / Hidimbi | Vanguard; 375 / 6.8 | Forest Boundary → Canopy Guard → Grove Watch | Protect an objective with a visible zone, nearby shields and temporary sentinels. Pressure from another lane draws her away from that position. |
| `chitrangada` / Chitrangada | Vanguard; 350 / 7.5 | Crossing Step → Spear Arc → Defender's Vow | Cross an approach, strike a short forward arc and shield nearby allies. More mobile than the heavier Vanguards, with less health. |
| `ulupi` / Ulupi | Keeper; 320 / 7 | River Draw → Cooling Current → Naga Basin | Pull opponents toward an aimed point, heal close allies and slow an approach. Alternate routes and distributed pressure limit the zone's value. |

### Mechanical meanings shared with the server

- `bolt` and `line` are aimed projectiles. Line is faster; its name does not promise piercing. Ordinary cover and authoritative hit rules apply.
- `burst` and `cone` damage a forward area. `nova` damages a circle centred on the caster.
- `dash` and `leap` move forward up to their authored range, respecting solid collision; leap also adds jump height. Their `power` field does not imply an extra damaging landing attack.
- `heal` restores nearby allies, including the caster. `ward` grants nearby allies temporary shields. Both centre on the caster; their radius determines the area.
- `slow` creates an aimed ground zone that damages and slows opponents. `pull` damages enemies in an aimed circle and moves them toward its centre subject to collision.
- `summon` creates two allied temporary minions beside the caster. Both authored summon durations currently produce nine-second sentinels; the simulator uses `max(6, duration × 3)` seconds. Power is their projectile damage.

Ability fields are parameters of a shared kind, not independently promised effects. In particular, duration is not a stun timer, and a radius field does not make a projectile explode. No kit promises homing, stealth, invulnerability or an unimplemented ultimate meter.

Three R slots extend those shared kinds through an explicit `mechanic` field. Rama's Dawn Volley locks preparation/aim for one second, then fires three separate arrows at 32 base power each and 28 m range. Hanuman's Mountain Pulse has a 0.7 s preparation followed by a 0.45 s authoritative, collision-limited arc up to 14 m; actual landing applies 65 base enemy damage and 45 ally healing within 7 m. Sita's Shelter of Mithila has a 0.8 s preparation, then creates a fixed 8 m sanctuary for six seconds: an initial 70 base shield and 9 base health/s for living allies remaining within the visible area. Existing power upgrades scale the payloads. These three exceptions supersede their old immediate line/nova/ward behavior.

Preparation locks movement, jump, fire and other casts. Target/facing lock when accepted. Damage alone does not cancel; death cancels a pending cast without a cooldown refund, and disconnect preserves server progress. A sanctuary that has already formed persists for its duration after its caster dies. Art must communicate those timings rather than creating its own local outcome; the full presentation contract is in [HERO_ART_BIBLE.md](../art/HERO_ART_BIBLE.md).

Basic attacks use the same aimed-projectile framework for all weapon silhouettes, including maces, staffs and spears. A mace mesh does not mean a separate melee collision system. Weapon forms and colours make characters readable; team indicators communicate allegiance independently of costume colours.

### Initial tuning and acceptance

The authored health range is 275–410; movement speed is 6.2–7.8. Basic damage divided by fire interval ranges from 41.67 to 57.14 before misses, cover, upgrades and abilities. These are starting constraints, not evidence of equal win rates. Each hero has a distinct ordered three-kind combination, although abilities intentionally share server mechanics.

The expanded content gate passed: fourteen unique IDs, three abilities per hero, five Vanguards/four Strikers/five Keepers, all twelve supported ability kinds represented, unique ordered kit combinations, valid colours, nonempty descriptions and all agreed stat/cooldown/power/range/radius/duration bounds. The internal `heroById` fallback returns Rama; joins must separately reject unknown IDs.

An independent simulator/content review found two discrepancies before integration: ordinary dash/leap added unadvertised destination damage and haste, and pull damage was absent from the original two descriptions. The simulation owner removed the movement additions; all pull descriptions now include their intended damage. `tests/content.test.ts` passes 71 cases exercising all fourteen basic attacks and all forty-two ability slots through public input/command/step APIs, plus duplicate receipts, cooldowns, allied/enemy separation, movement collision, projectile cover and summon expiry. The three explicitly redesigned R abilities have separate timing/payload assertions. These are positioned unit fixtures, not physical browser traversal. They also guard against reintroducing hidden damage/haste on ordinary movement abilities.

Lane waves begin at one second and repeat every eighteen seconds: three escort units per lane per team, with distinct soldier, city-watch and minister roles. Every third wave, beginning at 37 seconds, adds a king siege unit per lane per team. The king is slower and tougher and prefers visible structures; its rounds can still be intercepted. Temporary Subhadra/Hidimbi summons retain the nine-second lifetime and collision-safe placement, and award neither gold nor team score when defeated. Seven real unit assets and the four jungle courts are documented in [MINIONS_AND_JUNGLE.md](MINIONS_AND_JUNGLE.md); their current technical/native evidence is separate from human art approval.

Integration acceptance belongs to simulation/network/browser reports. Required follow-up balance evidence includes completed matches across team compositions, damage and objective contribution by role, shield/heal uptime, summon impact, map-side bias and human reports on readability. Bot completion or a passing typecheck cannot establish competitive balance. No human playtest or cultural-consultation result is claimed here.

The later [all-roster mechanics review](ROSTER_MECHANICS_REVIEW.md) rereads all42 effective skills and counters, records actual model heights/shared hit volumes, verifies all14 GLB hashes/126 required clips and identifies three presentation repairs: depleted-shield visibility, reconnect cast-slot selection and authoritative full-body timed-R playback. Seven new playback-policy tests pass; actual Rama/Hanuman/Sita body/pose acceptance remains a separate native gate. This pass changes no hero health, damage, speed or cooldown to flatten the earlier AI results.

## Optional guide and Practice focus

[shared/hero-guide.ts](../shared/hero-guide.ts) now supplies all fourteen heroes with a first useful action, positioning, three current ability notes, counterplay and Power/Vitality/Tempo tradeoffs. Independent source review compared all 42 notes with the actual simulator; exact roster/name checks, typecheck and lint passed. These are intended choices to try, not optimal-build or human balance claims. The selected hero's first action is shown directly, while the longer guide is optional.

The guide preserves the actual upgrade distinctions: Power adds 17% of base primary damage and 12% of ability payload per rank where that branch consumes power; Vitality adds 65 maximum/current health; Tempo divides the primary interval by `1 + 0.12 × rank`. Tempo does not shorten skill cooldowns. Upgrades have three ranks and cost 120/100/140 times the next rank respectively, bought while alive near the player's own spawn. Range, duration, summon lifetime and movement distance are not secretly upgraded.

[client/practice-goals.ts](../client/practice-goals.ts) offers five optional observations: reach a point 12 metres from the attempt's start, land an authoritative hit, start an accepted ability, buy a rank, or earn actual camp credits/blessing. Free play is the default. An accepted windup can count as starting an ability even if later interrupted; a camp goal is not proof that the player personally landed the final hit. Goal receipts grant no currency or account power and make no mastery judgment. Pause/settings retain progress; dismissal hides it, and replay or a new attempt gets a fresh baseline. The hero-specific prose exercise is a suggestion rather than a second automated goal.

The new UI integration is under its own [three-round review](NEXT_PHASE_PANEL.md). Its native goal lifecycle/dismissal/paused-forge/online exclusion and mobile all14 first-actions/42 skill notes/forge labels passed focused checks. The replay-reset check deliberately used an eight-second Practice test fixture; the earlier native 480-second result remains a separate baseline. Final release acceptance is still open. All heroes and skills stay unlocked, without paid combat advantage, compulsory lessons or a claimed learning/health effect.

## Source ledger — passages actually read

Accessed 16 October 2026. The following are pinned GitHub mirrors of older English editions. Their value is traceable literary or historical context, not a claim that these translations represent all communities or current scholarship. No source prose, scanned artwork or third-party character models are bundled into the game.

### R1 — Ramayana, Griffith translation

[The Rámáyan of Válmíki, translated into English verse](https://github.com/GITenberg/The-R-m-yan-of-V-lm-ki-translated-into-English-verse_24869/blob/b48a7a226e8a20bed61131382aa5b8bf2206e039/24869-0.txt), Ralph T. H. Griffith, 1870–1874; Project Gutenberg text 24869. Pinned mirror commit `b48a7a226e8a20bed61131382aa5b8bf2206e039`; file SHA-256 `63f32651220b712149b6b497dbedeb692c098bf08ded21581617d452b84c6847`.

Read the title/contents and these selected passages:

- Book I, Janak's account of finding Sita while ploughing and the Mithila bow test; Canto LXVII, “The Breaking of the Bow” (mirror lines 8504–8618). This supports the Sita/Mithila/earth association and Rama's bow motif.
- Ravana's described arms and heads (lines 31085–31109). A ten-faceted crown is our readable visual abstraction, not an attempt to reproduce that passage literally.
- Book V, Canto I, “Hanumán's Leap” (lines 45405–45450). The leap and search for Sita inform movement and aid motifs; the arena heal and blast are inventions.
- Book VI, Canto LXXIV, “The Medicinal Herbs” (lines 55454–55590), additionally read for the expanded art/mechanics brief: Hanuman seeks medicinal plants and carries a mountain portion back to aid the wounded. This supplies a literary aid/mountain motif; the game's landing, damage, healing amounts and timing remain original.
- Book VI, Canto XV, “Indrajít's Speech” (lines 50065–50113), and the edition's Book VII summary on Meghanáda/Indrajit (lines 58666–58686 and 58760–58782). The summary supplies the “Roaring Cloud” name association. It is an editorial layer, not an independently checked Sanskrit critical text.

Older editorial interpretations elsewhere in this edition, including speculative solar-myth explanations, are not adopted as historical conclusions.

### M1 — Mahabharata, Ganguli translation, Adi Parva

[The Mahabharata of Krishna-Dwaipayana Vyasa — Adi Parva](https://github.com/GITenberg/The-Mahabharata-of-Krishna-Dwaipayana-Vyasa-Translated-into-English-Prose--13-Adi-Parva_7864/blob/f2f859e66ad29dce989b6cd14d15f31a34cfeed4/7864.txt), Kisari Mohan Ganguli, translation published 1883–1896; Project Gutenberg text 7864. Pinned mirror commit `f2f859e66ad29dce989b6cd14d15f31a34cfeed4`; file SHA-256 `7057fd0f93e93780a155188f3b30ebb41c3190e91d2b31940124eba981347110`.

Read the title/translator's preface and these selected passages:

- Sambhava Parva, sections CXXXVI–CXXXIX (lines 13610–13840): Bhima and Duryodhana's mace contest, Arjuna's bow demonstrations, and Karna's armour, earrings, challenge and association with Duryodhana. These inform weapon silhouettes and contrasts. Social hierarchy expressed in the old translation is not a character-stat or team rule.
- Hidimva-vadha Parva, section CLVII (lines 15340–15445): the female Hidimva offers protection and swift travel. The game uses the name Hidimbi to distinguish her from her brother in this translation. Forest shields and sentinels are our additions.
- Chaitraratha Parva, section CLXIX (lines 16275–16326): Draupadi/Panchali/Krishna's appearance in the sacrificial setting. This informs a restrained flame motif; it does not establish her arena shield, pull or heal as textual abilities.
- Haranaharana Parva, section CCXXIII (lines 20440–20510): Subhadra, her family relationships and Abhimanyu. The spear, command role, restorative circle and sentinels are original adaptation choices rather than powers established by this passage.
- Arjuna-vanavasa Parva, section CCXVI (lines 19864–19959), additionally read for Ulupi: her identification as Kauravya's naga daughter and association with the river/waters. Her control/support staff kit is original; the game's combat has no water invulnerability.
- Arjuna-vanavasa Parva, section CCXVII (lines 19961–20023), additionally read for Chitrangada: Chitravahana's named daughter and the dynastic arrangement. This passage does not itself establish the spear-duelist role; that is an original arena adaptation. Tagore's treatment and regional versions have not been read in this pass, and the literary Manipura is not asserted here as a settled modern geographic identification.

The mirror includes editorial use and attribution language in addition to the older text. This project uses source associations and original wording; it does not redistribute that electronic edition.

### A1 — Historical architectural reference

[History of Indian and Eastern Architecture](https://github.com/GITenberg/History-of-Indian-and-Eastern-Architecture_61178/blob/589a61bea768cec87738850395421a92d9bf56e2/61178-0.txt), James Fergusson, displayed London/John Murray edition 1891; Project Gutenberg text 61178. Pinned mirror commit `589a61bea768cec87738850395421a92d9bf56e2`; file SHA-256 `427ed50e6c2cb0733c4d1291ff69fa2cb08beac623bb29a4bdefb387382b00db`.

Read the title, transcriber note and selected preface material, then the Mahavellipore/Mamallapuram raths discussion (lines 12407–12512), including the caption for “Arjuna's Rath.” The useful visual observations are distinctions among roof profiles, rectangular cells, porticoes and entrances. This colonial-era account contains dated terminology and speculative chronology; those claims are not used as current archaeological authority. A monument's popular epic-associated name is not proof of a character's historical residence.

Sangam City combines original sandstone, modern and garden forms around three clear combat lanes. It is not a reconstruction of Mamallapuram or any other heritage site. Gateway masses, colonnade rhythms and open approaches can guide later visual study, while collision and sight lines remain the game's design constraints. Existing map geometry should not be described as a detailed architectural reconstruction.

### Additional environment reading

[ENVIRONMENT_MYTHOLOGY_RESEARCH.md](ENVIRONMENT_MYTHOLOGY_RESEARCH.md) records the later, bounded research-agent pass over the same pinned files: Ramayana Book II Canto VI on festal city lamps; Mahabharata Paushya III on the interpretation of light/dark weaving and a wheel; and selected courtyard, reservoir and observatory descriptions in Fergusson. It supplies exact lines, context and limits. These are motifs for an original civic space and match-time lighting, not evidence for a canonical eight-minute Yuga, a reconstructed sacred diagram or new hero powers. Its separate contemporary Reddit sample supplies competing source leads and preferences, not textual proof or cultural-consultation approval.

[LANKA_COAST_RESEARCH.md](LANKA_COAST_RESEARCH.md) adds selected Griffith passages describing Lanka's coastal city, gates and fortifications, with separate Pampa clear-water/reed passages. The west gate and shallow Reed Court compose those motifs into original Sangam City scenery. They are not a recovered Lanka site plan or a source-attested swamp. The additional three-community API attempts returned 403 before content collection: six requests, zero posts/comments, and no new community recommendation.

### Access and interpretation limits

Direct requests to the Project Gutenberg catalogue and the UNESCO Mamallapuram listing returned proxy HTTP 403 in this environment. The pinned mirror texts above were accessible and read; the UNESCO page was not read. No restriction was bypassed. Modern heritage guidance, regional versions and consultation with knowledgeable players remain future research.

Names such as Rama/Ram, Ravana/Ravan and Meghanada/Meghnad/Indrajit vary with language and edition. The displayed labels are stable game names. This pass did not read Kamban, Tulsidas, Madhusudan Dutt or a representative set of regional oral and devotional traditions, and therefore does not claim to resolve their differences. Hidimbi's local traditions also deserve a separate source pass before adding location-specific lore.

## What comes from a source, and what we invented

| Hero | Association used from the selected passages | Original game decisions |
| --- | --- | --- |
| Rama | Bow test and measured bow imagery, R1 | Aim/dash kit, Dawn Volley, all tuning and costume geometry |
| Ravana | Multiple heads/arms and command presence, R1 | Ten-faceted crown abstraction, chakram, shields, pull and nova |
| Arjuna | Archery demonstrations, M1 | Fan attack, dash, projectile timings and silhouette |
| Duryodhana | Mace contest, M1 | Defensive Vanguard role, allied ward and wave attack |
| Hanuman | Leap and aid/search mission, R1 | Healing circle, circular damage pulse and exact mobility limits |
| Karna | Bow challenge, armour/earrings and solar association, M1 | Timed ally shield and close solar blast |
| Bhima | Strength and mace contest, M1 | Leap, cone and circular damage kit |
| Meghnad | Indrajit/Meghanada naming and cloud association, R1 editorial summary | Visible slowing zone, dash and fan attack |
| Sita | Mithila and earth/plough association, R1 | Active protector role, staff, roots, healing and shielding |
| Draupadi | Sacrificial-setting appearance, M1 | Guardian role, flame staff, pull, shields and healing |
| Subhadra | Named epic character and family relationships, M1 | Field commander role, spear and temporary allied sentinels |
| Hidimbi | Protection and swift movement in the forest episode, M1 | Vanguard role, leaf mantle, spear, slowing zone and sentinels |
| Chitrangada | Named daughter of Chitravahana and dynastic setting, M1 CCXVII | Agile spear-duelist role, crossing dash, energy arc and allied ward |
| Ulupi | Naga lineage and water association, M1 CCXVI | Humanoid staff guardian, damaging pull, nearby heal and slowing basin |

These adaptations give women direct, mechanically useful roles rather than making them rescue objectives. That is an authored design choice, not a retroactive claim that the translations describe these kits. Hero GLBs use a licensed CC0 anatomical mesh, rig and weights with original proportions, costume, hair, weapons and authored motion; effects and city geometry are original runtime art. Religious identity, caste, language and skin tone do not determine a team's virtue or power.

Future lore should preserve that distinction: name the specific edition or regional source when making a textual claim, mark invented details as adaptation in the source notes, and keep actual ability descriptions focused on what players can do.
