"""
Retrieval agent — handles open-ended clinical questions that aren't a
direct graph lookup or risk score request, by retrieving relevant note
chunks and asking an LLM to answer grounded in them.

"""

from openai import OpenAI

from app.core.config import settings
from app.rag.vector_store import query_notes

_client = OpenAI(api_key=settings.openai_api_key)


def answer_from_notes(question: str, patient_id: str) -> dict:
    results = query_notes(question, patient_id=patient_id, top_k=4)

    if not results:
        return {
            "answer": "No clinical notes found for this patient to answer from.",
            "evidence_sources": [],
            "confidence": 0.0,
        }

    context = "\n\n---\n\n".join(r["text"] for r in results)

    prompt = (
        "You are a clinical decision support assistant. Answer the "
        "question using ONLY the context below. If the context doesn't "
        "contain the answer, say so explicitly rather than guessing.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )

    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    answer = response.choices[0].message.content

    avg_distance = sum(r["distance"] for r in results) / len(results)
    confidence = max(0.0, min(1.0, 1 - avg_distance))  # rough proxy, not a calibrated score

    return {
        "answer": answer,
        "evidence_sources": [f"Clinical note chunk: {r['id']}" for r in results],
        "confidence": round(confidence, 2),
    }
