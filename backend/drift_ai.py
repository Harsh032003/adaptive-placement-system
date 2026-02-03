import json
import os
import time
from typing import List, Dict

import requests

from .llm_gemini import RateLimitError
from .rag_config import DRIFT_AI_COOLDOWN_SECONDS


def _build_prompt(logs: List[Dict]) -> str:
    return (
        "You are a strict evaluator for student skill drift.\n"
        "Drift is defined as 2+ consecutive errors OR taking >60s on an 'Easy' question.\n"
        "Return ONLY valid JSON with keys drift_detected (boolean) and reason (string). No markdown.\n"
        f"Logs: {json.dumps(logs)}"
    )


_last_call_ts: Dict[int, float] = {}


def _heuristic_drift(logs: List[Dict]) -> Dict:
    if not logs:
        return {"drift_detected": False, "reason": "Not enough data."}
    consecutive_errors = 0
    for log in logs:
        if log.get("correct") is False:
            consecutive_errors += 1
        else:
            consecutive_errors = 0
    easy_slow = any(
        (log.get("difficulty") == "easy" and (log.get("time_taken_seconds") or 0) > 60)
        for log in logs
    )
    drift = consecutive_errors >= 2 or easy_slow
    reason = "Heuristic fallback."
    if consecutive_errors >= 2:
        reason = "Heuristic: consecutive errors."
    elif easy_slow:
        reason = "Heuristic: slow on easy question."
    return {"drift_detected": drift, "reason": reason}


def ai_drift_detector(user_id: int, logs: List[Dict]) -> Dict:
    if not logs:
        return {"drift_detected": False, "reason": "Not enough data."}

    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        return _heuristic_drift(logs)

    now = time.time()
    last_ts = _last_call_ts.get(user_id, 0)
    if now - last_ts < DRIFT_AI_COOLDOWN_SECONDS:
        return _heuristic_drift(logs)
    _last_call_ts[user_id] = now

    prompt = _build_prompt(logs)
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ]
    }
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    response = requests.post(url, params={"key": gemini_api_key}, json=payload, timeout=30)
    if response.status_code == 429:
        raise RateLimitError("Gemini rate limit exceeded")
    response.raise_for_status()
    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        return {"drift_detected": False, "reason": "No response from model."}
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        return {"drift_detected": False, "reason": "No response from model."}

    text = parts[0].get("text", "{}").strip()
    try:
        result = json.loads(text)
        if isinstance(result, dict) and "drift_detected" in result:
            return result
    except json.JSONDecodeError:
        pass
    return _heuristic_drift(logs)
