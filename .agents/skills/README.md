# YUGA project skills

Six canonical skills for the existing desktop-first game roadmap. Start with
[the local model and squad guide](../../games/yuga-native/docs/LOCAL_MODEL_SWARM.md)
and [AGENTS.md](../../AGENTS.md). The lead assigns one bounded packet and
exclusive files to each active worker; the roles do not create six GPUs or
prove the complete game exists.

| Worker | Skill | Use for |
| --- | --- | --- |
| W1 | [yuga-evidence-review](yuga-evidence-review/SKILL.md) | Sources, controlled analysis and independent actual-game review |
| W2 | [yuga-ui-flow](yuga-ui-flow/SKILL.md) | Screens, controls, accessibility and player journeys |
| W3 | [yuga-hero-art](yuga-hero-art/SKILL.md) | Character geometry, materials, rig/skin and hero quality |
| W4 | [yuga-world-art](yuga-world-art/SKILL.md) | City/swamp, lanes, buildings, armies and collision |
| W5 | [yuga-motion-combat](yuga-motion-combat/SKILL.md) | Animation, action events, effects/audio and authority |
| W6 | [yuga-models-build](yuga-models-build/SKILL.md) | Local model capacity, source provenance, builds and packaging |

These are repository files, not globally installed plugins. Current Codex and
Kimi Code source documentation supports `.agents/skills`. Claude Code discovers
`.claude/skills`; explicitly load the canonical file or create a project-local
link using the instructions below. Keep one authoritative copy and preserve any
existing skill with the same name. Do not assume discovery means a small model
can reliably follow a long workflow: qualify one bounded task first.

For Linux/WSL, from the repository root, an optional link for one skill is:

```sh
mkdir -p .claude/skills
ln -sT ../../.agents/skills/yuga-hero-art .claude/skills/yuga-hero-art
```

This command deliberately does not force replacement. Windows-native links
require appropriate filesystem support/permissions; direct file use avoids
creating divergent copies. See [client-specific source evidence](../../games/yuga-native/docs/research/local-swarm-oct23/interop/README.md).

The confirmed laptop has **8 GB dedicated VRAM plus 16 GB shared system RAM**.
Use one qualified local model and serialize heavy GPU jobs. A skill may request
research or review from another role, but must respect available worker slots,
assigned paths and the lead's resource queue. The existing acceptance gates and
the user's current instructions remain authoritative.
