# Live World Counter Clock (NeoBorg hive)

Tiny always-on Cloudflare Worker that stores the permanent collective TOKEX tally.

## Why B (not hybrid Pages)

Local engines POST vetted savings here; tokenish UI polls `GET /clock`.
That is the live hive. A marketing site can later poll the same URL — no second store.

## Deploy

```bash
cd packages/tokex-clock
npx wrangler deploy
```

Then in tokenish (Connect clock popup or env):

```
TOKENISH_HIVE_URL=https://tokenish-tokex-clock.<your-subdomain>.workers.dev
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/clock` | Live World Counter Clock tally |
| POST | `/contribute` | NeoBorg posts `{node_id,saved_tokex,total_tokex}` |
