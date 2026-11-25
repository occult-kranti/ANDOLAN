# Four ability keyframe studies

Four new illustrated planning boards show anticipation, contact and recovery for YUGA's Hanuman, Rama, Shiva and Krishna. They retain the previously generated character sheets as visual references. The images are 2D ImageGen concepts, and the separate Blender study supplies editable 3D motion. [Hanuman](hanuman.png) · [Rama](rama.png) · [Shiva](shiva.png) · [Krishna](krishna.png) · [Editable five-action Hanuman study](../hanuman-motion-panel-2026/README.md)

## Animation handoff

| Character and sequence | Shipped or proposed | What an animator should carry forward |
| --- | --- | --- |
| Hanuman · Mountain Pulse | Playable | Raise and release over the 14-tick windup, follow the accepted target during 9 ticks of travel, and reserve impact for tick 23. Keep the gada in the right-hand socket throughout and let the tail settle after the torso. The image's pose is an art target. [Timing and effects](../../docs/design/combat-panel-2026/HANUMAN_RAMA.md) |
| Rama · Dawn Volley | Playable | Keep the bow in the anatomical right hand and draw with the left, matching the real game rig. The three bright paths in the illustration summarize the volley. The authority staggers its arrows, so animate each release on its own recorded tick. [Timing and effects](../../docs/design/combat-panel-2026/HANUMAN_RAMA.md) |
| Shiva · Tandava Downbeat | Proposed | Lead with one planted foot and a lifted knee. The footfall, trident and ground ring need separate silhouettes. Preserve the proposed one-contact rule when producing animation. [Proposal](../../docs/design/combat-panel-2026/SHIVA_KRISHNA.md) |
| Krishna · Govardhan Canopy | Proposed | Transfer the flute to a hip socket before raising the left hand. The protected group and canopy communicate support. The cue, shield and socket transfer still require gameplay and rig implementation. [Proposal](../../docs/design/combat-panel-2026/SHIVA_KRISHNA.md) |

The panel reviewed eight museum-provided public-domain works separately. The Hanuman miniature, Nataraja bronze and Govardhan folio inform future silhouette and grouping discussions. The drawings above were generated from the earlier YUGA sheets; they were not produced by editing those museum reproductions. [Museum source gallery](../../docs/research/art-history-panel-2026/README.md)

## Art correction passes

The [first Hanuman image](variants/hanuman-initial.png) dropped the gada in the recovery panel. A subsequent image edit restored it to the same anatomical hand. The [first Rama image](variants/rama-initial.png) used the opposite bow grip from the native rig. The final Rama board was regenerated using both the character sheet and the actual four-view Blender rig photograph, with the right-hand grip called out. These are illustrative images; hand contact, prop ownership, action timing and support feet still need review on the actual rig. [Rama rig photograph](../four-hero-motion/media/stills/rama.webp) · [Hanuman motion checks](../hanuman-motion-panel-2026/README.md)

## Generation record

The four initial boards were generated with ImageGen on 25 November 2026. Source images were the corresponding YUGA character sheets in [four-hero-motion/media/art](../four-hero-motion/media/art/). The shared brief asked for a three-stage, full-body action sequence, clear anatomy and silhouettes, no text or UI, and premium realistic game-concept presentation. The prompts requested the following action-specific direction.

- **Hanuman** gathers a small herbal mountain during the windup, sends it to a defined ground mark and recovers with a delayed tail. An edit retained the rest of the plate and restored the missing right-hand gada.
- **Rama** draws and releases an ornate gold bow, with three clear paths over a moonlit ghat. The final attempt used the original Rama sheet and the actual Blender rig still, explicitly facing image-left and gripping the bow with his anatomical right hand.
- **Shiva** raises a knee, places one clear footfall inside a broken ring, and lets the tied drum and cloth settle. The pose uses the existing two-armed YUGA design.
- **Krishna** stows the flute, raises the left index finger under a rocky protective canopy and then recovers. This is a proposed fictional game action inspired by the Govardhan story.

| Output | SHA-256 |
| --- | --- |
| Hanuman | `11af8a7dacf45fa957c0dd58ef7b6e44d524faab41158d5d55bafbd955a24dfe` |
| Rama | `b9d25e658a229d9618e7b158ad894a2790be7411d1bac38436a0f0642f0d7123` |
| Shiva | `a03d6d90f3e24284e2accbd7aa753ce18ae59232404d9d9ba2e23754fffa054d` |
| Krishna | `204dfe4ffaa04c8b6aa63fc40c33a306bffb94314a5e99136745fce066b614ab` |
