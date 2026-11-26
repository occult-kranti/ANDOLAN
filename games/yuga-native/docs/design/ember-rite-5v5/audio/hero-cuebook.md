# Voices and weapons at the Ember courts

At the Bazaar entrance, Krishna's disc should be identifiable at the turn. Kali's blade should leave a gap that a teammate can hear. The audience can hear a feint at the next door and still trust the sound of a real quench. This cuebook gives the performers, sound editors and gameplay programmers a common set of events for those decisions.

The casting sheet contains one English take and one modern Hindi take per cue, with a speaker, trigger, audience and acting note. The ten Ember Rite concepts are Arjuna, Hanuman, Kali, Krishna, Durga, Karna, Shakuni, Ravana, Ghatotkacha and Draupadi. Rama has a separate eleventh entry in the balance plan. The Rust Confluence knockout build plays Hanuman and Rama. Krishna has a separate motion study. Shiva appears only in the fieldbook's motion appendix. The solo Ember rehearsal, the isolated Rust ritual and the private knockout rooms are distinct entry points. Source baseline `2acb45b3d61973a924fe5518c617e4fd2afb02d7`. [Bilingual casting sheet](hero-voice-lines.csv) · [Roster](../HEROES_AND_COLOR.md) · [Field profiles and scope IDs](../atlas/vertical-play/heroes.json) · [Private rooms and rehearsal](../../../../../yuga-rust/README.md)

## Giving the listener the right information

| Casting-sheet audience | Where the sound belongs | Caption example |
| --- | --- | --- |
| `self` | Owner's centered feedback for selection, a requested call preview or a personal resource. An opponent listening at the same spot gets no resource readout. | “One arrow recovered” |
| `team` | A team call the player chose or information the team is already entitled to receive. Play at comms level. Preserve the marker's authorized lifetime. | “Arjuna · Watch the crossing” |
| `recipient` | Private confirmation for the specific participant whose shield, link or health changed. Check the applied amount when reporting a benefit. | “Hanuman · Healed” |
| `local` | A spatial action the listener is allowed to perceive. Attach a draw to the hand, a public landing tell to the disclosed endpoint, a collision to the observed surface. | “Enemy disc returning · left” when both relation and direction are disclosed |
| `public` / `story` | The ritual authority announces an actual public transition once. A story editor can place a line in a named scene. | “Site B · Fire lit” with the site taken from the result |

Keep the same action onset, direction, range and apparent weight on both teams. For a disclosed boundary, give the friendly edge a rounded tap and the hostile edge a rasp of equal length and loudness. Pair the tap with the ally triangle and the rasp with the opponent brackets and text. Sun and Moon swap duties at halftime. Resolve allegiance for the **listener**, including when both teams have the same hero. An indistinct source can remain “footsteps” or “disc” until its owner is disclosed.

An eligible local listener gets the same cue and caption at the same time. Distance, occlusion, left/right and above/below follow the same permitted observation in stereo, mono and captions. Hand an occluded listener a coarse direction only if the audibility rule grants one. Keep an undisclosed point out of the audio event entirely. A muted player still sees the marked edge, call, cancellation and outcome. A scored pulse may duck under a tell. The gameplay transient and caption start on the event even between musical beats. Use one locale per performance. Leave silence under overlapping warnings and drop a late bark once the action has passed.

For the future network adapter, key each onset by round generation, cast, event sequence and, where present, projectile or recipient. A projected cursor, animation impact pose, count of visible meshes or incoming HP snapshot cannot create a hit. Release, wall impact, paid shield contact and health change have distinct meanings. On interruption close the tell. On death, disconnect, round change or reconnect discard retired one-shots and restore only the still-authorized field state. The existing ritual experiment consumes trusted observations. Server-issued per-listener events and this routing are production work. [Round authority and visibility](../ROUND_AND_TECH.md) · [Rust rules](../../../../../yuga-rust/src/ritual.rs)

## Recording palette

