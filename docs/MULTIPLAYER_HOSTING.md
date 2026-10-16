# Render deployment for an invited multiplayer beta

**Prepared for City Reform Beta 0.3, not deployed.** The root [`render.yaml`](../render.yaml) defines one paid Docker web service and one persistent disk. No Render account, purchase or service was created in this session, and no hosted multiplayer address is available. The GitHub Pages website now serves the verified Beta 0.3 client; static hosting does not operate the multiplayer server.

This guide uses the beta lobby's **Game server address** field. Use the matching Beta 0.3 client for the GitHub Pages connection steps. City Reform 0.3 uses **protocol 2**: update client and server together. An older protocol-one game service is incompatible even if its `/health` endpoint responds.

The Beta 0.2 baseline passed all ten local browser cases in 491.765 seconds. City Reform 0.3 passes local source gates, focused browser checks and production/standalone builds. Its non-root container also passed actual 0.2 volume migration with backup/identity/job retained and new-case progress preserved through restart. Release `c20e912` passed all thirteen CI browser cases, production builds and Pages deployment, followed by exact public-file and native-browser checks; see [current QA](CITY_REFORM_QA.md), which also retains the earlier failed attempt. The test-only follow-up retains the same application/build inputs. Passed public smoke covers local browser play. Local results do not satisfy the Render-hosted acceptance checks below.

## What the Blueprint runs

| Setting | Prepared value and reason |
| --- | --- |
| Service | `andolan-crew-beta`, Docker web service from repository `main` |
| Image build | Existing pinned, multi-stage `Dockerfile`; it builds the client/server and starts Node as the non-root `node` user |
| Compute | Paid `standard` plan; the pinned Render example identifies 1 CPU / 2 GB RAM. Confirm its current allocation and price in the Dashboard. This is a starting allocation for invited testing, not measured capacity. |
| Instances | Exactly one. Room authority is in one process; the attached disk is not shared storage. |
| Region | Oregon is an explicit initial choice. The owner may select a supported region nearer the invited crew before creating the service. |
| Network | Node binds `0.0.0.0:3001`; Render supplies the public HTTPS endpoint and routes WebSocket upgrades to `/ws` |
| Health | HTTP `/health`; it establishes process readiness, not successful co-op play or working persistence |
| Durable state | A 1 GB disk mounted at `/app/.data`, matching `ANDOLAN_DATA_DIR` |
| Updates | `autoDeployTrigger: "off"`; later code deploys are deliberate. Allow up to 60 seconds for graceful shutdown. |

A service-attached disk requires an eligible paid service. Do not substitute a free instance or ephemeral directory while expecting room saves to survive restarts. The paid service and disk incur provider charges once created; this guide does not quote current pricing. Check the service allocation, disk capacity and estimated charges on Render's review screen before creation. Confirm that the selected disk size and mount path pass Render's current validation.

The Docker image already creates `/app/.data` for its non-root user. A provider-mounted volume can have different ownership: **verify writability on the actual mounted disk**. The local image's ownership is not proof of the remote mount's permissions. If the service reports `EACCES`, correct the volume ownership for the image's user with the provider/operator before inviting players. Do not silently switch to ephemeral storage or change the long-running process to root.

Disk-backed services have one instance and an interruption during replacement. Plan brief reconnects for deploys. Do not add autoscaling or multiple instances to this file: shared room routing and external state storage would require separate implementation.

## Create the service when the owner is ready

