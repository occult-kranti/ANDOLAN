# Lane unit render review — revision 2

Reviewed the actual 1280 × 720 engine images on 2026-10-17. The revision improves team and role readability enough to retain for this offline prototype. It remains visibly procedural prototype art, below the requested Deadlock/Overwatch visual target.

## Evidence

- Art source: `scripts/lane_unit_art.gd`, SHA-256 `5861731faf1fc4dc77be7d99861a8c8eb885dba95c82cd074fe2b260e805482d`.
- Arrival view: `/tmp/yuga-traversal-full-r2/frame-00000.png`, SHA-256 `3526f038b01e6be2a836cb50efe225419308a3a28b61937a62c944bac8871c02`.
- Combat view: `/tmp/yuga-traversal-full-r2/still-army-engagement.png`, SHA-256 `3b8d47d69798440096c8d8f267ecbb4267e724dc5b565f5d982ea07f101389db`.
- Capture report: `/tmp/yuga-traversal-full-r2/traversal-render-review.json`, SHA-256 `f2c82e388888ceb66dc9b0e0672f2d7d2af7a3299753cf923428d3396b4a8fab`.

The report records 180 sequential frames and 360 physics ticks. All recorded frame states are finite: `True`. Peak recorded scene totals are 931 draw calls and 587,431 rendered primitives. These are whole-scene counters from a staged software-rendered take, not a real-time frame-rate benchmark. The combat still uses a separate documented army simulation advance and camera staging; it is not a frame from the six-second traversal take.

## Observations

| Feature | Visible result |
| --- | --- |
| Teams | Rust Sun and teal Moon cuirasses are distinct; cream lower garments, dark boots and restrained trim break up the previous large uniform-colour blocks. |
| Spearman | Upright spear point and round shield read clearly in the combat still. |
| Bow guard | Bow curve, extended arms and quiver make the role distinct, especially in the lower-left foreground. The grip/draw pose remains stiff. |
| Commander | Crown and tall notched banner distinguish the larger unit in the arrival view. The banner is the stronger cue at distance. |
| Body connections | No gross detached head, missing limb or weapon crossing a torso is evident in these two stills. Segmented arms and legs still look mechanical rather than anatomical. |
| Ground contact | Stationary combat units appear grounded. Walking units lift their feet in the arrival view; two stills cannot establish correct foot planting or absence of sliding throughout the cycle. |

## Remaining art limits

The nearby banner has visible speckling; its coincident double-sided faces, self-shadowing and medallion overlap warrant a close-up review before final art acceptance. Bow-string/finger contact and weapon grips need animation-specific review. Broad untextured surfaces, simplified faces, rigid cloth, basic shading, visible polygon edges and repetitive pose silhouettes remain evident. No continuous walk/attack/hit/fall clip has been visually approved by this review. The finite-articulation and combat tests establish bounded computation, not animation polish.

No runtime or asset edits were made during this review. Further sculpted anatomy, cloth/armour detailing, authored animation and lighting work is needed for the user's target quality.
