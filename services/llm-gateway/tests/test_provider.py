from __future__ import annotations

import math

from app.providers.base import MockProvider


def test_embed_is_deterministic() -> None:
    provider = MockProvider()
    v1 = provider.embed("hello world")
    v2 = provider.embed("hello world")
    assert v1 == v2


def test_embed_is_unit_normalized() -> None:
    provider = MockProvider()
    v = provider.embed("some text")
    norm = math.sqrt(sum(x * x for x in v))
    assert abs(norm - 1.0) < 1e-4


def test_embed_differs_for_different_text() -> None:
    provider = MockProvider()
    assert provider.embed("a") != provider.embed("b")


def test_complete_mentions_risk_language_for_risk_prompts() -> None:
    provider = MockProvider()
    text = provider.complete("Assess the risk of this change")
    assert "risk" in text.lower()
