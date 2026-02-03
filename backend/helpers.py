from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import Question, TestLog, User


def detect_drift(db: Session, user_id: int) -> bool:
    recent = (
        db.query(TestLog)
        .filter(TestLog.user_id == user_id)
        .order_by(TestLog.created_at.desc())
        .limit(2)
        .all()
    )
    if len(recent) < 2:
        return False
    return all(not log.is_correct for log in recent)


def mock_rag_pipeline(topic: str) -> str:
    return f"[RAG Generated] Here is a simplified concept summary for {topic}..."


def pick_question(db: Session, user: User) -> Optional[Question]:
    target_difficulty = "medium"
    if user.drift_detected or user.current_skill < 0.4:
        target_difficulty = "easy"
    elif user.current_skill > 0.7:
        target_difficulty = "hard"

    candidate = (
        db.query(Question)
        .filter(Question.difficulty == target_difficulty)
        .order_by(func.random())
        .first()
    )
    if candidate:
        return candidate

    return db.query(Question).order_by(func.random()).first()


def seed_if_empty(db: Session) -> None:
    if db.query(Question).count() > 0:
        return

    seeds = [
        Question(
            topic="Arrays",
            difficulty="easy",
            text="What is the time complexity of accessing an element in an array?",
            correct="O(1)",
        ),
        Question(
            topic="Arrays",
            difficulty="medium",
            text="Find the missing number in an array of 1 to N.",
            correct="n*(n+1)/2 - sum",
        ),
        Question(
            topic="Arrays",
            difficulty="hard",
            text="Explain the logic for trapping rain water problem.",
            correct="Two pointer",
        ),
        Question(
            topic="DP",
            difficulty="easy",
            text="What is the base case for Fibonacci DP?",
            correct="n<=1",
        ),
    ]
    db.add_all(seeds)
    db.commit()
