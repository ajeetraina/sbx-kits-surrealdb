# Embedding providers for the SurrealDB kit

SurrealDB is the database in every flavor of this kit - an embedded, multi-model
store that gives you documents, graph edges, and **native vector search** in one
process, with no server and no external vector database. What changes between the
image tags is only the **embedder**: the model that turns text into the vectors
SurrealDB indexes and searches.

The kit ships wired to a local [Docker Model Runner](https://docs.docker.com/ai/model-runner/)
(DMR), so it works with no cloud keys. But you can point the embedder at OpenAI or
Gemini instead. This folder has a focused page per provider with copy-paste config.

Why DMR is the default (and why Claude users especially need it): Anthropic
[does not offer an embeddings model](https://docs.anthropic.com/en/docs/build-with-claude/embeddings).
Their docs point you to Voyage AI. So a Claude-agent user has no embedder in their
existing credentials, and vector search needs one. DMR fills that gap locally.
OpenAI and Gemini users can reuse a key they already have.

## Provider matrix

| Provider | Vector store | Embedder runs where | Credential | Embed model | Dims |
|---|---|---|---|---|---|
| [DMR](./dmr.md) (default) | SurrealDB (embedded) | local | none | `ai/mxbai-embed-large` | 1024 |
| [OpenAI](./openai.md) | SurrealDB (embedded) | cloud | `OPENAI_API_KEY` | `text-embedding-3-small` | 1536 |
| [Gemini](./gemini.md) | SurrealDB (embedded) | cloud | `GOOGLE_API_KEY` | `gemini-embedding-001` | 768 |

## Two notes that apply to every provider

1. **Dimensions must match.** Each embedder emits a fixed vector size (mxbai 1024,
   OpenAI `3-small` 1536, Gemini 768). That number must appear in the embedder
   config (`dims`) **and** in the `DIMENSION` of the SurrealDB vector index. A
   mismatch causes an index error or garbage retrieval. The runbooks read `dims`
   from `~/.surrealdb/config.json` and define the index accordingly, so keep the
   two in sync when you edit the config.
2. **Changing dimensions needs a fresh index/table.** SurrealDB won't reinterpret
   an HNSW index built at one dimension as another. When you switch providers,
   either use a different `database` in the config (each provider tag already
   does - `memory`, `memory_openai`, `memory_gemini`) or drop the old store:
   `rm -rf /home/agent/.surrealdb/data`.

## How to switch provider

Each provider is published as an image tag (`:dmr`, `:openai`, `:gemini`), and the
same specs live under [`kits/`](../kits). Pick one, store its key if it's a cloud
provider, and run it:

```bash
sbx secret set -g openai            # cloud providers only (or -g google)
sbx run --kit docker.io/ajeetraina777/sbx-surrealdb-kits:openai claude
# or from this repo: sbx run --kit ./kits/openai claude
```

No hand-editing of `config.json` or `spec.yaml`. The matching `allowedDomains`,
install steps, and `config.json` are already baked into each kit. Keys are never
stored in the kit; the sbx proxy injects them from the stored secret, so they
never enter the sandbox (`sbx run` has no `-e` flag). Each provider's page has the
details.
