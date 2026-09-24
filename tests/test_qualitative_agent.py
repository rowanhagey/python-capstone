import pytest
from agents.qualitative_agent import QualitativeAgent
from llm_client import MockLLMClient


@pytest.fixture(scope="module")
def agent():
    return QualitativeAgent(MockLLMClient())


def test_retrieve_returns_relevant_chunks(agent):
    results = agent.retrieve("What is our security policy on passwords?")
    assert len(results) > 0
    assert all("similarity" in r for r in results)
    # top result should come from the security policy doc
    assert results[0]["source"] == "security_policy"


def test_retrieve_code_review_query(agent):
    results = agent.retrieve("How long should a code review take?")
    assert any(r["source"] == "code_review_process" for r in results)


def test_answer_includes_sources(agent):
    result = agent.answer("Explain the code review process")
    assert result["agent"] == "qualitative"
    assert len(result["sources"]) > 0
    assert result["sources"][0]["document"] == "code_review_process"


def test_answer_with_no_relevant_docs_returns_graceful_message(agent, monkeypatch):
    # Force retrieval to return nothing above threshold
    monkeypatch.setattr(agent, "retrieve", lambda query, k=3: [])
    result = agent.answer("What is the airspeed velocity of an unladen swallow?")
    assert "couldn't find" in result["answer"].lower()
    assert result["sources"] == []

