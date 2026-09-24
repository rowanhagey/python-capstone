import os
import pytest
from llm_client import get_llm_client, MockLLMClient, GeminiClient


def test_get_llm_client_returns_mock_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    client = get_llm_client()
    assert isinstance(client, MockLLMClient)


def test_mock_client_classify_pattern():
    client = MockLLMClient()
    result = client.generate(
        "What is our security policy?",
        system_instruction="You classify a user's business question...",
    )
    assert result in ("qualitative", "quantitative", "complex")


def test_mock_client_sql_pattern():
    client = MockLLMClient()
    result = client.generate("Show me revenue", system_instruction="You translate to SQL query")
    assert result.lower().startswith("select")


def test_mock_client_generic_fallback():
    client = MockLLMClient()
    result = client.generate("Some random prompt with no special pattern")
    assert "MOCK RESPONSE" in result


def test_gemini_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        GeminiClient(api_key=None)

