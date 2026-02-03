import os

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", "1536"))
RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "3"))
RAG_EXPLANATION_COOLDOWN_SECONDS = int(os.environ.get("RAG_EXPLANATION_COOLDOWN_SECONDS", "180"))
DRIFT_AI_COOLDOWN_SECONDS = int(os.environ.get("DRIFT_AI_COOLDOWN_SECONDS", "120"))
