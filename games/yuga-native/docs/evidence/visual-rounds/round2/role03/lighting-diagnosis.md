# R2-03: residual skin stippling diagnosis

Source: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`, native YUGA.
Disposition: retain the accepted sun-shadow policy at depth **0.2**, normal
**0.35**. No lighting runtime change is justified by the current evidence.
Both roughness-mips and SSS-off originals retain the defect; lighting comparisons
remain pending.

## Actual originals inspected

The four historical `capture-face-ablation-r1` originals were opened, including
baseline, sun-shadow-off, skin-normal-off and SSAO-off. The baseline has broad
cheek/neck triangles and fine scalp dots. The normal-off and SSAO-off originals
retain both visible patterns; sun-shadow-off removes the conspicuous patches and
scalp-dot band in that historical fixture. This favors a shadow-path contribution
there. It does not identify the responsible filter, prove every current dot has
that cause, or authorize disabling shadows.

The accepted `capture-shadow-bias-r2/shadow-bias-depth2-face-day.png` original
shows that the depth 0.2 correction greatly reduces broad patches while a narrow
dot band survives behind the ear and below the earring. Accepted Confluence day
and night depth-0.2 portraits also retain dots at the ear and neck/chest, most
clearly in day. Final day/night hero anchors retain shadows and show the chest
region at normal figure scale. These fixed images cannot establish moving
cascade contact. Historical lower/higher-bias trials retain their original
rejected or limited dispositions; none is reclassified here.

The new Round 2 courtyard three-quarter-left day original at
`/workspace/scratch/visual-round2/capture-baseline-court-r1/` was opened at native
1280x960. A narrow stippled strip remains behind the outer ear, across the skin
visible through the earring and down the rear neck. Smaller speckles appear
under the crown/forehead edge. Portrait fill is off. Its raw SHA256 is
`1cabca9ec2dea9762eac7f28384a48f0519a880414ffa1a683e4eb388a5e2438`;
the pose pin is
`f343eebf75c980ea8ce92dbe6be35635b272f344254b069a0b49c4c9d67d3366`.
This is the selected comparison frame, not the differently lit historical title
portrait. Both current material candidates were subsequently rejected as useful corrections
in this fixture; see the outcome below.

## Material and lighting path

`rama_surface_finish.gd` binds named skin through `StandardMaterial3D`, retaining
the GLB albedo, normal, UVs and geometry. The custom secondary cloth shader does
not shade the named skin. The finish replaces roughness with the existing
512x512 grayscale map in RED at multiplier 1, specular 0.34, scattering enabled
at 0.08 in skin mode. The actual original roughness and normal PNGs were opened;
the roughness contains fine grain and its import disables mip generation.
Role01's sampling hypothesis is therefore testable without replacing maps.
Role07 records exact embedded/extracted image equality and unchanged face data.

Courtyard `ProductionLighting` enables sun shadows with angular distance 0.7;
Confluence `WorldLighting` uses 0.6. Both use depth 0.2/normal 0.35 and four split
shadows. The project explicitly sets a 2048 directional shadow atlas and MSAA2x;
it has no explicit TAA setting. `HeroAtmosphere` changes court sun direction and
color/specular but does not write shadow bias or angular distance. Fills do not
cast shadows. The exact-path flat-ground casting whitelist remains untouched.

The retained official Godot 4.6 `Light3D.xml`, whose bytes match the earlier
source receipt, describes positive `light_angular_distance` as directional
PCSS soft shadows in Forward+. That makes a zero-angular-distance comparison a
specific possible follow-up: keep shadows enabled and change only softness.
No engine PCSS shader source was inspected here; this is a mechanism hypothesis,
not a confirmed explanation or performance claim.

## Smallest useful current test

Use role01's already-staged **roughness-mips** and **sss-off-diagnostic** in two
separate one-frame renders against the selected court baseline. Freeze camera,
pose, morph state, near LOD, exposure, time, sun and warmup. Keep the 0.2/0.35
policy. Judge ear, rear-neck, crown/forehead and visible chest pixels separately;
also inspect jewelry boundaries, cheek form and skin color. The current tightly
framed portrait cannot close lower-chest or foot-contact acceptance.

The renderer was asked to record the actual skin roughness image mip state,
scattering enable/strength and sun angular distance, plus `.import` source pins.
Its earlier generic source scan omitted `.import`; source equality alone would
otherwise miss the only roughness candidate change. The renderer reports these
observations are now included in the later harness. The earlier baseline's exact
harness and import-freeze receipt must be preserved; added logging is not an
unexplained product-source delta.

Decision rules are machine-readable in `lighting-probes.json`. If one material
probe removes the band, the result identifies a contribution under this fixture;
it is not automatically a production treatment. If both retain it, retain maps
and lighting policy, then request one separately scheduled PCSS-off comparison
(`sun.light_angular_distance = 0.0`, restore exact prior value afterward).
That follow-up is **deferred**, outside the current two-view budget. It must not
be combined with a material or bias change. A clean result would justify a
bounded shadow-filter investigation, not immediate hard-shadow promotion.

The roughness-mips original has now arrived and was opened at native size. The
same narrow ear/earring/neck band remains conspicuous; there is no useful visible
stippling correction in this fixture. Camera, pose pin, facial state, LOD,
motion state, player transform, viewport, context and every baseline-recorded
light value match exactly. The renderer records nine generated mip levels and
SSS still enabled. This is a failed correction hypothesis in the inspected
fixture, not proof that mipmaps are useless in other minification/motion cases.

Root requested one TAA-on alternative after the material probes. The newly
fetched official 4.6 `Viewport.use_taa` and `ProjectSettings` member documents
confirm Forward+ support, temporal jitter/history and potential skinned-mesh or
particle ghosting. They also record an automatic mip LOD bias adjustment. Thus a
TAA improvement is a practical filtering result, not pure isolation of the
shadow mechanism. Keep MSAA2x and all other lighting/material inputs fixed. A
matched moving blink/draw/cancel clip must be reviewed for eyelid, hair, jewelry,
bow and arrow smearing before any promotion. Preserve the four-frame still
settle and record history age after the camera cut; a short-history still is not
proof of fully converged TAA behavior.

`stage_lighting_probe.py` produced two separate, source-guarded scratch overlays:
`directional-pcss-off` changes only the courtyard sun angular distance 0.7 to 0;
`taa-on` adds only the startup TAA setting. Neither is applied to runtime. The
generator refuses stale pinned inputs, checkout-local outputs and reused output
directories. Seven offline checks confirm exact single-property overlays,
admission guards and unchanged runtime pins. It does not run Godot.

No runtime setting, map, mesh, shader, bloom, fog, exposure or light was changed.
No import, Blender process or renderer was run by this role. Source and
historical visual investigation is complete; remaining causal acceptance awaits
the separately scheduled angular-distance and TAA lighting pixels.

The SSS-off original subsequently arrived and was also opened. Its actual
materials report SSS disabled and zero roughness mip levels; camera, pose, face,
LOD, motion and all common lighting controls match exactly. The ear and rear-neck
stipple remains conspicuous. Both material ablations therefore fail as useful
corrections in this fixture. The trigger for the two staged lighting alternatives
is met. Their pixels and TAA motion result remain pending with R2-06/root.

Final overlays use `directional-pcss-off-r2` and `taa-on-r2` beneath the role-03
scratch directory. The initial generator incorrectly inferred repository bounds
from an arbitrary supplied scratch project; the corrected guard protects the real
checkout and supplied project subtree. The earlier generator/outputs and failed
check are preserved, and the corrected seven checks pass.
