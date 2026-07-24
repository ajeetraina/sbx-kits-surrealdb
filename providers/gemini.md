# Gemini: Google (cloud embedder)

SurrealDB stays embedded and local; only the embedder moves to Google Gemini.

| | |
|---|---|
| Vector store | SurrealDB (embedded, on-disk surrealkv) |
| Embedder runs where | Cloud (`generativelanguage.googleapis.com`) |
| Credential | `GOOGLE_API_KEY` |
| Embed model | `gemini-embedding-001` |
| Vector dimensions | 768 |

## Credential (store it as a secret, never on the command line)

`sbx run` has no `-e` flag. Store the key once with sbx's secret manager.
`google` is a built-in service, so the proxy injects it into outbound requests
and it never enters the sandbox or your shell history:

```bash
echo "$GOOGLE_API_KEY" | sbx secret set -g google   # -g = all sandboxes
# or run `sbx secret set -g google` for an interactive prompt
```

## Run

This provider is published as a ready-made image. Store your key, then launch:

```bash
echo "$GOOGLE_API_KEY" | sbx secret set -g google
sbx run --kit docker.io/ajeetraina777/sbx-surrealdb-kits:gemini claude
```

Or run the same spec straight from this repo, no Hub pull:

```bash
sbx run --kit ./kits/gemini claude
```

## What the kit contains

Gemini needs two things beyond the OpenAI setup, and `kits/gemini/spec.yaml`
already handles both:

- It installs the `google-genai` SDK (the `gemini` embedder imports it, and it is
  not otherwise present).
- It sets a placeholder `GOOGLE_API_KEY`, because the SDK won't send a request
  without a key present and the proxy only replaces the value on the wire. The
  real key arrives from the stored `google` secret.

It also adds `generativelanguage.googleapis.com` to `allowedDomains` and writes
this `config.json`:

```json
{
  "db": {
    "url": "surrealkv:///home/agent/.surrealdb/data",
    "namespace": "sandbox",
    "database": "memory_gemini"
  },
  "embedder": {
    "provider": "gemini",
    "model": "gemini-embedding-001",
    "dims": 768
  }
}
```

## Notes

- **Dimensions come from `output_dimensionality`.** `gemini-embedding-001`
  natively defaults to 3072 but supports Matryoshka truncation. The runbook
  requests `dims` (768 by default) via `output_dimensionality`, so the vectors
  match the SurrealDB index `DIMENSION`. To use 1536 or 3072, set `dims` to the
  same value and start a fresh store (`rm -rf /home/agent/.surrealdb/data`).
- **Model names move.** Google retires Gemini model ids over time. If
  `gemini-embedding-001` starts returning 404, list what your key can use:
  ```python
  from google import genai
  for m in genai.Client().models.list():
      print(m.name, m.supported_actions)
  ```
