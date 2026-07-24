# OpenAI (cloud embedder)

SurrealDB stays embedded and local; only the embedder moves to OpenAI.

| | |
|---|---|
| Vector store | SurrealDB (embedded, on-disk surrealkv) |
| Embedder runs where | Cloud (`api.openai.com`) |
| Credential | `OPENAI_API_KEY` |
| Embed model | `text-embedding-3-small` (1536) or `text-embedding-3-large` (3072) |
| Vector dimensions | 1536 for `3-small` |

## Credential (store it as a secret, never on the command line)

`sbx run` has no `-e` flag, and you should never put a key in the command anyway.
Store it once with sbx's secret manager. `openai` is a built-in service, so the
proxy injects the key into outbound OpenAI requests and it never enters the
sandbox, shell history, or `ps`:

```bash
echo "$OPENAI_API_KEY" | sbx secret set -g openai   # -g = all sandboxes
# or run `sbx secret set -g openai` for an interactive prompt
```

## Run

This provider is published as a ready-made image. Store your key, then launch:

```bash
echo "$OPENAI_API_KEY" | sbx secret set -g openai
sbx run --kit docker.io/ajeetraina777/sbx-surrealdb-kits:openai claude
```

Or run the same spec straight from this repo, no Hub pull:

```bash
sbx run --kit ./kits/openai claude
```

## What the kit contains

`kits/openai/spec.yaml` already wires everything:

- `network.allowedDomains` includes `api.openai.com`.
- `config.json` sets the `openai` embedder with `base_url` pinned to
  `https://api.openai.com/v1` and `dims` 1536:

```json
{
  "db": {
    "url": "surrealkv:///home/agent/.surrealdb/data",
    "namespace": "sandbox",
    "database": "memory_openai"
  },
  "embedder": {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "base_url": "https://api.openai.com/v1",
    "dims": 1536
  }
}
```

The key is never in the kit or `config.json`. The sbx proxy injects it from the
stored `openai` secret.

## Notes

Using `text-embedding-3-large` instead? That's 3072 dims, so change `dims` to
`3072` and start a fresh store (`rm -rf /home/agent/.surrealdb/data`, or use a new
`database` name) so the SurrealDB vector index is rebuilt at the new dimension.
