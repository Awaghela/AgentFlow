# AgentFlow

Enterprise agent workflow platform: turns a business request into a multi-step AI plan,
retrieves context, calls tools, validates its own output, and routes to a human when it
should — with a full audit trail and a 120-scenario eval suite that continuously checks
the failure paths, not just the happy path.

```
Request → Plan → Retrieve context → Call tools → Validate → Respond → Approval gate
```

**Backend:** Python · FastAPI · LangGraph · PostgreSQL + pgvector · Cohere Embed/Rerank
**Frontend:** React · TypeScript · Vite · Tailwind · Recharts

<br />

## Quickstart

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (docs at `/docs`)

The backend seeds itself on first boot — creates tables, inserts the 120 eval scenarios,
runs the suite once, submits a handful of demo requests — so the dashboard has real
numbers the moment it loads. Runs fully offline by default, zero API keys required.

**Deploying to production?** See [`DEPLOYMENT.md`](./DEPLOYMENT.md) — Railway (backend +
Postgres) + Vercel (frontend).

<br />

## What's actually in here

- **LangGraph orchestration**, not a linear script — conditional routing means missing
  context or a failed tool call both fall through to a `fallback` node that produces a
  clearly-flagged degraded response instead of crashing or hallucinating a confident
  answer.
- **Real retrieval, pluggable.** TF-IDF by default (in-memory, zero dependencies — what
  the eval suite always runs against). Add `COHERE_API_KEY` and retrieval and reranking
  both auto-switch to real Cohere Embed + Rerank calls, stored in and queried from a
  genuine `pgvector` column in Postgres — an actual cosine-distance SQL query, not an
  in-memory scan. No key needed to try it either way; a misconfigured or unreachable
  backend degrades gracefully instead of failing the request.
- **Tools** — `crm_lookup`, `calculate_refund`, `knowledge_search`, `create_ticket`, each
  timed and logged so every call shows up in the trace.
- **120-scenario eval suite** across 7 failure categories (missing context, failed tool
  calls, incorrect retrieval, unsafe outputs, latency issues, approval routing, fallback
  behavior), each with concrete pass/fail assertions checked against the graph's actual
  output — not just "did it run." Always deterministic: it never touches a live API,
  regardless of what's configured elsewhere, so it gives the same 120/120 every run.
- **Human approval gate** — low confidence, high risk, or a blocked unsafe draft routes
  to a review queue instead of straight to output.
- **Full audit trail** — every plan, every node's input/output, every tool call, every
  retrieval hit, and every approval decision persisted to Postgres and viewable in a
  flight-recorder-style trace timeline in the UI.

<br />

## Try it with real Cohere retrieval

```bash
export COHERE_API_KEY=your_key
python -m scripts.ingest_documents   # embeds the corpus into pgvector via Cohere
uvicorn app.main:app --reload         # retrieval + reranking now use Cohere automatically
```

No key set → falls back to TF-IDF automatically, no flags to flip either way. Open any
request's trace in the UI and expand "Retrieve context" — a green "✓ reranked via cohere"
badge confirms it's genuinely working, not silently falling back. Full details on the two
corpora (a fictional demo set and a 14-document real-world corpus grounded in actual FTC/
HIPAA regulatory guidance), the local-embeddings alternative, and forcing a specific
backend are in `backend/app/rag/` and `backend/.env.example`.

<br />

## Architecture

```
 React / TypeScript console
          │
          ▼
   FastAPI  ( /workflows  /approvals  /metrics  /eval )
          │
          ▼
   LangGraph orchestrator
   plan → retrieve → tools → validate → respond → approval → END
   (fallback node catches missing context / failed tools along the way)
          │                    │
          ▼                    ▼
   RAG (TF-IDF /          Tools: crm_lookup, calculate_refund,
   pgvector + Cohere)     knowledge_search, create_ticket
          │
          ▼
     PostgreSQL — trace logs, approvals, eval results
```

<br />

## The console

- **Overview** — success rate, fallback rate, latency percentiles, eval pass rate by
  category, tool performance, and a box to submit new requests
- **Workflow runs / trace** — every request, and a full node-by-node trace with retrieval
  hits and tool call details for each one
- **Approvals** — the human-review queue, approve/reject with notes
- **Eval suite** — pass rate by category, full scenario list, and a button to re-run all
  120 live

<br />

## Project layout

```
backend/
  app/
    orchestration/   # LangGraph state, nodes, graph wiring
    rag/              # corpora, TF-IDF + pgvector backends, Cohere embed/rerank, retriever
    tools/            # crm_lookup, calculate_refund, knowledge_search, create_ticket
    eval/             # 120-scenario generator + assertion-checking runner
    api/, db/, models/, schemas/
  scripts/           # seed_db.py, run_eval.py, ingest_documents.py
  tests/             # pytest — fast suite + skippable pgvector integration tests

frontend/
  src/
    pages/            # Dashboard, Workflows, WorkflowDetail, Approvals, EvalResults
    components/       # trace timeline, metrics charts, approvals, layout
    api/, types/       # typed client + schemas mirroring the backend
```

<br />

## Design notes

Dark "control tower" palette — amber for pending/attention states, green/red/cyan for
the rest — monospace type for anything that's data (latencies, IDs, trace output), and a
signature trace timeline styled after a flight recorder: each step is a tick on a
vertical tape, width-scaled to its latency, colored by outcome. Built to look like an
audit/observability tool for AI agent decisions, because that's what it is.