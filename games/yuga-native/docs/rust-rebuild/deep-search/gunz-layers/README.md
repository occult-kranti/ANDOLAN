# Hanuman's running attack, replayed with GunZRs

A right-wrist key pair in classic YUGA's shipped Hanuman model turns **179.53° in 33.33 ms**. GunZRs and PlayCanvas agree on both authored action endpoints. They differ by **8.06°** a quarter of the way through. Adding three intermediate keys along the same rotation arc reduces the worst interpolation difference on that interval to **0.111°**. This gives the animator a specific span to inspect in Blender, before considering any change to the character exporter. [Measurements and sampled timeline](results.json) · [YUGA browser asset](../../../../../yuga/client/assets/heroes/hanuman.glb) · [Live browser animation controller](../../../../../yuga/client/hero-models.ts)

## What ran

We used the open-source GunZRs reconstruction of GunZ: The Duel. The probe fetches one pinned animation source file and its exact locked quaternion math crate. It compiles the original key sampler, transform blend, clock modes, easing and per-tick upper-layer transition body. The harness supplies compatible transform, key, speed and layer fields. It feeds YUGA's own right-handed, parent-local GLB rotations directly into the sampler. The upstream ECS, ANI parser and coordinate conversion serve the donor's model format and are outside this experiment. No GunZ media is required. [GunZRs description](https://github.com/OpenRsG/GunZRs/blob/485575b7451912ed1d62661c388663b08dce4faf/README.md) · [Sampler](https://github.com/OpenRsG/GunZRs/blob/485575b7451912ed1d62661c388663b08dce4faf/src/anim.rs#L337-L377) · [Quaternion blend and clip clocks](https://github.com/OpenRsG/GunZRs/blob/485575b7451912ed1d62661c388663b08dce4faf/src/anim.rs#L528-L548) · [Upper-layer scheduler](https://github.com/OpenRsG/GunZRs/blob/485575b7451912ed1d62661c388663b08dce4faf/src/anim.rs#L629-L657) · [Upper-layer application](https://github.com/OpenRsG/GunZRs/blob/485575b7451912ed1d62661c388663b08dce4faf/src/anim.rs#L759-L773)

PlayCanvas 2.23.3 parses the same shipped GLB and evaluates its actual tracks, layer fade and overwrite blend on CPU. The run starts 0.67 s into its 0.833 s cycle and wraps during the 0.733 s fire clip. Both implementations receive the same sampling clocks. The test compares 144 frames at 120 Hz across all 163 skinned joints, or 23,472 paired local rotations. The 299 STEP rotation tracks are checked for constant values. The largest time adjustment onto the donor's 4,800-tick-per-second grid is below 0.04 microseconds. The probe reads the YUGA fire duration cap and fade times from the live controller. It uses a first shot with no preceding action and level aim. It isolates the overwrite layer, with no previous action crossfade, aiming correction, translation, scale, mesh deformation, camera or renderer. This classic browser asset is separate from the native trial's 167-joint enhanced Hanuman. [PlayCanvas side](compare.mjs) · [Donor calling convention](driver.rs) · [Separate native-trial pose comparison](../../HERO-ANIMATION.md)

| Question | Measured result |
| --- | --- |
| Can the donor's skeleton split be used directly? | No joint matches `Bip01 Spine1`. The existing YUGA `spine03` subtree selects 120 upper joints and protects 43 lower joints. |
| Does the lower body retain its running motion? | The largest difference between donor playback and unmodified PlayCanvas run was 0.000965° on the left shin. |
| Do moving upper joints agree at authored action keys? | At full overlay weight, the worst error was 0.000028°. |
| What changes between keys at identical overlay weight? | At 0.10833 s the right wrist differs by 8.06°. The enclosing keys are at 0.10000 s and 0.13333 s. GunZRs uses spherical interpolation. PlayCanvas performs component interpolation and quaternion normalization. |
| What changes when the original schedulers control the weight? | The peak difference reaches 77.55° on the right forearm at 0.70833 s. YUGA caps `fire` at 0.60 s and fades for 0.10 s. GunZRs releases at the clip end using its supplied 0.05 s fade. The final sampled positive weights occur at 0.700 s and 0.775 s respectively. The donor also smooths its raw layer weight. |

## Blender and Rust handoff

1. Inspect `wrist.R` through 0.100–0.133 s in Blender's quaternion curves and in a side view with the weapon attached. Check that the almost half-turn belongs to the intended attack. Endpoint agreement alone cannot reveal this motion.
2. If that spherical arc is intentional, preview a targeted subdivision of this one channel. The offline test evaluates 121 positions along the existing spherical arc with PlayCanvas's actual normalized-linear blend. Zero additional keys yielded 8.077° maximum error, one midpoint yielded 0.911° and three interior keys yielded 0.111°. This predicts local angular behavior. Weapon-tip position, perceived recoil and other clips still need an art review before exporting a replacement asset.
3. For a Rust runtime port, take the split path and event release duration from the YUGA controller. Preserve the unwound running clip while the upper-body action fires. Keep the enclosed pose trace as a regression check. The donor's default naming and release timing have measurable consequences for this hero. [Pinned ancestor walk](https://github.com/OpenRsG/GunZRs/blob/485575b7451912ed1d62661c388663b08dce4faf/src/anim.rs#L414-L431) · [Measured interval](results.json)

## Reproduce

From the repository root, install the repository's locked Node dependencies and use Python 3.12+, Node and Rust on PATH. The first run downloads 2 digest-pinned files. The cache can then be reused offline. The command writes its candidate trace outside version control so the checked-in result can be compared.

```sh
npm ci
probe=games/yuga-native/docs/rust-rebuild/deep-search/gunz-layers
cache="$(mktemp -d)"
python3 "$probe/prepare.py" "$cache"
node "$probe/compare.mjs" "$cache/probe" "$cache/results.json"
diff -u "$probe/results.json" "$cache/results.json"
```

The comparison exits nonzero for missing joints, changed motion-policy hooks, unsupported interpolation, moving STEP tracks, nonfinite samples, collapsed masking, or a larger-than-baseline angular error. Review small floating-point differences across toolchains and architectures with the embedded angular tolerances. The repository carries the probe and measurements. The executable and downloaded dependencies remain in the selected cache. GunZRs publishes its implementation under Apache-2.0. The pinned glam 0.32.1 math crate offers MIT or Apache-2.0. [GunZRs license](https://github.com/OpenRsG/GunZRs/blob/485575b7451912ed1d62661c388663b08dce4faf/LICENSE) · [Donor dependency lock](https://github.com/OpenRsG/GunZRs/blob/485575b7451912ed1d62661c388663b08dce4faf/Cargo.lock) · [glam 0.32.1](https://docs.rs/crate/glam/0.32.1) · [Source digests and exact extracted line ranges](prepare.py)
