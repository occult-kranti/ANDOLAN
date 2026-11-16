# YUGA · Sanctum

The active native direction is a **first-person 5v5 tactical hero shooter, first team to 13 wins**, with original mythic firearms and a South Asian fantasy city. Casual runs locally with one human and nine bots. Ranked is a visible future mode. This replaces the long single-match, lane-army format as the active product direction; the earlier Rama/Sangam checkpoint remains available separately.

Latest continuation: [animated Rama studio and repository handoff](studio3/README.md), with [native previews](studio3/PREVIEW.html). The hero page now has ability selectors, source-backed cost/charge facts, counterplay, explicit pose previews, and hero/first-person views.

Run from the repository root:

```sh
godot --path games/yuga-native
```

Choose **Play Casual → Deploy as Rama**. Buy equipment during the 20-second preparation, approach either sanctum, and hold F to attune the Astra. Defenders hold F to sever it. One life per round, sides switch after round 12, and Casual ends at 13 wins. A planted Astra keeps running after its attackers fall. Each match starts with 800 credits; rewards fund weapons, armor and utility in later rounds.

| Control | Action |
| --- | --- |
| WASD / Shift / Space | Move / walk / jump |
| Mouse / LMB / RMB | Aim / fire / aim down sights |
| R | Reload from finite reserve |
| Q | Solar veil: 12-second sight blocker |
| E | Measured step: short grounded dash |
| C | Ward wall: temporary physical cover |
| X | Dawn volley: three aimed piercing solar shots, earned with six points |
| Hold F | Attune or sever at the active site; movement/fire/reload interrupt |
| B / Tab | Buy at spawn / hold scoreboard |
| F1 / Esc | Hero guide / pause and settings |

The ARKA sidearm and SURYA carbine have original first-person geometry, recoil, reload and ADS motion. Rama's tactical utility replaces the old cooldown-based bow kit in this mode. The new Sangam Crossing uses existing original sandstone/indigo/brass district meshes in a smaller two-site layout, physical cover, middle connector and flank routes. Reused infantry parts become firearm-equipped local wardens; this does not claim a new roster of nine finished heroes.

The menus use generated original YUGA key art, native controls and bundled typography. The Rama page renders the actual hero and SURYA with front/back, drag rotation and zoom. The shared articulated hand presents all four casts; the map uses a common stone/glaze/relief kit. The HUD reads actual authority state: team score, clock, living teammates, ammunition, armor, purchased charges, earned ultimate, objective progress, kill feed and teammate minimap. Settings persist independently of the older training controls.

Start continuation at [the roadmap](ROADMAP.md), [exact shared implementation contract](CONTRACT.md) and [prompt/decision record](PROMPTS.md). Primary reference adaptations and reused source notes live in [research](research/README.md); generated-art prompt lives in [MENU_PROMPT](../../art/tactical/MENU_PROMPT.md). The delivered detailed SURYA build, native gallery, movie, Linux/Windows packages and editable art are in [art delivery](ART_DELIVERY.md). The current CPU Raea and distributed hero/map build is in [finish2 delivery](finish2/DELIVERY.md), with [exclusive ownership and resumption](finish2/README.md). The separate earlier publication remains in [delivery](DELIVERY.md).

The priority is the native art and complete player experience. Browser delivery is deferred. The current iteration does not establish online matchmaking, ranks, a finished multi-hero roster, commercial art parity, physical-GPU performance or human balance/audio acceptance. Those are separate roadmap items, not hidden behind the local Casual label.
