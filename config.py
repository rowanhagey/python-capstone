"""
Environment-based configuration for API keys, database paths, and model names.
Centralizes what used to be scattered os.environ.get() calls and hardcoded
paths across llm_client.py and the agents.
"""
import os

# LLM
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DEFAULT_MODEL = os.environ.get("GEMINI_DEFAULT_MODEL", "gemini-3.6-flash")

# Embeddings
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_DB_PATH = os.environ.get("SQL_DB_PATH", os.path.join(BASE_DIR, "data", "enterprise.db"))
DOCS_DIR = os.environ.get("DOCS_DIR", os.path.join(BASE_DIR, "data", "docs"))
VECTORDB_DIR = os.environ.get("VECTORDB_DIR", os.path.join(BASE_DIR, "vectordb", "chroma"))

# Retrieval
RELEVANCE_THRESHOLD = float(os.environ.get("RELEVANCE_THRESHOLD", "0.35"))

# API
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8000"))

