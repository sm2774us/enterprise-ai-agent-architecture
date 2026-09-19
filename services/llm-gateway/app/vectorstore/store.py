"""In-memory vector store: cosine-similarity nearest-neighbour search.

Deliberately dependency-light (numpy only, no Pinecone/pgvector/FAISS
binary) so the showcase runs anywhere; the `VectorStore` protocol is the
seam a real deployment would swap for a managed vector DB without touching
call sites in `app.main`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class VectorRecord:
    doc_id: str
    text: str
    embedding: list[float]
    metadata: dict = field(default_factory=dict)


@dataclass
class ScoredRecord:
    doc_id: str
    text: str
    score: float
    metadata: dict


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._records: list[VectorRecord] = []

    def upsert(self, record: VectorRecord) -> None:
        self._records = [r for r in self._records if r.doc_id != record.doc_id]
        self._records.append(record)

    def count(self) -> int:
        return len(self._records)

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[ScoredRecord]:
        if not self._records:
            return []
        query = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query)

        scored: list[ScoredRecord] = []
        for record in self._records:
            vec = np.array(record.embedding, dtype=np.float32)
            denom = query_norm * np.linalg.norm(vec)
            similarity = float(np.dot(query, vec) / denom) if denom > 0 else 0.0
            scored.append(
                ScoredRecord(
                    doc_id=record.doc_id,
                    text=record.text,
                    score=similarity,
                    metadata=record.metadata,
                )
            )
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]
