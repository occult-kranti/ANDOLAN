# YUGA hero art bible

Production brief for fourteen playable heroes, forty-two abilities and lane units. Priority order: Rama, Hanuman, Sita; then the remaining roster. This document specifies work and acceptance criteria. Concept images, an anatomical base or a successful GLB import do not by themselves establish finished character quality.

## Visual reference and intended result

Inspected references supplied in this session:

- Original YUGA key art: `/workspace/generated_images/exec-571f2b18-3fcc-4603-8627-5889095d99c9.png`. SHA-256 `d5e7c51e3882abe14cca5b3f6ffd7b94c6433d7cdff702ae462037edc7433faa`.
- Rama / Hanuman / Sita sheet: `/workspace/generated_images/exec-57e6a947-9a10-4716-8e53-38bef217ee09.png`.
- Ravana / Meghnad / Karna sheet: `/workspace/generated_images/exec-2ae49956-83a6-4e69-bed0-b413820bfe92.png`.

The full-body sheets are the more specific costume references. In particular, Sita's sheet resolves her emerald/ivory clothing and leaf staff; the original poster's central archer supplied a quality and facial-expression reference, not a change to her staff kit. Later sheets should be recorded as actually inspected before being treated as production references.

The shared visual language is idealised adult anatomy, purposeful expressive faces, coherent hand grips, layered draped fabric, sculpted hair masses, warm engraved metal and restrained magical light. The desired detail is concentrated around the face, upper torso, weapon and garment silhouette. The poster's dramatic sunlight is presentation lighting, not a substitute for materials that remain readable under neutral daylight.

The current procedural rig in `client/world.ts` uses shared spherical heads/torso forms, capsule limbs, a rectangular eye mark and largely common cloth shapes. Its crests and weapons identify a prototype roster, but adding more jewellery to that construction will not produce the reference's anatomy or faces. Production replacements need continuous skinned surfaces, individual proportions, original facial shaping, fitted costume volumes and deliberate poses.

## Shared character construction

**Anatomy and face.** Build continuous shoulder/upper-arm, pelvis/thigh and neck/jaw transitions. Resolve clavicles, elbow direction, kneecaps and ankle taper without bodybuilder grooves on everyone. Every face needs eyelids surrounding actual eyes, a brow plane, nose bridge and nostrils, separated upper/lower lips, jaw and ears. Eyes must look toward the aim or interaction; a dark stripe across a sphere fails this requirement. Hands have five articulated fingers, a working thumb saddle and convincing grips. Broad proportions, age, face shape and posture distinguish the roster before costume colour is applied.

**Clothing.** Establish real attachment points: shoulder pin, wrapped waist, seam or belt. Broad folds follow gravity and movement; narrow trim follows those folds. Layer thickness appears at hems, cuffs and overlaps. Preserve coverage through crouching, running and casts; hidden anatomical faces may be removed under opaque clothing. Create fitted costume meshes and weights rather than relying on a body texture to suggest a garment. Jewellery rests against supported surfaces rather than floating above skin.

**Materials.** Skin and fabric are nonmetallic. Skin should have broad soft highlights; use restrained roughness variation, not a polished-plastic surface. Gold/brass uses metallic response and several roughness values across worn edges, recessed engraving and larger planes. Ivory cloth remains cloth, not white metal. Silk may have a smoother highlight than coarse wraps, but visible weave belongs primarily in close views. Hair uses sculpted strands/masses with limited cards where supported; fur has direction and colour variation. Use emissive only for gems, weapon energy and abilities. An entire glowing costume loses both material separation and team readability.

**Palette.** Use approximately 60% major fabric, 25% secondary cloth/armour, 10% skin/hair accents as composition permits, and at most a small final area of bright trim/emission; this is a composition guide, not a literal skin-coverage formula. Preserve the concept's warm metal against cooler cloth. The hero's `color`/`accent` fields identify UI and effect colour; they do not require every mesh surface to share one flat tint. Sun/Moon indicators remain separately readable by outline/ring/mark, not by recolouring a character's skin or equating a costume with moral allegiance.

**Scale and collision.** Use metres, feet at origin, Y-up after export and forward +Z in PlayCanvas. Target roughly 2.2 m overall including a modest crown; head/torso remain close to the existing 1.1 m hit centre. Height differences are visual adaptations, not assertions about epic characters' historical stature. Do not silently change collision to fit an ornament. Cloth, crown tips, tails and weapon flourishes can extend beyond the shared body volume but must remain visibly decorative. The camera's shoulder/aim corridor must stay open.

