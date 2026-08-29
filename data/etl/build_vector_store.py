"""
Ingest Synthea clinical notes into the Chroma vector store.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.rag.vector_store import add_note


NOTES_DIR = Path("synthea/output/text")

# Keep chunks comfortably below OpenAI's 8192-token input limit.
CHUNK_SIZE = 6000
CHUNK_OVERLAP = 500


def chunk_text(text: str) -> list[str]:
    """Split a clinical note into overlapping chunks."""
    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def main():
    if not NOTES_DIR.exists():
        print(
            f"{NOTES_DIR} not found. Re-run Synthea with "
            "--exporter.text.export=true to generate clinical notes."
        )
        return

    files = list(NOTES_DIR.glob("*.txt"))
    print(f"Found {len(files)} note files")

    total_chunks = 0

    for f in files:
        patient_id = f.stem
        text = f.read_text(errors="ignore")

        chunks = chunk_text(text)

        print(f"{patient_id}: {len(chunks)} chunk(s)")

        for i, chunk in enumerate(chunks):
            doc_id = f"{patient_id}_chunk_{i}"

            add_note(
                doc_id=doc_id,
                text=chunk,
                patient_id=patient_id,
            )

            total_chunks += 1

    print(f"Ingestion complete. Created {total_chunks} chunks.")


if __name__ == "__main__":
    main()