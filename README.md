# AI Knowledge Inbox

Save notes and web pages, then ask questions about them in plain English. Answers come from your own saved content, with the sources they were drawn from.

**Live:** https://ai-knowledge-inbox-pgvector-rag.vercel.app

Under the hood it's a retrieval-augmented generation (RAG) app: saved content is split into chunks, embedded with OpenAI, stored in Postgres with pgvector, and searched by meaning when you ask something. Each user has their own private inbox.

> The free hosting sleeps when idle, so the first request after a while can take up to a minute while the backend wakes up. The app shows a "Can't reach the server — try again" screen during that window.

---

## Features

- Accounts with name, email and password; sessions last a day
- Save a note or a URL (the page text is fetched and extracted)
- Ask a question and get an answer grounded in your saved items, with cited sources
- Suggested questions generated for each saved item
- Every item and every search is scoped to the logged-in user
- Works on desktop and phone widths

## Tech stack

| Layer | Tools |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS 4, React Router 7, Zustand, axios |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, Pydantic 2, Alembic |
| Database | PostgreSQL 16 + pgvector (HNSW index, cosine distance) |
| AI | OpenAI `text-embedding-3-small` (embeddings), `gpt-4o-mini` (answers) |
| Auth | Argon2id password hashing, JWT in an httpOnly cookie, double-submit CSRF token |
| Testing | pytest (75 tests against real Postgres), Playwright (16 end-to-end browser tests), ruff, oxlint, tsc |
| Infra | Docker / Docker Compose, GitHub Actions (CI + CD) |
| Hosting | Vercel (frontend), Render (backend, Docker), Neon (Postgres) |

## Architecture

```
                         ┌──────────────────────────────── Vercel ─────────────────────────────┐
browser ── HTTPS ───────▶│  static React build                                                  │
                         │    /login /register /inbox …  → index.html (React Router)            │
                         │    /api/*  ── rewrite ──────────────────────────────┐                │
                         └─────────────────────────────────────────────────────┼────────────────┘
                                                                               ▼
                                                   Render (Docker, FastAPI) ──▶ Neon (Postgres + pgvector)
                                                            │
                                                            └──▶ OpenAI (embeddings, chat)
```

**Saving an item:** fetch the page (for URLs) → split into ~1200-character overlapping chunks → embed all chunks in one OpenAI call → store the item and its chunks in a single transaction.

**Asking a question:** embed the question → nearest-neighbour search over *your* chunks in Postgres (`embedding <=> question`, HNSW index) → drop weak matches → send the top chunks to the chat model with numbered context → return the answer and its sources.

## Design decisions

**Cookie-based auth instead of localStorage.** The JWT lives in an `HttpOnly` cookie, so JavaScript on the page can never read it, and an XSS bug can't steal the session. The trade-off is CSRF exposure, handled two ways: `SameSite=Lax`, plus a double-submit token (a readable `csrf_token` cookie that the frontend echoes in an `X-CSRF-Token` header on every state-changing request). `/docs`, tests and scripts get a plain Bearer token from `POST /auth/token` instead.

**One origin through a proxy.** The frontend calls `/api/...` on its own domain, and Vercel rewrites those requests to Render. The browser never talks to the backend's domain, so the auth cookie is first-party (Safari and Firefox block third-party cookies) and no CORS is needed. Local development does the same with Vite's dev proxy.

**Vector search in the database.** The first version of this project kept embeddings in SQLite and compared them in a Python loop. Here pgvector does the search next to the data, with an HNSW index. Because the index finds neighbours across all users before the `user_id` filter applies, a user with only a few chunks could get nothing back; `hnsw.iterative_scan` makes Postgres keep scanning until it has enough of that user's chunks.

**Ownership enforced in the query.** Routes filter by the logged-in user inside the SQL `WHERE`, and someone else's item returns 404, not 403, so ids can't be probed. The user id always comes from the verified token, never from the request body. Ids are UUIDs.

**Migrations that survive a deploy.** Schema changes go through Alembic and follow expand → contract: a new required column is added as nullable, backfilled, and only tightened later, because during a deploy the old code briefly runs against the new schema.

**Unreachable isn't logged out.** The frontend treats a missing response or an empty 502/503/504 as "server unreachable" (show a retry screen), and only a real 401 as "not logged in". Otherwise a sleeping free-tier backend would bounce everyone to the login page.

