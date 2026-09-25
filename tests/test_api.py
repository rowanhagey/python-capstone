import pytest
from fastapi.testclient import TestClient
from api import app


@pytest.fixture(scope="module")
def client():
    # TestClient must be used as a context manager to trigger FastAPI's
    # startup event (which initializes the agents) — without "with", the
    # agents stay None and every request 500s.
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["llm_client"] == "MockLLMClient"
    assert data["sql_db_available"] is True


def test_qualitative_endpoint(client):
    response = client.post("/agents/qualitative/query", json={"query": "Explain the code review process"})
    assert response.status_code == 200
    data = response.json()
    assert data["agent"] == "qualitative"
    assert len(data["sources"]) > 0


def test_quantitative_endpoint(client):
    response = client.post("/agents/quantitative/query", json={"query": "Show me revenue by region"})
    assert response.status_code == 200
    data = response.json()
    assert data["agent"] == "quantitative"
    assert data["generated_sql"] is not None


def test_manager_endpoint(client):
    response = client.post("/agents/manager/query", json={"query": "How do we handle customer complaints?"})
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "qualitative"
    assert data["handled_by"] == ["qualitative"]


def test_manager_endpoint_complex_query(client):
    response = client.post(
        "/agents/manager/query",
        json={"query": "Analyze our sales performance and recommend policy changes based on our customer success strategies"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["handled_by"] == ["qualitative", "quantitative"]


def test_query_endpoint_rejects_empty_query(client):
    response = client.post("/agents/manager/query", json={"query": ""})
    assert response.status_code == 422


def test_openapi_docs_available(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/agents/manager/query" in paths
    assert "/agents/qualitative/query" in paths
    assert "/agents/quantitative/query" in paths

