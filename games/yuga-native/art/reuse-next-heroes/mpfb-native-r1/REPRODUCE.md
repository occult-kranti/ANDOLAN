# Reproduce the isolated candidate

Run from the repository root. Use Blender 4.3.2, Godot 4.6.3, Python/NumPy, existing imported native resources and fresh output directories. The canonical body is never overwritten. The source `.blend` is already archived in the [parent packet](../../../docs/research/reuse-next-ten/reuse-advisor-hero/REPRODUCE.md); recover it with that packet's verified helper.

```sh
blender --background --disable-autoexec --threads 2 --python-exit-code 1 \
  --python games/yuga-native/tools/hero-donor-groom/mpfb_native/build_candidate.py -- \
  --source /absolute/recovered/rama-mpfb-density-material-study.blend \
  --output /absolute/fresh/cards
```

The current builder includes the reviewed sRGB correction. The **actual recorded execution** was the retained R1 builder, followed by `repair_color_space.py` over the saved R1 master. The R1 executed source is preserved byte-exact in `evidence/build-candidate-executed-r1.py.gz`. Rebuilding a new `.blend` serialization need not recreate an old file hash; verify geometry, image bytes, settings and source identities again. No claim is made that the revised single-command route was fully re-executed here.

The recorded no-rebake repair command is:

```sh
blender --background --disable-autoexec --threads 1 --python-exit-code 1 \
  --python games/yuga-native/tools/hero-donor-groom/mpfb_native/repair_color_space.py -- \
  --receipt /absolute/original/cards-r1/receipt.json --output /absolute/fresh/color-repair
```

Use the portable existing card asset for immediate native inspection. Build the exact original-byte masked comparison body from the small proven selection:

```sh
python3 games/yuga-native/tools/hero-donor-groom/mpfb_native/masked_glb.py \
  --source games/yuga-native/assets/heroes/rama-hero.glb \
  --mask games/yuga-native/art/reuse-next-heroes/mpfb-native-r1/source/nape-mask.json \
  --output /absolute/fresh/rama-nape-masked.glb

godot --headless --path games/yuga-native \
  --script res://tools/hero-donor-groom/mpfb_native/probe_native.gd -- \
  --base=/absolute/fresh/rama-nape-masked.glb \
  --hair=/absolute/ANDOLAN/games/yuga-native/art/reuse-next-heroes/mpfb-native-r1/candidate/mpfb-nape-cards-near.glb \
  --output=/absolute/fresh/native-eligibility.json
```

`export_nape_mask.py` reproduces the selection proof from the parent master/fit receipt using the prior exact ordered POSITION+UV mapping. `masked_glb.py` refuses source changes, mixed selected/protected triangles and an empty retained hair region.

For the **separate rejected layered** candidate, recover the already archived [R1 sculpt](../rama-posterior-sculpt-r1/source/MASTER-RECOVERY.md) and its prior `artist_r1/carry_exact_glb.py` output `85c16967…`, then run `fit_underlayer.py --receipt <corrected-card-receipt> --underlayer <R1-GLB> --mask <nape-mask.json> --output <fresh>`. That tool uses only standard Blender projection against the exact audited nine nape components, saves a compressed numerical witness and refuses inverted/collapsed/stretched geometry. The first JSON-serialization failure and corrected second execution are retained.

Actual native raster requires the shared heavy lane and the previously qualified software raster runtime:

```sh
python3 games/yuga-native/tools/hero-donor-groom/mpfb_native/run_native_capture.py \
  --output /absolute/fresh/native-stills \
  --runtime /absolute/qualified/runtime \
  --engine /absolute/qualified/godot \
  --base /absolute/fresh/rama-nape-masked.glb \
  --hair /absolute/ANDOLAN/games/yuga-native/art/reuse-next-heroes/mpfb-native-r1/candidate/mpfb-nape-cards-near.glb \
  --phase stills --timeout 180
```

Use `--phase correction` for three candidate-only ordinary/close views. For the layered take, `--base` must be the **unmasked R1 sculpt** and `--hair` the separate projected cards. `--phase motion` would produce 120 frames at 30 Hz (4 seconds), but it was **not executed** because appearance failed. Do not spend that render budget until the root/artist accepts the revised stills.

The wrapper reuses the qualified UI-campaign helper, pins source/engine/adapter files, uses an owned fresh X display, two render threads and inherited warm cache, then stops its processes. These captures do not establish hardware FPS or human input feel. Current active source is recorded in each receipt; historical code versions remain immutable evidence.
