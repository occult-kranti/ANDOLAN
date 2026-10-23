# Subscription clients and laptop/PS4 control

Reviewed 23 October 2026. **Recommended control point: run the selected coding CLI on the laptop, in the actual project directory.** Give that laptop a separately configured SSH route to a PS4 only if Linux and an SSH service really exist on the console. This cloud chat does not gain a route to either device, or access to the user's subscriptions, merely because the user owns them.

This deliverable is documentation research and an implementation contract. Public sources were retrieved and hashed; **no laptop/PS4 was contacted, no client was installed or logged in, no account entitlement was inspected, no inference/API request was made, and nothing was downloaded to or deleted from either device**. The command blocks below are templates, not executed results. The source ledger records retrieved, reused and blocked evidence separately.

## What the subscriptions can and cannot supply

| Client/profile | Supported account route found in official sources | Required distinction |
| --- | --- | --- |
| Codex using a ChatGPT plan | Run `codex`, choose **Sign in with ChatGPT**. Current README names Plus, Pro, Business, Edu and Enterprise. Existing saved login can be reused. | ChatGPT authentication and API-key authentication are separate routes. Do not infer API balance, unlimited use or organization permission from a chat subscription. The README list is not an account-specific entitlement check. |
| Codex using an API key | Separately configured API-key authentication. | Opt-in API usage; never switch here automatically when ChatGPT usage is exhausted. No API key is needed merely to reuse an eligible ChatGPT login. |
| Claude Code using an eligible subscription | Official Anthropic setup material documents an OAuth route for Pro/Max; launch the installed `claude` client and use its existing subscription login/account flow. | Exact user plan, organization seat, usage allowance and other current eligible tiers were not verified. Official web authentication docs were blocked. Do not represent this subscription as Console API credit. |
| Claude Code using an API/provider account | Official Anthropic material separately documents `ANTHROPIC_API_KEY` and provider routes. | Keep it separate from subscription OAuth. Do not extract browser cookies, reuse a chat session as an unofficial API, or copy tokens among clients. |
| Kimi Code using membership | `/login` in `kimi`, or documented `kimi login`, performs Kimi Code OAuth device authorization. | “I pay for Kimi chat” alone does not verify the coding product, account region, allowance or device-control entitlement. Confirm the account in the actual Kimi Code UI. |
| Kimi using its Platform API | The first-use selector separately offers a Kimi Platform API key. | Do not switch to this paid API route because membership login or quota fails. The provider/key and billing decision must be explicit. |
| Any client with a local model | Explicit local Ollama/compatible provider profile and an actual installed model ID. | The client program can run locally while inference is hosted. Selecting local inference uses a separate local checkpoint; it does not download proprietary OpenAI/Claude weights or make Kimi K2 fit laptop VRAM. |

The existence of an OAuth token is not permission to use it as a generic API credential. Anthropic's official Action documentation describes its own supported token workflow, but this plan does **not** generate or export that token: the laptop's regular CLI login is sufficient for the initial workflow. Keep auth state with the client, OS account and environment that created it. Windows-native and WSL clients may have different configuration and credential stores.

## Reuse login before replacing it

First use the installed client's help/version and account UI. For Codex, the source implements a local status check and explicitly recommends device authorization for a headless machine:

```sh
# LAPTOP: documented templates; not executed here.
codex --version
codex login status
```

Record only the auth mode (for example `ChatGPT`) and whether it is usable. Do not archive raw authentication files or token-bearing output. Codex status can report a configured API credential without checking server authorization; the source says authentication is checked when a request is sent. A saved-login status is therefore not proof that a subscription task will succeed.

If Codex has no usable login, start the documented interactive ChatGPT flow locally, or use this documented device flow on a headless terminal:

```sh
codex login --device-auth
```

The person who owns the account completes the provider's device/browser authorization. Some organizations can disable a login method or device flow. Stop on that error; do not silently choose API billing. The pinned Codex source clears existing auth when starting a fresh login, which is why a valid login should be reused first.

For Claude Code, the documented starting command is:

```sh
claude
```

Use the existing login, or the installed client's account selector if it is not authenticated. Verify subscription versus API mode in the UI before an inference task. This research does not invent a headless Claude login flag: its live authentication page returned CONNECT 403, and the public CLI README only establishes the normal `claude` entry point. Review installed help/UI locally for additional supported auth commands.

For modern Kimi Code, the documented device authorization can run without entering the TUI:

