"""
Pydantic request/response schemas for the FastAPI layer.
"""
from typing import Optional, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language question")


class SourceCitation(BaseModel):
    document: str
    chunk: int
    similarity: float


class QualitativeResponse(BaseModel):
    agent: str = "qualitative"
    answer: str
    sources: list[SourceCitation] = []


class QuantitativeResponse(BaseModel):
    agent: str = "quantitative"
    answer: str
    generated_sql: Optional[str] = None
    columns: Optional[list[str]] = None
    rows: Optional[list[list[Any]]] = None
    error: Optional[str] = None


class ManagerResponse(BaseModel):
    classification: str
    answer: str
    handled_by: list[str] = []
    sources: list[SourceCitation] = []
    generated_sql: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    llm_client: str
    sql_db_available: bool