**Back after logout.** Browsers can restore a frozen copy of a page from their back/forward cache, logged-in content included. The app listens for `pageshow` with `persisted` and re-checks the session when that happens.

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # routes: auth, items, query, and the current-user dependency
│   │   ├── core/         # settings, security (hashing, JWT, CSRF), logging
│   │   ├── db/           # SQLAlchemy models and session
│   │   ├── schemas/      # request/response models
│   │   └── services/     # chunking, embeddings, retrieval, answering, ingestion, URL fetching
│   ├── alembic/          # migrations
│   ├── tests/            # pytest suite
│   ├── Dockerfile
│   └── requirements.txt  # requirements-dev.txt adds pytest and ruff
├── frontend/
│   ├── src/
│   │   ├── api/          # axios client and interceptors (CSRF header, session expiry)
│   │   ├── components/   # screens and UI pieces
│   │   ├── store/        # Zustand stores (auth, inbox)
│   │   └── utils/
│   ├── e2e/              # Playwright tests
│   ├── playwright.config.ts
│   ├── vite.config.ts    # includes the /api dev proxy
│   └── vercel.json       # /api rewrite to the backend + SPA fallback
├── docker-compose.yml    # Postgres + backend for local development
└── .github/workflows/ci.yml
```

## Running it locally

### Prerequisites

- **Docker** with Compose. Docker Desktop, OrbStack or Colima all work. On a Mac without Docker Desktop:
  ```bash
  brew install colima docker docker-compose docker-buildx
  colima start --cpu 2 --memory 4 --disk 30
  ```
- **Node 24** (the version is pinned in `frontend/.nvmrc`) and **pnpm**
- **Python 3.13**, only if you want to run the backend or its tests outside Docker
- An **OpenAI API key** with credit, for saving and asking

### 1. Backend and database

```bash
git clone https://github.com/TejoVarma/AI-Knowledge-Inbox-pgvector-RAG.git
cd AI-Knowledge-Inbox-pgvector-RAG
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```bash
OPENAI_API_KEY=sk-...
JWT_SECRET=...            # generate one: openssl rand -hex 32
COOKIE_SECURE=false       # local dev is plain http
```

Then start Postgres and the API:

```bash
docker compose up -d --build
```

This starts Postgres with pgvector, runs the Alembic migrations, and serves the API on http://localhost:8000. Interactive docs are at http://localhost:8000/docs; use the **Authorize** button with your email (as username) and password.

Postgres is exposed on **port 5433** on your machine (user `postgres`, password `dev`, database `inbox`), so it doesn't clash with a Postgres already running on 5432. Inside Compose the API reaches it as `db:5432`.

### 2. Frontend

```bash
cd frontend
nvm use          # Node 24
pnpm install
pnpm start       # http://localhost:3000
```

The dev server forwards `/api/*` to `http://localhost:8000`. To point it somewhere else, for example the live backend, create `frontend/.env`:

```bash
BACKEND_URL=https://ai-knowledge-inbox-pgvector-rag.onrender.com
```

Open http://localhost:3000, register, and you're in.

### Running the backend without Docker

```bash
cd backend
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

This still needs a Postgres with pgvector. The Compose `db` service is the easiest way to get one (`docker compose up -d db`).

## Configuration

### Backend (`backend/.env` locally, environment variables in production)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `OPENAI_API_KEY` | yes | — | |
| `JWT_SECRET` | yes | — | No default on purpose: a guessable fallback would let anyone forge sessions. The app won't start without it |
| `DATABASE_URL` | no | local Compose database | Must use the `postgresql+psycopg://` scheme. Leave it out locally |
| `COOKIE_SECURE` | no | `true` | Set `false` for plain-http local development |
| `CORS_ORIGINS` | no | `[]` | JSON list of exact origins. Not needed with the proxy setup; `"*"` is rejected |
| `JWT_EXPIRE_MINUTES` | no | `1440` | Session length (one day) |
| `EMBEDDING_MODEL` / `CHAT_MODEL` | no | `text-embedding-3-small` / `gpt-4o-mini` | |
| `CHUNK_SIZE_CHARS` / `CHUNK_OVERLAP_CHARS` | no | `1200` / `150` | |
| `TOP_K_CHUNKS` / `MIN_SIMILARITY` | no | `4` / `0.45` | How many chunks feed an answer, and the cosine-similarity cut-off |

Inside Docker Compose, `backend/compose.env` supplies a `DATABASE_URL` pointing at the `db` service. A `DATABASE_URL` in `backend/.env` overrides it.

### Frontend (`frontend/.env`, optional)

| Variable | Default | Notes |
|---|---|---|
| `BACKEND_URL` | `http://localhost:8000` | Where the dev server forwards `/api`. Read by Vite's server only; it never ends up in the browser bundle |

The frontend has no production settings: it calls `/api` on its own origin.

## Tests

### Backend

The suite runs against a real Postgres database (`inbox_test`, created automatically and built with the real migrations), with OpenAI calls mocked. It refuses to run against any database whose name doesn't end in `_test`.

```bash
docker compose up -d db
cd backend && source .venv/bin/activate
pytest -q          # 75 tests
ruff check .
```

### Frontend