Ask for isolated instrument stems and close foley. The first transient tells a player what happened. A short musical answer gives the person behind it a voice. The following assignments are original to YUGA. Allen Roda's Met essay distinguishes Hindustani and Karnatak practice and describes each instrument's construction. A recorded musician can shape articulation and ornament in their own idiom. A programmed techno bass and clock can supply the electronic layer. Keep a synthesized study labelled as such. [Musical Instruments of the Indian Subcontinent](https://www.metmuseum.org/essays/musical-instruments-of-the-indian-subcontinent)

| Instrument or prop | Session request | Place in the mix |
| --- | --- | --- |
| Mridangam and pakhawaj | Record a short open stroke and a damped stroke on each barrel drum. Give the mridangam to Kali's rhythmic stops, the pakhawaj to Hanuman's wide, heavy arrivals. | Keep the skin contact in the midrange on both. Each phrase must read on a small speaker with the bass rolled off. |
| Tabla | Separate the high dayan taps from a single low bayan pressure bend. Record both without accompaniment. | Shakuni's selected face gets dry upper taps. The beat of the music may use the bass bend, outside the deception pattern. |
| Shehnai and shankh | Have the double-reed player articulate a brief swell for Durga. For the shankh, collect a single lip-blown conch onset and breath release from a consenting performer. A band-limited synthesized tone can stand in at the sketch stage. | Dress a ward with the reed. Reserve the conch's long rise for the briefing or story cut, clear of the accepted-ignition sound and ordinary character calls. [Met shankh, catalogued as *Sankh*](https://www.metmuseum.org/art/collection/search/502310) |
| Tanpura and plucked strings | Let the tanpura sound a quiet drone in score space. Ask the sitar and sarod players for a single pluck and a hand-damped tail. | The drone carries continuity through a menu or post-round pause. Arjuna's sitar is narrow and high, Karna's sarod slides under metal friction. Avoid aiming a drone at a hidden actor. |
| Bamboo flute, sarangi and vina | Record breath into a transverse bamboo flute, a short bowed sarangi swell and a low stopped vina pluck. | Give Krishna the breath, Draupadi the bow and Ravana the pluck. Close mics preserve onset before any room tail. |

For a recording pass, slate the casting-sheet ID, language and take. Keep dry dialogue, isolated instruments, props and room tone on separate tracks. Request a conversational and a projected read of each warning. Deliver the selected spoken take as a mono 48 kHz, 24-bit master with its natural ending and a marked first consonant for subtitle sync. Store the performer's credit, language, approved uses and recording date with the take. In the mix, start the nonverbal tell on the gameplay tick even when a long Hindi line needs more time to finish.

## Ten hero sessions

Times on the ten player cards are **field-study budgets** unless marked live. One tick is 50 ms. A note such as “80 ms tail” is an edit length and grants no windup, protection or recovery. Where the roster has only an ability description, follow its eventual begin, release, contact and end events. The numbers below for local cues describe playback after those events. [Ability concepts](../HEROES_AND_COLOR.md) · [Numerical field profiles](../atlas/vertical-play/hero-abilities.md)

### Arjuna · अर्जुन · `arjuna`

A precise observer with a small reserve of breath. Record the nock settling against wood, a drawn fibre creak and a high, damped sitar pluck. The bow has a narrow double click and a clean release. Rama's lower bow has a single, more hollow knock.

- **Gandiva Line** (`gandiva_line`). Start the scrape on the 0.40 s committed draw. Let the wood click through the pluck at release on tick 8. Carry the arrow hiss from the projectile until first contact or range. An observed cover hit gets a dry chip, a clean miss gets air fading. A defender at Dry Bank can leave the revealed line during the draw.
- **Side Step**, **Shared Sight** and **Sky Arc**. Track a short sole scuff to the collision-limited Step endpoint. Shared Sight earns one team click only when the specified visible mark is issued. Let the mark expire quietly. For Sky Arc, make the initial warning one rising string slide, then give each actual released arrow its own tick.
- **Call** on a confirmed Shared Sight mark. “There. Watch the crossing.” / “वहाँ। रास्ते पर नज़र रखो।”

### Hanuman · हनुमान · `hanuman`

Address the escort as an equal. Build weight from a leather grip shift, gada head ringing against a padded prop, a pakhawaj palm stroke and air passing the shoulder. Preserve space around his spoken invitation. Five guardian silhouettes resolve to one audible field.

- **Windward Vault** and **Protective Fan** are Ember concepts. Pan a single lifting breath with the body and close it on supported landing. Open the Fan with a hand strike and a brief outward scrape. An eligible ally hears their own shield receipt. The vertical lab's **Maruti Ribbon** (`vayu_flight`) has a 2.4 s thrust budget and a 4 m height cap. Fade upward thrust on a blocked ceiling. Place the final foot sound on actual grounded contact. The separate Confluence vault uses the timing below.
- **Vanara Sena** and **Mountain Pulse** have live Confluence rules. Expose a different tell for each. Sena gathers breath into one hand-drum slap at the field centre. Mountain Pulse has a broad descending stone scrape before one impact. Allow a defender to hear which marked patch to leave, and keep ally healing private to eligible listeners.
- **Call** at accepted Sena placement. “Friends! Stand with me!” / “साथियो! मेरे साथ खड़े रहो!” The optional follow-up “Steady. I've got you.” / “सँभलो। मैं यहीं हूँ।” belongs only to the aided teammate.

### Kali · काली · `kali`

Ask for poise and precise endings. Rub the flat of a safe metal prop with cloth for preparation. Layer a single clean metal sweep with a muted mridangam stroke and leave the recovery beat empty. Multiple arms describe one body.

- **Crescent Advance** (`crescent_advance`). Start the close cloth pull on commit and make the dry stroke the beginning of the 0.30 s lunge after its 0.25 s tell. Route one verified contact through the single swept hit volume. A blocked lunge closes with a flat clack. A defender can step away, take height or stand behind the hard edge.
- **Ash Veil**, **Break Step** and **Dance of Thresholds**. A short pour of dry grain opens the two-sided veil. Break Step has a lateral sole slide and the resolved endpoint. For the Dance, mark each disclosed arc with a short rim stroke, then a gap at its actual recovery. Distinguish its sequential arcs from Crescent's single volume. The rehearsal audition name `kali_tandava` is a sound sketch for this proposed dance. Keep the competitive call and caption under **Dance of Thresholds**.
- **Call** at the Dance tell. “Make room for my next step.” / “मेरे अगले क़दम को जगह दो।” On first-arc recovery the teammate can hear “Your turn. Go!” / “अब तुम्हारी बारी। बढ़ो!”

### Krishna · कृष्ण · `krishna`

Rest the voice between phrases. Pair a dry bamboo flute breath with a smooth spun-metal rim. Separate the musical breath that helps a teammate from the travelling disc that threatens a crossing. The Met's flute-playing figure is one specific Orissa sculpture. [Krishna Playing a Flute](https://www.metmuseum.org/art/collection/search/38422)

- **Sudarshana Return** (`sudarshana_return`) is a distinct vertical-lab action. Give its 0.25 s windup a fingertip rub. On release use a continuous rim tone going out and a pulsed rim tone coming back to the recorded release anchor. Place the change at the real turn. In a clear 12 m path that is 0.75 s after release. A wall ends the flight with a tap. A target can pay once across both legs. A second crossing by the same target gets no second paid-hit accent.
- **Guiding Note**, **Maya Screen**, **Echo Feint** and **Still Horizon**. One airy note opens the support pulse. The affected ally receives a separate soft exhale. A two-sided screen has a sustained breath at its disclosed edge. Echo Feint displaces a flutter to its authored point. Give the control field a low, slow two-note swell at the marked boundary, then an 80 ms dry cutoff at expiry. A screen opens an alternate route for either side. A feint has no target knowledge.
- **Call** on the disclosed disc release. “It comes back here.” / “चक्र यहीं लौटेगा।” A positive support receipt may prompt “Take a breath with me.” / “मेरे साथ एक साँस लो।”

### Durga · दुर्गा · `durga`

Steady enough for someone under pressure to follow. Couple a tap on stretched leather and a warm shehnai onset. Give the lion motif a gentle rasp as the ward opens. A scouting roar would suggest information the kit cannot supply.

- **Lion Ward** (`lion_ward`). Use two hand contacts to frame its 0.40 s formation. Start a narrow reed swell when the 2.6 m floor ring opens. The field lasts 3 s. Give an eligible ally one short private shield receipt per cast. The public ring has the same tail for an empty field and one with occupants.
- **Guard Sigil**, **Shelter** and **Aegis Circle**. Plant the detectable sigil with a brass pin and sound a separate clasp only on its real trigger for authorized listeners. Build Shelter's frontal face with a forward cloth pull and leave its exposed rear clear. For Aegis, use one reed swell followed by a hand-muted cutoff at expiry. An opponent can approach from the open angle or wait for closure.
- **Call** on opening Lion Ward. “Inside the ring!” / “घेरे में आओ!”

### Karna · कर्ण · `karna`

Give him the confidence of a player who has picked a difficult line and accepted the recovery. Rub two brass plates for a rising edge and lay a single low sarod slide under it. Leave the bow family to Arjuna and Rama.

- **Sun Lance** (`sun_lance`). Let a metal rasp rise over the 0.55 s commitment. Bring its second overtone forward with the final 0.20 s lane glint. A short metallic crack marks the actual release. The single bolt travels up to 32 m in 0.64 s. A covered observer hears only what their path permits. The shooter hears no contact embellishment for a bolt that ran out of range.
- **Solar Step**, **Sun Screen** and **Daybreak Line**. For Step, start an armor slide at departure and close it at the actual endpoint. A Screen unfolds like a single hinged plate in front of the caster. Daybreak uses the sustained brass edge at the selected line, a brief silence for the commitment and one reed-free strike at its delayed effect. Leave the side route conspicuously outside the zone.
- **Call** on the disclosed Daybreak tell. “Watch where the light falls.” / “देखो रोशनी कहाँ पड़ती है।”

### Shakuni · शकुनि · `shakuni`

Speak in plain hearing, with the clarity of someone who wants a witness to his choice. Roll two wooden dice onto cloth for the foley. Hand-stop one high tabla stroke. Keep the incidental rolling irregular and the selected face's sign deliberate.

- **Loaded Choice** (`loaded_choice`). The roster calls for a public choice of tools. The numerical study defines the **smoke face**. Give it one audible wood seat followed by an airy scrape during the 0.40 s base tell. The bilateral 2.8 m screen opens for 2.5 s. Other faces require an approved mechanic and readable tell before audio authoring.
- **Dice Smoke**, **False Trail** and **Clever Turn**. Smoke pours with a grainy roll at the selected boundary. False Trail plays a short prerecorded cadence of ordinary-class steps at chosen points with a soft rolling-die tail. Its endpoint and duration are fixed by the tool. Clever Turn keeps a dry die impact at the disclosed real origin before the area misdirection. An observer may check the base, take height or hold the other door. Preserve the same real objective cues throughout.
- **Call** on the publicly selected smoke face. “Smoke this time.” / “इस बार धुआँ।” The owner may hear “Let the steps echo over there.” / “उधर क़दमों की आहट गूँजे।” when False Trail is set. Hearing a footstep alone gives an opponent “Footsteps”. If the same listener can hear the die tail, add “Faint rattle” to the caption.

### Ravana · रावण · `ravana`

One speaker with the authority to reorganize a hall. Couple a low vina pluck with a wooden bolt sliding into stone. Keep his consonants centered. Additional crown forms can supply a brief harmonic tail attached to the same source.

- **Lanka Wall** (`lanka_wall`). Start the bolt sliding at commit. At 0.60 s a solid 3 m wall forms for both sides. A single deep knock marks its formation, a rough stone settle its removal after 3 s. Expose the two ends of the visible wall, keeping a clear exit. An invalid preview stays private to the caster. Only the accepted placement gets a world onset.
- **Crown Veil**, **Resonant Mark** and **Tenfold Array**. A descending cloth sound opens the veil. A low vibrating wood strip marks the real pressure zone. Use successive stopped vina attacks on the disclosed active segments of the Array and leave audible gaps between pulses. Ten faces make one cast, with no independent scanning voices, head positions or aim targets.
- **Call** on collision activation. “The wall stands.” / “दीवार खड़ी है।”

### Ghatotkacha · घटोत्कच · `ghatotkacha`

A quick wit in a large body. Let the landing feel substantial through sole-on-plank contact, granular stone and one short cavity resonance from a clay pot. Use the midrange ceramic knock for listeners whose device loses the low end. His ordinary floor steps carry the same information budget as everyone else's.

- **Night Vault** (`night_vault`). Give the valid endpoint a soft clay rim tap at the start of the 0.45 s tell. Source the 0.50 s travelling cloth from his body. Land with one grounded thud on accepted contact. Interrupting the cast removes the pending marker and its sound. A defender can guard the marked landing or leave it.
- **Grounded Rush**, **Stone Guard** and **Night Canopy**. Rush is a running cloth strain that stops on actual collision or completion. Place the guard's short scrape on its front face. For the Canopy, stretch canvas overhead and drop the shuffling tail as the openings settle. An enemy walking outside or hiding inside adds no signal to the structure.
- **Call** when the Vault endpoint is disclosed. “I'm landing there!” / “मैं वहाँ उतरूँगा!”

### Draupadi · द्रौपदी · `draupadi`

She makes plans while others are catching their breath. Pair a real thread drawn over a wooden spool with a short bowed sarangi swell. Separate the sound of tension in the tether from the private warmth of healing received.

- **Ember Thread** (`ember_thread`). Use a 0.35 s fibre draw. Open the one-second tether with the bowed swell. Each of its two pulses can restore up to 10 HP. Sound a private, soft double-string contact only for a positive pulse. Stop the strand on a genuine break in line, an excess of the 8 m range or a feet-height difference above 2.4 m. A distant spectator receives no patient beacon.
- **Clear Flame**, **Woven Ward** and **Sanctuary of Resolve**. Damp the bow with a fingertip on an actually removed status. An empty cleanse can give the owner a neutral action end. Tighten a cloth knot once as the Ward forms at its selected point. Give Sanctuary one open sarangi note at the marked area and a soft bow lift at expiry. Restoring health after a broken channel leaves the interrupted hold at zero.
- **Call** on a real link. “Keep hold of the thread.” / “डोर थामे रहो।” A severed link gets “The thread has parted.” / “डोर टूट गई।”

## Transferring the two playable kits

The Confluence browser already loads audio buffers. It dispatches Rama's draw and release sounds, a generic contact sound on an impact with receipts, Hanuman release sounds and a Mountain Pulse impact sound. Measured Step's recovered arrow currently produces a status message. The next table is the proposed sound edit against those actual gameplay actions. The Godot Rama audio subscriber is a separate offline reference for bounded voices and validated events. [Browser dispatch](../../../../../yuga-rust/web/main.ts) · [Hanuman authority](../../../../../yuga-rust/src/combat.rs) · [Rama authority](../../../../../yuga-rust/src/rama.rs) · [Godot subscriber](../../../../scripts/rama_action_audio.gd)

| Live action / control | Earliest accepted beats at 20 Hz | Sound edit and response |
| --- | --- | --- |
| Hanuman · Vajra Gada · LMB | 0.25 s tell, 0.30 s recovery | Grip creak into a short, centered metal sweep. Place body, shield or hard-surface contact according to the actual report. An empty arc ends on air. |
| Hanuman · Vajra Kavacha · Q | 0.35 s tell, eligible shield up to 3 s | Fan opens with a hand strike and cloth. An eligible caster or ally hears their own shield catch. A defender may use the open rear or take cover. |
| Hanuman · Maruti Udayana · E | 0.20 s tell, up to 0.45 s travel | Separate heel lift, moving breath and the real landing foot. The Rust kit currently emits an `impact` at release for movement acceptance. Use actual landing state or an explicit landing event for the thud. A shortened route must sound short. The rehearsal cue `hanuman_leap` is a local audition. |
| Hanuman · Lanka Dahan · C | 0.45 s to rear sweep, field active 2 s | Place a ribbon of crackle behind the actor, then keep the field at its authoritative origin. Read incoming damage from a recipient event, with one onset per exposure and a restrained sustain. |
| Hanuman · Mountain Pulse · X | Release at 0.70 s, impact at 1.15 s | Broad stone descent to the chosen patch, one drum-and-scree landing. An ally restored by the pulse hears an exhale. An opponent who moved outside can still hear the ground strike through the normal audible path. |
| Hanuman · Vanara Sena · V | Arrival at tick 12, caster recovery tick 20, field ends after tick 52's final payment | Fold five short breaths into one shared swell at the announced ground point. One landing per cast, followed by a quiet field bed. A visible wounded teammate within 3 m can receive up to 12 HP once on arrival. Exclude the caster. An opposing recipient can take 12 on arrival and 8/s during the two-second field. Never turn the forty field ticks into forty hit markers. |
| Rama · Kodanda · LMB | Authored 0.18 s draw releases on tick 4 at 0.20 s | One hollow nock, bow-wood tension, dry release, feather hiss. This is a travelled arrow. Stop the flight at the reported wall, unit or range with the matching tail. A range expiry carries no contact. |
| Rama · Piercing Dawn · Q | Release at 0.65 s | Stretch the lower bow resonance into a single dark scrape. Each actual paid contact can give its recipient a response. A hard wall cuts off the line. The shooter receives only the feedback allowed by the visibility policy. |
| Rama · Measured Step · E | 0.10 s tell, up to 4.5 m, final movement tick 7 at 0.35 s | Sole and sash follow actual movement. The owner hears a quiet quiver seat **only on `step_nock`** after a completed step of at least 3 m with room in the quiver. A wall-shortened step, full quiver or interrupt cannot mint this sound. |
| Rama · Guardian Circle · C | 0.55 s to field, active 4.5 s | Open with a hollow wood ring at the accepted ground point. Eligible allies hear the first shield catch and their own health response. Consolidate continuing recovery into a soft sustain. |
| Rama · Dawn Volley · X | 0.95 s draw, then three lanes staggered 0.10 s | Play one draw. Place the three separate releases at 0.95, 1.05 and 1.15 s if the authoritative projectile stages are reached. Track each arrow separately. Stop each on its first valid contact or wall. |
| Rama · Reload · R or empty primary | Completion after 32 ticks / 1.60 s | Bundle shafts with a brief scrape, then seat the quiver on the owner's completed reload transition. Cancel/reset suppresses that final accent if the completion does not occur. |

Rama · राम · `rama` is the additional ranged anchor. Have him address one nearby companion, even when his voice has to carry. His English/Hindi line on a confirmed Step return is “One arrow back.” / “एक तीर फिर तरकश में।” Arjuna's committed Gandiva draw, Hanuman's lab flight and the fiction-only cosmetics each have their own cues. [Rama kit](../../../../assets/design/rama-ability-kit.json) · [Hanuman kit](../../../../assets/design/hanuman-ability-kit.json) · [Sena profile](../../../../../yuga-rust/assets/vanara-sena.json) · [Field and cast milestones](../../vanara-sena-2026/ACTION_SCRIPT.md)

## Fire, deception and the announcer

The announcer leaves a short space after the official completion sound. Speak the chosen language once. Keep the score, site letter and timer on the HUD. “Yagna” is the requested English showcase spelling for the fictional ritual. Hindi uses यज्ञ. Its pronunciation and the word अग्नि can be recorded in normal contemporary speech.

| Audition name | When the line is allowed | English | Hindi |
| --- | --- | --- | --- |
| Yagna Ignited | Current-round ignition completes, after the 80th eligible hold tick | The ritual fire is lit. | यज्ञ की अग्नि जल उठी। |
| Fire Extinguished | A successful quench completes, after the 70th eligible hold tick | The fire is out. | अग्नि बुझ गई। |
| Agni Blessing | Optional future fiction or story-gallery audition on explicit selection | May the fire light your way. | अग्नि तुम्हारी राह रोशन करे। |

In the solo rehearsal, `kindle_start` and `quench_start` open an interruptible local hold. `cancel` releases its sound immediately. `kindled` and `quenched` correspond to the first two confirmed states above. `burned` and `expired` have their own results. An Agni Blessing audition has no dispatch from a round, healing receipt, score or timed buff. The optional guide voices and the hero casting sheet have separate recording status. [Rehearsal state changes](../atlas/rehearsal/engine.mjs) · [Original fiction and voice direction](../STORY.md)

| Test case | What each listener must be able to hear or read |
| --- | --- |
| A defender taps quench and releases at tick 69 | A listener authorized to hear the real tap gets the channel onset, then the cutoff. Both teams keep the already public fire state and timer. The quench ending and “The fire is out” belong only to a later successful hold. |
| False Trail crosses the opposite doorway while Krishna sends Echo Feint | Use the chosen path and the displaced flutter. Caption each perceptible layer, including the faint rattle when audible. A listener with only the step or flutter gets “Footsteps” or “Flutter”. Identification, actor counts, carrier identity, damage, drop, rescue, plant and quench confirmations come only from their corresponding game events. A decoy never calls the announcer or copies a completion timbre. |
| Sena lands while two players hide behind cover | The disclosed 3 m field can be heard forming once. Hidden bodies neither steer nor multiply its swells. A cleared listener may hear their own benefit or harm. Public expiry uses the same sound for occupied and empty circles. |
| A Krishna disc passes the same player twice | A return tick changes the directional texture even on a miss. Pay and accent at most one hit per target and cast. A different target can receive a first hit on the return. An earlier wall impact removes both the hidden contact and the later return. |
| A flank, a wall and two copies of one hero coincide | Mirror Sun and Moon listening seats. Repeat with captions only and in mono. Check that a listener can name the side of the *disclosed* risk, take a surviving route, and distinguish a true completion from an interrupted hold. Take the same seats through a stale packet and a reconnect. |

For a first comprehension session, audition the dry cue before playing the full mix. Ask the listener what happened, where they would move, and what the sound actually confirmed. Repeat the same crowded scene with music, voice and each supported locale. Record confusion pairs, especially Arjuna/Rama draws, Vault/Sena arrivals and feint/real hold. Accept roster VO after a Hindi-speaking director and the performers have heard the timed takes in context. The bilingual entries are original scripts. Instrument references, proposed timings and structural checks establish different things from a performance or a human listening result.

## Name and performance references

- For the casting room, start with **Arjun** (ar-jun), **Hanuman** (ha-nu-maan), **Kali** (kaa-lee), **Krishna** (krishn), **Durga** (dur-gaa), **Karna** (karṇ), **Shakuni** (sha-ku-ni), **Ravana** (raa-vaṇ), **Ghatotkacha** (gha-ṭot-kach), **Draupadi** (drau-pa-dee) and **Rama** (raam). These are prompts for Hindi dialogue. The aspirated *gh* is one onset, and *ṭ* and *ṇ* mark retroflex consonants. Let a speaker's own regional pronunciation guide the final take. Keep the project IDs and the Devanagari headings on each slate. [Project name register](../atlas/vertical-play/heroes.json)
- Ganguli's English *Mahabharata*, *Adi Parva*, connects Arjuna with Gandiva and Vasudeva with the discus, places Shakuni's dice play and Draupadi in the account of the hall, and names Ghatotkacha and Karna. The selected passages ground names and props. They supply none of the spoken lines above. [Bow and discus](https://github.com/GITenberg/The-Mahabharata-of-Krishna-Dwaipayana-Vyasa-Translated-into-English-Prose--13-Adi-Parva_7864/blob/f2f859e66ad29dce989b6cd14d15f31a34cfeed4/7864.txt#L20828-L20870) · [Dice hall](https://github.com/GITenberg/The-Mahabharata-of-Krishna-Dwaipayana-Vyasa-Translated-into-English-Prose--13-Adi-Parva_7864/blob/f2f859e66ad29dce989b6cd14d15f31a34cfeed4/7864.txt#L1186-L1204) · [Ghatotkacha and Karna](https://github.com/GITenberg/The-Mahabharata-of-Krishna-Dwaipayana-Vyasa-Translated-into-English-Prose--13-Adi-Parva_7864/blob/f2f859e66ad29dce989b6cd14d15f31a34cfeed4/7864.txt#L15474-L15490)
- The *Ramayana* and museum sources provide Rama's bow, Hanuman's purposeful leap and gathered Vanara companies. Rama and Ravana's encounter is also named in Ganguli's summary. The fictional ground field, aid amounts and the five simultaneous echoes are game decisions. [Hanuman passages and Rajasthan mountaintop object](../../vanara-sena-2026/SOURCES.md) · [Rama and Lakshmana at rest](https://www.metmuseum.org/art/collection/search/53684) · [Rama and Ravana in the epic summary](https://github.com/GITenberg/The-Mahabharata-of-Krishna-Dwaipayana-Vyasa-Translated-into-English-Prose--13-Adi-Parva_7864/blob/f2f859e66ad29dce989b6cd14d15f31a34cfeed4/7864.txt#L1304-L1311)
- The Met's Kolkata chromolithograph presents Kali as a protector. Its Nepalese Durga depicts the confrontation with Mahishasura. Its Chola *Shiva Nataraja* depicts Shiva dancing. “Kali's Tandava” is a showcase title here. Work with a cultural dramaturg and the performer on a specific dance vocabulary before attributing any form to a deity or tradition. Use original non-devotional text and commission the performers for the actual cues. [Kali, the wrathful protector](https://www.metmuseum.org/art/collection/search/849500) · [Durga](https://www.metmuseum.org/art/collection/search/38341) · [Shiva as Lord of Dance](https://www.metmuseum.org/art/collection/search/39329)
