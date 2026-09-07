# Sovereign AI Workbench — Frontend

React + Vite + TypeScript workbench UI for the Sovereign AI Workbench backend (FastAPI, `app/`).

## Run

```bash
npm install
npm run dev
```

Opens on `http://localhost:5173`.

## Backend

The dev server proxies these path prefixes to `http://localhost:8000` (see `vite.config.ts`), so it
expects the FastAPI backend running locally on port 8000 — no CORS setup needed:

`/chat`, `/tasks`, `/models`, `/knowledge`, `/files`, `/health`, `/artifacts`, `/audit`

To run the backend, from the repo root:

```bash
uvicorn app.api.main:app --reload
```

Without the backend running, pages that fetch data (Dashboard, Models, Knowledge Base, Artifacts,
Security Monitor) will show their loading/error states rather than crash — that's expected.

Some flows additionally need models pulled/cached locally (see the backend's own setup docs once
they exist):
- Task execution (Task Workspace, `/chat`, `/tasks`) needs Ollama running with `qwen3:4b`,
  `qwen2.5-coder:7b`, and `qwen2.5vl:3b` pulled.
- Knowledge base search needs the `BAAI/bge-m3` embedding model already in the local Hugging Face
  cache (it runs fully offline and will not auto-download it).

## Structure

- `src/api/` — typed client for the FastAPI backend (`types.ts` mirrors the real Pydantic/dataclass
  response shapes in `app/api/*.py`; `client.ts` wraps `fetch`)
- `src/components/` — shared UI (app shell/nav, execution trace renderer, panels/badges/spinners)
- `src/pages/` — one file per screen (Dashboard, Task Workspace, Knowledge Base, Models, Artifacts,
  Security Monitor)
