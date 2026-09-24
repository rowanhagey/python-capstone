import pytest
from agents.quantitative_agent import QuantitativeAgent, SQLSafetyError
from llm_client import MockLLMClient


@pytest.fixture(scope="module")
def agent():
    return QuantitativeAgent(MockLLMClient())


def test_generate_sql_returns_select_statement(agent):
    sql = agent._generate_sql("Show me revenue by region")
    assert sql.lower().strip().startswith("select")


def test_validate_sql_rejects_forbidden_keywords(agent):
    with pytest.raises(SQLSafetyError):
        agent._validate_sql("DROP TABLE customers;")
    with pytest.raises(SQLSafetyError):
        agent._validate_sql("DELETE FROM monthly_revenue;")


def test_validate_sql_rejects_non_select(agent):
    with pytest.raises(SQLSafetyError):
        agent._validate_sql("UPDATE customers SET plan = 'Basic';")


def test_validate_sql_accepts_select(agent):
    # should not raise
    agent._validate_sql("SELECT * FROM monthly_revenue;")


def test_execute_returns_columns_and_rows(agent):
    columns, rows = agent._execute("SELECT region, SUM(revenue) as total FROM monthly_revenue GROUP BY region")
    assert "region" in columns
    assert "total" in columns
    assert len(rows) == 4  # 4 regions


def test_answer_end_to_end(agent):
    result = agent.answer("What is total revenue by region?")
    assert result["agent"] == "quantitative"
    assert "generated_sql" in result
    assert "Query results" in result["answer"] or "error" in result

