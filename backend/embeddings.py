import os
from typing import List, Optional

import requests

from .rag_config import EMBEDDING_DIM, EMBEDDING_MODEL

GEMINI_BASE_URL = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")


def _model_path(model: str) -> str:
    return model if model.startswith("models/") else f"models/{model}"


def get_embedding(text: str, task_type: Optional[str] = None) -> List[float]:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    payload = {
        "content": {"parts": [{"text": text}]},
    }
    if task_type:
        payload["taskType"] = task_type
    if EMBEDDING_DIM:
        payload["outputDimensionality"] = EMBEDDING_DIM

    response = requests.post(
        f"{GEMINI_BASE_URL}/{_model_path(EMBEDDING_MODEL)}:embedContent",
        params={"key": gemini_api_key},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["embedding"]["values"]
