# YUGA art production plan

Prepared 16 October 2026 from the existing source, manifests, generated reference sheets and saved actual renders. This is an artist-led production plan for **14 heroes, 7 unit models, 42 abilities and Sangam City**. The new illustrations below are concept art. The coordinator subsequently reopened the environment source for the user's day/night, lighting and circular-plaza request; that bounded implementation is recorded in section 6. The existing 21 GLBs remain unchanged. This document itself creates no new collision, ability, character model or finished video.

The intended result is a readable, expressive Indian-epic-inspired arena: individual adult faces and body proportions, purposeful cloth and weapon shapes, warm engraved metal against quieter fabric, and a city whose ancient and modern districts remain easy to navigate during combat. Competitive clarity takes priority over decorative detail. The current browser game is an original prototype; commercial-game fidelity and parity with the illustration remain unachieved goals.

## 1. Inspected reference hierarchy

| Reference | Use | Boundary |
| --- | --- | --- |
| [Lobby key art](../client/assets/confluence-keyart.png) | Golden late-afternoon city mood; depth, material separation and confident poses | Illustration, not runtime footage. Its central archer is not a reference for changing Sita's staff kit. |
| R1 · [Rama / Hanuman / Sita](../art/references/rama-hanuman-sita.png) | Primary costume/weapon reference for the first three production passes | Rama has bow/quiver, Hanuman mace/tail, Sita emerald/ivory layers and a leaf staff. |
| R2 · [Ravana / Meghnad / Karna](../art/references/ravana-meghnad-karna.png) | Crown, scarf, shoulder-disc and palette separation | Engraving is a visual motif, not permission to copy religious text or commercial assets. |
| R3 · [Arjuna / Bhima / Duryodhana](../art/references/arjuna-bhima-duryodhana.png) | Archer versus broad mace silhouettes and stance | Keep all three distinct from Rama/Hanuman rather than recolouring a shared outline. |
| R4 · [Draupadi / Subhadra / Hidimbi](../art/references/draupadi-subhadra-hidimbi.png) | Flame-staff, pennant-spear and broad leaf-mantle identities | Flame ornament does not add damage to Draupadi's support abilities. |
| R5 · [Chitrangada / Ulupi](../art/references/chitrangada-ulupi.png) | Copper/cream versus teal/jade fabric, hair and silhouette | The image gives Ulupi a hand-held ring; the implemented kit uses a **water-ring staff**. Preserve the staff. |
| [Hero art bible](../art/HERO_ART_BIBLE.md) | Detailed identity, material, rig and effect briefs | Some introductory baseline prose predates the actual GLBs. Use the current manifests and captures for present implementation status. |

All five roster sheets and the lobby image were opened for this plan. They cover all fourteen reference identities. The anatomical foundation is the pinned MakeHuman CC0 data; costume/weapon additions, motions and generated concept work are separately authored and recorded in [provenance](REUSE_LEDGER.md). Generated illustration is neither historical costume evidence nor a recovered commercial asset.

### New production boards, inspected in this pass

The coordinator generated these original images using the existing YUGA references. Originals remain in `/workspace/generated_images`; repository copies are the review targets. None has replaced a GLB, animation clip or gameplay screenshot.

| Board | Accepted art direction | Corrections before implementation |
| --- | --- | --- |
| [Priority model direction](../art/production-concepts/priority-model-direction.png) | Front/rear costume separation; Rama's asymmetric drape, Hanuman's broad fur/tail outline, Sita's braid and staff; material swatches | The bottom strip repeats trio views, not fourteen different heroes. Generated epithets differ from the game and are not approved UI copy. Tiny jewellery and weave must become selective detail, not high-frequency noise on every surface. |
| [Priority ability storyboard](../art/production-concepts/priority-ability-storyboard.png) | Prepare/release/resolve rhythm; low effects that leave targets visible; clear change from attack to recovery | Rama's actual volley is a **horizontal yaw fan at 0 and ±0.12 radians**, although the drawing separates arrows vertically. Hanuman's debris is cosmetic, with no new crater/collision or extra hits. Only eligible allies receive healing. Sita's sanctuary remains fixed at the accepted origin for six seconds after release, even if she leaves. |
| [Sangam City direction](../art/production-concepts/sangam-city-direction.png) | Honey stone, warm grazing light, teal metro/glass, varied skyline and a clear central view | The overhead illustration invents waterways and route shapes. It is a mood board, not a replacement for `shared/map.ts`, the eight solids or the four camp coordinates. Decorative balconies, trains, stairs and trees do not become traversable routes or ground cover. |

