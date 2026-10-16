# Deadlock player feedback: bounded firsthand sample

Reviewed 16 October 2026 UTC. Official Reddit access succeeded after an earlier network restriction changed. This report uses the returned public post/comment text, not the previously inaccessible Google share link, generated GitHub summaries or imagined observations of gameplay. It informs original YUGA experiments; it does not verify Deadlock bugs, current balance or proprietary implementation.

## Sample and reading boundary

Two successful official-API collections at **18:37:55 and 18:40:55 UTC** used **26 requests**. Deduplication by permalink gives **40 posts and 145 comments**: the initial 40/69 sample, followed by eight existing threads and 86 comments, with ten overlapping comments. Post dates span **13 January–16 October 2026**. These are collected-record counts, not counts of substantive human reviews; the sample includes moderator/bot replies, jokes, media-only posts and removed-text placeholders.

The first collection took ten posts each from New, Top/month, a criticism/new-player search, and an enjoyment/improvement search. Its round-robin comment selection included several art/meme threads. We therefore selected eight existing design-relevant threads for at most 15 top comments each. Comment depth was at most two; no expanded-comment crawl occurred. Search terms are selection rules, not sentiment labels. Ranking, thread selection and the follow-up all introduce bias. No prevalence, satisfaction percentage or retention effect can be estimated from this sample.

We read all 40 post titles and initial body excerpts up to 1,600 characters, fuller text for the selected threads, the focused follow-up's 86 comment records, and relevant initial replies. This is not exhaustive coding of every initial comment or full reading of every long post. In the deduplicated records, two posts and two comments remain truncated, and 15 posts have no body text; when observations overlap, these counts retain the longer text. Linked images, video and commercial gameplay were **not viewed**. Exact game versions are generally unknown, and older complaints may have changed. Author names and personal/medical disclosures are excluded from this report. Raw sanitized corpora remain outside the repository. [Collection evidence](DEADLOCK_FEEDBACK_EVIDENCE.json) records hashes, dates, counts and selection without republishing the corpus.

## Evidence-linked themes

### F1 — Knowing controls does not ensure noticing the right cue

