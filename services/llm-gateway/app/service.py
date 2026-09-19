from __future__ import annotations

from pydantic import BaseModel

from app.providers.base import get_default_provider
from app.vectorstore.store import InMemoryVectorStore, VectorRecord


class CompletionRequest(BaseModel):
    prompt: str
    system: str = ""


class CompletionResponse(BaseModel):
    text: str


class IngestRequest(BaseModel):
    doc_id: str
    text: str
    metadata: dict = {}


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


class SearchResultItem(BaseModel):
    doc_id: str
    text: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    results: list[SearchResultItem]


def ingest_document(store: InMemoryVectorStore, request: IngestRequest) -> None:
    provider = get_default_provider()
    embedding = provider.embed(request.text)
    store.upsert(
        VectorRecord(
            doc_id=request.doc_id,
            text=request.text,
            embedding=embedding,
            metadata=request.metadata,
        )
    )


def search_documents(store: InMemoryVectorStore, request: SearchRequest) -> SearchResponse:
    provider = get_default_provider()
    query_embedding = provider.embed(request.query)
    results = store.search(query_embedding, top_k=request.top_k)
    return SearchResponse(
        results=[
            SearchResultItem(doc_id=r.doc_id, text=r.text, score=r.score, metadata=r.metadata)
            for r in results
        ]
    )
