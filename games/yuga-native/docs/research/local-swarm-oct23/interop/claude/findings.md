# Claude Code with Ollama: pinned documentation findings

Research only; neither CLI execution nor model inference has been tested. All source fetches were public GitHub GETs. Read response bodies total 245,569 bytes (plus unmeasured protocol overhead; two 404 response bodies were not read).

- Ollama's official Claude Code integration at revision `1472203c47d93d64020fdafa33f9b038bc1583e9` documents its Anthropic-compatible API and manual connection recipe below. Ollama CLI convenience `ollama launch claude` is also documented, but its selector can choose cloud models. The `--yes` form can pull missing models, so it is not suitable for a no-download check.
- The manual environment recipe sets `ANTHROPIC_AUTH_TOKEN=ollama` (a dummy local string), clears `ANTHROPIC_API_KEY`, and uses `ANTHROPIC_BASE_URL=http://localhost:11434`. The chosen model must already exist locally; substitute its exact resolved local ID, not a vendor model family or invented downloadable Claude model.
- Localhost alone does not mean local inference: the same official page explicitly shows `kimi-k2.7-code:cloud` routed via localhost. The FAQ documents `OLLAMA_NO_CLOUD=1` on the Ollama SERVER, or `disable_ollama_cloud: true` in `~/.ollama/server.json`, followed by restarting Ollama. Expected server log: `Ollama cloud disabled: true`. This disables Ollama cloud models and web search. It does not prove all third-party client network features are disabled.
- Official guidance recommends a 64k+ context window for large repositories. That is not a laptop feasibility guarantee. Keep context and concurrency within measured memory; no tested sizing or quality claim is supplied here.
- Claude Code settings can override shell variables. Check `/status` and existing settings before declaring the route local. Main-model selection alone is not an audit of every subagent or auxiliary route.
- Claude Code's own `LICENSE.md` at `30fa83c68c77d2e3a7a42f1407831ec252511130` states © Anthropic PBC, all rights reserved, subject to Commercial Terms of Service. This is not an open-source license for the Claude Code executable and it does not provide Claude model weights. Anthropic's separately published skill files may have other licenses; those do not change the client/model license.
- Official Claude Code v2.1.0 release source at `870624fc1581a70590e382f263e2972b3f1e56f5`, CHANGELOG, explicitly documents automatic skill hot reload from personal `~/.claude/skills` and project `.claude/skills`. Per-skill entry is `SKILL.md`; frontmatter name/description supported by the separately pinned Anthropic skills README. Only the first 40,000 bytes of this old changelog were retrieved; the relevant line is in that captured prefix.

## Local-model connection example

This is a source-verified recipe, not a validated installation or a guarantee of fully offline client behavior. Start/configure the existing Ollama server with cloud disabled first and verify the already-local model. No `ollama pull` is included.

```bash
# In the terminal/service that starts the existing Ollama server:
OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 ollama serve

# In a separate terminal, use an exact model ID already installed locally:
: "${LOCAL_MODEL_ID:?Set the exact verified local Ollama model ID}"
ANTHROPIC_AUTH_TOKEN=ollama \
ANTHROPIC_API_KEY='' \
ANTHROPIC_BASE_URL=http://localhost:11434 \
claude --model "$LOCAL_MODEL_ID"
```

Do not start a second server if an existing Ollama service owns port 11434; configure its environment and restart that service using the platform's supported method. `OLLAMA_HOST` binding should be checked against the existing service configuration. Keep the local and cloud profiles explicit and separate; do not configure automatic fallback.

## Optional, separately authorized cloud profile

The same official integration docs show direct cloud routing. This is intentionally NOT part of the local setup, and has not been run. An actual cloud invocation needs explicitly selected hosted model, configured secret, Internet and billing authorization:

```bash
: "${OLLAMA_API_KEY:?Configure the cloud secret securely}"
: "${CLOUD_MODEL_ID:?Set the explicitly selected hosted model ID}"
ANTHROPIC_BASE_URL=https://ollama.com \
ANTHROPIC_AUTH_TOKEN="$OLLAMA_API_KEY" \
ANTHROPIC_API_KEY='' \
claude --model "$CLOUD_MODEL_ID"
```

See `evidence.json` for exact source URLs, revisions and SHA-256 hashes of the cited local artifacts.
