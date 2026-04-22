import os
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..db import get_db
from ..models import DocumentEmbedding, Question, TheoryNote, User
from ..note_ingestion import ingest_all_notes, process_note
from ..schemas import QuestionCreate, QuestionOut, TheoryNoteOut, UserAdminUpdate

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

router = APIRouter(prefix="/admin")
logger = logging.getLogger(__name__)


def validate_question_payload(payload: QuestionCreate) -> tuple[list[str], str]:
    option_labels = {"A", "B", "C", "D"}
    options = [option.strip() for option in payload.options]
    if len(options) != 4 or any(not option for option in options):
        raise HTTPException(status_code=400, detail="Exactly 4 non-empty options are required")
    correct_option = payload.correct_option.strip().upper()
    if correct_option not in option_labels:
        raise HTTPException(status_code=400, detail="Correct option must be one of A, B, C, or D")
    return options, correct_option


def serialize_note(
    note: TheoryNote,
    embedding_chunks: Optional[int] = None,
    ingestion_error: Optional[str] = None,
) -> TheoryNoteOut:
    file_url = f"/uploads/{os.path.basename(note.file_path)}" if note.file_path else None
    chunk_count = embedding_chunks if embedding_chunks is not None else len(note.embeddings or [])
    if chunk_count > 0:
        ingestion_status = "ready"
    elif note.content or note.file_path:
        ingestion_status = "pending"
    else:
        ingestion_status = "empty"

    return TheoryNoteOut(
        id=note.id,
        title=note.title,
        topic=note.topic,
        content=note.content,
        file_path=note.file_path,
        file_url=file_url,
        embedding_chunks=chunk_count,
        ingestion_status=ingestion_status,
        ingestion_error=ingestion_error,
    )


@router.post("/questions", response_model=QuestionOut)
def create_question(
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    options, correct_option = validate_question_payload(payload)

    question = Question(
        topic=payload.topic,
        difficulty=payload.difficulty,
        text=payload.text,
        options=options,
        correct_option=correct_option,
        correct=options[ord(correct_option) - ord("A")],
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.put("/questions/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    options, correct_option = validate_question_payload(payload)
    question.topic = payload.topic
    question.difficulty = payload.difficulty
    question.text = payload.text
    question.options = options
    question.correct_option = correct_option
    question.correct = options[ord(correct_option) - ord("A")]
    db.commit()
    db.refresh(question)
    return question


@router.delete("/questions/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(question)
    db.commit()
    return {"message": "Question deleted"}


@router.get("/questions", response_model=list[QuestionOut])
def list_questions(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return db.query(Question).order_by(Question.created_at.desc()).all()


@router.post("/theory-notes", response_model=TheoryNoteOut)
def upload_theory_note(
    title: str = Form(...),
    topic: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = None
    if file:
        safe_name = f"{int(datetime.utcnow().timestamp())}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(file_path, "wb") as handle:
            handle.write(file.file.read())

    note = TheoryNote(
        title=title,
        topic=topic,
        content=content,
        file_path=file_path,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    ingestion_error = None
    try:
        process_note(db, note)
        db.refresh(note)
    except Exception as exc:
        logger.exception("Auto-ingestion failed for note %s: %s", note.id, exc)
        ingestion_error = "Upload succeeded, but ingestion needs to be retried."
        db.rollback()
        db.refresh(note)

    return serialize_note(note, ingestion_error=ingestion_error)


@router.put("/theory-notes/{note_id}", response_model=TheoryNoteOut)
def update_theory_note(
    note_id: int,
    title: str = Form(...),
    topic: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    note = db.query(TheoryNote).filter(TheoryNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Theory note not found")

    note.title = title
    note.topic = topic
    note.content = content

    if file:
        old_file_path = note.file_path
        safe_name = f"{int(datetime.utcnow().timestamp())}_{file.filename}"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(file_path, "wb") as handle:
            handle.write(file.file.read())
        note.file_path = file_path
        if old_file_path and os.path.exists(old_file_path):
            os.remove(old_file_path)

    db.commit()
    db.refresh(note)

    ingestion_error = None
    try:
        process_note(db, note)
        db.refresh(note)
    except Exception as exc:
        logger.exception("Re-ingestion failed for note %s: %s", note.id, exc)
        ingestion_error = "Note updated, but ingestion needs to be retried."
        db.rollback()
        db.refresh(note)

    return serialize_note(note, ingestion_error=ingestion_error)


@router.post("/theory-notes/ingest-all")
def ingest_theory_notes(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        note_count, total_chunks = ingest_all_notes(db)
    except Exception as exc:
        logger.exception("Bulk note ingestion failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to ingest notes")
    return {
        "notes_processed": note_count,
        "chunks_created": total_chunks,
        "message": f"Ingested {total_chunks} chunks from {note_count} notes.",
    }


@router.post("/theory-notes/{note_id}/ingest", response_model=TheoryNoteOut)
def ingest_theory_note(
    note_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    note = db.query(TheoryNote).filter(TheoryNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Theory note not found")
    try:
        process_note(db, note)
        db.refresh(note)
    except Exception as exc:
        logger.exception("Manual note ingestion failed for note %s: %s", note_id, exc)
        raise HTTPException(status_code=500, detail="Failed to ingest note")
    return serialize_note(note)


@router.delete("/theory-notes/{note_id}")
def delete_theory_note(
    note_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    note = db.query(TheoryNote).filter(TheoryNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Theory note not found")
    file_path = note.file_path
    db.delete(note)
    db.commit()
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    return {"message": "Theory note deleted"}


@router.get("/theory-notes", response_model=list[TheoryNoteOut])
def list_theory_notes(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    notes = db.query(TheoryNote).order_by(TheoryNote.created_at.desc()).all()
    note_ids = [note.id for note in notes]
    counts = {}
    if note_ids:
        embeddings = (
            db.query(DocumentEmbedding)
            .filter(DocumentEmbedding.note_id.in_(note_ids))
            .all()
        )
        for embedding in embeddings:
            counts[embedding.note_id] = counts.get(embedding.note_id, 0) + 1
    return [serialize_note(note, embedding_chunks=counts.get(note.id, 0)) for note in notes]


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {"id": user.id, "username": user.username, "is_admin": user.is_admin}
        for user in users
    ]


@router.patch("/users/{user_id}")
def update_user_admin(
    user_id: int,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id and not payload.is_admin:
        raise HTTPException(status_code=400, detail="Cannot remove your own admin access")
    user.is_admin = payload.is_admin
    db.commit()
    return {"id": user.id, "username": user.username, "is_admin": user.is_admin}
