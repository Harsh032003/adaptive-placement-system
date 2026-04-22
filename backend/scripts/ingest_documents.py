from dotenv import load_dotenv

load_dotenv()

from backend.db import SessionLocal
from backend.note_ingestion import ingest_all_notes


def main() -> None:
    db = SessionLocal()
    try:
        notes_count, total_chunks = ingest_all_notes(db)
        print(f"Ingested {total_chunks} chunks from {notes_count} notes")
    finally:
        db.close()


if __name__ == "__main__":
    main()
