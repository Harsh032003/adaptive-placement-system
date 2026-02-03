import os
from typing import List

from dotenv import load_dotenv
from pypdf import PdfReader
from sqlalchemy.orm import Session

load_dotenv()

from backend.db import SessionLocal
from backend.embeddings import get_embedding
from backend.models import DocumentEmbedding, TheoryNote


def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    content = []
    for page in reader.pages:
        content.append(page.extract_text() or "")
    return "\n".join(content)


def chunk_text(text: str, max_chars: int = 800) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    for para in paragraphs:
        if len(para) <= max_chars:
            chunks.append(para)
            continue
        start = 0
        while start < len(para):
            chunks.append(para[start:start + max_chars])
            start += max_chars
    return chunks


def process_note(db: Session, note: TheoryNote) -> int:
    text = ""
    if note.content:
        text += note.content + "\n"
    if note.file_path and os.path.exists(note.file_path):
        if note.file_path.lower().endswith(".pdf"):
            text += extract_text_from_pdf(note.file_path)
        else:
            with open(note.file_path, "r", encoding="utf-8", errors="ignore") as handle:
                text += handle.read()

    text = text.strip()
    if not text:
        return 0

    db.query(DocumentEmbedding).filter(DocumentEmbedding.note_id == note.id).delete()
    db.commit()

    chunks = chunk_text(text)
    for idx, chunk in enumerate(chunks):
        embedding = get_embedding(chunk, task_type="RETRIEVAL_DOCUMENT")
        row = DocumentEmbedding(
            note_id=note.id,
            chunk_index=idx,
            content=chunk,
            embedding=embedding,
        )
        db.add(row)
    db.commit()
    return len(chunks)


def main() -> None:
    db = SessionLocal()
    try:
        notes = db.query(TheoryNote).all()
        total = 0
        for note in notes:
            total += process_note(db, note)
        print(f"Ingested {total} chunks from {len(notes)} notes")
    finally:
        db.close()


if __name__ == "__main__":
    main()
