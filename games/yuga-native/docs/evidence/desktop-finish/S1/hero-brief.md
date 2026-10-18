# S1 / W3 hero brief — desktop finish

**First candidate: soften the broad gold glare with one original, bounded roughness asset.** Keep the G2 upper-hair tier inactive until a matched comparison shows a useful improvement. Cloth volume needs its own geometry decision; another roughness increase cannot supply missing folds.

This is the initial audit/preparation checkpoint. Inspected working-tree HEAD: `0fb96d108b1d886a4ebf84d3b5140abca3905465`. The G1 finish sources are still local changes at this point. Runtime edits wait for the coordinator's pushed source checkpoint and explicit edit gate. No import, render, GLB, player, package or shared provenance-manifest edit was performed for this brief. Mobile work is deferred.

## Actual images inspected

Re-opened all three original full-frame PNGs under `/tmp/yuga-g1-hero-r1/`:

| Image | SHA-256 | Visible finding |
| --- | --- | --- |
| `light-front.png` | `ad2d0b5a8e82c06f4e6f100cb8b103d91cb79bd353cfc1c4e36a052651ac9fb9` | Wide bright orange strips on the bow and shoulder plates dominate small jewelry relief. The blue sash reads as a broad planar band. |
| `dark-profile.png` | `5cc0ae03f3fd072ea4be70a8522cf74eb93f8184524c2242ae37e007befce5aa` | Gold has a continuous highlight; the visible hair is a few large smooth lobes. Raised quiver ornament has a detached-wire appearance. |
| `dark-rear.png` | `347cbeab362cedcc5ea051c5c5a26e9be8a0e0cb29cc59c1ba7773f0b37fb0f2` | Hair terminates in thick repeated points and merges into the dark backdrop. The mantle forms broad flat panels with repeated motifs. |

The retained `run.json` records actual Godot 4.6.3 Forward+ frames on llvmpipe, exit0, eight originals and no warnings. These selected stills establish the observations above, not hardware performance, continuous shimmer, current S1 runtime identity or a causal G1-vs-earlier improvement. No G2 candidate image has been accepted by this brief.

## Top three defects and bounded response

1. **Gold glare obscures shape.** The current G1 forged-gold map is 512×512 linear red-channel roughness with actual range 87–124/255, approximately 0.341–0.486. The finish owner sets roughness multiplier1.0; the shader multiplies that scalar by the map. Proposed S1 asset `assets/hero-finish/s1-hammered-gold-roughness.png` will use an original analytic periodic field with a target effective range approximately **0.48–0.63**, restrained broad forging variation and low-amplitude tool marks. It will retain a metallic reading and modeled relief. Route only `Worked warm gold` through it using the existing finish owner; preserve albedo, original normal, metallic value, texture transform, secondary motion and every other material profile. Keep the G1 map/generator/notice as historical source. Original generator belongs under `art/hero-finish/`; provenance belongs in the owned evidence/notice agreed at the edit gate.
2. **Cloth has insufficient fold volume and thickness.** Current woven roughness is already 197–207/255, approximately **0.773–0.812**, at multiplier1.0. Its source is `assets/materials/rama-finish/woven-roughness.png`, SHA `eec110e598ac1a2fa95fb5899fac5fc314a191bff8e670547d79dfaf1468e500`. Increasing this value again would mainly flatten response. S1 preserves that accepted map and records front/rear planar-drape evidence. A later original fold/hem candidate must address actual geometry and bone weights under separate coordinator scope; neither texture grain nor extra gold trim will count as that improvement. Broad smooth skin and restrained expression are also open, but are outside this first gold candidate.
3. **Hair is a solid pointed mass.** Inspect the already built G2 upper tier before adding anything further. It provides seven broad short overlapping layers, one head attachment, 1,904 triangles/1,085 vertices and no new texture/material or per-frame callback. All alpha values are0, so it follows the head without another secondary-motion owner. It may merely thicken the cap or read as attached leaves; reject it if so. The old temple wisps stay inactive. The constant added cost at far LOD remains a budget question, not an accepted optimization.

The current actual hero input is **`assets/heroes/rama-hero.glb`**, SHA `8b6cf0f4c5520696d1d843e5bdebb2454c1dbd4341e17171c5b6d20353384d5c`, as selected by `player.gd`. The separate legacy `rama.glb` is not the current rendered hero and supplies no material conclusion here.

## Implementation and focused checks after the gate

The proposed mutation set is the finish owner's gold map binding, one new original lossless grayscale PNG and matching linear/mipmap import descriptor, the editable generator, a notice append and narrow owned verification/evidence. No existing generated map is overwritten. Do not change current material suffix/version or shared test expectations merely for a map-path change unless the coordinator's provenance contract requires it; preserve old fixtures.

Verify deterministic regeneration and exact source/output hashes; finite bounded values; identical opposing wrap edges; full mip/filter intent; linear red-channel sampling; and the **effective** roughness after scalar multiplication. Check all near/mid/far slots share the expected imported resource after the renderer's single import. Existing material configure/release/idempotence and competing-owner tests must remain meaningful. Confirm source GLB, rig, original albedo/normal resources and secondary parameters remain exact. Supplied-map tests can check owner behavior before import, but do not qualify the new actual imported texture.

The G2 helper is frozen at `989d069b1364e50a3ae31530f778659e5910ea1c3e05f7b81edccf90e3101732`; guides at `181ecd859cc0569ca7ed5e4c48f60620a986189c730f3aff771ff3f51e562242`; generator at `8b929a7b6481b8b95d611e90a10b8d8c80d70169ee8ff3fa087726dee4add934`. Its retained [G2 report](../../graphics-six/G2/hero.md) has 26/26 actual imported-rig checks, zero nonhair triangle crossings in rest and21 unique historical stress poses, and the preserved rejected lower-tip candidate. That historical pose set is not current S1 action execution; face morphs, secondary extremes and continuous motion remain separate gates.

## Counterexample captures for the renderer

Renderer worker owns CPU0/1, source freeze/import and actual originals. Use fixed camera, source pose/time, exposure, lights, background and wait count; hash the controlling inputs. Do not combine material and geometry changes in one unexplained before/after pair.

| Comparison | Small requested set | Reject when |
| --- | --- | --- |
| S1 gold baseline/candidate, hair helper off | Two matched pairs: light front/initial-screen portrait and dark profile. Keep the same shoulder/bow/jewelry pixels framed in both branches. | The gold becomes brown/plastic/chalky, loses modeled edge/engraving definition, still has a dominant unbroken glare strip, or creates new noisy highlight breakup. A darker frame from different lighting is not evidence. |
| G2 hair off/on, one fixed material state | At most six originals: front, profile and rear pairs. Use existing `configure(hero_visual)` / `release()` hook from the G2 report after finish/secondary binding. Parent supplies review-only integration. | Extra layers form leaves/scales, increase cap bulk without separation, clip ear/circlet/raised arm, expose seams or worsen silhouette against either backdrop. Do not activate by default on numeric clearance alone. |
| Subsequent motion gate | A short source-bound turn and raised-arm/cast passage after a still candidate survives; reuse the same light/material state. | Grain shimmers, highlights crawl, hair layers intersect during current actions, or the change hides unresolved collar/cloth/foot-contact defects. |

Parent decides whether to run the hair ablation before or after the gold pair, within the serialized budget. The first S1 implementation is one gold-response candidate, not a claim that the hero sculpt, cloth silhouette, face, contact or Deadlock-quality target is complete.
