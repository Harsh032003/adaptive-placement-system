from typing import List

from sqlalchemy.orm import Session

from .embeddings import get_embedding
from .llm_gemini import generate_explanation, RateLimitError
from .models import DocumentEmbedding
from .rag_config import RAG_TOP_K
from .rag_cache import get_cached, set_cached


def retrieve_chunks(db: Session, topic: str) -> List[str]:
    query_embedding = get_embedding(topic, task_type="RETRIEVAL_QUERY")
    results = (
        db.query(DocumentEmbedding)
        .order_by(DocumentEmbedding.embedding.cosine_distance(query_embedding))
        .limit(RAG_TOP_K)
        .all()
    )
    return [row.content for row in results]


def explain_with_rag(db: Session, topic: str, user_answer: str) -> str:
    cached = get_cached(topic)
    if cached:
        return cached
    chunks = retrieve_chunks(db, topic)
    if not chunks:
        return "I couldn't find any relevant notes yet."
    try:
        explanation = generate_explanation(chunks, user_answer, topic)
    except RateLimitError:
        # Fallback: return a simple summary from retrieved notes without calling Gemini
        preview = "\n\n".join(chunks[:2])
        explanation = f"Here are key notes to review:\n\n{preview}"
    set_cached(topic, explanation)
    return explanation
