# Exact CC0 hair assets — bounded GitHub mirror check

18 October 2026. **No exact, officially linked GitHub payload was verified.**
No model is proposed for download; no payload URL/license/hash qualification can
be supplied from this pass. No model, pack, preview image or software was
acquired. C5 and all canonical geometry remain unchanged.

The targets remain the official Hair 01 catalog entries
`elvs_reverse_french_braid_bun` (Elvaerwyn, node 1337), `o4saken_long01`
(punkduck, node 1471), and `rehmanpolanski_hair_bun_brown` (RehmanPolanski,
node 2477). The pinned catalog labels each CC0, but a catalog declaration is not
verification of an individual payload's included license, textures or geometry.
See the separate `FUTURE_HAIR_ASSET_ROUTE.md` for exact catalog pins.

## Official sources checked

| Source | Exact inspected evidence | Result |
| --- | --- | --- |
| MakeHuman GitHub organization | `https://api.github.com/orgs/makehumancommunity/repos?per_page=100&page=1`; all 25 returned public repositories | No separate published community-hair payload repository was listed. This is the inspected public listing, not proof that no mirror exists anywhere. |
| Official WIP assets | `communityassets-wip` hair tree `79cc11c69d71cc4aab57a9f5b3aab3dd546f12fb` | README only, no hair payload. Already pinned in the preceding study. |
| Official legacy archive | `googlecode/makehuman/data/hair` directory | Only `clear.thumb`; no exact target asset. |
| Official MakeHuman 2 | Commit `13b7ff56b388826bee548bc18d78c8d492cf3512`, recursive hair tree `13efab8612d6164838d652d2176c256168de971e` | `hm08/selection_filter.json` and two generic icons, no OBJ/mhclo/blend or exact target. No icons were downloaded. |
| Official downloader source | `community-plugins-assetdownload/8_asset_downloader/assetdb.py`, immutable Git blob `ef4e840f0db233d06306db67e9450024a936af84` | Lines 318/320 obtain the asset database from `http://www.makehumancommunity.org/sites/default/files/assets.json`, not a GitHub payload mirror. No database request or blocked-host retry was made. |
| Official remote-asset descriptor | `remoteasset.py`, Git blob `c45ae4f19fa83ae15b8c57ea96f05a5e7895bd2d` | Reads the individual asset's `license` field from remote metadata; the source does not supply these three assets' actual files or licenses. |
| Official MakeHuman 2 package loader | `getpackages.py`, Git blob `ab79deb48545a4f0d26192d46814800b8a142a54` | Gets packs from configured MakeHuman file servers; no author-linked GitHub copy of a target was established. No pack request ran. |

The official static website's `old_data/OldSite` root contains Documentation,
FAQ and Uncategorized sections; it did not provide an asset-repository mirror
at that level. No complete historical-site audit is claimed.

Exact-spelling public GitHub profile metadata was also checked as identity
leads, without treating matching names as proof of authorship. `Elvaerwyn`
returned 404; `Punkduck` returned zero public repositories and no name/blog/bio;
`RehmanPolanski` returned zero public repositories, no blog and bio `LSL`.
Neither returned profile establishes a MakeHuman author link. No untrusted fork,
search-result mirror or guessed model URL was scraped or followed.

## Compatibility and remaining bridge

Because no actual payload was identified, file size, solid/card topology,
vertex count, grouped-lock quality, units, base-version fitting, textures and
rig/weight compatibility remain **unmeasured**. There is no justified claim of
an adaptable <=10 MB model or direct compatibility with Rama's 164-joint rig.
The existing head/crown/tie and native nonhair/animation arrays remain protected;
shared MakeHuman ancestry alone cannot establish matching vertex IDs or weights.

A useful next bounded acquisition needs an official asset-page/author link and
an inspectable individual file license plus file size/hash before a model
request. The previous direct official node-page reads returned proxy 403; this
pass did not retry them through another host, proxy, account or mirror. Normal
GitHub metadata requests used the existing environment authentication unchanged.
The source/rights bridge is therefore still open, and no download or integration
approval is implied. The desired licensed-model route remains distinct from
another C5 geometry loop.

Small metadata/source read records are retained at
`/workspace/scratch/yuga-continuation-W3-r1/asset-mirror-research/`. Selected
immutable official source blobs were read; no downloaded plugin was installed
or executed and no implementation was copied into the game.