## Priority production briefs

### Rama — poised archer

- **Body and face:** lean athletic adult, long but grounded stance, clear clavicle and shoulder articulation, strong hands without oversized fists. Oval face with defined cheek plane, calm focused brows and a composed mouth; distinguish him from Arjuna's narrower, more alert face and Karna's heavier facial planes.
- **Silhouette and hair:** tall recurved bow, high quiver and asymmetric blue shoulder drape. Half-tied long dark hair with a shaped top knot and several controlled locks framing the face. Preserve a clear space between bow, face and drawing hand. A small blue-stone head ornament is sufficient; do not give all archers the same tall cone crown.
- **Costume and palette:** deep lapis `#214f9a`, ivory `#eee5d2`, warm gold `#c99a4c`, dark blue inner fabric and restrained cyan gem accents. Layer fitted bracers, one sculpted shoulder guard, tied chest straps, pleated lower wrap and split blue outer panels. Engraving is original leaf/curve geometry rather than copied sacred text. The sheet's sash has weight and a readable gold border.
- **Weapon:** a continuous curved bow with a plausible grip, flexible-looking limbs and a string attached to actual tips. Engraved surfaces support the silhouette; tiny perforations may be baked. Arrow and string follow the drawing fingers. The current game fires energy projectiles; animation should visibly release them from the bow rather than from a generic palm.
- **Rig and performance:** two-hand bow constraint, elbow pole targets, finger grip pose, upper-body aim layer and quiver clearance. Normal fire needs a short release/recovery that fits the authored 0.48 s interval. R adds the actual one-second held draw and three locked directions. A three-arrow image must resolve into three server projectiles, not a decorative cone that implies continuous area damage.
- **Acceptance:** neutral front/profile face looks adult and distinct; full draw does not collapse the shoulder or pass the string through the forearm; back-view running retains quiver/drape identity; arrow directions and cover impacts are readable at normal combat distance.

### Hanuman — powerful, expressive vanara ally

- **Body and face:** broad chest and upper back, strong forearms, weight-bearing feet and an upright heroic carriage with a flexible crouch. Sculpt a dignified vanara face with a coherent brow, short muzzle, cheeks, mobile lips and rounded ears. It must not read as a human head with a sphere attached to the nose. Express warmth in idle and concentration in the leap.
- **Silhouette and fur:** recognisable long arcing tail, wide shoulders, crown and heavy rounded mace. Fur follows cheeks, jaw, forearms, calves and tail; it should not hide the hands or facial expression. Use auburn/brown fur with lighter facial planes as the sheet suggests, avoiding a single orange plastic material.
- **Costume and palette:** crimson `#a9322f`, saffron `#dda22f`, aged gold `#c99445`, auburn `#8b4b2c` and cream facial highlights. Thick red shoulder cloth, pleated lower wraps, fitted bracers, belts and scaled jewellery create the sheet's layered weight. Crown fittings sit on the skull, clear of ear motion.
- **Weapon and rig:** separate mace mesh and hand socket, forearm twist, convincing fingers, toe/foot placement and a tail chain. The mace's centre of mass should affect the pose. Tail animation is bounded and does not masquerade as an attack or obscure the reticle. Fur and tail LOD should keep the outline without a heavy transparent-card cloud.
- **Performance:** athletic leap with hip compression, extended travel and controlled landing. Q remains movement only. R has an actual 0.7 s preparation, 0.45 s server-driven arc, then impact; its heal and damage happen at landing. A small mountain/herb motif can appear in R's energy crest, but no giant opaque boulder should hide opponents or imply new terrain collision.
- **Acceptance:** face reads in neutral light and three-quarter view; fingers securely grip the mace; tail survives turns without passing through torso/camera; body height visibly follows authoritative travel; the landing ring, hostile impact and allied recovery read as different cues.

### Sita — active protector of the grove

