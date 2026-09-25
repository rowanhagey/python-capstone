"""
FastAPI layer exposing each agent and the manager over HTTP.

Run: uvicorn api:app --host 0.0.0.0 --port 8000
Docs: http://localhost:8000/docs (auto-generated OpenAPI/Swagger UI)
"""
import os
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

import config
from schemas import (
    QueryRequest,
    QualitativeResponse,
    QuantitativeResponse,
    ManagerResponse,
    HealthResponse,
)
from llm_client import get_llm_client
from agents.manager_agent import ManagerAgent
from agents.qualitative_agent import QualitativeAgent
from agents.quantitative_agent import QuantitativeAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("api")

# Shared singletons — built once at startup, reused across requests.
_llm_client = None
_manager_agent = None
_qualitative_agent = None
_quantitative_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _llm_client, _manager_agent, _qualitative_agent, _quantitative_agent
    logger.info("Initializing LLM client and agents...")
    _llm_client = get_llm_client()
    _qualitative_agent = QualitativeAgent(_llm_client)
    _quantitative_agent = QuantitativeAgent(_llm_client)
    _manager_agent = ManagerAgent(_llm_client)
    logger.info("Agents ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Multi-Agent RAG System API",
    description="Manager, Qualitative RAG, and Quantitative NL-to-SQL agents for enterprise documentation Q&A.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health():
    return HealthResponse(
        status="ok",
        llm_client=type(_llm_client).__name__ if _llm_client else "not initialized",
        sql_db_available=os.path.exists(config.SQL_DB_PATH),
    )


@app.post("/agents/manager/query", response_model=ManagerResponse, tags=["manager"])
def query_manager(request: QueryRequest):
    try:
        result = _manager_agent.handle_query(request.query)
        return ManagerResponse(**result)
    except Exception as e:
        logger.error(f"Manager agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/qualitative/query", response_model=QualitativeResponse, tags=["qualitative"])
def query_qualitative(request: QueryRequest):
    try:
        result = _qualitative_agent.answer(request.query)
        return QualitativeResponse(**result)
    except Exception as e:
        logger.error(f"Qualitative agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/quantitative/query", response_model=QuantitativeResponse, tags=["quantitative"])
def query_quantitative(request: QueryRequest):
    try:
        result = _quantitative_agent.answer(request.query)
        return QuantitativeResponse(**result)
    except Exception as e:
        logger.error(f"Quantitative agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

