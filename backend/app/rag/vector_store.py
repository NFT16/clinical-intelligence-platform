
from pathlib import Path

import chromadb
from openai import OpenAI

from app.core.config import settings


CHROMA_DIR = Path(__file__).resolve().parent / "chroma_store"

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_openai_client = OpenAI(api_key=settings.openai_api_key)


class OpenAIEmbedder:
    """
    Custom OpenAI embedding function for ChromaDB.
    """

    def __init__(
        self,
        client: OpenAI,
        model: str = "text-embedding-3-small",
    ):
        self._client = client
        self._model = model

    def __call__(self, input: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(
            model=self._model,
            input=input,
        )
        return [item.embedding for item in response.data]


_embedding_fn = OpenAIEmbedder(_openai_client)

_collection = _client.get_or_create_collection(
    name="clinical_notes",
    embedding_function=_embedding_fn,
)


def add_note(doc_id: str, text: str, patient_id: str):
    _collection.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[{"patient_id": patient_id}],
    )


def query_notes(
    query: str,
    patient_id: str | None = None,
    top_k: int = 4,
) -> list[dict]:

    where = {"patient_id": patient_id} if patient_id else None

    results = _collection.query(
        query_texts=[query],
        n_results=top_k,
        where=where,
    )

    docs = results.get("documents", [[]])[0]
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]

    return [
        {
            "id": doc_id,
            "text": text,
            "distance": dist,
        }
        for doc_id, text, dist in zip(ids, docs, distances)
    ]