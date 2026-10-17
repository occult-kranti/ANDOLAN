# Shadow bias follow-up: source and test dependencies

This is a read-only policy review. Root reports that the matched face ablation
removes the triangular patches only when sun shadows are disabled; normal-map
and SSAO ablations retain them. The renderer is now testing shadow-enabled bias
variants. This note does not independently approve those newer pixels.

## Official Godot 4.6 guidance

Read the official tagged source documentation:

- [Light3D.xml, 4.6-stable](https://github.com/godotengine/godot/blob/4.6-stable/doc/classes/Light3D.xml):
  `shadow_bias` defaults to 0.1. Too little produces self-shadowing; too much
  detaches shadows from the caster. `shadow_normal_bias` defaults to 2.0 and
  offsets the shadow lookup along the object's normal; tune it together with
  depth bias. The proposed 0.1 / 1.0 trial is plausible, not an art acceptance.
- [DirectionalLight3D.xml, 4.6-stable](https://github.com/godotengine/godot/blob/4.6-stable/doc/classes/DirectionalLight3D.xml):
  extending maximum shadow distance reduces overall detail and adds rendering
  cost. Blending splits trades detail/performance for smoother transitions.
  Neither setting needs to change for the bounded bias experiment.

These are property values, not an established fixed offset measured in meters.
The XML is from Godot's 4.6 tag; runtime qualification still uses installed 4.6.3.
Retrieved files, exact hashes and source pins are in `shadow-policy-receipt.json`.

## Both native policies must be considered

| Owner | Current bias / normal bias | Retain |
| --- | --- | --- |
| `scripts/production_lighting.gd`, `apply()` | 0.025 / 0.35 | `sun.shadow_enabled = shadows`; 4 splits; 70 m; blend splits; no new shadow-casting fill/practical |
| `scripts/world_lighting.gd`, `apply()` | 0.025 / 0.35 | supplied shadows flag; 4 splits; 72 m; blend splits; existing phase interpolation |

Courtyard settings call `ProductionLighting.apply()` and then
`HeroAtmosphere.configure()`. The atmosphere owner does not write bias or
`shadow_enabled`; it will neither propagate a courtyard change to Confluence nor
undo it. Confluence configures its separate `WorldLighting` controller. A
courtyard-only fix would leave the world film and world hero affected.

`ground_shadow_policy.gd` selects only exact-path, verified flat ground receivers
and disables **their casting**. It preserves receiving materials, visibility,
collision and all hero/building/raised-platform casters. Preserve that whitelist
and its dimensions; do not use a broader shadow-caster disable to hide this issue.

## Acceptance before source promotion

Compare matched baseline and candidate with **shadows still enabled** in both
Courtyard and Confluence, day and night:

- Face front/three-quarter and posed neck/shoulder: remove the triangles and
  scalp stippling while retaining facial depth and cast shadow detail.
- Normal gameplay distance: heels/soles must remain grounded; bow, hands,
  clothing, columns and raised platforms must retain credible shadow contact.
  Inspect for detached shadows, thin-geometry leaks and washed-out shadow edges.
- A short moving-camera/caster sequence across a cascade transition: inspect
  contact drift, edge swimming and split changes. A portrait still cannot close
  these motion checks. Preserve the user's shadows-off option and test restoring
  shadows on after day/night changes.

Use the smallest of the actually reviewed bias combinations that removes the
artifact without visible detachment. A combined depth/normal adjustment can be
accepted as a bounded profile, but does not attribute the improvement to either
parameter individually.

## Required regression and source identity impact

After any accepted source change, run:

1. `tests/production_lighting_quality_cases.gd`: both policies, shadow option,
   light allocations, actual imported ground receivers, other casters/collision.
   Existing courtyard bounds at line 43 and world normal-bias bound at line 72
   encode the superseded 0.025 / 0.35 profile. Update only those intentional
   bounds and their rationale after actual art acceptance; retain all ownership
   and receiver counterexamples. These property bounds do not prove contact.
2. `tests/world_presentation_cases.gd`: its line 78 normal-bias ceiling is 0.6;
   update intentionally if a 1.0 profile is accepted. Retain the 72 m budget,
   actual floor/target rays and settings/collider checks.
3. `tests/world_lighting_cases.gd`: unchanged light budget, phase/reconfigure,
   72 m distance and shadows-off behavior.
4. `tests/hero_atmosphere_cases.gd` and
   `tests/hero_environment_adversarial_cases.gd`: upstream settings ownership,
   restore/reconfigure and practical-light constraints.

The first suite is already in `tools/run-quality-checks.py` as
`lighting-properties`; world lighting also runs directly from cloud setup and
CI. The visual runner captures all runtime files, so its next complete receipt
must use the final lighting sources. Existing rejected/earlier receipts retain
their original source hashes.

Runtime-wide capture/export/package identities change for either policy edit.
New Courtyard and Confluence renders and any final action film must pin final
policy bytes. The native content contract currently pins fifteen gameplay/owner
files and excludes both lighting policies: a lighting-only change does **not**
require another wire/content-contract revision. Do not edit historical catalogs
or earlier release receipts to match new art.

No runtime or test files were changed, and no engine or render calls were made
for this review.
