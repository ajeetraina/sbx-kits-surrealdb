# SurrealDB kit for Docker Sandboxes

A standalone [Docker Sandboxes](https://docs.docker.com/ai/sandboxes/) kit
(`kind: mixin`) that adds an embedded, multi-model [SurrealDB](https://surrealdb.com/)
— documents, graph edges, and native vector search — plus the `surrealdb` Python
SDK to any sandbox agent. SurrealDB runs in-process (embedded storage engines
ship with the SDK), so there is no server and no external database.

Vector search needs an embedder. This image ships in three flavors, one per tag;
SurrealDB is the same in all of them and only the embedder changes.

Source and full docs: https://github.com/ajeetraina/sbx-kits-surrealdb

## Image tags

| Tag | Vector store | Embedder | Dims | Credential |
|-----|--------------|----------|------|------------|
| `latest`, `dmr` | SurrealDB (embedded) | `ai/mxbai-embed-large` (local DMR) | 1024 | none |
| `openai` | SurrealDB (embedded) | `text-embedding-3-small` | 1536 | `OPENAI_API_KEY` |
| `gemini` | SurrealDB (embedded) | `gemini-embedding-001` | 768 | `GOOGLE_API_KEY` |

DMR is the default because it needs no cloud keys. It matters most for Claude
agents: Anthropic does not offer an embeddings model
(https://docs.anthropic.com/en/docs/build-with-claude/embeddings), so a Claude
user has no cloud embedder. DMR fills that gap locally. OpenAI and Gemini users
can reuse a key they already have.

## Quick start

Local default (DMR). Enable Docker Model Runner and pull the two models on the host:

    docker model pull ai/gemma3
    docker model pull ai/mxbai-embed-large
    sbx run --kit docker.io/ajeetraina777/sbx-surrealdb-kits:latest claude

OpenAI. Store the key once with sbx (never on the command line), then run:

    echo "$OPENAI_API_KEY" | sbx secret set -g openai
    sbx run --kit docker.io/ajeetraina777/sbx-surrealdb-kits:openai claude

Gemini:

    echo "$GOOGLE_API_KEY" | sbx secret set -g google
    sbx run --kit docker.io/ajeetraina777/sbx-surrealdb-kits:gemini claude

The cloud tags hold no key. The sbx proxy injects it from the stored secret, so the
key never enters the sandbox. `sbx run` has no `-e` flag by design.

## How it works

Each kit installs the `surrealdb` SDK (with embedded engines), writes
`/home/agent/.surrealdb/config.json` with the connection and the right embedder
(model + vector dimensions: DMR 1024, OpenAI 1536, Gemini 768), and adds the
matching embedder domain to the sandbox allow list. The store persists on disk at
`~/.surrealdb/data`. Runnable demos ship under `~/runbooks/` (`travel.py` for
vector memory, `graph.py` for multi-model graph queries).

Per-provider setup notes, validation details, and the raw `spec.yaml` for each kit
live on GitHub:
https://github.com/ajeetraina/sbx-kits-surrealdb/tree/main/providers