```sh
kimi --version
kimi login
```

Use `kimi login` only if a fresh login is needed; `/login` inside the TUI is the alternative. The resulting token is stored by Kimi itself, and subsequent sessions load it. The current command-reference page says bare `kimi login` has no flags, while a separate remote-control page mentions a region flag; the template deliberately uses the mutually supported bare command. Do not guess an account region or copy another environment's OAuth files.

## A concrete prompt-to-device process

1. **Establish one laptop execution environment.** Use the existing repository checkout and real runtime paths in either Windows-native or WSL/Linux. Verify device, disk, process permissions and current working directory. Start with the laptop-local CLI: it can inspect the workspace through its own file/shell tools without a cloud-to-laptop tunnel. An SSH login into the laptop is optional for an external trusted controller.
2. **Separate transport and inference profiles.** The `local` profile uses the local model and has no hosted fallback. A named `chatgpt-subscription`, `claude-subscription` or `kimi-membership` profile uses that client's verified existing login. A separately authorized API profile is a different choice. A hosted model can operate laptop-local tools; that does not mean its inference is local.
3. **Record each task before work.** Bind a task ID to a baseline commit, exact allowed paths, chosen client/provider/model, host identity, permitted operations, acceptance checks, timeout and output directory. One lead owns shared manifests; six worker roles get exclusive paths and small handoffs. CLI sessions do not automatically share conversation state with each other or with this chat.
4. **Qualify read-only control.** In the actual project, check files and versions; obtain a host identity receipt over any configured SSH route. Do not begin model download, deletion, deployment or PS4 package installation merely because a transport handshake succeeded.
5. **Perform scoped changes.** Use the existing local-swarm inventory, queue and cooperative lock tools where appropriate. Return diffs and actual test receipts. A role assignment or command string is not an autonomous agent service; a real CLI/process still has to execute it.
6. **Advance only the tested capability.** First prove a read-only laptop task, then one bounded repository edit and its test. Qualify a PS4 Linux read-only task separately if the PS4 prerequisites are proven. Controller input, frame capture and game automation need their own actual interfaces; SSH file access alone does not provide them.

Example Linux/WSL interactive starting profiles, in the actual project directory:

```sh
# Uses the currently selected and verified hosted Codex authentication.
# A prompt may consume that account's allowance; not run by this research.
codex --sandbox read-only --ask-for-approval on-request

# For a separately selected write task, after the task's exact paths are assigned:
codex --sandbox workspace-write --ask-for-approval on-request

# Kimi's interactive plan mode prioritizes read-only work.
kimi --plan
```

Codex's sandbox is the execution guard, not a universal restriction on remote devices reached by SSH. A remote command executes under the remote account's permissions; constrain that account and its allowed command wrapper separately. Kimi Plan mode is a behavior/permission mode, not a claim of an OS sandbox. Keep its `default_permission_mode = "manual"` for interactive work. **`kimi -p` is non-interactive `auto` permission mode**, even if the interactive default is manual; do not substitute it unnoticed in a scheduler. Avoid bypass-permission flags in the initial qualification. Claude's installed permission settings must likewise be checked before allowing file/shell actions.

### SSH templates and present prerequisites

The laptop/control agent owns host configuration and the executable control scripts. This research supplies no hostnames, IPs, keys or installation commands. These illustrative aliases must already exist in trusted SSH configuration, with their host keys verified and a narrowly scoped account:

```sh
# CONTROL MACHINE → LAPTOP, if this separate route was actually configured.
# Read-only identity command; BatchMode prevents hanging on password prompts.
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes laptop-control hostname

# LAPTOP → PS4 LINUX, only after Linux + SSH availability is established.
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes ps4-linux hostname
```

A cloud-based controller additionally needs a supported reachable network/VPN path and configured authentication. This chat presently has neither a verified laptop endpoint nor a verified PS4 endpoint. An account subscription supplies neither route. Do not weaken host-key checking or expose the model server publicly to make these templates connect.

The PS4 is reported as the **original model**. The user's “yes” about jailbreaking/Linux is ambiguous: firmware, actual Linux boot status, distribution, network address and SSH service remain unknown. Treat it as an unqualified target until the person/device inventory supplies those observations. A jailbroken console is not automatically booted Linux, and a stock console is not an ordinary SSH host. Do not promise that prompts can install software, control gamepad input, run CUDA or launch a local LLM there from the current evidence. The laptop remains the primary model/tool machine.