- **Body and face:** adult athletic support silhouette, stable feet and shoulders capable of wielding the staff. Use a distinct oval/heart-shaped face, strong brows, attentive eyes and assured expression. Preserve the sheet's poise and agency; idle and casts should show her making decisions and directing protection.
- **Silhouette and hair:** tall leaf-crowned staff on one side, a clear long braid/controlled waves on the other, compact seed/jewel headpiece and layered shoulder drape. Hair ornaments can suggest flowers in large readable clusters. Keep hair away from her aiming eye and staff grip.
- **Costume and palette:** emerald `#206d50`, warm ivory `#eee3c9`, muted gold `#c5a154`, leaf green `#80ad71` and a small luminous jade gem. Use a fitted upper layer, secure shoulder pieces, wrapped waist and split pleated skirt panels over a movement-compatible base. The cloth needs visible depth, folded edges and controlled translucency only at optional thin outer panels.
- **Weapon and hands:** a continuous wooden/gold staff with branching leaf forms and a contained green gem; no bow substitution. Give the staff a comfortable grip and actual shaft thickness. The free hand opens to direct a nearby heal or establish the sanctuary boundary; it should not remain a mitten fixed to her torso.
- **Rig and performance:** staff-hand constraint, expressive off-hand fingers, braid/hem chains and a broad grounded stance. Q draws a compact recovery circle around her; E directs a visible ground patch; R plants/raises the staff during the real 0.8 s preparation. The sanctuary remains at the cast origin when she moves away.
- **Acceptance:** cloth preserves coverage in run/crouch/turn; no elbow or wrist crushing; grove symbols remain legible without rendering an opaque tree in combat; the sanctuary's outer edge accurately shows its 8 m radius and six-second lifetime.

## Remaining eleven identities

These are production directions, not additional stat changes. Skin tones should vary naturally across the full roster without coding virtue, power or caste through colour.

| Hero | Anatomy, face and hair | Costume / material / palette | Essential silhouette and animation distinction |
| --- | --- | --- | --- |
| Ravana | Mature broad frame; angular jaw, prominent brows, shaped beard/moustache, long controlled hair | Crimson/near-black layers, substantial engraved gold, dark red gems; use the inspected sheet | Ten-faceted crown/halo abstraction and chakram. Upright commanding stance, deliberate open-hand pull; halo stays behind the head and is bounded for aiming. |
| Arjuna | Leaner and slightly narrower than Rama; alert face, sharper cheek line, high tied hair with short loose locks | Indigo/steel-blue, light ivory and restrained silver-gold; fitted archery protection | Long bow, high quiver and split scarf. Springy lateral footwork and compact draw, visibly quicker than Rama's held posture. |
| Duryodhana | Broad neck/chest, powerful hips; square jaw, firm mouth, short controlled hair | Bronze/brown, deep maroon and cream; substantial plate over textile | Squared shoulder guards, low crown, heavy rounded mace. Stable low centre of gravity; defensive brace and broad forward sweep. |
| Karna | Athletic heavy archer; strong cheek planes, clear nose bridge, wavy tied-back hair | Use inspected solar-gold/ivory/saffron sheet, dark under-armour, warm gem accents | Distinct radiant shoulder discs, fitted torso armour and large bow. Measured weight transfer; shield gesture stays compact and final burst opens outward. |
| Bhima | Largest barrel torso, thick limbs and broad hands; expressive broad face, substantial tied hair/beard | Deep forest green, bronze, weathered leather and ivory wraps | Crossed straps and long-headed mace. Weighty strides, large shoulder-led sweep, deep leap compression; avoid sharing Duryodhana's rigid guard pose. |
| Meghnad | Light, long-limbed archer; angular youthful adult face, narrow brows, swept/tied hair | Inspected violet/ink-blue sheet, cooler dark metal, small gold edges | Forked crest, compact bow and layered trailing scarf. Low angled stance, sharp direction changes, cloud-zone cast from the bow hand. |
| Draupadi | Upright athletic frame; strong expressive brows, individual cheek/lip shape, thick controlled braid | Wine/magenta, flame copper, ivory and dark woven fabric | Five-point clasp and flame-tipped staff. Firm planted stance and broad off-hand gestures; distinguish fiery material motifs from damaging fire mechanics she does not have. |
| Subhadra | Mobile athletic commander; rounded/defined cheek planes, alert eyes, side braid | Teal-blue, cream and brass with sturdy cloth panels | Spear pennant, rounded guards and asymmetrical braid. Quick rally gestures and a high signalling spear pose; summoned standards share her pennant motif. |
| Hidimbi | Tall broad guardian; confident face with pronounced cheek planes, thick braided crown | Moss/olive, bark brown, muted brass; layered leaf-shaped leather/cloth rather than a solid foliage ball | Broad mantle and forked spear. Wide stabilising steps, protective sweep of the mantle, grounded summon gesture. Nature identity does not require dehumanised facial caricature. |
| Chitrangada | Compact athletic duelist; defined brow/nose planes and focused expression, braided knot | Copper/terracotta, indigo undercloth, cream and warm brass | Short segmented mantle, crescent spear, visible hip mobility. Quick crossing step and precise sweep; shield stance keeps the spear ready. Her warrior kit is an original adaptation of the named character. |
| Ulupi | Slender but grounded guardian; calm direct gaze, distinct cheek/jaw structure, swept hair with an aquatic crest | Teal/deep petrol, pale jade, pearl and aged gold; scale texture as selected decorative edging | Wave crest, scale-edged collar and water-ring staff. Flowing arm paths with firm feet. Humanoid locomotion is retained; a snake body or swimming system is not implied. |

