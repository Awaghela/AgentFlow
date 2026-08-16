# Deploying AgentFlow

Backend + Postgres on **Railway**, frontend on **Vercel**. Both platforms deploy
straight from a GitHub repo, so push this project there first if you haven't:

```bash
cd agentflow
git init && git add -A && git commit -m "AgentFlow"
gh repo create agentflow --source=. --public --push   # or push to an existing remote
```

<br />

## 1. Backend + Postgres on Railway

1. **New Project** → **Deploy from GitHub repo** → pick your repo.
2. Railway will try to deploy the repo root — you need it to build from `backend/`.
   In the new service's **Settings → Root Directory**, set it to `backend`. It will
   then pick up `backend/railway.toml` and `backend/Dockerfile` automatically.
3. **New** → **Database → Add PostgreSQL** in the same project.
4. Back on the backend service → **Variables**, add:

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (reference the Postgres plugin — Railway autocompletes this) |
   | `LLM_MODE` | `simulation` (or `live` if you're setting `ANTHROPIC_API_KEY`) |
   | `ANTHROPIC_API_KEY` | *(optional — only if `LLM_MODE=live`)* |
   | `CORS_ORIGINS` | `http://localhost:5173` for now — you'll update this in step 3 |

   `DATABASE_URL` works whether it comes through as `postgres://` or
   `postgresql://` — the app normalizes the scheme itself.
5. **Deploy**. On first boot the container creates tables, seeds the 120 eval
   scenarios, runs the suite once, and seeds demo workflow runs — check the
   deploy logs for `Seed complete.`
6. **Settings → Networking → Generate Domain** to get a public URL, e.g.
   `https://agentflow-backend-production.up.railway.app`. Confirm it's alive:

   ```bash
   curl https://<your-railway-domain>/health
   ```

<br />

## 2. Frontend on Vercel

1. **Add New Project** → import the same GitHub repo.
2. Set **Root Directory** to `frontend`. Vercel auto-detects Vite; `frontend/vercel.json`
   handles the build command, output directory, and the SPA rewrite react-router needs
   (without it, refreshing `/workflows/<id>` 404s).
3. **Environment Variables** → add:

   | Variable | Value |
   |---|---|
   | `VITE_API_BASE_URL` | `https://<your-railway-domain>/api/v1` |

   Vite bakes env vars in at build time, not runtime — if you change the backend
   URL later you'll need to redeploy the frontend, not just restart it.
4. **Deploy**. You'll get a domain like `https://agentflow.vercel.app`, plus a
   unique preview URL on every push/PR.

<br />

## 3. Close the loop: allow the frontend's origin on the backend

Back in Railway, update the backend's `CORS_ORIGINS` variable to your real Vercel
domain(s), comma-separated:

```
CORS_ORIGINS=https://agentflow.vercel.app,https://agentflow-git-main-yourteam.vercel.app
```

(Vercel preview deployments on `*.vercel.app` are covered automatically by a
regex in `app/main.py`, so you mainly need your production domain here — add
preview URLs too if you want to be explicit.)

Redeploy the backend for the change to take effect, then load the Vercel URL —
the dashboard should populate with the seeded metrics.

<br />

## Notes

- **Seeding is idempotent.** `scripts/seed_db.py` checks row counts before
  inserting, so every redeploy is safe — it won't re-seed or duplicate data.
- **Postgres data persists** across redeploys (Railway volumes the plugin's
  storage); it does *not* reset unless you delete the plugin.
- **Simulation mode by default.** The eval suite and demo data are generated
  deterministically with zero external API calls, so nothing here requires an
  Anthropic API key to run. Set `LLM_MODE=live` + `ANTHROPIC_API_KEY` on the
  Railway backend to switch the plan/respond nodes to real Claude completions.
- **Costs.** Railway's Postgres + a small backend service and Vercel's frontend
  hosting both fit comfortably in each platform's free/hobby tier for a
  portfolio project.
- **Real embeddings (optional).** `EMBEDDING_BACKEND` and `RERANK_PROVIDER` both default
  to `auto` — setting `COHERE_API_KEY` on Railway is enough to switch retrieval and
  reranking over to real Cohere calls, no other flag needed. Railway's managed Postgres
  plugin supports `CREATE EXTENSION vector`, so no extra setup is needed there, but you do
  need to run `python -m scripts.ingest_documents` once against the deployed backend
  (Railway's one-off command runner, or a local shell with `DATABASE_URL` pointed at the
  Railway Postgres) to populate the store before real embeddings show up in results. The
  120-scenario eval suite always runs against tfidf regardless of this key, so it stays
  reproducible and doesn't spend live API quota on every redeploy.