Board SHA-256 values:

- Model direction: `af7e445e93392daaf377eca301466b01a3949403d54998d277ffb2f87035a1bb`.
- Ability storyboard: `51cdc878a0e96796d2446593f123aaf0b37ab2fcd61e9fa2a5ccb5bc5ce605dd`.
- City direction: `11e757e42af1e4163e85964c603d6c955935c92431657a005f995a33acf6e0b6`.

## 2. Present assets and observed gaps

The [hero manifest](../art/hero-assets.json) contains fourteen actual skinned GLBs: **46,520,992 bytes**, 47,648–52,548 triangles each, 9–10 material sections and 163–164 joints. Every hero has `idle`, `run`, `fire`, `cast`, `cast1`, `cast2`, `cast3`, `jump`, `defeat`. The [unit manifest](../art/unit-assets.json) contains seven actual skinned GLBs: **4,477,524 bytes**, 7,400–10,000 triangles each, four materials, eighty joints and `idle`, `run`, `fire`, `defeat`. These are measured inventory values, not a mobile performance guarantee. The actual total is 50,998,516 bytes before other client resources.

The hero and unit loaders already instantiate independent skins and layer locomotion/actions. The city is authored runtime geometry with shared textures/materials. Most effects are reusable geometric projectiles, contours and pulses; the three special R preparations additionally use authoritative `Actor.cast` data. There is no verified finished cloth simulation, facial-performance system or whole-roster LOD pipeline.

| Observed evidence | Finding | Production response |
| --- | --- | --- |
| [Rama](../art/previews/rama-actual-model.png), [Hanuman](../art/previews/hanuman-actual-model.png), [Sita](../art/previews/sita-actual-model.png) actual-model renders versus R1 | The current trio shares a similar flat front panel, cape and tied hair mass. Their outlines and facial/material treatment remain much simpler than the references. | Resolve large cloth volumes, individual head/hair proportions and shoulder/waist shapes before adding engraving. Keep Rama/Hanuman/Sita as the proving set. |
| [Actual Rama gallery](evidence/final-hero-rama-gallery.png) | The loaded model is visible with real controls, but the full-body scale leaves limited face/hand detail in one frame. | Capture a close neutral-lit face/grip view plus the existing gameplay-size view; neither substitutes for the other. |
| [Production arena](evidence/jungle-production-arena-root.png) | Ancient and modern blocks are differentiated, but large facade planes are flat and bright environmental rings compete with combat markers. | Apply a small shared facade-material pass and reduce environmental inlay emission. Preserve readable hero/reticle contrast. |
| [King model](../art/previews/units/king-actual-model.png), [watch fixture](evidence/jungle-unit-city-watch-fire.png) | Crown/standard identify the king in close view. Several fixture units occupy only roughly 40–60 pixels vertically, and the watch is partly hidden by Rama. | Keep the true gameplay-scale shot, add an unobstructed three-quarter contact view, and do not certify grip quality from the obscured frame. |
| [Actual Yaksha encounter](evidence/jungle-native-yaksha-aggro.png), [mobile reward fixture](evidence/jungle-fixture-mobile-reward-components.png) | The guardian/court and reward components are present and readable in these frames. Still images cannot prove full animation continuity or first-time comprehension. | Retain native encounter footage, label fixture footage, and test recognition with an observer after technical capture. |

These are file-based observations requested for this planning pass. No new browser interaction or performance measurement was performed. Existing QA remains the authority for the scope of prior native tests.

## 3. Fourteen-hero production register

Each linked GLB exists now. Each row's next deliverable is **one four-view actual-model contact sheet** (front, profile, rear, weapon-contact pose) plus **one approximately fifteen-second actual 3D motion chapter**. That is fourteen contact sheets and fourteen chapters, not fourteen new generated illustrations. A model revision is accepted only after its source, manifest hash, all nine clips and independent-instance checks are refreshed. Priority trio revisions precede any full-roster propagation.