## Rig, import and animation delivery

Deliver a working glTF 2.0/GLB with one deforming armature, validated skin weights, metres/Y-up export and a neutral bind pose. Renderer motion is authoritative: no animation root motion should move the player. Socket mappings matter more than cosmetic bone names. The proposed generic mapping (`Hips/Spine/Chest/Neck/Head`, upper/lower arms/hands and thighs/shins/feet) may map directly to the MakeHuman names `root`, `spine01..05`, `head`, `upperarm01.*`, `lowerarm01.*`, `wrist.*`, `upperleg01.*`, `lowerleg01.*`, `foot.*`. Source skeleton names need not be renamed if tracks bind correctly.

Hand/weapon sockets, bow-string or staff constraints, fingers and forearm deformation are required for the model's actual poses. Hanuman additionally needs a tail chain; cloth/hair chains should be bounded and inexpensive. Preserve the existing collision/body centre and projectiles' authoritative aim even if a cosmetic muzzle socket is added. Large weapon offsets must not move hit detection through cover.

The initial engine clip contract is `idle`, `run`, `fire`, `cast`, `jump`, `defeat`, with in-place movement and tracks actually exported. Final-quality coverage needs directional locomotion/blending, an upper-body aim/fire layer, jump start/air/land, hit reaction, recovery/respawn and the three distinctive ultimate sequences. Shared locomotion can be retargeted; identical shoulders/hands/weapon timing across bows, maces and staffs is not acceptable. A decorative cast clip must not delay an immediate server effect. For ordinary abilities, a small pose anticipation may happen in the same event response, followed by recovery; only the three authoritative windups introduce actual preparation time.

### Asset budgets and honest stages

The renderer's first integration target is 15–30k triangles per hero, at most six material sections and a 1k atlas. The research agent has reported a MakeHuman CC0 visible base of approximately 26.8k triangles before original clothing; that is a usable anatomy starting point, not a finished hero. If costume/detail requires a higher source model, retopology and LOD are part of delivery. A provisional close-view LOD0 ceiling of 35–55k triangles is reasonable only after measured scene cost; the first gameplay/mobile LOD should return to the smaller target. The budgets are proposed engineering limits, not benchmark results.

Preserve original source/licence records, remove helper geometry, use at most four normalised weights per vertex where supported, and keep exported skin, costume and animation names inspectable. Prefer a small material set with atlas/normal/roughness maps over a separate draw for each necklace bead. Add compressed textures only through the tested loader. Avoid transparent-card layers that multiply mobile overdraw. Hair and jewellery can simplify strongly at distance while head, hands, weapon and primary cloth outline remain.

Each finished hero handoff includes: editable source scene; game GLB and any required textures; licence/provenance manifest; bone/socket mapping; actual animation list; triangle/material/texture counts; neutral front/side/back and three-quarter renders; and screenshots from the real engine at lobby, shoulder-camera and distant combat sizes. Include an animation deformation capture, not only a flattering still. Do not label a generated image, unrigged sculpt or base-body export as an implemented hero.

## Ability effects: visual grammar

The following forty-two rows specify intended presentation. They do not claim that every effect has already reached this fidelity. The shared content and authoritative simulator determine actual power, radius, timing, cover and allegiance. All effect boundaries must agree with those values.

Three channels must remain distinct: **preparation/target boundary**, **effect/impact**, **recovery/expiry**. Use shape and movement as well as colour: hostile ground areas have inward ticks/segmented edges; allied protection has outward leaf/shield marks; projectiles have direction and a small impact. Keep team edges separate from the hero's decorative hue. Limit bloom and screen coverage so an opponent remains visible through a cast. Reduced motion removes camera shake and excess particle travel, not the target boundary or timing information.

