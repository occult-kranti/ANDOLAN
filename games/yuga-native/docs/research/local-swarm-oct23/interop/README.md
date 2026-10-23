# Local coding-client interoperability research

**Status: official documentation/source checked; no clients installed, model weights downloaded, model inference or client compatibility tests run.** Retrieved 2026-10-23. These are reviewable connection examples for the user's laptop, not evidence that the cloud machine or laptop can execute them. Source hashes and URLs are in `evidence.json`; raw responses are retained under `sources/` and `claude/`.

## Hardware and execution contract

The user confirmed RTX 4070 Laptop GPU with **8 GB dedicated VRAM plus 16 GB shared system memory**. Shared memory does not make this a 24 GB VRAM GPU. Begin with one already-installed quantized 3B/7B candidate, a 4096-token context, one loaded model, and one GPU inference request at a time. A 7B candidate can still exceed the usable memory budget depending on quantization, KV cache, backend overhead and display use; measure it. Six agents are six logical task contexts queued through the same backend, not six resident models.

The three programs are clients. Running Codex, Claude Code or Kimi Code locally does not download the proprietary OpenAI/Claude hosted models. Claude weights are not supplied by Claude Code. Kimi K2 has open weights under its own **Modified MIT** license, but its 1 trillion total / 32 billion active parameter architecture is not an 8 GB laptop model: at a nominal four bits per total parameter, weights alone would be roughly 500 GB before metadata and runtime state. Active-parameter count does not remove the other experts from the weight-storage requirement. The 3B/7B choice is a separate local model, not Kimi K2 or Claude renamed.

## Shared local Ollama preparation

These snippets assume the executables are already installed on the laptop. This research performs no installation or download. Configure the existing Ollama service rather than launching a competing server on port 11434. For a foreground server, the documented settings are:

```bash
OLLAMA_HOST=127.0.0.1:11434 \
OLLAMA_NO_CLOUD=1 \
OLLAMA_CONTEXT_LENGTH=4096 \
OLLAMA_NUM_PARALLEL=1 \
OLLAMA_MAX_LOADED_MODELS=1 \
ollama serve
```

These settings belong to the **server process**, not merely a client shell. Restart the existing service after configuring it and verify `Ollama cloud disabled: true` in its logs. On Windows/macOS, apply the variables to the process/service that actually runs Ollama. The context variable establishes a default; inspect any model `num_ctx` override and the actual loaded context. Do not raise the context to vendor recommendations such as 64k before measuring this laptop's memory.

In a separate terminal, select the exact name from the already-installed model list. The placeholder deliberately is not a downloadable model recommendation:

```bash
ollama --version
ollama list
LOCAL_MODEL_ID='__REPLACE_WITH_EXACT_ALREADY_INSTALLED_LOCAL_MODEL_ID__'
ollama show "$LOCAL_MODEL_ID"
```

Before launching any client, verify exact ID membership, local weight provenance, model license/quantization and tool support. A cloud alias can appear behind a localhost server; reject remote/cloud model tags and verify the server's cloud-disabled state. Do not use `ollama pull`, an auto-pull launcher, or a made-up model family name during this preflight. Existing settings, startup hooks, plugins, MCP servers, model aliases and inherited auxiliary model choices also need review when asserting a local route. **Local model routing does not establish that every CLI feature is network-isolated**; an operating-system egress boundary is needed to prove full offline operation.

## Client recipes and actual wire protocols

| Client | Local route | Source-confirmed constraints |
| --- | --- | --- |
| Codex CLI | Ollama `/v1/responses` | Current source rejects `wire_api = "chat"` and `ollama-chat`; requires Ollama >=0.13.4 when version can be parsed. |
| Claude Code | Ollama Anthropic-compatible `/v1/messages` | `ANTHROPIC_BASE_URL` is the host root, without `/v1`; specify the actual local model ID. |
| Kimi Code | Ollama OpenAI-compatible Chat Completions | Current `MoonshotAI/kimi-code` uses provider `type = "openai"`; its archived Python predecessor is a different configuration generation. |

### Codex CLI

```bash
: "${LOCAL_MODEL_ID:?Set and verify an exact installed local model ID}"
CODEX_OSS_BASE_URL=http://127.0.0.1:11434/v1 \
codex --oss --local-provider ollama --model "$LOCAL_MODEL_ID" \
  --sandbox read-only --ask-for-approval on-request
```

The `CODEX_OSS_BASE_URL` override is explicitly marked experimental in the pinned source; recheck it against the installed release. Audit existing provider config overrides and ensure the session shows the local Ollama provider. Never use bare `codex --oss` on this machine: its source default is `gpt-oss:20b`, and the readiness path can **pull a missing model**, including a mistyped explicit ID. A successful exact-local-model preflight is therefore required. Do not use `wire_api = "chat"` workarounds from old tutorials. Ollama docs say Responses was introduced in 0.13.3, but the pinned Codex client checks >=0.13.4. The local API documents non-stateful Responses only; client tool use/streaming/replay still needs a real compatibility test. The command starts read-only for that initial validation.

