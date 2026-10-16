# Cloud setup record

Validated on 16 October 2026 in the existing isolated `/workspace/ANDOLAN` checkout. No API key is required for the game. Node 24, npm, Git, Chromium and Docker are available in this environment.

- The pinned application dependencies install successfully. `tools/cloud/setup.sh` was executed in a fresh temporary copy with no existing `node_modules`; installation and both production builds passed.
- `npm run dev` provides the development client and authoritative room service. The documented internal ports are 5173 and 3001. Local Chromium runs exercise the game; this ChatGPT surface exposes no embedded canvas or public preview tunnel.
- The pinned Docker image builds and starts as the unprivileged `node` user. Health, production HTML, real WebSocket progression, identity restoration and story persistence across a graceful container restart passed; see `evidence/container-final-check.json`.
- REA source analysis is installed separately and was exercised against pinned permissive source. It is optional for running the game. The restore procedure and the signature-verification limitation are in `research/REA_RUNBOOK.md`.

The cloud configuration draft saves the complete installation script and startup instructions, plus four additional network destinations: `api.github.com`, `occult-kranti.github.io`, `uploads.github.com` for release assets and `results-receiver.actions.githubusercontent.com` for Actions logs. The save was confirmed by the configuration tool. A draft save alone does not prove runtime activation or publish a snapshot: **review and save the changes in environment settings, then publish the environment** to activate them. Fresh-task restoration of the published snapshot has not been verified in this session. API/Actions reads became reachable during release checks. Earlier Pages administration requests returned integration HTTP 403. After the user enabled Pages, Actions successfully published the solo preview; see `DEPLOYMENT.md`. Website publication does not establish activation of the separate environment draft or restoration of a published cloud snapshot.

The existing repository membership was preserved. Research checkouts outside the game remain optional tooling, with pinned provenance and restoration instructions in the repository. No hosting account, domain purchase, external paid service or new secret was created.