`Immediate` below means there is no gameplay windup. Any shoulder/hand anticipation is cosmetic and must not postpone the server result. For instant effects, an impact visual follows the acknowledged effect at the correct position. Recovery is also cosmetic unless a cooldown or cast lock explicitly applies. Normal bolts and lines hit once and stop; they do not pierce. Q/E movement has no damaging landing or haste. Spells obey their implemented cover rules.

### Priority nine

| Hero / ability | Preparation and shape | Impact and recovery | Player response / association |
| --- | --- | --- | --- |
| Rama Q · Steady Arrow | Immediate compact draw; one narrow cyan/gold arrow shape aligned to aim | Small bright contact and two short fragments; relaxed bow recovery | Sidestep or use cover. Bow motif is source-associated; projectile spell is original. |
| Rama E · Measured Step | Immediate forward step, two light cloth streaks; no expanding hazard ring | Feet settle and sash catches up; no blast, damaging trail or speed aura | Follow his new angle. Mobility tuning is original. |
| Rama R · Dawn Volley | Actual 1 s held draw, three separated arrow glints and a readable locked facing | Three independent arrows at centre and ±0.12 rad; individual cover/hit impacts; short bow recovery | Break the lane or flank during preparation. Each arrow is 32 base power; 96 only if all three land. Original extension of bow imagery. |
| Hanuman Q · Windward Leap | Immediate compression/forward leap; scarf and tail follow the motion | Foot dust and tail recovery, with no damage shockwave | Track the landing and regroup. Leap motif is source-associated; movement rules original. |
| Hanuman E · Bring Them Home | Immediate open free hand; small warm-green circle centred on him | Brief upward leaf/spark motion on healed allies, then fades | Allies gather close; opponents can spread pressure. Healing aid is loosely informed by the medicinal-herbs episode, not a literal reenactment. |
| Hanuman R · Mountain Pulse | Actual 0.7 s brace; locked landing circle; then actual 0.45 s rising/falling arc | On landing only: outward impact inside 7 m, separate gentle allied recovery marks; tail/cloth settle | Leave the marked area or use solid cover; allies approach the arrival. 65 base enemy damage/45 ally heal. Mountain/herb association; original combat effect. |
| Sita Q · Grove Renewal | Immediate small staff tilt; a five-leaf motif opens around her feet | Soft green/ivory recovery marks rise on living allies; no enemy hit flash | Stay near the caster for the cast. Original protection using an earth/plant motif. |
| Sita E · Rooted Path | Immediate pointing staff; an aimed ring of shallow root/leaf tracery | Sparse moving roots stay within the actual zone; damage/slow cues on enemies; edge dissolves at expiry | Walk around or leave the area. No solid wall or root immobilisation is implied. |
| Sita R · Shelter of Mithila | Actual 0.8 s grounded staff preparation; fixed 8 m leaf-ring boundary at origin | Initial shield marks, then restrained 9 health/s recovery cadence while allies remain; six-second edge drains/fades | Allies choose to hold the area; opponents flank, pressure another lane or outlast it. Original sanctuary, not a textual spell claim. |

### Remaining thirty-three

