import logging

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..helpers import detect_drift, pick_question, seed_if_empty
from ..drift_ai import ai_drift_detector
from ..rag import explain_with_rag
from ..models import Question, TestLog, User
from ..schemas import AnswerSubmission, FeedbackResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/get-question")
def get_next_question(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seed_if_empty(db)
    question = pick_question(db, user)
    if not question:
        raise HTTPException(status_code=404, detail="No questions available")
    return {
        "id": question.id,
        "topic": question.topic,
        "difficulty": question.difficulty,
        "text": question.text,
    }


@router.post("/submit", response_model=FeedbackResponse)
async def submit_answer(
    submission: AnswerSubmission,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == submission.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = submission.user_answer.strip().lower() == question.correct.strip().lower()

    if is_correct:
        user.current_skill = min(1.0, user.current_skill + 0.1)
    else:
        user.current_skill = max(0.0, user.current_skill - 0.1)

    # AI drift detection using recent logs
    recent_logs = (
        db.query(TestLog)
        .filter(TestLog.user_id == user.id)
        .order_by(TestLog.created_at.desc())
        .limit(5)
        .all()
    )
    log_payload = [
        {
            "time_taken_seconds": log.time_taken_seconds,
            "difficulty": log.question.difficulty if log.question else None,
            "correct": log.is_correct,
        }
        for log in recent_logs
    ]

    try:
        drift_result = await run_in_threadpool(ai_drift_detector, user.id, log_payload)
        user.drift_detected = bool(drift_result.get("drift_detected", False))
    except Exception as exc:
        logger.exception("AI drift detection failed: %s", exc)
        user.drift_detected = detect_drift(db, user.id)
    explanation = "Correct!"
    if not is_correct:
        if user.drift_detected:
            try:
                explanation = f"Drift Detected! {explain_with_rag(db, question.topic, submission.user_answer)}"
            except Exception as exc:
                logger.exception("RAG explanation failed: %s", exc)
                explanation = "Drift Detected! I could not generate a tailored explanation right now."
        else:
            explanation = f"Incorrect. The right answer is {question.correct}."

    log = TestLog(
        user_id=user.id,
        question_id=question.id,
        user_answer=submission.user_answer,
        is_correct=is_correct,
        time_taken_seconds=submission.time_taken_seconds,
        explanation=explanation,
    )
    db.add(log)
    db.commit()

    next_question = pick_question(db, user)
    next_payload = None
    if next_question:
        next_payload = {
            "id": next_question.id,
            "topic": next_question.topic,
            "difficulty": next_question.difficulty,
            "text": next_question.text,
        }

    return {
        "correct": is_correct,
        "explanation": explanation,
        "next_question": next_payload,
        "skill_update": user.current_skill,
        "drift_alert": user.drift_detected,
    }


@router.get("/stats/topic-mastery")
def topic_mastery(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            Question.topic.label("topic"),
            func.count(TestLog.id).label("total"),
            func.sum(case((TestLog.is_correct.is_(True), 1), else_=0)).label("correct"),
        )
        .join(Question, TestLog.question_id == Question.id)
        .filter(TestLog.user_id == user.id)
        .group_by(Question.topic)
        .all()
    )
    result = []
    for row in rows:
        total = row.total or 0
        correct = row.correct or 0
        percent = round((correct / total) * 100) if total else 0
        result.append({"topic": row.topic, "percent": percent, "total": total})
    return {"topics": result}


@router.get("/history")
def session_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(TestLog)
        .filter(TestLog.user_id == user.id)
        .order_by(TestLog.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "items": [
            {
                "id": log.id,
                "topic": log.question.topic if log.question else None,
                "difficulty": log.question.difficulty if log.question else None,
                "question": log.question.text if log.question else None,
                "user_answer": log.user_answer,
                "correct": log.is_correct,
                "explanation": log.explanation,
                "time_taken_seconds": log.time_taken_seconds,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    }
