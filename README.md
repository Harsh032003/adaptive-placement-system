# Adaptive Placement System

## Local Setup
1. Create and activate a virtual environment.
2. Install backend dependencies:
   `pip install -r backend/requirements.txt`
3. Configure environment variables:
   - `DATABASE_URL` (example: `postgresql+psycopg://postgres:postgres@localhost:5432/adaptive_placement`)
   - `SECRET_KEY` (JWT signing key)
   - `ADMIN_SIGNUP_CODE` (optional; use to create admin accounts)
   - `REACT_APP_API_URL` (frontend API URL; local default: `http://localhost:8000`)
   - `GEMINI_API_KEY` (for embeddings + RAG explanations)
   - `EMBEDDING_MODEL` (optional, default `gemini-embedding-001`)
   - `EMBEDDING_DIM` (optional, default `1536`)
   - `GEMINI_MODEL` (optional, default `gemini-2.0-flash`)
   - `RAG_EXPLANATION_COOLDOWN_SECONDS` (optional, default `180`)
   - `DRIFT_AI_COOLDOWN_SECONDS` (optional, default `120`)
   - You can place these in a `.env` file at the repo root when using `python-dotenv`.
4. Run database migrations:
   `alembic upgrade head`
   - For an existing local dev DB that already has the current tables, use `alembic stamp head` once instead.
   - For a fresh DB, always use `alembic upgrade head`.
5. Start the backend:
   `uvicorn backend.main:app --reload`
6. Install frontend dependencies:
   `cd frontend && npm install`
7. Start the frontend:
   `npm start`
8. Ingest theory notes for RAG if you want to run it manually:
   `python -m backend.scripts.ingest_documents`
   - Admin uploads now also attempt ingestion automatically.

## Docker Compose Setup
Use this for a full local stack with Postgres + pgvector, FastAPI, and React/Nginx.

Prerequisite: Docker Desktop must be installed and running.

1. Copy env values:
   `cp .env.example .env`
2. Update `.env` with your real `GEMINI_API_KEY` and a strong `SECRET_KEY`.
3. Start the stack:
   `docker compose up --build`
4. Open:
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
5. Stop the stack:
   `docker compose down`

Useful Docker commands:
- Restart services: `docker compose restart`
- View logs: `docker compose logs -f backend`
- Reset local Docker DB data: `docker compose down -v`

The backend container runs `alembic upgrade head` automatically before starting Uvicorn.

## Deployment Path
Recommended low-cost/free-friendly path for a capstone demo:

1. Database: Supabase Postgres
   - Create a Supabase project.
   - Enable the `vector` extension.
   - Copy the Postgres connection string.
   - Use that as `DATABASE_URL` in the backend service.

2. Backend: Render Web Service
   - Create a new Python web service from this repo.
   - Root directory: repository root.
   - Build command:
     `pip install -r backend/requirements.txt`
   - Start command:
     `alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables:
     `DATABASE_URL`, `SECRET_KEY`, `ADMIN_SIGNUP_CODE`, `GEMINI_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`, `GEMINI_MODEL`.

3. Frontend: Vercel Hobby
   - Import the repo in Vercel.
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `build`
   - Add environment variable:
     `REACT_APP_API_URL=https://your-backend-url`

4. After deployment:
   - Visit the frontend URL.
   - Sign up with the admin code.
   - Add questions/notes from Admin.
   - Upload notes and use `Ingest Now` or `Ingest All` if needed.

Notes:
- Free tiers are good for demos, not production.
- Render free services may sleep after inactivity.
- Uploaded PDFs on many free backend hosts may not persist unless you attach persistent storage. For a demo, text notes are simpler and safer.
- Gemini free tier can rate-limit; the app includes fallbacks, but AI explanations may sometimes be delayed.

## Backend Structure
- `backend/main.py` boots the FastAPI app, mounts uploads, and includes routers.
- `backend/db.py` defines the database engine, session, and base model.
- `backend/models.py` contains SQLAlchemy models.
- `alembic/` contains versioned database migrations.
- `backend/schemas.py` contains Pydantic request/response schemas.
- `backend/auth.py` handles JWT, password hashing, and auth dependencies.
- `backend/helpers.py` holds quiz and selection helpers.
- `backend/drift_ai.py` runs AI-based drift detection over recent logs.
- `backend/routes/auth_routes.py` handles signup/login/me.
- `backend/routes/quiz_routes.py` handles questions and submissions.
- `backend/routes/admin_routes.py` handles admin content and user management.
