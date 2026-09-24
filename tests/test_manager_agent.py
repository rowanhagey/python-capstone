import pytest
from agents.manager_agent import ManagerAgent
from llm_client import MockLLMClient


@pytest.fixture(scope="module")
def manager():
    return ManagerAgent(MockLLMClient())


def test_classify_qualitative_query(manager):
    result = manager.classify("Explain the code review process")
    assert result == "qualitative"


def test_classify_quantitative_query(manager):
    result = manager.classify("What's our customer churn rate?")
    assert result == "quantitative"


def test_classify_complex_query(manager):
    result = manager.classify(
        "How does our employee satisfaction compare to industry standards and what policies might impact this?"
    )
    assert result == "complex"


def test_handle_query_routes_qualitative(manager):
    result = manager.handle_query("How do we handle customer complaints?")
    assert result["handled_by"] == ["qualitative"]
    assert result["classification"] == "qualitative"


def test_handle_query_routes_quantitative(manager):
    result = manager.handle_query("Show me monthly revenue trends")
    assert result["handled_by"] == ["quantitative"]
    assert "generated_sql" in result


def test_handle_query_routes_complex_merges_both(manager):
    result = manager.handle_query(
        "Analyze our sales performance and recommend policy changes based on our customer success strategies"
    )
    assert result["handled_by"] == ["qualitative", "quantitative"]
    assert "Qualitative (documentation)" in result["answer"]
    assert "Quantitative (data)" in result["answer"]


def test_handle_query_ambiguous_asks_for_clarification(manager, monkeypatch):
    monkeypatch.setattr(manager, "classify", lambda q: "ambiguous")
    result = manager.handle_query("thing")
    assert result["handled_by"] == []
    assert "clarify" in result["answer"].lower()