## Download and deletion contract for the controller

The user wants managed downloads/deletes. Convert each request into an exact manifest within the already authorized scope; do not silently broaden it to unrelated paths or accounts.

- **Download:** approved source URL, immutable revision when available, actual artifact/filename and license, expected checksum or signature, expected bytes, free-space reserve, destination under the chosen model/assets root, and a bounded retry policy. Download into a partial/temp path, verify integrity, then promote. No invented model IDs, missing-weight auto-pulls, unbounded installer scripts or subscription-to-API fallback.
- **Delete:** enumerate canonical paths and byte sizes; reject symlinks or traversal outside the declared cache/output roots; preserve original art, repository history, user saves, credentials and unique evidence. Prefer reversible quarantine with a manifest when suitable. Only delete the explicitly approved artifacts when ownership, retention and expected identity still match. A broad cleanup goal does not identify arbitrary user files.
- **Receipt:** task ID, host, working directory, operation, source/destination paths, selected client/provider/model ID, input/output hashes, exit status, stdout/stderr artifact paths, resource use and next step. Store only sanitized account/mode status; omit auth values, device codes, cookies and private control links.

No downloading or deleting controller was implemented here; those tools remain owned by the root/laptop implementation agent.

## Six roles, one 8 GB inference lane

Use the confirmed RTX 4070 Laptop **8 GB dedicated VRAM**, with **16 GB shared system memory reported separately**. Start one measured small quantized model at 4k context, one loaded model and one inference request at a time. Six role queues can share that service. Their CPU-side source review and tests can proceed independently where capacity permits; six role prompts do not create six independent GPUs.

Explicit local Ollama settings belong to the server process: loopback binding, `OLLAMA_NO_CLOUD=1`, `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`, bounded context. Localhost alone can still route Ollama cloud model aliases. Resolve an exact already-installed local model and verify cloud-disabled server state before using it. Codex's OSS path can pull a missing ID and defaults to a larger model when no ID is supplied; never use an unqualified bare `--oss` command in the download-controlled flow.

Current protocol requirements remain: Codex → Responses API; Claude Code → Anthropic-compatible route; modern Kimi `openai` provider → Chat Completions. A server implementing one protocol does not prove the other clients work. Large system/tool prompts can exceed 4k; fail qualification instead of silently truncating or raising memory demands. For generation/rendering, finish requests and explicitly unload the coding model before the next GPU job; a cooperative command lock alone does not unload memory.

This is **task routing**, not training or creating a mixture-of-experts model. A real MoE checkpoint still needs its total weights/storage and runtime state. Proprietary hosted weights remain hosted; Kimi K2's 1T-total architecture is not an 8 GB model merely because fewer parameters are active per token. A PS4 node does not merge its RAM or graphics memory into laptop VRAM.

## Optional Kimi-native remote control

A newly checked official capability is `kimi rc` (alias `kimi remote`). It starts a foreground local process and a remote browser interface through Kimi's relay. The docs require paid membership, the same logged-in Kimi account, Internet connectivity and an awake machine; they currently describe about three devices per account. It binds locally to loopback, supports one instance per machine, and cannot combine with the auth-bypass flag. The browser can send tasks, inspect work and handle approvals; file/shell work executes on the selected machine. Model inference still follows that session's configured provider.

This is an optional **vendor-relayed** path, not the offline/local profile and not an installed connection from this cloud chat. Starting it creates a remote-control surface and prints a private device link; do not publish that output or add it to repository receipts. It can only control a PS4 Linux session if a compatible client/runtime and that specific machine's prerequisites are independently qualified. The first implementation should keep general device transport in the laptop agent's scoped SSH wrapper.

## Evidence and limits

[source-ledger.json](source-ledger.json) records exact URLs, revisions, hashes and relevant passages. Fresh GitHub HEAD checks matched the earlier Codex, Claude Code and Kimi Code pins. Official OpenAI/Claude web authentication and the attempted Kimi membership page returned CONNECT 403; live pricing, exact user-plan entitlements and account quotas remain unverified. Official GitHub source was used within those bounds.

Completed: public-source retrieval, hash validation and the process design above. Not performed: account login/verification, client invocation, SSH connection, remote-control activation, model inference, model/asset download, deletion, PS4 execution, controller input, game rendering or runtime tests. No external messages were sent and no charged API request was issued.
