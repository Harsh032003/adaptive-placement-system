import time
from typing import Dict, Optional

from .rag_config import RAG_EXPLANATION_COOLDOWN_SECONDS

_cache: Dict[str, dict] = {}


def get_cached(topic: str) -> Optional[str]:
    entry = _cache.get(topic)
    if not entry:
        return None
    if time.time() - entry["timestamp"] > RAG_EXPLANATION_COOLDOWN_SECONDS:
        return None
    return entry["text"]


def set_cached(topic: str, text: str) -> None:
    _cache[topic] = {"text": text, "timestamp": time.time()}
