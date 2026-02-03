import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..db import get_db
from ..models import Question, TheoryNote, User
from ..schemas import QuestionCreate, QuestionOut, TheoryNoteOut, UserAdminUpdate

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

router = APIRouter(prefix="/admin")


@router.post("/questions", response_model=QuestionOut)
def create_question(
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    question = Question(
        topic=payload.topic,
        difficulty=payload.difficulty,
        text=payload.text,
        correct=payload.correct,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


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
    file_url = f"/uploads/{os.path.basename(note.file_path)}" if note.file_path else None
    return TheoryNoteOut(
        id=note.id,
        title=note.title,
        topic=note.topic,
        content=note.content,
        file_path=note.file_path,
        file_url=file_url,
    )


@router.get("/theory-notes", response_model=list[TheoryNoteOut])
def list_theory_notes(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    notes = db.query(TheoryNote).order_by(TheoryNote.created_at.desc()).all()
    return [
        TheoryNoteOut(
            id=note.id,
            title=note.title,
            topic=note.topic,
            content=note.content,
            file_path=note.file_path,
            file_url=f"/uploads/{os.path.basename(note.file_path)}" if note.file_path else None,
        )
        for note in notes
    ]


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
