# Inactive S4 diadem comparison

The original rail refit is ready for a matched image review. The source, stored frames, retained near-hand replay and actual import checks passed. Both complete native-scene headless preflights passed with four views each; this is projection/input evidence, not a rendered art decision.

Frozen children are `/tmp/yuga-s4-diadem-review-r1/baseline` and `/tmp/yuga-s4-diadem-review-r1/candidate`. Each has a standard `.graphics-six-snapshot.json` marker and uses the new private store under that parent directory. The shared W1 base/store are unchanged. `snapshot.verify()` works on both children. There are exactly nine pair differences: three raw hero GLBs, three compiled SCNs and three MD5 receipts. All descriptors and textures match. The same helper is staged at `res://tools/graphics-six/s4_diadem_capture.gd`, inside the verified inventory.

The four requested originals, in order, are `rest-front.png`, `rest-profile.png`, `rest-rear.png` and `cast-three-quarter.png`. The first three reuse the original close-view station geometry. The fourth invokes the actual public Piercing Dawn cast against Target03, advances to 0.30 seconds of windup, pauses and frames the observed final head pose. No new bone, material, LOD or geometry owner is installed. Rejected wisps, optional upper hair and optional fletching must remain absent. The helper admits only the exact three baseline/candidate raw hashes and motion `8c3771a3…` / finish `6eb51ce8…`.

The render owner supplies an explicitly pinned engine, fresh X11 display, identical cache seed and fresh XDG directories for each branch, through their bounded process watchdog. Use identical renderer/camera/time controls. Required engine arguments after its executable are:

```text
--display-driver x11 --rendering-method forward_plus
--path /tmp/yuga-s4-diadem-review-r1/BRANCH
--audio-driver Dummy --disable-vsync --fixed-fps 30
--script res://tools/graphics-six/s4_diadem_capture.gd
-- --mode=groom-stills --output=/FRESH/ABSOLUTE/OUTPUT
```

Set `YUGA_DIADEM_REVIEW=baseline` or `candidate` to match the child. CPU affinity and the render watchdog belong to W1/root; do not pass unsupported `--max-threads`. The headless command was exercised by `preflight_review.py`; these raster commands have not been run by W3. No import or canonical asset overwrite is needed.

Before and after either run, verify both snapshot markers, all inventory files and private store blobs. Retain engine hash, exact arguments/environment controls, source-before/after, full unedited PNGs, `capture.json`, logs and any failure. Only permit raw/cache identity and explicit branch metadata to differ between the pair; actual camera/light/pose/secondary/morph/time/LOD metadata must match. Current headless reports differ only in five branch labels and the three raw GLB hashes; all recorded final bone transforms and cast controls match exactly.

Review questions: does the side/rear gold rail sit coherently on the head, without losing the separate front crest or burying the rail; is the rest/profile/rear silhouette cleaner; and does the live draw preserve crown/hand separation? Reject new clipping, jagged shading or a visually worse crown. A smaller numerical clearance is not visual acceptance. The broad dark hair cap remains unresolved, and this packet does not qualify mid/far posed clearance or continuous motion.

Reconstruction without the temporary children: use the sealed candidate GLBs plus `candidate-import-cache-r1.tar.gz` (three new SCNs/MD5s, unchanged descriptors) and the exact W1 base identified by `review-preparation-r1.json`; `prepare_review.py` records the finite overlay. Its original imported-cache input must be reconstructed under the named private import directory, never into canonical assets. The exact compiled archive and generated raw-array archives are retained under `docs/evidence/desktop-finish/S4/W3/`.