### Claude Code

```bash
: "${LOCAL_MODEL_ID:?Set and verify an exact installed local model ID}"
ANTHROPIC_AUTH_TOKEN=ollama \
ANTHROPIC_API_KEY='' \
ANTHROPIC_BASE_URL=http://127.0.0.1:11434 \
claude --model "$LOCAL_MODEL_ID"
```

`ollama` is a local protocol placeholder, not a secret. Ollama officially documents this recipe. Review Claude `/status`, environment settings, explicit subagent models and auxiliary model routing before the first prompt; pin every role to the same verified local model or disable the role until tested. Do not use skip-permission flags. `ollama launch claude` can expose cloud model selections, so it is omitted. Ollama's integration page recommends 64k+ context for large repositories; that is not a promise this 4k/8GB setup fits the client's initial prompt. Start with a tiny task and minimal tools/skills. If the prompt does not fit or tool calling fails, mark that client unsupported at the measured budget; do not automatically increase context or route to cloud.

### Modern Kimi Code

The old `MoonshotAI/kimi-cli` repository is archived; current docs point to `MoonshotAI/kimi-code`. The modern configuration filename is always `config.toml`, by default `~/.kimi-code/config.toml`, relocated by `KIMI_CODE_HOME`.

Review `kimi-local.toml.example`, replace `__RESOLVED_LOCAL_MODEL_ID__`, and save it as `config.toml` in a **new, dedicated local data directory**, preserving any existing profile. The example has only one local provider, forces subagents to the same model, disables telemetry/title generation and web tools, and limits attempts. `max_running_tasks=6` controls logical background tasks; the Ollama server still serializes inference. The `tool_use` capability declaration is a requirement to test, not evidence that a selected model supports it. Once prepared:

```bash
KIMI_CODE_HOME=/absolute/path/to/dedicated-kimi-local-profile \
kimi --model local
```

This is intentionally interactive: `default_permission_mode = "manual"` applies to new interactive sessions. **`kimi -p` uses `auto` permission mode regardless of that default**, so it is not a permission-preserving substitution. Avoid resuming an unrelated/cloud session. Inspect the selected model and provider before prompting. The default system/tool prompt may exceed a 4k window; the current provider docs' schema is not a guarantee of practical capability at that context budget.

## Shared skill discovery

Use a small, reviewed `SKILL.md` with `name` and `description` frontmatter. Keep repository rules and secrets out of skill payloads. Reading a skill is not proof a small model will follow it correctly; test one bounded instruction before enlarging a skill catalog.

| Client | Project path | User path | Evidence |
| --- | --- | --- | --- |
| Codex | `.agents/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` | Current `host_roots.rs` walks project ancestors and user home. `$CODEX_HOME/skills` is deprecated compatibility behavior. |
| Claude Code | `.claude/skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` | Official release changelog and Anthropic skills docs. |
| Kimi Code | `.kimi-code/skills/<name>/SKILL.md` or `.agents/skills/<name>/SKILL.md` | `$KIMI_CODE_HOME/skills/<name>/SKILL.md` or `~/.agents/skills/<name>/SKILL.md` | Current Kimi skills docs. |

The same reviewed skill can be copied into each supported project directory; do not assume native path support transfers between clients. Codex and current Kimi share `.agents/skills`; Claude uses `.claude/skills`. Kimi `--skills-dir` **replaces** auto-discovery, while `extra_skill_dirs` adds to it.

## Optional hosted profiles, kept separate

Cloud use is optional, explicitly selected and separately authenticated. Do not add a cloud provider or fallback to the local files. A local endpoint failure must stop that local run. `kimi-cloud.toml.example` is a separate inactive example with an explicit hosted model placeholder and environment-secret reference; it is not merged with `kimi-local.toml.example`. Check the provider's actual model catalog and account access before use. The client and model licenses are separate:

| Component | Verified terms |
| --- | --- |
| Codex CLI source | Apache-2.0. |
| Ollama source | MIT. Individual models have their own licenses. |
| Kimi Code CLI source | MIT. |
| Claude Code executable | Anthropic all-rights-reserved notice and Commercial Terms; public repo is not an open-source grant for Claude models. |
| Kimi K2 code/weights | Modified MIT, including the stated large-service attribution condition. Not the Kimi CLI license. |

`claude/findings.md` contains an explicit, separate Ollama-cloud endpoint example from Ollama's docs. No cloud credential was requested, read, supplied or used here. A cloud-capable client binary being local does not make its hosted inference local.

## Remaining validation gates

No generation/streaming/tool-loop result is claimed. On the actual laptop, record CLI and server versions, actual selected model ID/digest, quantization, model license, free/peak dedicated VRAM, actual 4096 context, request timings and errors. Validate plain generation, streaming completion, one harmless tool-call/tool-result round trip, cancellation and offline failure for each client. Inspect the actual selected endpoint/model for main, auxiliary and subagent calls. Validate six queued logical roles at server parallelism one. Mark unsupported combinations as failures; never turn a missing compatible model into an automatic download or hosted fallback.
