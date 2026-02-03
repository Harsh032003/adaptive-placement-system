# Adaptive Placement System

## Setup
1. Create and activate a virtual environment.
2. Install backend dependencies:
   `pip install -r backend/requirements.txt`
3. Configure environment variables:
   - `DATABASE_URL` (example: `postgresql+psycopg://postgres:postgres@localhost:5432/adaptive_placement`)
   - `SECRET_KEY` (JWT signing key)
   - `ADMIN_SIGNUP_CODE` (optional; use to create admin accounts)
   - `GEMINI_API_KEY` (for embeddings + RAG explanations)
   - `EMBEDDING_MODEL` (optional, default `gemini-embedding-001`)
   - `EMBEDDING_DIM` (optional, default `1536`)
   - `GEMINI_MODEL` (optional, default `gemini-2.0-flash`)
   - `RAG_EXPLANATION_COOLDOWN_SECONDS` (optional, default `180`)
   - `DRIFT_AI_COOLDOWN_SECONDS` (optional, default `120`)
   - You can place these in a `.env` file at the repo root when using `python-dotenv`.
4. Start the backend:
   `uvicorn backend.main:app --reload`
5. Install frontend dependencies:
   `cd frontend && npm install`
6. Start the frontend:
   `npm start`
7. Ingest theory notes for RAG:
   `python -m backend.scripts.ingest_documents`

## Backend Structure
- `backend/main.py` boots the FastAPI app, mounts uploads, creates tables, and includes routers.
- `backend/db.py` defines the database engine, session, and base model.
- `backend/models.py` contains SQLAlchemy models.
- `backend/schemas.py` contains Pydantic request/response schemas.
- `backend/auth.py` handles JWT, password hashing, and auth dependencies.
- `backend/helpers.py` holds quiz and selection helpers.
- `backend/drift_ai.py` runs AI-based drift detection over recent logs.
- `backend/routes/auth_routes.py` handles signup/login/me.
- `backend/routes/quiz_routes.py` handles questions and submissions.
- `backend/routes/admin_routes.py` handles admin content and user management.