| Hero / present GLB | Reference | Visual goal and highest-value correction | Motion/contact emphasis |
| --- | --- | --- | --- |
| [Rama](../client/assets/heroes/rama.glb) | R1 | Lean archer; asymmetric lapis drape, shaped dark hair, high quiver, quiet ivory folds; face and bow lead the eye | String/nock/draw-hand contact, shoulder clearance, purposeful held R draw |
| [Hanuman](../client/assets/heroes/hanuman.glb) | R1 | Broad adult vanara anatomy, expressive muzzle/brow, auburn fur planes, red/saffron fabric, tail arc distinct from cape | Weight under mace; compression/travel/landing; tail never blocks reticle |
| [Sita](../client/assets/heroes/sita.glb) | R1 | Assured adult face, emerald/ivory layered garment, controlled braid, leaf-crowned staff | Free-hand intention, staff grip, mobile hem coverage, fixed sanctuary; inspect known defeat hem/prop floor clipping |
| [Ravana](../client/assets/heroes/ravana.glb) | R2 | Broad commanding torso, dark-red layers, ten-faceted crown silhouette and clear ring blade | Upright guard versus inward pull; halo stays outside aim corridor |
| [Arjuna](../client/assets/heroes/arjuna.glb) | R3 | Narrower alert archer; split scarf and high quiver distinguish rear view from Rama | Brisk compact draw and lateral-looking footwork without changing forward-dash authority |
| [Duryodhana](../client/assets/heroes/duryodhana.glb) | R3 | Square shoulders, bronze/maroon plate over cloth, low crown, stable hips | Low brace and broad mace sweep; distinguish from Bhima's loose weight |
| [Karna](../client/assets/heroes/karna.glb) | R2 | Solar shoulder discs, ivory/saffron panels, heavier face planes and bow | Deliberate release; compact guard gesture; restrained radial flare |
| [Bhima](../client/assets/heroes/bhima.glb) | R3 | Broadest torso, forest-green straps/wraps, strong hands, long-headed mace | Weight transfer through stride, two-hand sweep, clear foot plant |
| [Meghnad](../client/assets/heroes/meghnad.glb) | R2 | Narrow forked crest, violet/ink scarf and compact bow; sharper angled stance | Quick direction change; cloud effects remain low and transparent |
| [Draupadi](../client/assets/heroes/draupadi.glb) | R4 | Wine/ivory layers, five-point clasp, distinct braid and flame staff | Firm staff plant and expressive open hand; support effects do not imply fire damage |
| [Subhadra](../client/assets/heroes/subhadra.glb) | R4 | Teal/cream commander, readable side braid and pennant spear | High rally signal; paired summon marks match actual temporary units |
| [Hidimbi](../client/assets/heroes/hidimbi.glb) | R4 | Broad moss/bark mantle made of layered planes, forked spear, strong grounded stance | Mantle weight, protective sweep and owner-specific summoned-unit motif |
| [Chitrangada](../client/assets/heroes/chitrangada.glb) | R5 | Copper/cream duelist, short segmented mantle and visible hip movement | Precise forward crossing step, spear arc and ready defensive stance |
| [Ulupi](../client/assets/heroes/ulupi.glb) | R5 plus staff contract | Teal/jade guardian, wave crest and scale-edged collar; ring becomes staff head | Flowing arm path with planted feet; no slither, flight or swimming system |

Shared art constraints: distinguish faces and hair rather than applying one head recolour; preserve adult agency and clothing coverage in all clips; use nonmetallic skin/cloth and selective gold; expose hands/weapon contact; keep the existing body hit volume and camera corridor. Ornament extending beyond a collider must read as ornament. Team identity remains independent of costume and epic allegiance, using shape/mark/label as well as hue.

## 4. Seven-unit production register

Each existing unit receives one four-state contact sheet and an approximately eight-second actual-model chapter: idle, run, attack, late defeat. Lane defeats must also be shown once from a fresh authoritative defeat event, because a staged zero-health pose alone does not prove the removed-minion lifecycle. Keep repeated lane units simpler than heroes.

