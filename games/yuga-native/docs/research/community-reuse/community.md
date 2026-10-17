# Community evidence for the next reuse trials

Reviewed 17 October 2026 against source commit `7c86cd430e2c878b4f5e6ba1b21f562b73fdc32f`. **No fresh Reddit posts or comments were obtained.** The supplied application credentials worked, but the official public-community endpoint returned HTTP 403. The retained mythology report supports several small design hypotheses; there is no inspected community evidence here for ranking graphics or animation software as “best.” [The machine-readable receipt](community.json) records the distinction.

## Actual access and coverage

| Check performed in this pass | Result and implication |
| --- | --- |
| Managed environment status and `/etc/codex/network-policy.json` | Connected; current observations; restricted HTTP policy with enforcement state `unknown`; neither Reddit host appears in the reported effective allowlist. A saved configuration draft does not establish current API access. |
| `GET https://www.reddit.com/r/gamedev/about.json`, 21:40:11 UTC | HTTP **403**, `text/html`; one request, no redirects, no authentication. No explicit domain-policy marker or `x-proxy-error-code` was identified. Denial origin remains unknown; the body was discarded. |
| Existing collector's `--check-config` on the user-supplied external attachment | Fixed `invalid_config` result. Presence-only diagnosis then confirmed all required fields; six extra metadata fields caused strict-format rejection. This was a format issue, not missing credentials. |
| Official application OAuth plus `GET https://oauth.reddit.com/r/gamedev/about`, 21:50:38 UTC | Application authentication **succeeded**; the public-community request returned **HTTP 403**. Two requests total, before any search or comment request. No raw authentication/error body was retained. |
| Current corpus | **0 posts, 0 comments, 3 total HTTP requests** across the public check and official workflow. Current existence/public status of all proposed communities remains unconfirmed. |
| Existing collector self-test | `python3 games/yuga/tools/collect-reddit.py --self-test`: exit 0, **19 dummy-only checks passed**, no network. |
| External normalization/preflight helper | **11 dummy-only checks passed**. Inert allowlisted keys were selected in memory; only the required three fields entered the existing application-authentication reader. No secret copy, account login, posting, voting, private access or attachment-content modification. |

The normal configured proxy and TLS verification remained active. No alternate host, relay, account or policy bypass was attempted. The auth success establishes usable application credentials for that exchange; it does not establish permission to read a community. No extra credential or duplicate configuration request is needed to explain this result.

The final live command was `python3 /tmp/yuga-community-research-20261017/official-preflight.py <authorized-external-config-path>` (exit 2, `http_403` at public metadata). The sanitized public and official receipts are retained at `/tmp/yuga-community-research-20261017/access-check.json` and `official-preflight.json`; their relevant fields and helper hash are also in `community.json`. The placeholder avoids republishing the attachment locator. Earlier parse-only failures made zero requests.

## Retained evidence actually reviewed

This pass read the existing [environment/mythology report](../../../../yuga/docs/ENVIRONMENT_MYTHOLOGY_RESEARCH.md), [its source ledger](../../../../yuga/docs/research/ENVIRONMENT_RESEARCH_SOURCES.json), the [coastal-map report](../../../../yuga/docs/LANKA_COAST_RESEARCH.md) and [its source ledger](../../../../yuga/docs/research/LANKA_COAST_SOURCES.json). It did **not** reread the historical raw posts/comments or their linked media.

| Historical run, 16 October 2026 | Retained post records | Retained comment records | Requests | What is available now |
| --- | ---: | ---: | ---: | --- |
| `r/IndianMythology`, 19:10:29 UTC | 7 | 5 | 10 | Report, links, retrieval metadata and corpus hash; raw file absent |
| `r/hinduism`, 19:10:55 UTC | 12 | 16 | 10 | Report, links, retrieval metadata and corpus hash; raw file absent |
| Combined mythology sample | 19 | 21 | 20 | The historical ledger labels these unique records; uniqueness was not recomputed in this pass |
| `r/gamedev`, `r/gamedesign`, `r/IndianGaming`, 19:37:22–28 UTC | 0 | 0 | 6 | Each official run stopped at public metadata with HTTP 403 |

Comment counts mean records actually retained, not the submission's advertised comment totals or independent expert opinions. The old report explicitly includes automated, promotional and very short responses. Crossposts or shared underlying stories were not deduplicated as independent ideas in this pass because the raw samples are missing. The two historical mythology communities were confirmed public during those earlier runs; that finding is not a current access check. The historical Deadlock player-feedback corpus concerns a different question and is not counted as graphics-tool research.

The documented `/tmp/yuga-reddit-research` directory is absent. Filename checks under `/tmp` and `/workspace/tooling` found no historical raw Reddit sample. A wider filename-only check found an unrelated saved TF2 HTTP 403 response under `/workspace/scratch`, which is not a usable community corpus. Neither hashes nor surviving paraphrases reconstruct missing comments.

## Source-linked hypotheses for small trials

These are **paraphrases of the retained report**, with original permalinks for a later context check. No fresh primary-source reading or community consensus is implied.