| Hero / ability | Preparation and shape | Impact and recovery | Player response / association |
| --- | --- | --- | --- |
| Ravana Q · Tenfold Guard | Immediate closed hand/chakram lift; ten small crown facets frame a close shield circle | Thin faceted shields on affected allies; facets dim with expiry | Reposition or expend the shield. Crown association; ward is original. |
| Ravana E · Commanding Circle | Immediate commanding hand closes toward an aimed ring | Short inward strands show damaging pull; no stun icon; hand opens after | Leave the target area/use cover. Original control power. |
| Ravana R · Crownfire | Immediate crown facets brighten around caster; self-centred radius edge | One low expanding circular blast, not ten sequential hits; mantle recovery | Stay outside close range/use cover. Original arena nova. |
| Arjuna Q · Converging Volley | Immediate bow-hand snap; clearly forward fan, not a full circle | Several cosmetic streaks resolve into one cone-area hit event; brisk arm recovery | Move behind or beyond the fan. Source-associated archer, original area spell. |
| Arjuna E · New Angle | Immediate lateral-looking preparation pose but actual forward dash | One thin scarf ribbon and foot plant; no damage pulse | Track his facing/new firing lane. Original mobility. |
| Arjuna R · One Clear Line | Immediate precise draw; single fast bright shaft | One contact/cover impact and quick release recovery | Dodge or use cover. No piercing implied. |
| Duryodhana Q · Mace Shock | Immediate short mace drive; low forward fan | Dust/metal-coloured energy ends at forward range; shoulder resets | Back away or move around the arc. Mace association; ranged energy original. |
| Duryodhana E · Hold the Ground | Immediate mace-braced posture; compact shield plates | Plates appear on nearby allies then dim; no immovable-root promise | Spread pressure or wait out the ward. Original allied defence. |
| Duryodhana R · Iron Crescent | Immediate broad shoulder-led sweep; crescent-shaped forward volume | Single sweeping contact band; controlled mace follow-through | Evade behind or beyond its range. Original cone extension. |
| Karna Q · Sunshaft | Immediate firm bow release; thin hot-gold shaft | One bright impact that does not persist as a damaging beam | Cover/side movement. Solar and bow motifs are source-associated. |
| Karna E · Borrowed Dawn | Immediate shoulder discs tilt/light; close soft-edged guard | Short-lived gold shield facets on allies, then warm fade | Challenge after expiry or change target. Original ward. |
| Karna R · Solar Reprisal | Immediate sun-disc gesture; circle centred on him | One low radial flare inside the radius, brief recoil/recovery | Keep distance/use cover. Original nova, no global sun attack. |
| Bhima Q · Heavy Sweep | Immediate two-hand mace sweep; close forward wedge | Heavy dust streak and bounded shock arc; weighted recovery | Flank or leave close range. Source-associated mace, original projected force. |
| Bhima E · Closing Stride | Immediate powerful leap; clear body travel | Weighty footfall dust without damage or slow | Keep distance after he commits. Original movement tuning. |
| Bhima R · Thunder at Your Feet | Immediate mace-ground gesture; circle centred on him | One broad low blast and stones that vanish quickly; lift mace back | Leave the circle or use cover. Cosmetic stones do not create obstacles. |
| Meghnad Q · Cloud Snare | Immediate aimed bow/staff-like hand direction; visible cloud-edged ground ring | Low translucent cloud wisps with clear edge; enemy slow/damage ticks, clean expiry | Route around or leave; never obscure opponents in thick fog. Cloud name association, original zone. |
| Meghnad E · Storm Step | Immediate forward dash with narrow blue-violet scarf trail | Trail stops at destination; feet reset with no stealth or haste aura | Track the moving outline. Original dash. |
| Meghnad R · Gathered Squall | Immediate forward bow sweep; long clear fan | One fan-shaped gust impact; short cloth settle | Step behind/outside fan. Original burst; no untargetable storm form. |
| Draupadi Q · Circle of Resolve | Immediate upright staff plant; small five-point shield motif | Nearby allies receive warm translucent facets, then fade | Nearby grouping gains value. Original ward. |
| Draupadi E · Stand Accountable | Immediate open hand draws toward aimed centre | Clear inward ribbons and one damaging contact; no stun/command debuff | Leave circle/use cover. Original pull, not a claim about textual coercive powers. |
| Draupadi R · Unbroken Assembly | Immediate arms open while staff anchors stance; broad nearby circle | Strong recovery marks on allies, no hostile flames; settle to stance | Allies gather for instant heal; opponents distribute pressure. Fire motif is literary association, healing original. |
| Subhadra Q · Signal Lance | Immediate spear-point release; one clean teal/gold projectile | Small contact flash, spear returns to ready | Dodge/use cover. Commander/spear role is original adaptation. |
| Subhadra E · Rally Close | Immediate short pennant gesture; small circle at her feet | Brief allied recovery marks, pennant settles | Gather close; small radius demands positioning. Original heal. |
| Subhadra R · Twin Standards | Immediate spear raised; two separate spawn marks beside caster | Two temporary banner sentinels take form, act and expire at nine seconds | Fight/avoid temporary units; do not show permanent reinforcements. Original summons. |
| Hidimbi Q · Forest Boundary | Immediate low spear sweep toward aimed circle | Sparse leaf/branch traces show damage/slow; roots remain non-solid | Route around or leave. Forest episode association, zone original. |
| Hidimbi E · Canopy Guard | Immediate mantle opens slightly; leaf-edged close ward | Shields settle on allies; a leaf-tip fade signals expiry | Stay close for application. Original protection. |
| Hidimbi R · Grove Watch | Immediate spear plants and two leaf crests appear beside her | Two temporary grove sentinels form and expire at nine seconds | Oppose or outlast temporary lane pressure. Original summons. |
| Chitrangada Q · Crossing Step | Immediate precise forward lunge/dash; short copper ribbon | Fast balanced foot plant with no damaging endpoint | Track the commitment. Entire duelist mechanic is original. |
| Chitrangada E · Spear Arc | Immediate spear sweep; narrow readable forward crescent | One bounded energy arc, followed by spear-ready recovery | Move behind/outside arc. Original spear attack. |
| Chitrangada R · Defender's Vow | Immediate planted spear and raised free arm; close shield boundary | Strong temporary shield facets, then four-second fade | Pressure another angle or outlast the guard. Original defensive role. |
| Ulupi Q · River Draw | Immediate circular staff motion toward aimed basin | Low inward water ribbons show damage and displacement; water vanishes | Move out/use cover. Water/naga association, arena pull original. |
| Ulupi E · Cooling Current | Immediate small staff dip; circle centred on her | Gentle upward water-light strokes on allies, then fade | Gather nearby. Original healing power in this game. |
| Ulupi R · Naga Basin | Immediate aimed staff ring; broad 7 m water-pattern boundary | Low translucent ripples deliver damage/slow for six seconds; edge drains cleanly | Leave or route around; no drowning, swimming or new terrain collision. Original control zone. |