| Unit / present GLB | Role and art goal | Specific acceptance shot |
| --- | --- | --- |
| [Soldier](../client/assets/units/soldier.glb) | Narrow helmet, spear/shield uniform; crisp marching rank | Unobstructed spear/hand contact, advancing legs under repeated fire |
| [City Watch](../client/assets/units/city-watch.glb) | Compact civic uniform, distinct held ranged implement and support hand | Both wrists visible in three-quarter fire; normal play-distance silhouette |
| [Minister](../client/assets/units/minister.glb) | Tall collar and scroll/seal gesture; rally mark distinct from projectile | Scroll grip and small shield pulse on eligible lane allies, not heroes |
| [King](../client/assets/units/king.glb) | Crown/standard and heavier ceremonial silhouette; no new throne/cart collider | Slow, deliberate attack and standard clear from hero crown shapes |
| [Grove Yaksha](../client/assets/units/yaksha.glb) | Broad grounded woodland guardian, branch/stone motifs and heavy club | Native aggro→return→reset and clear→reward→respawn; Vigor identity |
| [Reed Naga](../client/assets/units/naga.glb) | Grounded humanoid with hood/tail silhouette and reed/water motifs | Idle/attack/defeat at both reed courts; no implied snake locomotion; Ward identity |
| [Cloudwing](../client/assets/units/sky-sentinel.glb) | Grounded avian guardian, folded wings/crest, light silhouette | Arms/wing pieces clear through fire and run; no implied flight; Haste identity |

Subhadra and Hidimbi summons reuse existing unit assets with owner/expiry presentation; they are not additional unlisted models. Current lane ground radius remains 0.42 m, neutral body radius 0.8 m. A visually wider standard, feather or tail must not promise extra collision. Neutral markers retain their own diamond/state vocabulary rather than borrowing a team colour alone.

## 5. Forty-two ability delivery register

Present assets for every row are the hero's real `cast1`, `cast2` or `cast3` clip, its current [ability definition](../shared/heroes.ts), and the original [world effect renderer](../client/world.ts). The three named timed mechanics also use [cast-effects.ts](../client/cast-effects.ts). This register defines targeted refinement and capture, not forty-two new mechanics. Immediate abilities must not acquire a cosmetic windup that suggests a gameplay delay.

Every row receives **one three-beat card** (accepted/committed state, action/release, result/expiry) and **one actual arena clip**, generally six seconds; extend timed fields until expiry and summons through their nine-second lifetime. These form forty-two cards and forty-two labelled clips. A gallery motion does not demonstrate an ability effect. `Q/E/R` maps to `cast1/2/3` respectively. All contours, target centres, teams, accepted timestamps and hit/expiry cues come from authority.

