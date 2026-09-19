from __future__ import annotations

from app.providers.base import MockProvider
from app.vectorstore.store import InMemoryVectorStore, VectorRecord


def test_search_returns_closest_matches_first() -> None:
    store = InMemoryVectorStore()
    provider = MockProvider()
    docs = {
        "doc-a": "Payment gateway latency incident triage runbook",
        "doc-b": "Quarterly finance close checklist",
        "doc-c": "Payment gateway latency incident triage runbook",
    }
    for doc_id, text in docs.items():
        store.upsert(VectorRecord(doc_id=doc_id, text=text, embedding=provider.embed(text)))

    results = store.search(provider.embed(docs["doc-a"]), top_k=2)
    assert results[0].score >= results[1].score
    # doc-a and doc-c are identical text -> identical mock embedding -> perfect match
    assert {results[0].doc_id, results[1].doc_id} == {"doc-a", "doc-c"}


def test_upsert_replaces_existing_doc_id() -> None:
    store = InMemoryVectorStore()
    store.upsert(VectorRecord(doc_id="d1", text="v1", embedding=[1.0, 0.0]))
    store.upsert(VectorRecord(doc_id="d1", text="v2", embedding=[0.0, 1.0]))
    assert store.count() == 1


def test_search_on_empty_store_returns_empty_list() -> None:
    store = InMemoryVectorStore()
    assert store.search([1.0, 0.0]) == []
