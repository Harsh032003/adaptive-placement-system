from typing import Optional
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
    correct: str


class QuestionOut(BaseModel):
    id: int
    topic: str
    difficulty: str
    text: str
    correct: str

    class Config:
        from_attributes = True


class TheoryNoteOut(BaseModel):
    id: int
    title: str
    topic: Optional[str]
    content: Optional[str]
    file_path: Optional[str]
    file_url: Optional[str]

    class Config:
        from_attributes = True


class UserAdminUpdate(BaseModel):
    is_admin: bool