| ID | Hero / slot / current ability | Current kind | Art target for the card and clip |
| --- | --- | --- | --- |
| FX01 | Rama Q · Steady Arrow | bolt | One narrow cyan/gold shaft, clean cover impact, restrained draw recovery |
| FX02 | Rama E · Measured Step | dash | Short cloth streak and clear foot plant; no damaging trail or endpoint blast |
| FX03 | Rama R · Dawn Volley | line; dawn-volley | Actual 1 s brace, three horizontal directions 0/±0.12 rad, separate projectile impacts; show a cover counterexample |
| FX04 | Ravana Q · Tenfold Guard | ward | Ten-facet shield motif, close allied application, expiry without an invulnerability promise |
| FX05 | Ravana E · Commanding Circle | pull | Low inward strands toward the accepted point; no stun icon or opaque vortex |
| FX06 | Ravana R · Crownfire | nova | One low circular impact, crown flare and mantle recovery; no ten-hit implication |
| FX07 | Arjuna Q · Converging Volley | burst | Readable forward fan and quick release; cosmetic arrows do not imply separate hit accounting |
| FX08 | Arjuna E · New Angle | dash | Split-scarf trail and balanced stop; actual travel remains forward |
| FX09 | Arjuna R · One Clear Line | line | Single fast bright arrow and cover contact; no beam or piercing promise |
| FX10 | Duryodhana Q · Mace Shock | burst | Short low forward shock fan with weighted shoulder recovery |
| FX11 | Duryodhana E · Hold the Ground | ward | Compact braced plates on affected allies; no root/immovable promise |
| FX12 | Duryodhana R · Iron Crescent | cone | Broad crescent edge, one sweep and controlled mace follow-through |
| FX13 | Hanuman Q · Windward Leap | leap | Body/scarf/tail travel with light foot dust; no landing damage |
| FX14 | Hanuman E · Bring Them Home | heal | Warm-green recovery marks on actual healed allies; small open-hand gesture |
| FX15 | Hanuman R · Mountain Pulse | nova; mountain-descent | 0.7 s preparation, 0.45 s real arc, landing-only 7 m contour; distinct hostile impact and allied recovery |
| FX16 | Karna Q · Sunshaft | line | Thin hot-gold shot with one contact; no persistent damaging light beam |
| FX17 | Karna E · Borrowed Dawn | ward | Shoulder-disc gesture and brief warm shield facets |
| FX18 | Karna R · Solar Reprisal | nova | Close low radial flare centred on caster, visible opponents beyond it |
| FX19 | Bhima Q · Heavy Sweep | cone | Weighty two-hand arc and sparse dust confined to the forward wedge |
| FX20 | Bhima E · Closing Stride | leap | Strong compression, clear motion, heavy but nondamaging footfall |
| FX21 | Bhima R · Thunder at Your Feet | nova | One broad ground pulse; transient stones do not add obstacles |
| FX22 | Meghnad Q · Cloud Snare | slow | Cloud-edged ground boundary with sparse wisps; no vision-blocking fog |
| FX23 | Meghnad E · Storm Step | dash | Thin violet scarf streak ending at destination; no stealth/haste implication |
| FX24 | Meghnad R · Gathered Squall | burst | Long forward gust fan and short cloth settle, no global storm |
| FX25 | Sita Q · Grove Renewal | heal | Compact five-leaf circle and gentle allied recovery, no enemy hit cue |
| FX26 | Sita E · Rooted Path | slow | Shallow root tracery inside actual area; no solid roots or immobilisation promise |
| FX27 | Sita R · Shelter of Mithila | ward; mithila-sanctuary | 0.8 s preparation, fixed 8 m field for 6 s, initial shield then periodic recovery; caster visibly leaves while field stays |
| FX28 | Draupadi Q · Circle of Resolve | ward | Five-point shield motif with clear allied application and fade |
| FX29 | Draupadi E · Stand Accountable | pull | Inward ribbons and one contact, with cover-limited displacement |
| FX30 | Draupadi R · Unbroken Assembly | heal | Broad nearby recovery and resolute pose; decorative flame motif never reads as hostile damage |
| FX31 | Subhadra Q · Signal Lance | bolt | One teal/gold spear-point projectile and small clean contact |
| FX32 | Subhadra E · Rally Close | heal | Brief pennant signal, close recovery circle and cloth settle |
| FX33 | Subhadra R · Twin Standards | summon | Two distinct spawn marks and temporary banner units; show true nine-second expiry |
| FX34 | Hidimbi Q · Forest Boundary | slow | Sparse leaf/branch traces with clear damaging/slow boundary; nonsolid roots |
| FX35 | Hidimbi E · Canopy Guard | ward | Leaf-edged shield accents, distinct from a full canopy or damage zone |
| FX36 | Hidimbi R · Grove Watch | summon | Two owner-specific leaf crests and temporary sentinels; show actual expiry |
| FX37 | Chitrangada Q · Crossing Step | dash | Precise copper lunge trail and stable stop; no endpoint hit |
| FX38 | Chitrangada E · Spear Arc | cone | Narrow forward crescent and immediate spear-ready recovery |
| FX39 | Chitrangada R · Defender's Vow | ward | Strong close shield facets and four-second visual expiry |
| FX40 | Ulupi Q · River Draw | pull | Low inward water ribbons and visible destination; no permanent water surface |
| FX41 | Ulupi E · Cooling Current | heal | Small upward water-light strokes on affected allies |
| FX42 | Ulupi R · Naga Basin | slow | Broad 7 m ripple boundary, six-second drain/expiry; no swimming, drowning or terrain change |

Visual priority order is danger boundary/release, reticle/eligible target, actor/team/neutral identity, then rewards and decoration. Hostile triangles and friendly bars/marks must survive reduced motion and colour loss. Never hide an enemy behind an opaque spell volume. Do not inflate an effect past its actual radius to make a trailer more dramatic.

## 6. Sangam City area register

The [shared map](../shared/map.ts) is authoritative: 140×170 m arena, lane axes x = −40/0/+40, eight solids, flat gameplay ground. The [scenery](../client/scenery.ts) supplies material/architecture and [jungle view](../client/jungle-view.ts) supplies camp/shard state. Distances and routes below are current source facts, not measurements inferred from the generated overhead art.

