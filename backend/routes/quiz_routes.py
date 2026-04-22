import logging

from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.concurrency import run_in_threadpool
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..helpers import detect_drift, detect_drift_from_logs, pick_question, seed_if_empty, serialize_question
from ..drift_ai import ai_drift_detector
from ..rag import explain_with_rag
from ..models import Question, TestLog, User
from ..schemas import AnswerSubmission, FeedbackResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/get-question")
def get_next_question(
    topic: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seed_if_empty(db)
    active_drift = detect_drift(db, user.id, topic)
    question = pick_question(db, user, topic=topic, drift_detected=active_drift)
    if not question:
        raise HTTPException(status_code=404, detail="No questions available for this topic")
    return serialize_question(question)


@router.get("/topics")
def list_topics(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seed_if_empty(db)
    rows = (
        db.query(Question.topic)
        .distinct()
        .order_by(Question.topic.asc())
        .all()
    )
    return {"topics": [row[0] for row in rows if row[0]]}


@router.post("/submit", response_model=FeedbackResponse)
async def submit_answer(
    submission: AnswerSubmission,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == submission.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    selected_topic = submission.selected_topic.strip() if submission.selected_topic else None
    if selected_topic and question.topic != selected_topic:
        raise HTTPException(status_code=400, detail="Question does not match selected topic")

    submitted_option = submission.user_answer.strip().upper()
    if submitted_option not in {"A", "B", "C", "D"}:
        raise HTTPException(status_code=400, detail="Answer must be one of A, B, C, or D")
    is_correct = submitted_option == question.correct_option.strip().upper()

    selected_answer_text = question.option_text(submitted_option)

    if is_correct:
        user.current_skill = min(1.0, user.current_skill + 0.1)
    else:
        user.current_skill = max(0.0, user.current_skill - 0.1)

    # AI drift detection using recent logs
    recent_logs = (
        db.query(TestLog)
        .join(Question, TestLog.question_id == Question.id)
        .filter(TestLog.user_id == user.id)
        .order_by(TestLog.created_at.desc())
    )
    if selected_topic:
        recent_logs = recent_logs.filter(Question.topic == selected_topic)
    recent_logs = recent_logs.limit(4).all()
    log_payload = [
        {
            "time_taken_seconds": log.time_taken_seconds,
            "difficulty": log.question.difficulty if log.question else None,
            "correct": log.is_correct,
        }
        for log in reversed(recent_logs)
    ]
    log_payload.append(
        {
            "time_taken_seconds": submission.time_taken_seconds,
            "difficulty": question.difficulty,
            "correct": is_correct,
        }
    )

    try:
        drift_result = await run_in_threadpool(ai_drift_detector, user.id, log_payload)
        user.drift_detected = bool(drift_result.get("drift_detected", False))
    except Exception as exc:
        logger.exception("AI drift detection failed: %s", exc)
        user.drift_detected = detect_drift_from_logs(log_payload)
    explanation = "Correct!"
    if not is_correct:
        if user.drift_detected:
            try:
                explanation = f"Drift Detected! {explain_with_rag(db, question.topic, selected_answer_text)}"
            except Exception as exc:
                logger.exception("RAG explanation failed: %s", exc)
                explanation = "Drift Detected! I could not generate a tailored explanation right now."
        else:
            explanation = f"Incorrect. The right answer is {question.option_text(question.correct_option)}."

    log = TestLog(
        user_id=user.id,
        question_id=question.id,
        user_answer=submitted_option,
        is_correct=is_correct,
        time_taken_seconds=submission.time_taken_seconds,
        explanation=explanation,
    )
    db.add(log)
    db.commit()

    next_question = pick_question(
        db,
        user,
        topic=selected_topic,
        drift_detected=user.drift_detected,
    )
    next_payload = None
    if next_question:
        next_payload = serialize_question(next_question)

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


@router.get("/analytics/user")
def user_analytics(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(TestLog)
        .join(Question, TestLog.question_id == Question.id)
        .filter(TestLog.user_id == user.id)
        .order_by(TestLog.created_at.asc())
        .all()
    )

    topic_stats = defaultdict(
        lambda: {
            "total": 0,
            "correct": 0,
            "time_total": 0,
            "drift_events": 0,
        }
    )
    mastery_trend = []
    previous_correct_by_topic = {}
    running_correct = 0

    for index, log in enumerate(logs, start=1):
        question = log.question
        if not question:
            continue

        topic = question.topic
        time_taken = log.time_taken_seconds or 0
        is_correct = bool(log.is_correct)
        topic_stats[topic]["total"] += 1
        topic_stats[topic]["time_total"] += time_taken
        if is_correct:
            topic_stats[topic]["correct"] += 1
            running_correct += 1

        drift_event = (
            (not is_correct and previous_correct_by_topic.get(topic) is False)
            or (question.difficulty.lower() == "easy" and time_taken > 60)
        )
        if drift_event:
            topic_stats[topic]["drift_events"] += 1
        previous_correct_by_topic[topic] = is_correct

        mastery_trend.append(
            {
                "attempt": index,
                "created_at": log.created_at.isoformat(),
                "topic": topic,
                "mastery_percent": round((running_correct / index) * 100),
            }
        )

    topic_summaries = []
    for topic, stats in topic_stats.items():
        total = stats["total"]
        correct = stats["correct"]
        avg_time = round(stats["time_total"] / total, 1) if total else 0
        mastery_percent = round((correct / total) * 100) if total else 0
        drift_rate = round((stats["drift_events"] / total) * 100) if total else 0
        topic_summaries.append(
            {
                "topic": topic,
                "total": total,
                "correct": correct,
                "mastery_percent": mastery_percent,
                "avg_time_seconds": avg_time,
                "drift_events": stats["drift_events"],
                "drift_rate_percent": drift_rate,
            }
        )

    weak_topics = sorted(
        topic_summaries,
        key=lambda item: (
            item["mastery_percent"],
            -item["drift_events"],
            -item["avg_time_seconds"],
        ),
    )[:3]
    for topic in weak_topics:
        if topic["mastery_percent"] < 50:
            topic["recommendation"] = "Revise fundamentals and practice easy questions first."
        elif topic["drift_events"] > 0:
            topic["recommendation"] = "Review mistakes and retry medium questions slowly."
        elif topic["avg_time_seconds"] > 60:
            topic["recommendation"] = "Focus on speed with timed practice."
        else:
            topic["recommendation"] = "Keep practicing to build consistency."

    total_attempts = len(logs)
    total_correct = sum(1 for log in logs if log.is_correct)
    total_time = sum((log.time_taken_seconds or 0) for log in logs)
    total_drift_events = sum(item["drift_events"] for item in topic_summaries)

    return {
        "summary": {
            "total_attempts": total_attempts,
            "accuracy_percent": round((total_correct / total_attempts) * 100) if total_attempts else 0,
            "avg_time_seconds": round(total_time / total_attempts, 1) if total_attempts else 0,
            "drift_events": total_drift_events,
        },
        "mastery_trend": mastery_trend[-15:],
        "weak_topics": weak_topics,
        "response_time_by_topic": sorted(topic_summaries, key=lambda item: item["avg_time_seconds"], reverse=True),
        "drift_frequency_by_topic": sorted(topic_summaries, key=lambda item: item["drift_rate_percent"], reverse=True),
    }


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
                "user_answer_text": log.question.option_text(log.user_answer) if log.question else log.user_answer,
                "correct": log.is_correct,
                "explanation": log.explanation,
                "correct_option": log.question.correct_option if log.question else None,
                "correct_answer_text": log.question.option_text(log.question.correct_option) if log.question else None,
                "time_taken_seconds": log.time_taken_seconds,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    }
