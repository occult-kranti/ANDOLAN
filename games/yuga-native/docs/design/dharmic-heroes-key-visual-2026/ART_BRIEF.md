# Five-hero key visual · improved artist brief

## Intent and composition

Create original YUGA ensemble art that conveys protection, skill and distinct personalities through the visual languages of Indian miniature painting, mural composition, worked stone and contemporary cinematic game art. The five figures stand in a **wide, open crescent** on a mandala-engraved sandstone platform over a lotus pond at dusk. The arrangement suggests fellowship without making their relative size or an ability's spectacle a measure of sacred status.

Frame at a low three-quarter view, with Hanuman at the foreground center, Arjuna left foreground, Kali right foreground, Rama back left and Krishna back right. Each face, hands, feet and prop needs its own negative space; the two archers need distinguishable poses and equipment even as silhouettes. Place the palace on the warm horizon and the storm-lit plain on the opposite horizon. This juxtaposition is fictional, not a geographic or historical reconstruction. Keep an unobstructed center/edge-safe region for future title and responsive crops; the artwork itself should contain no text or logos.

**Lighting and materials:** a low golden key, cool blue-green fill and constrained rim lighting; soft green herb light on Hanuman's hand, a narrow cool arrow accent for Arjuna, restrained red-orange for Kali, warm ivory for Rama and deep-blue/violet for Krishna. Use stone, woven fabric, hammered brass and natural water reflections. Keep surfaces rich at close range but calm at thumbnail size. Choose whether to add grain or motion blur only after the unblurred anatomy, readable silhouette and value structure are approved; neither should disguise bad geometry.

The image is illustrative. It is not a requirement that the future arena contain this exact platform, a real landmark, water collision, these spells, or celestial actors. Any inscription must be selected from an identified text with correct script, context, translation and expert review. Until then, use non-linguistic geometric ornament.

## Character direction

