# Different hair route — licensed-source shortlist, no model acquired

18 October 2026. C5 is closed/rejected. This separate read-only study inspected
the existing MakeHuman cache and pinned community-reuse art catalog, then small
official GitHub metadata/license documents. No model, preview image, software,
asset pack or commercial-game extraction was downloaded or imported. No already
cached adaptable long-hair/topknot asset was found, and no candidate below is yet
qualified as containing real grouped volumetric locks.

The local MakeHuman manifest pins `makehumancommunity/makehuman` commit
`a8bc2d54ff0ac92e78ff71431b1023eda42bf482`: base OBJ, skeleton, weights and two
body targets, plus licenses. It contains no hair. Bundled data is CC0-1.0;
application code has separate terms. This does not license unrelated community
hair. The retained community-reuse art catalog covers authoring tools, materials
and mesh optimization, not a qualified prebuilt groom. The official WIP repo at
`f4e7477ced97c814ee41ff2d54f596f19ddd30ae` has only a README in its hair tree
`79cc11c69d71cc4aab57a9f5b3aab3dd546f12fb`; it supplies no candidate geometry.

## Specific official catalog candidates

The official [Hair 01 catalog](https://raw.githubusercontent.com/makehumancommunity/makehuman-static-website/883f19ca188e1cb458f2907d6f0c81187b9cf7da/content/Assets/AssetPacks/hair01.md)
labels these individual entries CC0:

| Asset / listed author | Individual source page | Possible role / known limit |
| --- | --- | --- |
| `elvs_reverse_french_braid_bun` / Elvaerwyn | `https://www.makehumancommunity.org/node/1337` | First bun candidate; name establishes a braid/bun listing, not inspected topology, editable history, or suitability around Rama's fixed tie. |
| `o4saken_long01` / punkduck | `https://www.makehumancommunity.org/node/1471` | First long-fall candidate; no verified vertex budget, solid/card classification, materials or grouping. The author is recorded exactly as the catalog lists it. |
| `rehmanpolanski_hair_bun_brown` / RehmanPolanski | `https://www.makehumancommunity.org/node/2477` | Alternative bun candidate; color/style would require original adaptation. No mesh or visual inspection yet. |

The [Hair 02 catalog](https://raw.githubusercontent.com/makehumancommunity/makehuman-static-website/883f19ca188e1cb458f2907d6f0c81187b9cf7da/content/Assets/AssetPacks/hair02.md)
describes mostly high-poly hair by Elvaerwyn and lists `elvs_braid_bun`, source
`https://www.makehumancommunity.org/node/2177`, as **CC-BY**. It is a fallback
metadata lead, not cleared reuse: the catalog does not state a CC-BY version or
provide the individual file's license text. Attribution/version/texture rights
must be verified before adopting any payload. The Hair 03 catalog explicitly
includes alpha-7 adaptations; it is a weaker first choice for this current
head/rig interface.

These are per-entry catalog declarations, not conclusions drawn from a GitHub
repository's general license or MakeHuman's bundled CC0 notice. The bun and long
individual source-page requests returned proxy `403 Forbidden`; no alternate
route or policy bypass was attempted. Thus actual file licenses, third-party
components, author provenance and visual/geometry fitness remain unresolved.
The full packs are 217 MB (Hair 01), 68 MB (Hair 02) and 38 MB (Hair 03); none was
requested. Prefer individual files, not these packs, in a future bounded task.

## Compatibility and integration plan

The catalog classifies these meshes as MakeHuman `clothes`. Expect a fitted
asset/OBJ/material workflow, but verify actual file formats and supported base
version when individual files are available. A MakeHuman proxy fitting relation
or source weight map is not a direct native Rama rig binding: the hero has its
own merged/rest-space geometry, proportions, 164-joint skeleton and animation
contract. Existing MakeHuman ancestry does not establish identical vertex IDs,
weights, units or head fit. No bone or geometry compatibility was measured here.

1. Inspect only one CC0 bun and one CC0 long candidate's individual files,
   declared licenses, texture notices, hashes and four-view geometry. Reject
   card-only, helmet/cape, unusable topology or uncertain provenance. A catalog
   name or screenshot cannot prove actual grouped locks.
2. In a fresh editable authoring copy, fit original grouped planes to the owned
   head and fixed crown/tie. Establish units/axis/rest transforms; adapt the
   gather and falling gesture without moving references or blindly stitching
   two unrelated styles. Preserve the source/rights record and all modifications.
3. Judge the same four actual clay views independently against the concept and
   the rejected C5 forms before detail or runtime preparation. Existing locks
   would provide real artist-authored geometry to adapt, rather than another
   contour/loft formula asserted to look like hair.
4. Retain the native skeleton and all nonhair/crown/eyebrow/material arrays.
   Transfer/rebuild weights only for approved principal hair; a head-only bind
   is an initial fit experiment, not long-lock motion approval. Validate shoulder,
   nape, draw/recoil and locomotion contact before promotion.
5. Only after all-view source approval derive three LODs, preserve notices and
   exact nonhair/rig/animation interfaces, then run import/deformation and fresh
   actual native gates. No commercial model or reverse-engineered client asset
   is part of this route.

## Exact metadata pins

All three catalog documents were independently matched to immutable Git blobs
and then byte-matched through the official repository's pinned commit
`883f19ca188e1cb458f2907d6f0c81187b9cf7da`:

| Document | Git blob | SHA256 / bytes |
| --- | --- | --- |
| `hair01.md` | `178fb97b837c96fd89158367bacb71c2b4d087dd` | `c2fbd374effe95da109aadbed5fa0900359b161f574c092f6d292d0503144722` / 4,865 |
| `hair02.md` | `f7f51bd1f9e6f1fbba97998f56db00598ff25400` | `22122fa60ed4c1759ddae474af8271936a72ec7b47ec49c999669c90709e405c` / 3,857 |
| `hair03.md` | `bb33c6f6601a0ca6cfd200468507e4dfc73a2285` | `ec516bd9c2f5bf09a648fbe90bcd3999c09579a22cbf03bf7891fc12f58c138b` / 2,861 |

Selected metadata/read/error records remain in
`/workspace/scratch/yuga-continuation-W3-r1/asset-research/`. Asset-pack tree
inspection used a bounded partial metadata prefix, not a complete repository
or asset audit. The immutable catalog documents above were read in full.