## Three bespoke mechanics: approved extension and visual contract

Only Rama, Hanuman and Sita's R slots received the approved bespoke redesign; the other thirty-nine ability slots use existing kinds. These extensions are implemented in content/simulation and covered by positioned tests; final art, human balance and browser presentation acceptance are separate gates.

- **Dawn Volley:** 1 s locked preparation, then three cover-blocked, non-piercing arrows at yaw offsets `-0.12/0/+0.12` radians, 32 base power each, 28 m range. Each is independently collidable. A miss or cover can reduce the theoretical 96 total. Counterplay is leaving the locked angle, using cover or pressuring the stationary archer.
- **Mountain Pulse:** 0.7 s locked preparation, then 0.45 s authoritative arc toward the locked point, up to 14 m with solid collision. Only actual landing applies 65 base damage to visible enemies within 7 m and 45 healing to nearby living allies including the caster. The visual landing indicator must reflect collision-limited arrival; it must not promise travel through a wall. Counterplay is leaving the destination, covering the impact or attacking during commitment.
- **Shelter of Mithila:** 0.8 s locked preparation; a fixed 8 m sanctuary at cast origin lasts six seconds. Initial 70 base shield, then 9 base health/s to living allies who remain inside with the implemented visibility rules. Enemies are not damaged. Counterplay is attacking another angle/objective, displacing pressure away from the area or waiting out the field. A shield is not invulnerability.

During preparation the actor cannot move, jump, fire or start another cast. Facing/target lock at acceptance. Damage alone does not interrupt; death cancels a pending cast without refunding its cooldown. Disconnect preserves authoritative cast progress. An already-created sanctuary remains for its duration after the caster dies. Upgrades apply through the shared power multiplier. Renderer progress must come from authoritative cast/zone state, not a local timer restarted on reconnect.

The current independent content suite passes 71 cases covering fourteen basic attacks, all forty-two ability slots, cooldown/receipt guards, ally separation, cover/collision and summons. The bespoke cases verify delayed projectile release, landing-only payloads and fixed-area healing/expiry. Those fixtures establish mechanics, not final art quality, physical browser traversal or equal competitive strength.

## Minions must look purposeful

Lane units receive original fitted armour/cloth and clear silhouettes at a smaller scale than heroes. Their face detail is lower priority than a readable helmet/body/weapon outline. They should not be miniature Rama/Ravana models merely because earlier internal defaults borrowed those hero IDs.

| Unit role | Readable art and motion | Authoritative distinction |
| --- | --- | --- |
| Escort | Light compact sentinel, one clear shoulder pennant, small forward projectile emitter; quick marching stride and brief shot recoil | Follow `minionRole: escort`; role, team and actual projectiles drive presentation. |
| Siege | Wider low silhouette, reinforced shoulder/cannon frame and slower deliberate movement/recoil; keep hero head/crown shapes absent | Follow `minionRole: siege`; show its real longer-range/heavier attack, not a decorative hero-sized blast. |
| Subhadra summon | Compact sentinel with paired standard/pennant motif, luminous seams rather than full-body transparency | Follow `minionRole: summon`, `summonerId`/hero identity and actual `expiresAt`; disappear on server expiry/death. |
| Hidimbi summon | Compact sentinel with leaf-shaped armour plates, split crest and earth-toned solid body | Same authoritative summon metadata, distinct owner style; never imply permanent terrain or additional unspawned creatures. |

