from __future__ import annotations

from fastapi import FastAPI

from app.providers.base import get_default_provider
from app.service import (
    CompletionRequest,
    CompletionResponse,
    IngestRequest,
    SearchRequest,
    SearchResponse,
    ingest_document,
    search_documents,
)
from app.vectorstore.store import InMemoryVectorStore

app = FastAPI(
    title="LLM Gateway",
    description=(
        "LLM completion, embeddings, and vector-search endpoints — "
        "ServiceNow Staff AI Engineer showcase."
    ),
    version="0.1.0",
)

_store = InMemoryVectorStore()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "llm-gateway"}


@app.post("/complete", response_model=CompletionResponse)
def complete(request: CompletionRequest) -> CompletionResponse:
    provider = get_default_provider()
    return CompletionResponse(text=provider.complete(request.prompt, system=request.system))


@app.post("/vector/ingest")
def ingest(request: IngestRequest) -> dict:
    ingest_document(_store, request)
    return {"ingested": request.doc_id, "store_size": _store.count()}


@app.post("/vector/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    return search_documents(_store, request)