1. Put the reviewed beta code, `Dockerfile` and `render.yaml` on the remote repository branch to deploy. Render reads that remote branch; local uncommitted files are not visible to it.
2. Sign in to Render using the owner's account. In the Dashboard, open **Blueprints → New Blueprint Instance** (or **New → Blueprint**, depending on the current Dashboard), connect `occult-kranti/ANDOLAN`, choose the intended branch and use `render.yaml` at the repository root.
3. Inspect the generated resource preview: one Docker web service, one instance, `/health`, port 3001, one disk at `/app/.data`, and no database or secret requirement. Review the paid compute/disk charges and current allocation. Resolve all provider validation errors before approving creation.
4. Create the Blueprint only after that review. Watch build and deployment logs. The Dockerfile performs `npm ci` and production builds; no separate Render build/start command is needed. The application needs no API key. The optional managed-cloud build CA/proxy configuration is not required on an ordinary Render build using public registry certificates.
5. Copy the actual assigned HTTPS service URL from Render's Dashboard. Do not assume the hostname matches the display name; it may include a suffix. Wait for the service to become healthy, then perform the checks below before distributing an invitation.

For later releases, push the reviewed code and use the service's **Manual Deploy → Deploy latest commit** action. Because automatic deployment is disabled, a source push alone does not update the server. Keep the client/server revision compatible, back up room data, and expect clients to reconnect during the replacement. The code migrates supported simulation schema 1/2 saves to 3 and retains original server files as `.legacy-v1.bak`/`.legacy-v2.bak`; this application copy supplements, rather than replaces, the operator's backup.

## Connect the GitHub Pages client

