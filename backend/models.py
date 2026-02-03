from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .db import Base, utcnow
from .rag_config import EMBEDDING_DIM


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    current_skill = Column(Float, default=0.5)
    drift_detected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    logs = relationship("TestLog", back_populates="user", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(100), nullable=False)
    difficulty = Column(String(20), nullable=False)
    text = Column(Text, nullable=False)
    correct = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    logs = relationship("TestLog", back_populates="question", cascade="all, delete-orphan")


class TestLog(Base):
    __tablename__ = "test_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    time_taken_seconds = Column(Integer, default=0)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="logs")
    question = relationship("Question", back_populates="logs")


class TheoryNote(Base):
    __tablename__ = "theory_notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    topic = Column(String(100), nullable=True)
    content = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    embeddings = relationship("DocumentEmbedding", back_populates="note", cascade="all, delete-orphan")


class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("theory_notes.id"), nullable=True)
    chunk_index = Column(Integer, default=0)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    note = relationship("TheoryNote", back_populates="embeddings")
