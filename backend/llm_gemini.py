import os
from typing import List

import time
import requests

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_BASE_URL = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")

class RateLimitError(RuntimeError):
    pass


def generate_explanation(chunks: List[str], user_answer: str, topic: str) -> str:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    context = "\n\n".join([f"Chunk {i+1}: {chunk}" for i, chunk in enumerate(chunks)])
    prompt = (
        "The student failed this question. Using these notes, explain the concept simply. "
        f"Topic: {topic}. User answer: {user_answer}.\n\nNotes:\n{context}"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ]
    }

    url = f"{GEMINI_BASE_URL}/models/{GEMINI_MODEL}:generateContent"
    for attempt in range(3):
        response = requests.post(
            url,
            params={"key": gemini_api_key},
            json=payload,
            timeout=30,
        )
        if response.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        response.raise_for_status()
        data = response.json()
        break
    else:
        raise RateLimitError("Gemini rate limit exceeded")
    candidates = data.get("candidates", [])
    if not candidates:
        return "I could not generate an explanation right now."
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        return "I could not generate an explanation right now."
    return parts[0].get("text", "I could not generate an explanation right now.")