Show team clearly even when summons share a hero's palette. A temporary unit may have a small dissolving crest or subtle lifetime accent based on authoritative expiry; it must not survive visually after removal. Bound active particle work and share low-detail materials/meshes across repeated units. Role balance, target selection and damage are simulator responsibilities; appearance should explain them.

## Map and counter readability

Sangam City is an original composite arena, not a surveyed historical city. Ghat promenade, Temple avenue and Metro gardens need distinct landmark forms, material families and route silhouettes while preserving the shared collision map. Ghat steps and water edges can support Ulupi's visual theme without conferring an unimplemented water bonus. Planted courtyards suit Sita/Hidimbi motifs without becoming extra cover. Temple gateways and civic colonnades must leave projectile lanes visible; decorative alcoves should not look like traversable routes when solid.

The earlier historical architecture reading supplies form vocabulary, not current archaeological validation. Epic place names in literary translations must not be mapped automatically to modern borders or used as proof of the characters' historical existence. Character gameplay should work on every lane. Analyse sight lines, approach options and objective distance when tuning counters; do not solve a strong hero by assigning an undocumented disadvantage to a themed district.

## Source associations and cultural interpretation

The pinned translations and architecture source are recorded in [MYTHOLOGY_AND_ROSTER.md](../docs/MYTHOLOGY_AND_ROSTER.md). Read selected passages only; do not present the art bible as a survey of all versions or a whole-book study. All costumes, faces, materials, combat numbers, effects and most ability groupings are original game design. The supplied generated images are original concept references for this project, not evidence of historical clothing or canonical appearance.

New passages actually read for this expansion:

- Griffith's *Ramayana*, Book VI, Canto LXXIV, “The Medicinal Herbs,” pinned mirror lines 55454–55590: Hanuman seeks healing plants, carries a mountain portion back, and the poem describes restored allies. This supports an aid/mountain motif. It does not establish the game's radius, shield, healing numbers or combat timing, nor any real medical claim.
- Ganguli's *Mahabharata*, Adi Parva, Arjuna-vanavasa Parva, section CCXVI, pinned mirror lines 19864–19959: Ulupi identifies herself as Kauravya's naga daughter and is associated with the river/waters. Her arena staff, healing and slowing basin are original. No water invulnerability is included despite a boon described in that passage.
- The same volume, section CCXVII, lines 19961–20023: Chitrangada is named as Chitravahana's daughter and the dynastic arrangement is described. This passage alone does not establish the spear-duelist kit. That role is explicitly our adaptation; later regional literature and Tagore's treatment have not been read in this pass. The translation's Manipura is not being asserted here as a settled modern geographic identification.

Use respectful individually authored faces and heroic agency across women and men. Ravana and Duryodhana remain expressive characters rather than racialised monsters; Hanuman's vanara anatomy is deliberately distinguished; naga motifs do not make Ulupi a generic villain. Teams are sporting allegiances, unrelated to religion/caste or epic virtue. Texts, sacred syllables or living ritual objects should not become random floor decals. If a later production choice invokes a particular regional iconography, record and review that actual source rather than claiming universal authenticity.

## Acceptance sequence

1. **Rama model gate:** neutral-lit head/hands and continuous anatomy; original layered costume; rigged bow grip; actual engine idle/run/fire view. Remove visible primitive construction and broken deformation before multiplying the workflow.
2. **Hanuman and Sita gate:** distinct anatomy/faces, tail versus braid/cloth solutions, correct weapon grips and all nine priority ability presentations. Inspect front, profile and the usual back/shoulder camera.
3. **Roster/minion gate:** fourteen distinguishable silhouettes and faces, purposeful escort/siege/summon roles, no same-body recolour substitution. Inspect thumbnails and normal-distance play as well as close views.
4. **Combat gate:** all forty-two presentations correspond to actual effects; cast progress, target boundary, team, impact and expiry remain readable with multiple actors/minions, both teams and reduced motion. Confirm the final nine priority cues with native gameplay captures.
5. **Budget gate:** measure real loading, GPU memory/draw cost and frame time on the supported desktop/mobile quality paths, including six active heroes and representative waves. Record hardware, resolution and scene. A target triangle count alone is not performance proof.

Keep a short evidence ledger for each gate: asset/version, view or test, observed issue, correction and result. Mark unfinished cloth, placeholder faces, missing clips and generic effects directly. A visually plausible promotional sheet is a reference; the accepted result is the animated character and effect visible in the actual game.