| Area | Present assets / geometry | Art goal | Finite delivery |
| --- | --- | --- | --- |
| Ghat promenade, x≈−40 | Sandstone solids, colonnade motifs, west boundary steps/water | Honey stone courses, darker recessed planes, clear ancient district silhouette | One normal shoulder-view before/after pair and one six-second route shot |
| Temple avenue, x≈0 | Wide inlaid central lane, tower/core sightline, compass decorations | Quiet paving with a clear objective axis; combat marks brighter than inlays | One forward/reverse view pair and one six-second route shot |
| Metro gardens, x≈+40 | Glass blocks, terrace trees and distant skyline | Cool teal glass with restrained pane variation; visible building base and edges | One shoulder-view before/after pair and one six-second route shot |
| West Reed Court (−54,0) | Naga, flat authored court and exact state markers | Reed/water motif as surface pattern; neutral territory distinct from pickup | One idle/aggro/return/dead four-state card |
| Stone Grove (−20,0) | Yaksha, flat court, Vigor/health label | Broad stone/leaf identity, open attack/retreat view | One native encounter clip plus four-state card |
| Sky Garden (+20,0) | Cloudwing, flat court, Haste identity | Air/feather surface motif with grounded enemy silhouette | One idle/aggro/return/dead four-state card |
| East Reed Court (+54,0) | Second Naga court | Same mechanical language as west, adapted to modern-material surroundings | One mirrored route/court comparison card |
| Sun/Moon bases | Forge/spawn motifs z=±69; hero entry z=±66; cores z=±72; tower lines z=±37 | Equal visual clarity from either team; no large props behind spawn camera | One paired spawn/forge/core-state card and two six-second shots |
| River edge and skyline | Out-of-bounds water/steps, far modern silhouettes, end gates | Strong distant city identity without false entrances or playable height | One overview shot and one annotated collision-boundary still |

No added ground-level tree, plinth, stair, wall, curb or market prop may occupy a passable route unless the shared gameplay contract changes deliberately. This pass does not change that contract. Decorative doors in solid facades must not advertise an accessible interior. Camp outlines remain exact and flat; growth of an ornamental grove must not hide a guardian or its retreat direction.

### Implemented environment expansion, browser review pending

The initial proposal was a material-only pass. The user's later request and coordinator's release explicitly expanded it to day/night, diyas/lanterns and circular visual routes. Source now includes two original shared 512×512 facade textures, a shared 512×512 twelve-spoke woven-plaza texture, a sparse cached star texture, five flat circular plaza surfaces, **24 wall-mounted diyas and 26 lanterns**. The existing boundary posts account for ten lanterns; sixteen more sit inside modern-building footprints. Flames/bowls remain inside sandstone footprints. No new collider, route height, visibility mechanic or map rule was added. The earlier material-only zero-geometry budget no longer describes this expanded scope.

The new [pure cycle sampler](../client/environment-cycle.ts) uses `snapshot.time` only: one 480-second cycle, with palette knots at dawn 0, day 120, dusk 240, night 320, predawn 400 and dawn 480. Invalid/negative clocks use zero; fixed Day samples 120 and fixed Night samples 320. The default is Cycle. The main settings owner exposes these cosmetic modes; they do not advance the simulation or alter target visibility rules. No-snapshot presentation uses the stable opening phase.

The world reuses its **two existing directional lights and single cached PBR environment atlas**. All ambient RGB channels stay at least 0.28, fill intensity at least 0.48; these are source guardrails, not a substitute for actual dark-scene inspection. Sky tint, fog, light colours and lamp emission update at most once per authoritative tenth-second. There are **zero point lights**, no added shadow map/light component, no runtime texture regeneration and no cycle-driven geometry/batch rebuild. The actual lanterns/diyas are emissive geometry; they do not cast individually simulated pools of local light. High quality adds the star overlay and existing directional shadows. Low quality and reduced motion disable flame-intensity variation. Reduced motion preserves the slow day/night palette; Fixed Day is available for consistent lighting.

Palette/intensity transitions are eased and continuous. Sun, moon and star opacity now uses smooth fades; entities disable only when fully transparent, with stars omitted on Low quality. Their positions are decorative rather than an astronomical simulation. The woven wheel is an original civic pattern; [environment source notes](ENVIRONMENT_MYTHOLOGY_RESEARCH.md) distinguish literary associations from canonical designs, chronology and live religious practice.

The first native four-frame review found a real presentation defect despite correct Night diagnostics: PlayCanvas's automatic skybox used the fixed environment atlas and painted over the authored dome. The repair excludes only that automatic layer from the gameplay camera, retaining the atlas for PBR assets. Cached architecture materials also receive a cooler, dimmer ambient/reflection contribution at night; hero materials and combat cues retain their existing readability. No atlas is regenerated, no per-update scene traversal occurs, and the same two-light budget remains. The replacement native low/high × day/night frames were inspected: the navy sky and cooler architecture visibly differ from day, while Rama, the reticle, team ring and structure cues remain readable at the tested spawn. This accepts those fixed-mode views, not a complete natural cycle or every distant combat situation. The first accepted build reported 14 scenery textures, 33 materials and 977 render components; these are construction counts, not draw calls, and precede the coastal extension below.

