# AGENTS.md

This repository contains a FastAPI backend that fetches Garmin data and calls Google Gemini for coaching, plus a React+TS frontend.

Key paths
- `backend/app/main.py`: primary FastAPI app (has `/api/coach/daily-analysis`)
- `backend/app/services/`: Garmin client, data processing, Gemini integration
- `src/`: shared config + services used by the backend (`src/core/config.py`, `src/services/*`)
- `scripts/`: runnable “test”/utility scripts (not a formal test suite)
- `frontend/`: Vite + React + TypeScript web app

Cursor rules in this repo
- See `.cursorrules` (summarized and incorporated below). If you change config/env variables, update `.env.example` and keep the conventions in `.cursorrules` aligned.


## Commands (Build / Lint / Test)

Backend (Python)
- Setup venv + deps:
  - `python3 -m venv venv`
  - `source venv/bin/activate`
  - `pip3 install -r requirements.txt`
- Configure env:
  - `cp .env.example .env` and set `GARMIN_EMAIL`, `GARMIN_PASSWORD`, `GEMINI_API_KEY`
  - China region: set `GARMIN_IS_CN=true`
  - Optional proxy (for Google API): set `PROXY_URL=http://127.0.0.1:7890`
- Run API (recommended entrypoint):
  - `uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000`
- Quick “smoke check” endpoints:
  - `GET http://localhost:8000/health`
  - `GET http://localhost:8000/api/coach/daily-analysis`

Backend lint/format
- No dedicated Python linter/formatter is configured in `requirements.txt` (no ruff/black/isort/mypy).
- Minimal sanity check you can run:
  - `./venv/bin/python3 -m compileall backend src scripts`

Backend tests (scripts-based)
- There is no `pytest` suite; “tests” are standalone scripts in `scripts/`.
- Run a single “test” script:
  - `./venv/bin/python3 scripts/test_garmin_auth.py`
  - `./venv/bin/python3 scripts/test_coach.py`
  - `./venv/bin/python3 scripts/test_data_processor.py`
- Run a single “test” for a specific date:
  - `./venv/bin/python3 scripts/test_data_processor.py 2026-01-23`

Frontend (React + TS)
- Install:
  - `cd frontend && npm install`
- Configure API base URL:
  - `cp .env.example .env` and set `VITE_API_BASE_URL=http://localhost:8000`
- Run dev server:
  - `cd frontend && npm run dev` (default `http://localhost:5173`)
- Build:
  - `cd frontend && npm run build`
- Lint:
  - `cd frontend && npm run lint`
- Preview production build:
  - `cd frontend && npm run preview`

Frontend: run a “single test” / single target
- No unit-test runner is configured (no `npm test`).
- Lint a single file:
  - `cd frontend && npm run lint -- src/components/Layout.tsx`
- Typecheck only:
  - `cd frontend && npx tsc -p tsconfig.json --noEmit`


## Code Style Guidelines

### General
- Prefer small, reviewable diffs; don’t reformat unrelated code.
- Keep secrets out of git: `.env` is ignored. Do not log or print credentials/tokens.
- Avoid editing generated/vendor dirs: `venv/`, `frontend/node_modules/`, build outputs.


### Python (backend + src + scripts)

Language/runtime
- Target Python 3.9+ (repo contains a `venv/` using 3.9).
- Add `from __future__ import annotations` in new modules when it helps typing (already used in `backend/app/services/data_processor.py`).

Imports
- Group imports in this order, separated by blank lines:
  1) standard library 2) third-party 3) local (`backend.*` / `src.*`)
- Avoid adding new “sys.path hacks” unless necessary; existing scripts add repo root to `sys.path` to allow `from src...` imports.

Typing
- Type key inputs/outputs, especially service boundaries and API responses.
- Use `Optional[T]` for nullable values; prefer concrete containers (`list`, `dict`) with type params.
- Keep API payload keys consistent with current responses (snake_case like `raw_data_summary`, `ai_advice`).

Naming
- `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Prefer descriptive names over abbreviations in new code (existing code uses some short locals like `hr`, `dur` inside tight loops).

Configuration (from `.cursorrules`)
- Read configuration only via `src.core.config.settings`.
- When adding settings: extend `Settings` in `src/core/config.py`; keep `extra = "ignore"` behavior.
- Garmin CN/International: construct Garmin clients with `is_cn=settings.GARMIN_IS_CN`.

Services (from `.cursorrules`)
- Keep sync-style services consistent with existing ones:
  - `GarminService(email, password)` logs in during `__init__`.
  - LLM/Gemini service config reads `settings.GEMINI_API_KEY` and calls `genai.configure(...)`.

Error handling
- Don’t swallow exceptions silently.
- In FastAPI handlers, raise `fastapi.HTTPException` with a clear `detail`.
- In services: catch expected failures, log context, and re-raise or return a meaningful fallback.
- In scripts: print actionable troubleshooting hints and exit with non-zero status on failure.

Logging
- Prefer `logging` over `print` in backend services and API routes.
- Avoid logging large payloads that may contain personal health data; log counts/summaries instead.

Mock mode
- `backend/app/main.py` has `USE_MOCK_MODE` for local development. Be careful not to change behavior unintentionally when editing API flow.


### TypeScript/React (frontend)

Tooling constraints
- ESLint is configured via `frontend/.eslintrc.cjs`.
- TypeScript is `strict: true` (`frontend/tsconfig.json`). Fix type errors; don’t “any” around them.

Formatting
- Follow the existing style:
  - single quotes
  - no semicolons
  - 2-space indentation
  - trailing commas where natural
- Prefer small components and early returns for readability.

Imports
- External imports first, then local imports, then side-effect imports (CSS).
- Use `import type { ... }` for type-only imports (already used in `frontend/src/api/coach.ts`).

Types and data shapes
- Backend responses use snake_case; keep frontend types aligned (`frontend/src/types/index.ts`).
- Avoid re-mapping keys unless you have a clear boundary (e.g., a mapper function at the API layer).

Error handling
- Keep network failures user-visible and actionable.
- Prefer handling errors at the React Query layer/hooks and rendering a consistent error UI (`frontend/src/components/Error.tsx`).
- Avoid `console.error` spam in components; centralize in API layer/interceptors when possible.

State/data fetching
- Prefer React Query for server state and caching (`@tanstack/react-query`).
- Keep hooks in `frontend/src/hooks/` and API calls in `frontend/src/api/`.

Styling
- Tailwind is used; follow existing utility-first patterns.
- Keep shared layout/navigation changes in `frontend/src/components/Layout.tsx`.