```bash
cd frontend
pnpm run typecheck
pnpm run lint
pnpm run build
```

### End-to-end (Playwright)

16 browser tests covering routing and redirects, registration and login, refresh, logout across tabs, user isolation, the back/forward-cache case, an unreachable server, and the phone layout. They run against a production build (`vite preview` on port 4173) and need the backend running on port 8000.

```bash
cd frontend
pnpm exec playwright install chromium   # once
pnpm test:e2e
pnpm exec playwright test --ui          # interactive runner
```

To smoke-test a deployed site instead:

```bash
E2E_BASE_URL=https://ai-knowledge-inbox-pgvector-rag.vercel.app pnpm test:e2e
```

This creates `e2e-…@example.com` accounts in that site's database, so clean them up afterwards.

No e2e test makes a successful OpenAI call, so the suite is free to run.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every pull request and on every push to `main`:

| Job | What it does |
|---|---|
| `tests` | ruff + pytest against a pgvector service container |
| `docker-build` | builds the backend image |
| `frontend` | typecheck, lint and build with the Node version from `.nvmrc` |
| `e2e` | starts Postgres and the backend, builds the frontend, runs Playwright; uploads the report, traces and backend log if anything fails |
| `migrate` | `main` only, after all four checks pass: `alembic upgrade head` on the production database |
| `deploy` | `main` only, after `migrate`: triggers the Render deploy hook |

Migrations run before the new backend goes live, so new code never meets an old schema. Runs on `main` queue rather than cancel each other, so a deploy is never interrupted mid-migration. `main` is branch-protected: a pull request can't be merged until the four checks are green.

Vercel deploys the frontend from `main` through its own GitHub integration, and builds a preview URL for each pull request.

CI needs no real secrets: tests mock OpenAI and use throwaway values. The two deploy secrets (`NEON_DIRECT_URL`, `RENDER_DEPLOY_HOOK`) are GitHub Actions secrets, used only by the `main`-only jobs.

## Deployment

| Piece | Where | Notes |
|---|---|---|
| Database | Neon, Postgres 16, Singapore | The app uses the pooled connection string, migrations use the direct one |
| Backend | Render free web service, Docker, Singapore | Build context `./backend`, health check `/health`, auto-deploy off (CD triggers it). Settings: `DATABASE_URL`, `OPENAI_API_KEY`, `JWT_SECRET` |
| Frontend | Vercel Hobby | Root directory `frontend`, no environment variables; `vercel.json` handles the `/api` rewrite and the SPA fallback |

The backend and database sit in the same region, since each question makes several database round trips.

## API

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/health` | — | Liveness check |
| `POST` | `/auth/register` | — | Create an account (`name`, `email`, `password`) |
| `POST` | `/auth/login` | — | Browser login: sets the session and CSRF cookies, returns the user |
| `POST` | `/auth/token` | — | Bearer token for tools (OAuth2 password form) |
| `POST` | `/auth/logout` | — | Clears the cookies |
| `GET` | `/auth/me` | yes | The current user |
| `POST` | `/ingest` | yes | Save a note (`{"source_type": "note", "content": …}`) or a URL (`{"source_type": "url", "url": …}`) |
| `GET` | `/items` | yes | Your saved items, newest first |
| `DELETE` | `/items/{id}` | yes | Delete one of your items |
| `POST` | `/query` | yes | Ask a question (`{"question": …}`) |

"Auth" means a session cookie (with the `X-CSRF-Token` header on POST/DELETE) or `Authorization: Bearer <token>`. Through the frontend these paths are prefixed with `/api`.

## Security notes

- Passwords are hashed with Argon2id, using OWASP's low-memory profile (19 MiB) so the hashing fits a 512 MB instance
- Unknown email and wrong password return the same message, and take the same time
- Sessions are httpOnly, `Secure` and `SameSite=Lax` cookies, with CSRF protection on every state-changing request
- CORS allows no other origins, and the app refuses to start with `"*"`
- Every query is scoped to the authenticated user
- Logs carry user ids, never emails, passwords or tokens

## Known limitations and next steps

- **Usage limits.** There's no per-user daily quota and no rate limiting on login and register yet, so a determined script could create accounts or spend OpenAI credit. Planned: a daily quota per user (an atomic upsert counter) and per-IP limits on the auth routes.
- **Sessions can't be revoked** before they expire, which is inherent to stateless JWTs. Refresh tokens or a deny-list would fix that.
- **No email verification or password reset.**
- **`users.name` is nullable in the database** and only enforced by the API. The column gets tightened to `NOT NULL` in a follow-up migration.
- **The similarity cut-off (0.45)** can filter out loosely worded questions. It needs tuning, or a low-confidence answer instead of none.
- **Saving a URL fetches it server-side**, and there's no guard yet against internal addresses (SSRF).