### Bounded coastal extension, native court review pending

The user's next request extends the western view with an original gold-and-terracotta coastal fort across the water: one gate centred at (−77,0), two adjacent turrets and two more skyline forms at (−85,±36). The closest solid extent remains west of −73.6, beyond the existing movement boundary. Gilded/turquoise bands on the four sandstone facades remain inside their shared solid footprints. The modern eastern half and all three lane routes remain intact.

A single original 512×512 water/mud/pad texture covers a 24×24 m shallow surface centred at (−55,0), at y=0.026 below the existing West Reed Court mosaic and danger/reward marks. Visible mud, ripple lines and the level mosaic communicate shallow wading ground. Six small reed clumps sit outside the western movement boundary; no opaque vegetation occupies the court or a walkable route. There is no depth, swimming, slow, damage, vision concealment or new collider. The high-quality star texture was tightened from soft large specks to small cached points; Low still omits it. Three additional shared materials and one texture are construction-time resources; the existing cached lighting loop also tints these environment materials at night.

[Lanka coastal source notes](LANKA_COAST_RESEARCH.md) distinguish literary gold gates/ramparts/turrets and turquoise courts from our invented layout and terracotta palette. Reed/sedge motifs come from a separate Pampā passage, so this is an original coastal wetland rather than a source-attested “Lanka swamp.” No historical reconstruction is claimed. Acceptance requires an actual playable court view around (−46,+5), looking west toward the guardian and gate, in day and night, with neutral identity, danger outline and any earned shard still readable. A labelled staged scene can supplement that evidence but cannot substitute for native gameplay footage.

Validation so far: **8 pure-cycle tests pass**, full YUGA TypeScript check and targeted ESLint pass. Independent source review checked resource ownership, reused light-colour updates, cached materials/textures and opaque prop bounds. Actual day/night low/high screenshots, rendering cost and native setting persistence remain the next browser gate. Existing `assetDiagnostics().lighting` reports mode, sampled state and construction counts; no new global production diagnostic API was introduced. Capture matching spawn/court views, preserve hero contour/reticle/hazard contrast, and record measured draw/frame/resource costs in the shared quiet browser window. Roll back a decorative change that impairs those cues.

## 7. Game-flow art delivery

Art supports the existing flow rather than replacing controls with decorative screens. UI implementation remains the coordinator's ownership.

1. **Lobby / hero choice:** concept art stays labelled; selected hero role, first useful action and weapon are clear. Use actual model preview for the chosen hero.
2. **Model inspection:** neutral lighting, front/rear rotation and motion buttons demonstrate the real loaded asset. Keep a short way back to play.
3. **Loading:** show honest model progress and cancellation. The 21-model payload is measured, so a new illustration must not imply instant entry or a reduced download.
4. **Spawn / first lane:** frame the actor below the aiming corridor, keep the lane objective visible, and make the three routes distinguishable without extra tutorial paragraphs.
5. **Fight / camp / reward:** preserve threat, neutral state and earned receipt priorities; show temporary power/expiry separately from an unclaimed shard.
6. **Finish / replay:** keep the result and explicit replay/leave choices clear; use a short actual highlight only when it does not delay leaving or pretend to measure mastery.

Deliver one six-step contact sheet using actual screenshots. It is not a claim of a complete accessibility audit. Contrast, keyboard/touch behavior, motion preference and observer comprehension need their own checks. [Design research](DESIGN_RESEARCH_NEXT.md) and [player feedback](research/DEADLOCK_PLAYER_FEEDBACK.md) motivate a single optional goal and recognizable cues, not compulsory practice or more simultaneous text.

## 8. Actual animated 3D reel plan

Coordinated with the audio/capture owner. Existing `ffmpeg`/`ffprobe` and Playwright recording can capture real PlayCanvas animation. No Blender rendering, browser capture or video encoding starts while QA owns the machine for public-release checks.

