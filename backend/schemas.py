from typing import List, Optional
from pydantic import BaseModel


class SignupRequest(BaseModel):
    username: str
    password: str
    admin_code: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class AnswerSubmission(BaseModel):
    question_id: int
    user_answer: str
    time_taken_seconds: int
    selected_topic: Optional[str] = None


class FeedbackResponse(BaseModel):
    correct: bool
    explanation: str
    next_question: Optional[dict]
    skill_update: float
    drift_alert: bool


class QuestionCreate(BaseModel):
    topic: str
    difficulty: str
    text: str
    options: List[str]
    correct_option: str


class QuestionOut(BaseModel):
    id: int
    topic: str
    difficulty: str
    text: str
    options: List[str]
    correct_option: str

    class Config:
        from_attributes = True


class TheoryNoteOut(BaseModel):
    id: int
    title: str
    topic: Optional[str]
    content: Optional[str]
    file_path: Optional[str]
    file_url: Optional[str]
    embedding_chunks: int = 0
    ingestion_status: str
    ingestion_error: Optional[str] = None

    class Config:
        from_attributes = True


class UserAdminUpdate(BaseModel):
    is_admin: bool