The [23 February situational-awareness post](https://www.reddit.com/r/DeadlockTheGame/comments/1rceuk1/advice_how_do_i_fix_tunnel_visionpoor_situational/) describes enjoying the game and practicing mechanics, yet missing important combat/map cues. This is a firsthand difficulty report, not an accessibility diagnosis or measured UI failure. A [small-goals reply](https://www.reddit.com/r/DeadlockTheGame/comments/1rceuk1/advice_how_do_i_fix_tunnel_visionpoor_situational/o6xszvq/) recommends improving one fundamental rather than judging only wins; the [author's response](https://www.reddit.com/r/DeadlockTheGame/comments/1rceuk1/advice_how_do_i_fix_tunnel_visionpoor_situational/o6xtums/) says that framing helps motivation. Both replies are from 23 February. A [longer coaching reply](https://www.reddit.com/r/DeadlockTheGame/comments/1rceuk1/advice_how_do_i_fix_tunnel_visionpoor_situational/o6y7fbu/) recommends a narrow practice/review focus.

**YUGA → H-3/H-4:** test one optional contextual goal, such as recognizing an incoming windup, alongside a stable lane objective. Do not respond with more simultaneous tutorial text or mandatory daily practice. **Gate:** a first-time participant identifies the objective and one dangerous cue without coaching, then can dismiss the hint. Existing automation verifies controls, menu neutrality and loading cancellation. The proposed optional-goal interaction and human outcome remain untested.

### F2 — Newcomer frustration and peer teaching have different remedies

The [1 February newcomer complaint](https://www.reddit.com/r/DeadlockTheGame/comments/1qtf225/cant_imagine_how_many_new_players_this_game_just/) reports mismatched opponents when trying the game with friends. Its broad numerical claims are unsupported. Crucially, the collected post includes the author's later update that ranking changed and their games became much better; the update's exact edit date is unavailable. It cannot honestly be presented as an unchanged current failure.

The [9 February teaching thread](https://www.reddit.com/r/DeadlockTheGame/comments/1qzyr18/can_we_normalize_teaching_new_players_instead_of/) asks for constructive help rather than hostility. A [tutorial reply](https://www.reddit.com/r/DeadlockTheGame/comments/1qzyr18/can_we_normalize_teaching_new_players_instead_of/o4eqo1b/) wants match progression and navigation explained, not only isolated controls. A [counterpoint](https://www.reddit.com/r/DeadlockTheGame/comments/1qzyr18/can_we_normalize_teaching_new_players_instead_of/o4f4vaj/) argues that peers should not have to teach every lobby. These are competing experiences, not a community-wide toxicity finding.

**YUGA → H-6/H-3:** explicitly label Practice/bots/invited rooms and provide useful in-app help. YUGA has no ranked matchmaking to “fix”; do not imply one exists. **Gate:** newcomers can distinguish a bot session from a human invitation and find current controls without relying on another player. Test help without forcing experienced players through a tutorial.

### F3 — Explain playstyle and upgrade reasons, not a supposed universal build

A [16 October, 18:23 UTC post](https://www.reddit.com/r/DeadlockTheGame/comments/1x7nw48/which_heroes_gameplay_wise_are_similar_to_shiv/) enjoys several heroes but cannot infer role similarities or why public builds emphasize particular damage types. A [reply](https://www.reddit.com/r/DeadlockTheGame/comments/1x7nw48/which_heroes_gameplay_wise_are_similar_to_shiv/ph5rbvc/) explains alternative builds and patch dependence. Its balance advice was not independently verified. Another [reply](https://www.reddit.com/r/DeadlockTheGame/comments/1x7nw48/which_heroes_gameplay_wise_are_similar_to_shiv/ph5r8hw/) stresses hero differences.

**YUGA → H-3:** keep each hero's intended range, first useful action, counter and actual upgrade effect understandable. **Gate:** after reading the existing roster/upgrade UI, a participant can explain one tradeoff and the purchased stat change. This supports clearer explanation, not adding a commercial game's item system or declaring an optimal build.

### F4 — A visible symbol can imply the wrong interaction

The title of a [4 March post](https://www.reddit.com/r/DeadlockTheGame/comments/1rksfsc/i_hate_this_thing_as_a_new_player_i_kept_thinking/) says a world marker looked like a pickup. Its body is empty and its image was not inspected. A [reply](https://www.reddit.com/r/DeadlockTheGame/comments/1rksfsc/i_hate_this_thing_as_a_new_player_i_kept_thinking/o8n5xgj/) reports players touching/punching it. However, [one commenter](https://www.reddit.com/r/DeadlockTheGame/comments/1rksfsc/i_hate_this_thing_as_a_new_player_i_kept_thinking/o8mvvf3/) describes a boss-status indicator while [another](https://www.reddit.com/r/DeadlockTheGame/comments/1rksfsc/i_hate_this_thing_as_a_new_player_i_kept_thinking/o8mybgp/) disputes that interpretation. The marker's actual semantics remain unresolved here.

A separate [23 June, 20:04 UTC comment](https://www.reddit.com/r/DeadlockTheGame/comments/1udr7ht/weekly_feedback_topic_46_obvious_jank_alpha/ote4iln/) reports discovering a stacking status late because its indicator appeared apart from other buffs.

**YUGA → H-2/H-4/H-5:** distinguish decorative signs, available targets, unclaimed shards and confirmed rewards; cluster status duration consistently. **Gate:** a participant distinguishes shared gold, an unclaimed shard, a confirmed secure/steal and the temporary buff after one encounter. Server wallet correctness and a screenshot alone cannot close this comprehension gate.

### F5 — Route and objective complaints need opposing-side checks

The [19 April camp-door thread](https://www.reddit.com/r/DeadlockTheGame/comments/1spqw43/new_player_here_can_someone_explain_why_this_door/) asks about an apparently asymmetric route; its image was not viewed. One [reply](https://www.reddit.com/r/DeadlockTheGame/comments/1spqw43/new_player_here_can_someone_explain_why_this_door/oh2e2v3/) says it disrupts a familiar loop. [Other replies](https://www.reddit.com/r/DeadlockTheGame/comments/1spqw43/new_player_here_can_someone_explain_why_this_door/oh27qb8/) speculate about deliberate experimentation; that is not an official explanation. A [counterpoint](https://www.reddit.com/r/DeadlockTheGame/comments/1spqw43/new_player_here_can_someone_explain_why_this_door/oh2gg94/) says different cover favors the other base in some circumstances.

The [16 October objective-space post](https://www.reddit.com/r/DeadlockTheGame/comments/1x7nisu/i_want_more_space_to_fight_objectives/) argues that confined objectives favor large-area abilities, while acknowledging their intended purpose. The focused response contained only an automated reply: this is **one design opinion**, not corroborated balance evidence.

**YUGA → H-4/H-5:** test camp approaches, visible blocked routes, retreat paths and objective cover from both teams using YUGA's own radii. **Gate:** actual solids match readable geometry, movement does not trap the player, and mirrored route cases pass. Do not enlarge arenas or weaken abilities solely from these posts.

### F6 — Separate reported jank from diagnosis, and polish from asset quantity

The [23 June weekly jank thread](https://www.reddit.com/r/DeadlockTheGame/comments/1udr7ht/weekly_feedback_topic_46_obvious_jank_alpha/) explicitly solicits criticism. Replies report [collision snags](https://www.reddit.com/r/DeadlockTheGame/comments/1udr7ht/weekly_feedback_topic_46_obvious_jank_alpha/ote2gwn/), a [death-damage display problem](https://www.reddit.com/r/DeadlockTheGame/comments/1udr7ht/weekly_feedback_topic_46_obvious_jank_alpha/ote2b3e/) and [performance degrading across matches](https://www.reddit.com/r/DeadlockTheGame/comments/1udr7ht/weekly_feedback_topic_46_obvious_jank_alpha/ote23m5/). The last reply guesses at a memory leak; we did not reproduce or diagnose one. Another [reply](https://www.reddit.com/r/DeadlockTheGame/comments/1udr7ht/weekly_feedback_topic_46_obvious_jank_alpha/ote2ggb/) notes an existing unstuck control, a partial remedy rather than proof there is no issue.

[Jungle appearance](https://www.reddit.com/r/DeadlockTheGame/comments/1udr7ht/weekly_feedback_topic_46_obvious_jank_alpha/ote0lw0/) and [camp architecture](https://www.reddit.com/r/DeadlockTheGame/comments/1udr7ht/weekly_feedback_topic_46_obvious_jank_alpha/ote2p7d/) also receive subjective criticism. This motivates coherent encounters, not an inference that more polygons improve play.

**YUGA → H-4/H-7:** retain authoritative colliders independent of ornamental meshes; inspect corners and repeated join/end/replay resource lifecycles. **Gate:** record renderer/resource state across repeated sessions and compare under the same hardware/settings; verify actual unit identity and attack cues at gameplay scale. Current bounded software-render checks do not establish consumer-device performance or human art approval.

### F7 — Preserve movement mastery while making actions discoverable

The [28 July movement-naming post](https://www.reddit.com/r/DeadlockTheGame/comments/1v98hlz/unpopular_opinion_we_should_agree_to_swap_the/) challenges terminology. A [reply](https://www.reddit.com/r/DeadlockTheGame/comments/1v98hlz/unpopular_opinion_we_should_agree_to_swap_the/p0c0shr/) dislikes needing external instruction for hidden movement techniques. A constructive [counterproposal](https://www.reddit.com/r/DeadlockTheGame/comments/1v98hlz/unpopular_opinion_we_should_agree_to_swap_the/p0btwae/) preserves depth while adding a visible contact/brace cue. Comments calling techniques bugs are opinions, not verified engine findings.

**YUGA → H-3/H-4:** use consistent control names and visible action commitment/release. **Gate:** text, input and actual motion agree on supported actions. This does not justify adding advanced traversal during the current freeze.

## Prioritized next review

1. Observe one first-time Practice encounter: identify objective, avoid a cue, interact with a camp, explain the rewards, return to lane. Test F1/F2/F4 together without coaching; record both mistakes and successful interpretations.
2. If that observation exposes confusion, revise the smallest relevant help/status/role explanation, then repeat with a different participant. F3/F7 support clarity, not a larger feature list.
3. Run a bounded repeated-session and mirrored-route regression for F5/F6, retaining exact build/settings and resource measurements. Diagnose any failure before changing architecture or balance.

These recommendations were formulated **after** the existing YUGA safeguards and many technical checks. They are not retroactive claims that Reddit research caused those changes. [PLAYER_EXPERIENCE_REVIEW.md](../PLAYER_EXPERIENCE_REVIEW.md) owns implementation/gate status. [DEADLOCK_ENGINEERING.md](DEADLOCK_ENGINEERING.md) separately records actual source/REA evidence and the GitHub archive: its title-only snapshots and generated secondary summaries are weaker evidence than this official text sample and are not additional independent reviews.