| Deliverable | Contents | Approximate duration / limit |
| --- | --- | --- |
| V1 · Priority highlight | Rama draw/release, Hanuman preparation/travel/landing, Sita sanctuary/application/leave; short ancient/modern route context | 60–90 s, default target 75 s |
| V2 · Hero chapters | Fourteen actual-model chapters covering stance, run, primary and three cast motions; selected jump/contact views | 14×about15 s; roughly3.5 min |
| V3 · Ability chapters | All FX01–FX42 in actual arena with accepted action, visible effect and result; longer fields/summons run through expiry | About4.5–5 min, never truncate a state merely to fit six seconds |
| V4 · Unit chapters | Seven actual models, idle/run/fire/defeat; separately identify staged displays and one genuine lane defeat/native camp sequence | 7×about8 s plus short native examples |
| V5 · Route chapter | Three lanes, two bases and one overview at player height where relevant | About36 s |

The complete review reel should stay around ten to twelve minutes, with chapter timestamps and individual clip files; the highlight is separate. Contact sheets cover fourteen heroes, seven units, forty-two abilities and the six-step flow. They are review artifacts, not substitutes for animated video.

Capture method and honesty:

- Begin with one single-browser 960×540 pilot and inspect the encoded file with `ffprobe`; expand resolution only after the pilot is usable. Record output dimensions, codec, duration and actual captured duplicate/changed frames. Encoded 30 fps does not prove 30 fps gameplay.
- Gallery footage is actual imported 3D motion but has no arena effects. Label it **model inspection**. Label test-harness arena setups **staged engine capture**; accepted actions should be processed by the original simulator rather than replacing animation with pictures.
- Keep native Practice/camp/online footage separately labelled. A staged visual setup is not evidence of earned kills, multiplayer latency or human balance.
- Preserve diagnostic records for source GLB/hash, skin identity, clip/state changes, accepted event/cast timing and no fallback. Use these alongside visible frames, not as a replacement for visual inspection.
- Avoid motion smoothing, optical-flow interpolation or speed changes in evidence masters. Edited trailers may cut between clips, with source timecodes retained. Never present an AI-generated video as a recording of the game.
- Capture original game audio only if the chosen path actually records it. Otherwise deliver a clearly labelled silent master; any later original soundtrack or cue dub is labelled separately and does not prove live audio behavior.
- Export a common H.264 MP4 review copy and retain the original capture plus a small JSON manifest of build/hash, shot, setup, resolution, capture path, timing and known issues. Keep large raw captures outside Git; publish selected reviewed exports through the coordinator's artifact path.

## 9. Finite production sequence and release gates

| Stage | Output | Exit condition |
| --- | --- | --- |
| A0 · Reference decision | Three generated boards above, this complete asset register and recorded mismatches | Board scope is explicit; all14/7/42 entries are covered; no concept is mislabelled as runtime |
| A1 · Baseline reel pilot | One short actual trio pilot with source/clip diagnostics | Real model/pose changes are visible, artifact decodes, no fallback; limitations documented |
| A2 · Environment expansion | Shared facade textures, five flat plazas, diyas/lanterns and deterministic cycle/fixed modes | Same collision/authority, bounded resources, low/high day/night readability and native settings accepted |
| A3 · Priority character refinement | Rama, Hanuman, Sita revised anatomy/cloth/hair/contact only where evidence justifies it | Four views, nine clips, grip/coverage/root-motion checks and actual shoulder-view combat pass before propagating |
| A4 · Roster and units | Eleven remaining identity refinements and seven role/contact reviews | Fourteen rear silhouettes and seven role silhouettes remain distinguishable at actual play distance; individual asset hashes/animations verified |
| A5 · Effects and flow | FX01–FX42 cards/clips and six-step actual flow sheet | Every cue matches authority; immediate versus timed actions, team, radius, movement, expiry and reduced motion remain truthful |
| A6 · Complete reel and validation | V1–V5, reviewed contact sheets and issue ledger | No hidden placeholders; effects and actors visible; no new resource leak or missing production asset; unresolved quality gaps named |

Art revisions do not get an automatic triangle/material increase: first spend the current budget on silhouette, folds and face/hand contact. A copied-asset offline optimization experiment may reduce unused data, but no blind whole-roster simplification is planned. The inspected simplifier does not evaluate skinned hand/face deformation; any candidate must pass the same clip/contact/loader checks. A one-frame development command capture can diagnose unexplained draw cost, while benchmark runs remain uninstrumented. No new runtime package or engine migration is required by this plan.

At each stage keep a short issue ledger: reference and actual image, asset/build hash, one visible problem, bounded correction, verification and remaining limitation. Technical validity is necessary; observer recognition and deliberate artistic judgement decide whether the result actually looks and plays better.