| Hero | Identity and pose | Reuse and review focus |
| --- | --- | --- |
| **Hanuman** | Copper-to-gold fur, saffron-red cloth, rudraksha and worked brass; athletic protective expression. One hand supports a small herb-covered mountain while the tail counterbalances a leap. | Reuse the [enhanced Hanuman](../../../art/hanuman-hero-finish/README.md), tail/weapon sockets and mountain study. Separate the carrying hand and mountain from his face; verify grip, elbow, tail and landing as real motion before runtime use. |
| **Arjuna** | Lean, diagonal archer; deep lapis, restrained silver, high asymmetrical quiver and split shoulder scarf. Gandiva is fully drawn with a distinct white-blue arrow. A small feather may decorate the headgear. | Start with the [Arjuna brief](../../hero-design/arjuna.md) and existing source, not a renamed Rama. Review string-hand contact, bow silhouette and thumbnail distinction from Rama; a glow does not create a new projectile rule. |
| **Kali** | A dignified, fierce dark-blue figure in a red sari, four intentionally separated arms, loose hair and a stylized skull garland. The original idea includes a curved/scythe-like blade and one foot on a demon skull; design a non-graphic stone or symbolic treatment and consult sources before finalizing. | Develop a separate look sheet, anatomy/arm attachment and movement study. Distinguish four intentional arms from accidental duplicates; verify costume, iconography and names against named sources and with knowledgeable reviewers. No current Rust character or ability is implied. |
| **Rama** | Calm upright silhouette, long Kodanda lowered yet ready, blue/ivory garments with a golden-yellow drape and a small, legible blessing gesture where the pose permits. | Begin with [Rama's concept and existing rig](../../../art/four-hero-motion/README.md). The current rig grips the bow in the right hand and draws with the left: check the actual pose before requesting a two-hand bow action. Keep his vertical form distinct from Arjuna's diagonal stance. |
| **Krishna** | Dark-blue skin, yellow dhoti, teal sash and a prominent peacock feather. Hold a flute naturally; behind him a symbolic, translucent cosmic motif can suggest multiple faces and arms without changing the body silhouette. | Use the [Krishna development study](../../../art/four-hero-motion/README.md), including flute and disc sockets. A three-face/multiple-arm cosmic motif is a proposed illustration, not a verified doctrinal description or implemented ability. Keep flute contact, head silhouette and any orbiting disc separately readable. |

The supplied hero names and traditional motifs are creative inputs; details vary across historical and living traditions. Do not promote an invented pose, weapon, shloka or symbolic arrangement as universally canonical. Plan cultural and historical review with named, relevant sources before final art approval.

## Visual and accessibility checks

1. Review the five heroes as full composition, grayscale silhouette and small thumbnail. Separate face, arms and weapons from scenery; distinguish both bow users without relying on blue versus yellow alone.
2. Make 16:9 desktop, 4:5 portrait and square crop guides as **new artist deliverables**, keeping essential faces, hands and weapons in safe areas. Do not crop away Kali's arms or Hanuman's mountain and still call it the approved key visual.
3. For any eventual game effect, pair team/danger colors with shapes and timing; check normal and reduced-effects settings, bright stone, water, and day/night. A promotional glow is not a damage area, hitbox, healing effect or proof of gameplay readability.
4. Review intentional multi-arm anatomy independently. A generic negative prompt of `extra limbs` conflicts with Kali's requested four arms; use **unintended extra limbs** and specify the expected arm count per character.

## Copyable ensemble prompt

> Create an original widescreen YUGA ensemble concept illustration with five full-body heroes in a spacious crescent on a carved sandstone mandala above a lotus pond at dusk. Center: protective copper-and-gold Hanuman in saffron-red cloth, one hand supporting a small green mountain and his tail counterbalancing a leap. Left foreground: lean Arjuna in deep lapis with an asymmetrical quiver and silver-accented bow, drawing one white-blue arrow. Right foreground: dignified and fierce Kali with dark-blue skin, exactly four clearly attached arms, flowing black hair, red-and-gold sari, stylized skull garland and curved blade, in a balanced dance stance. Back left: calm Rama with a lowered long bow, blue and ivory clothing and a yellow-gold drape; make his upright silhouette distinct from Arjuna. Back right: Krishna with dark-blue skin, yellow dhoti, teal sash and prominent peacock feather, holding a flute naturally; a separate translucent cosmic mural suggests symbolic multiple faces and arms. Make every face, hand, weapon and foot readable. A distant palace, a storm-lit plain, lotus reflections and restrained golden rays complete a fictional composite landscape. Use Indian miniature-painting composition, mural color harmonies and realistic cinematic game-concept rendering. No UI, logo, watermark, legible invented writing, graphic gore or recognizable characters from other games.

**Optional negative constraints** for generators that support them: `unintended extra limbs, merged hands, duplicate characters, occluded faces, broken bows, floating weapons, blurry focal subjects, watermark, logo, fabricated text`. Keep Kali's four arms and the separate cosmic motif as positive requirements; do not exclude all multiple arms. Generator syntax and aspect-ratio flags differ, so choose them for the actual tool rather than assuming a Midjourney or SDXL command is portable.

## Single-character prompts

Use the project sheet for that hero as a reference when available, and request both a clean neutral turnaround and a separate action image. Do not turn a painted turnaround into a claimed game model.

- **Hanuman close-up poster:** “Portrait of YUGA's Hanuman from chest up, expressive copper mane, thoughtful protective gaze, saffron-red cloth, rudraksha and worn engraved brass, one hand and a small herb-covered mountain entering frame. Warm gold rim and gentle green bounce, realistic fur planes and facial anatomy, readable tail curve in the background, no text or bloom over the eyes.”
- **Kali action study:** “Full-body Kali in a balanced protective dance on a temple platform, dark-blue skin, four intentionally separate articulated arms, red-and-gold sari and stylized skull garland, one curved blade, wind through black hair, restrained crimson rim light. A symbolic stone demon skull beneath one planted foot, no graphic gore. Show every hand and arm attachment clearly; leave a clean silhouette for animator review.”
- **Arjuna:** “Full-body lean Indian archer in deep lapis with silver bow fittings, high offset quiver and split shoulder scarf, drawing an illuminated single arrow. Front, side and rear neutral views plus a separate diagonal action pose; clear bowstring and finger positions, no body parts hidden by the quiver.”
- **Rama:** “Full-body Rama with an upright calm silhouette, blue-and-ivory cloth, golden-yellow drape and long Kodanda. Front, side and rear neutral views plus a separate lowered-bow pose; distinguish his shape from an agile second archer, and show both hands and the bow socket.”
- **Krishna:** “Full-body Krishna with dark-blue skin, yellow dhoti, teal sash, a prominent peacock feather, flute and a separate gold disc. Front, side and rear neutral views plus one natural flute-playing pose; a painted cosmic aureole sits behind the figure without obscuring body anatomy.”

## Deliverables and color management

The current generated file is **1672 × 941, flattened RGB**, without an embedded ICC profile; it is an art-direction candidate. The following are future production targets, not deliverables already made:

| Deliverable | Proposed specification | Acceptance |
| --- | --- | --- |
| Key art | A layered artist-authored master at least 4096 pixels on its long edge; 4096 × 2304 is one 16:9 target. Supply PNG/WebP exports and the editable working file. | Separately editable heroes, environment and VFX; approved crops and visual review. A flattened generated PNG cannot be assumed to contain recoverable PSD layers. |
| Portraits | 2048 × 2048 working images per hero, with separately authored export crops and safe margins. | Faces, hands and identity remain readable at actual UI size; optional alpha exports are checked separately. |
| In-game assets | Editable Blender source, retopologized mesh, UVs, textures, material, rig, clips, sockets, LODs and a versioned engine export. | Source-to-export provenance; animation/contact, real engine import, performance and team readability checks. A painting is not any of these assets. |
| Color | Tag web/game display exports sRGB; use the team's explicitly managed scene-linear workflow for rendering, with a documented view transform. | Verify the look in the target engine and displays. For print, use the printer's supplied ICC profile and a proof; Adobe RGB alone does not specify the final print condition. |
| Delivery size | Keep a compressed review package under the requested 50 MB **when feasible**; preserve the uncompressed master separately. | Verify quality, embedded profiles, transparency, file hashes and editability. The size cap must not silently discard required layers. |