| Retained observation | Next YUGA task and observable acceptance |
| --- | --- |
| A [9 September character-interpretation discussion](https://www.reddit.com/r/IndianMythology/comments/1wbwmkl/can_we_talk_about_the_kauravas_without_the/) sought moral complexity; a [10 September reply](https://www.reddit.com/r/IndianMythology/comments/1wbwmkl/can_we_talk_about_the_kauravas_without_the/p8w6gvx/) disputed the breadth of its characterization. A separate [8 September source-location question](https://www.reddit.com/r/hinduism/comments/1walhnh/the_bhanumatikrishna_story_mahabharata_passage_or/) shows uncertainty about a circulated story. | **Content:** attach edition, passage and adaptation notes to one Rama visual/ability brief; retain sporting team identities and avoid reducing an entire tradition to good/evil factions. Acceptance: every inherited narrative claim has a located passage; original game mechanics are labeled as adaptation; an independent reader can trace both. |
| A [13 February mandala post](https://www.reddit.com/r/hinduism/comments/1r3e19c/mandalas_are_spiritual_maps_as_a_window_to_the/) made broad cross-tradition claims and attracted appreciation/promotion. Its historical and therapeutic claims were not validated. | **World art:** continue one original radial court using the existing literary/architectural brief. Acceptance: two exits and orientation landmarks remain readable in matched day/night gameplay frames; a specific sacred-plan reconstruction claim requires separate sources. The thread supplies a question, not a plan or asset license. |
| A [23 October 2025 lamp discussion](https://www.reddit.com/r/hinduism/comments/1odqqqp/make_diwali_green_abstain_from_fireworks_return/) favored oil lamps; [a reply](https://www.reddit.com/r/hinduism/comments/1odqqqp/make_diwali_green_abstain_from_fireworks_return/nkwe24i/) disputed its framing of tradition. Pollution and historical assertions were not verified. | **Lighting/VFX:** test a small reused lamp mesh/material set with a bounded light budget. Acceptance: decorative lights remain distinct from loot and ability cues at day/night and low/high quality, with actual frame-cost measurements. This is a readability decision, not a religious ruling. |
| A [7 October carving post](https://www.reddit.com/r/hinduism/comments/1wzjlyq/700_year_old_carvings_of_hanuman_and_garuda_oc/) and [location reply](https://www.reddit.com/r/hinduism/comments/1wzjlyq/700_year_old_carvings_of_hanuman_and_garuda_oc/pec8tp2/) offered a possible heritage lead; images were not inspected or licensed. | **Reference acquisition:** verify provenance and rights against an institutional/source record before creating a reference sheet. Acceptance: creator/date/site/rights fields are supported; no photo, carving mesh or promotional artwork is imported on the strength of the thread. |

None of these observations establishes an animation workflow or software license. The coastal report's glTF Transform and Spector.js mentions came from earlier project/source inspection, explicitly **not** community recommendations. The native reuse packets must choose tools using upstream licenses, version compatibility and measured trials.

## Bounded follow-up after the access condition changes

Reuse [the existing collector](../../../../yuga/tools/collect-reddit.py) for its supported communities. It already permits `gamedev`, `gamedesign`, `IndianGaming`, `IndianMythology` and `hinduism`. `godot`, `blender` and `gamedevassets` are **candidate names**, outside its current allowlist; their existence/public status and any narrowly reviewed collector extension remain pending. No general-purpose URL fetcher or broad subreddit scrape is proposed.

For each accepted community, first validate the exact `/about` response as public, non-quarantined and non-NSFW. Then use four relevance-ranked, last-year searches with `restrict_sr=on`, at most **2 post slots per search, 8 posts, 2 comment threads, 3 comments per thread, 6 comments, 10 HTTP requests including auth/errors/retries, and 120 seconds**. Stop after one access refusal; do not exhaust the budget against a blocked endpoint. No pagination, account histories or `morechildren` expansion. Start with `gamedev` and `IndianMythology` only: at most **20 requests, 16 posts and 12 comments**; expand only if a specific unresolved question warrants it.

The existing `gamedev` queries are `(animation OR VFX) AND (readability OR telegraph OR clarity)`, `(ability OR abilities OR combat) AND (counterplay OR telegraph OR readability)`, `("level design" OR map OR lane) AND (route OR water OR swamp)`, and `("open source" OR Blender OR Godot) AND (animation OR workflow OR production)`. The existing mythology queries cover `(Ramayana OR Mahabharata) AND (passage OR translation OR source)`, `stepwell OR courtyard OR mandala OR observatory`, festival lamps, and `yaksha OR naga OR Garuda OR Jatayu`.

If the broader art/animation question remains unresolved, a separately reviewed four-query replacement may use:

| Candidate community | Specific follow-up queries; not yet executed |
| --- | --- |
| `godot` | `("Godot 4" AND glTF AND animation)`; `(retargeting AND (root motion OR foot sliding))`; `((materials OR shader) AND profiling)`; `((open source OR plugin) AND production)` |
| `blender` | `((rigging OR animation) AND glTF)`; `((NLA OR constraints) AND bake AND export)`; `((normal map OR tangent) AND seams)`; `((open source OR addon) AND game assets)` |
| `gamedevassets` | `((CC0 OR public domain) AND (material OR texture))`; `((CC-BY OR attribution) AND asset)`; `((animation OR rig) AND license)`; `((source file OR blend) AND game)` |
| `IndianMythology` focused follow-up | `(Rama AND (translation OR passage OR source))`; `((Ramayana OR Mahabharata) AND adaptation)`; `((bow OR attire OR ornaments) AND source)`; `((Lanka OR Ayodhya) AND (description OR translation))` |

For any later result, retain canonical post/comment links, creation/retrieval dates, query and rank, truncation flags and the distinction between promotional material and a reported limitation. Deduplicate permalinks and shared crosspost targets before counting viewpoints. Look for an incompatible-export or workflow-failure counterexample alongside endorsements. Community suggestions can nominate one bounded tool trial; upstream evidence and the actual YUGA asset test decide adoption.

The next owner is the research/reuse coordinator. Resume the official metadata check only after a meaningful access/configuration change; application credentials already proved usable. Keep raw samples external and publish only necessary source-linked paraphrases. No collector, runtime asset or shared production-roadmap file was changed by this packet.
