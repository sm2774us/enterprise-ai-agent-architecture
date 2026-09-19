"""LLM provider abstraction.

A `Provider` is any backend that can (a) complete a prompt and (b) embed
text. `MockProvider` is deterministic and offline -- what CI and unit tests
run against. `AnthropicProvider` shows the same interface wired to a real
enterprise-grade LLM API, which is the swap-in point for whichever model
ServiceNow's "Cloud & Platform LLM-based capabilities" ultimately route to
(the interface, not the vendor, is the point being demonstrated).
"""

from __future__ import annotations

import hashlib
import os
from typing import Protocol

import numpy as np


class Provider(Protocol):
    def complete(self, prompt: str, *, system: str = "") -> str: ...

    def embed(self, text: str) -> list[float]: ...


class MockProvider:
    """Deterministic, hash-based provider: no network calls, fully reproducible."""

    EMBEDDING_DIM = 32

    def complete(self, prompt: str, *, system: str = "") -> str:
        if "risk" in prompt.lower():
            return "Risk assessment: moderate. Recommend staged rollout with rollback plan."
        return f"[mock-completion] {prompt[:120]}"

    def embed(self, text: str) -> list[float]:
        # Deterministic pseudo-embedding: hash the text into a fixed-size,
        # unit-normalized vector. Not semantically meaningful, but stable and
        # dependency-free -- exactly what a hermetic CI unit test needs, while
        # keeping the exact same call shape a real embedding model would use.
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        raw_bytes = np.frombuffer((digest * 4)[: self.EMBEDDING_DIM * 4], dtype=np.uint8)
        raw = np.asarray(raw_bytes, dtype=np.float32)
        norm = np.linalg.norm(raw)
        vector = raw / norm if norm > 0 else raw
        return vector.tolist()


class AnthropicProvider:
    """Real-provider adapter. Requires ANTHROPIC_API_KEY; not used in CI/tests."""

    def __init__(self, model: str = "claude-sonnet-4-6") -> None:
        self._api_key = os.environ.get("ANTHROPIC_API_KEY")
        self._model = model

    def complete(self, prompt: str, *, system: str = "") -> str:
        if not self._api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set; cannot call the real provider.")
        import httpx

        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self._model,
                "max_tokens": 1024,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return "".join(block.get("text", "") for block in data.get("content", []))

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError(
            "Plug in a real embeddings endpoint (e.g. Voyage AI, OpenAI) here; "
            "kept out of scope to avoid a second paid dependency in this showcase."
        )


def get_default_provider() -> Provider:
    return MockProvider()
