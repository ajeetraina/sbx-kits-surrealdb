# DMR: Docker Model Runner (default, local, no keys)

This is what the kit ships with. SurrealDB is embedded and local; the embedder
(and the runbook's chat model) run locally via
[Docker Model Runner](https://docs.docker.com/ai/model-runner/), so no cloud
credentials and no external database are needed.

DMR isn't a separate embedder API. It's a local model runtime the kit reaches
through the OpenAI-compatible client, with `base_url` pointed at the DMR endpoint.

| | |
|---|---|
| Vector store | SurrealDB (embedded, on-disk surrealkv) |
| Embedder runs where | Local (host's Docker Model Runner) |
| Credential | none (`api_key: "dmr"` is a placeholder DMR ignores) |
| Embed model | `ai/mxbai-embed-large` |
| Chat model (runbook) | `ai/gemma3` |
| Vector dimensions | 1024 |
| Network | already covered by the kit |

## Prerequisites

Enable Docker Model Runner (Docker Desktop → Settings → AI / Beta features) and
pull both models on the host:

```console
docker model pull ai/gemma3              # chat model for the travel runbook
docker model pull ai/mxbai-embed-large   # embedder (1024-dim)
```

## Config (`/home/agent/.surrealdb/config.json`)

This is the default the kit installs; you don't have to write it yourself.

```json
{
  "db": {
    "url": "surrealkv:///home/agent/.surrealdb/data",
    "namespace": "sandbox",
    "database": "memory"
  },
  "embedder": {
    "provider": "openai",
    "model": "ai/mxbai-embed-large",
    "base_url": "http://host.docker.internal:12434/engines/v1",
    "api_key": "dmr",
    "dims": 1024
  }
}
```

## Run

Published as the Hub image (`:latest`, also tagged `:dmr`), or run the standalone
spec from this repo:

```console
sbx run --kit docker.io/ajeetraina777/sbx-surrealdb-kits:latest claude
# or from this repo:
sbx run --kit ./kits/dmr claude
```

## Verify (inside the sandbox)

```console
!curl -s http://host.docker.internal:12434/engines/v1/models | head
```

Expect a JSON list including `ai/gemma3` and `ai/mxbai-embed-large`.

## Notes

DMR is the well-justified default for Claude agents specifically: Anthropic ships
no embeddings API, so this is the only zero-extra-vendor way to give a Claude
agent SurrealDB-backed semantic memory. Small local embedders like
`mxbai-embed-large` are near state-of-the-art, so you lose almost nothing on
retrieval quality.
