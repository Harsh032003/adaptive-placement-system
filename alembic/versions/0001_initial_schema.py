"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-22 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=True),
        sa.Column("current_skill", sa.Float(), nullable=True),
        sa.Column("drift_detected", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("topic", sa.String(length=100), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("correct_option", sa.String(length=10), nullable=False),
        sa.Column("correct", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index(op.f("ix_questions_id"), "questions", ["id"], unique=False)

    op.create_table(
        "theory_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("topic", sa.String(length=100), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index(op.f("ix_theory_notes_id"), "theory_notes", ["id"], unique=False)

    op.create_table(
        "test_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("user_answer", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("time_taken_seconds", sa.Integer(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_test_logs_id"), "test_logs", ["id"], unique=False)

    op.create_table(
        "document_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("note_id", sa.Integer(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["note_id"], ["theory_notes.id"]),
    )
    op.create_index(op.f("ix_document_embeddings_id"), "document_embeddings", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_embeddings_id"), table_name="document_embeddings")
    op.drop_table("document_embeddings")
    op.drop_index(op.f("ix_test_logs_id"), table_name="test_logs")
    op.drop_table("test_logs")
    op.drop_index(op.f("ix_theory_notes_id"), table_name="theory_notes")
    op.drop_table("theory_notes")
    op.drop_index(op.f("ix_questions_id"), table_name="questions")
    op.drop_table("questions")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
