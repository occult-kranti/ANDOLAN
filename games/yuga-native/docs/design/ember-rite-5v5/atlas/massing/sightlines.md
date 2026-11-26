# Sightlines in the exported 3D maps

Blender imported the four district floor models and cast 48 sight rays through their triangles. Each of the 8 sights in the [drawings](../README.md) uses a pair of grounded endpoints. Each column raises both ends by the stated height above their local floors and tests the segment in both directions. Heights are example probes for low, standing and elevated views.

| Map | Sightline | Floor at start / end (m) | 0.9 m | 1.7 m | 2.8 m | First hit at 1.7 m, forward / reverse (m) |
| --- | --- | ---: | --- | --- | --- | ---: |
| Mandala Rift | Bell screen check | 0.00 / 0.00 | Bell screen | Bell screen | Clear | 2.50 / 9.50 |
| Mandala Rift | Market near lip | 0.00 / 0.00 | Clear | Clear | Clear | — / — |
| Lanka | Deck crossing | 5.00 / 5.00 | Clear | Clear | Clear | — / — |
| Lanka | Garden entry | 1.00 / 1.00 | Clear | Clear | Clear | — / — |
| Ayodhya | Gauge descent | 1.00 / 0.00 | Clear | Clear | Clear | — / — |
| Ayodhya | Wash exit | 0.00 / 0.00 | Clear | Clear | Clear | — / — |
| Kurukshetra | Porch reveal | 3.00 / 4.00 | Ledger Screen | Ledger Screen | Ledger Screen | 11.20 / 5.87 |
| Kurukshetra | Sill to ring | 1.00 / 1.00 | Clear | Clear | Clear | — / — |

A single label identifies the same first mesh from both ends. A slash lists different first hits, starting with the direction specified in the map JSON. **Clear** means the line reached the opposite endpoint. First-hit distances are measured along that 3D segment.

## Edges that screen a standing view

For each standing ray whose first hit from the start is a cover mesh, compare the top of the mesh with the elevated ray at that same forward edge. Both values use the map's common vertical datum. A screen on higher ground can still catch a ray raised by 2.8 m at both endpoints.

| Sightline | Cover | Top elevation (m) | Elevated ray at forward edge (m) | Elevated result from start |
| --- | --- | ---: | ---: | --- |
| Mandala Rift · Bell screen check | Bell screen | 2.60 | 2.80 | Clear |
| Kurukshetra · Porch reveal | Ledger Screen | 6.40 | 6.35 | Ledger Screen |

These meshes contain floor surfaces, exposed edge skirts, ground markings and the named cover pieces. The graybox still needs the final walls, ceilings, corner cameras and heroes. A clear central view can change when the camera moves to the outside shoulder. Check each entry again with the real camera offset, avatar height, aiming ray and visibility rules on both sides.

## Corridor grades

Blender took 46,890 floor samples at most 0.25 m apart along each physical corridor, at its centre and at 46% of its width on either side. The table shows the steepest sustained centreline grade per map, plus the Sluice descents to both sites. A moving window spans at least 2 m of horizontal travel. Water measures the modeled bed. These measurements guide character-controller trials.

| District | Floor samples | Measured route | Peak grade | Window |
| --- | ---: | --- | ---: | ---: |
| Mandala Rift | 15183 | Sluice → Bazaar Sanctuary | 25.6% | 2.19 m |
| Mandala Rift | as above | Sluice → Ghat Mandapa | 25.0% | 2.24 m |
| Lanka | 11025 | Fruit Stalls → Ashoka Garden | 50.0% | 2.00 m |
| Ayodhya | 11130 | Sluice Gate → Wash Steps | 25.0% | 2.00 m |
| Kurukshetra | 9552 | Gauge Bridge → Seal Porch | 33.3% | 2.00 m |

## Model identity and placement

A 2 m grid yielded 6,821 successful interior floor hits and 17,930 successful exterior misses. The occupancy checks omit samples within 0.15 m of the analytical boundary to allow for the tessellated curves.

After import, Blender checked the positions and local floor heights of 60 room anchors and the ground-relative top elevation and footprint of 26 cover meshes against the map JSON within 0.02 m. North is positive Y in Blender and negative Z in glTF. Dropping a ray onto the continuous floor mesh supplies the height at each probe end. Sightline casts then use the whole floor-study scene. The [separate architectural models and doorway tests](architecture-checks.md) use the same map registration.

The floor's embedded SHA-256 must match its full JSON input. Prefixes below identify the tested files.

| Map GLB | Map JSON SHA-256 prefix | GLB SHA-256 prefix |
| --- | --- | --- |
| [Mandala Rift](mandala.glb) | `52574c462698584b` | `d6da6f4758542823` |
| [Lanka](lanka.glb) | `ab2560e4156caa6d` | `e52d61f531a2f69a` |
| [Ayodhya](ayodhya.glb) | `db8f045cdbb7b0a7` | `887de1fc5e5854df` |
| [Kurukshetra](kurukshetra.glb) | `c24b4573aa87c9ed` | `92e46a1d1dbd8e3d` |

Reproduce from the repository root with Blender 4.3.2. Omit the final `-- --check` to regenerate this report.

```sh
blender -b --factory-startup -t 1 --python-exit-code 1 --python games/yuga-native/docs/design/ember-rite-5v5/atlas/probe_massing.py -- --check
```
