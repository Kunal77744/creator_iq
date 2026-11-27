# CreatorIQ — AI-Native Creator Analytics & Content Performance Platform

**Live App:** https://creatoriq-eight.vercel.app

A full-stack, multi-role SaaS analytics platform for **Creators**, **Agencies**, **Marketing Teams**, and **Administrators** — featuring live YouTube Data API v3 sync, PostgreSQL + `pgvector` RAG, a tool-calling Growth Agent, an MCP Server, Redis caching, Celery workers, and Docker Compose orchestration.

---

## Architecture

```text
React (Vite + Recharts) ──▶ FastAPI (/api/v1/*) ──▶ PostgreSQL + pgvector (Neon / Docker)
                                  │
                                  ├── Redis (Analytics Cache & Celery Broker)
                                  ├── Celery Worker (Scheduled YouTube Sync)
                                  └── AI Layer (pgvector RAG, Growth Agent, FastMCP Server)
```

---

## Tech Stack

- **Frontend:** React 18, Vite 5, React Router, Recharts, Axios, Vitest + React Testing Library
- **Backend:** FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, PyJWT, `bcrypt`, Celery, Redis
- **Database:** PostgreSQL 16 + `pgvector` (Neon Cloud in production; `pgvector/pgvector:pg16` in Docker)
- **AI & MCP:** `pgvector` cosine-similarity RAG + hybrid metric reranking, Google Gemini (`gemini-2.5-flash` & `text-embedding-004` when `LLM_API_KEY` is set, with deterministic fallback), and `FastMCP` server (`app.ai.mcp.server`)
- **DevOps & CI:** Docker, Docker Compose, GitHub Actions (`.github/workflows/ci.yml`), Vercel

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` (used by both local runs and `docker compose`):

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string (`postgresql+psycopg2://...`) |
| `SECRET_KEY` | Yes | Strong random secret for JWT signing (`HS256`) |
| `REDIS_URL` | Optional | Redis URL for caching & Celery (`redis://localhost:6379/0`) |
| `FRONTEND_ORIGIN` | Yes | Comma-separated allowed CORS origins (e.g. `http://localhost:5173`) |
| `SEED_DEMO_USERS` | Optional | `true` to seed 4 demo accounts (`Demo@1234`); keep `false` in production |
| `YOUTUBE_API_KEY` | Optional | YouTube Data API v3 key for live channel & video sync |
| `LLM_API_KEY` | Optional | Google Gemini API key for LLM synthesis & 384-dim embeddings |
| `RAPIDAPI_KEY` | Optional | RapidAPI key for Instagram profile sync |
| `LINKEDIN_CLIENT_ID` / `SECRET` | Optional | LinkedIn OAuth credentials |

---

## Quick Start (Docker Compose)

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your keys
docker compose up --build
```
- **Frontend:** http://localhost:5173
- **API & Swagger Docs:** http://localhost:8000/docs
- **Healthcheck:** http://localhost:8000/api/v1/health

---

## Local Development (Without Docker for App)

```bash
# 1. Start Postgres (pgvector) & Redis
docker compose up -d postgres redis

# 2. Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# 3. Frontend
cd frontend
npm install
npm run dev
```

---

## Testing

- **Backend (`68` pytest tests against PostgreSQL + `pgvector` + Redis):**
  ```bash
  cd backend
  pip install -r requirements-dev.txt
  pytest -v
  ```
- **Frontend (`5` Vitest + React Testing Library tests):**
  ```bash
  cd frontend
  npx vitest run
  ```

---

## CreatorIQ MCP Server (Claude Desktop / IDE)

```json
{
  "mcpServers": {
    "creatoriq": {
      "command": "python",
      "args": ["-m", "app.ai.mcp.server"],
      "cwd": "/path/to/creatoriq/backend",
      "env": {
        "DATABASE_URL": "postgresql+psycopg2://postgres:postgres@localhost:5433/creatoriq"
      }
    }
  }
}
```