After the compatible beta client is published, open [ANDOLAN on GitHub Pages](https://occult-kranti.github.io/ANDOLAN/) and select **Bring your crew**. Set **What are we playing?** to **City jobs · free roam** for repeatable work, or **Original story · co-op** for the optional campaign. Each room keeps its chosen activity; use a separate room for the other activity.

In **Game server address**, enter the actual Render address in either form:

```text
https://YOUR-ASSIGNED-HOST.onrender.com
wss://YOUR-ASSIGNED-HOST.onrender.com/ws
```

The client converts an HTTPS root address to WSS `/ws`. Use the assigned public hostname, not port 3001 in the browser URL. The address must not contain a password, query string or fragment. It is connection information, not a hosting credential. The browser remembers it locally.

Create a private room and use **Copy invite**. The current client includes the room, gameplay mode and server address in that invitation, so invited players reach the same backend. Each participant still needs a real connection; local City practice is explicitly solo and is not a successful online join.

The application has no separate account-login flow or production moderation operation. Room codes help the crew find a room; they are not an access-control guarantee for the publicly reachable server. Keep the initial audience to invited players. Four-player private rooms and the development room limits are application caps, not a measured capacity promise for the selected plan.

## Same-origin alternative

Open the assigned Render HTTPS URL itself. The Node service serves the compiled client as well as `/ws`, so the client can use that same host for multiplayer without a separately deployed frontend or `VITE_SERVER_URL`. This is the simplest way to keep the served client and server on the same revision during the first beta check.

If that browser previously saved another server address, replace it with the current Render URL in the lobby. GitHub Pages and Render are different browser origins: local Story/City practice saves do not automatically move between them. Shared room state lives on the server disk.

## Acceptance before invitations

Record the service URL, deployed commit, time, observed results and any errors. No Render-hosted result has been recorded yet.

1. **Health and full stack:** request `https://YOUR-ASSIGNED-HOST.onrender.com/health` and require HTTP 200 with the game health JSON and `protocol: 2`. Open the root URL and confirm the matching game client loads. Confirm the service runs as the intended non-root user and `/app/.data` is writable; look for checkpoint errors in logs.
2. **Two real clients:** use two independent browser sessions, preferably different devices or networks. Join the same private City Jobs room. Observe two separate crew identities, replicated movement and distinct seats. A passenger must not drive the vehicle. A local-practice session is not evidence for this gate.
3. **Shared job:** in a fresh room before a City Mandate, complete Clinic Restock with one player driving the loaded van and another unloading on foot beside it. Confirm both clients show the same progression and one room-owned reward: 100 credits, 2 reputation and 1 project point. Confirm a late join sees that total and replaying a completed action does not pay again. Test the Pages lobby and same-origin client if both will be advertised. After a mandate, compare against the route-adjusted reward shown on the job card instead of this base total.
4. **Reconnect:** briefly interrupt one participant's network, restore it and confirm its existing identity and room progress return without a duplicate avatar or reward. If automatic retry stops, use the game's Reconnect control. Repeat in the browser/tab that holds the original session identity.
5. **Persistent restart:** finish a job, wait longer than the server's five-second checkpoint interval, then use a graceful service restart or reviewed deploy. Reconnect with the same room/session and confirm credits, reputation, project state and identity remain. If the crew has earned case progress or a mandate, confirm its ledger/outcome and adjusted rewards remain too. A healthy endpoint alone does not establish this. Check files/logs under the mounted data path without publishing their contents.

These checks establish an invited functional beta. They do not establish unrestricted public matchmaking, broad hardware support, sustained peak concurrency or operation of the full planned game.

## Data and operational limits

Keep room JSON and reconnection identity data private. Back up the disk's application data after a graceful stop or other application-consistent checkpoint procedure, and retain the matching code/content version. A disk is durable storage, not a complete backup strategy. Exact provider snapshot scheduling, retention and restore behavior must be checked in current Render documentation before relying on them.

The existing provider-neutral Docker/Compose configuration remains available. Moving to another host should preserve the same port, WebSocket route, non-root process and persistent data directory. No provider account, payment details or deployment token belongs in the repository or lobby server-address field.

## Sources and validation scope

On 16 October 2026, the cloud proxy returned 403 for Render's canonical [Blueprint specification](https://render.com/docs/blueprint-spec), [disk documentation](https://render.com/docs/disks), [compute-plan documentation](https://render.com/docs/compute-plans) and [JSON Schema](https://render.com/schema/render.yaml.json), including their Markdown alternatives. Therefore no live JSON-Schema or Render API validation is claimed. The Blueprint must pass the provider's current validation preview before creation. If an authenticated Render CLI is available to the owner, `render blueprints validate render.yaml` is an additional read-only validation step; validation does not deploy the service.

The following accessible primary Render sources were read over HTTPS and pinned:

- [Blueprint field reference](https://github.com/render-oss/skills/blob/8675173fe30232384d51c8763d1eea4db0350419/skills/render-blueprints/references/field-reference.md): Docker fields, environment variables, health path, instance count, shutdown delay, auto-deploy and disk fields.
- [Persistent disk reference](https://github.com/render-oss/skills/blob/8675173fe30232384d51c8763d1eea4db0350419/skills/render-blueprints/references/persistent-disks.md): paid-service eligibility, mount-path persistence, single-instance operation, deployment interruptions and runtime-only availability.
- [Compute plan reference](https://github.com/render-oss/skills/blob/8675173fe30232384d51c8763d1eea4db0350419/skills/render-blueprints/references/compute-plans.md): legacy names such as `standard` remain valid, while current allocations/pricing require confirmation. This template keeps the documented legacy name rather than assuming an unverified newer schema enum.
- [Blueprint workflow reference](https://github.com/render-oss/skills/blob/8675173fe30232384d51c8763d1eea4db0350419/skills/render-blueprints/references/blueprints.md) and [deployment details](https://github.com/render-oss/skills/blob/8675173fe30232384d51c8763d1eea4db0350419/skills/render-deploy/references/deployment-details.md): remote Git source, validation, port binding and deployment checks.
- Render's [Docker example Blueprint](https://github.com/render-examples/hermes-render/blob/d3f00670418d7d9eee1c125124dc1dcb7c2bbbd4/render.yaml) and [README](https://github.com/render-examples/hermes-render/blob/d3f00670418d7d9eee1c125124dc1dcb7c2bbbd4/README.md): independently confirms current example use of Docker, `standard`, `autoDeployTrigger`, health checks and a persistent disk; its resource table describes `standard` as 1 CPU / 2 GB RAM. Its unrelated application, tokens and pricing are not part of this deployment.

Local validation checks YAML parsing and agreement with the application's Dockerfile, bind port, health path and data directory. Those checks do not establish provider acceptance, remote disk permissions, billing terms, actual capacity or a live multiplayer backend.
