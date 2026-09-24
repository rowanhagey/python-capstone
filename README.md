# Multi-Agent RAG System for Enterprise Documentation

A Python CLI system where a Manager Agent classifies user queries and routes
them to a Qualitative RAG Agent (policy/process documents) or a Quantitative
NL-to-SQL Agent (business metrics), merging results for complex queries that
need both.

## Architecture

~~~
                        ┌─────────────────────┐
                        │      CLI (cli.py)    │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │    Manager Agent      │
                        │  - classifies query   │
                        │  - routes to agent(s)  │
                        │  - merges responses    │
                        └──────┬────────┬────────┘
                               │        │
              qualitative /    │        │  quantitative /
              complex          │        │  complex
                    ┌──────────▼──┐  ┌──▼───────────────┐
                    │ Qualitative │  │  Quantitative      │
                    │ RAG Agent   │  │  NL-to-SQL Agent    │
                    │             │  │                     │
                    │ Chroma +    │  │  Gemini generates    │
                    │ Sentence-   │  │  SQL → SQLite        │
                    │ Transformers│  │  executes → results   │
                    │ embeddings  │  │                     │
                    └─────────────┘  └─────────────────────┘
                          │                    │
                 data/docs/*.md         data/enterprise.db
~~~

**Manager Agent** (`agents/manager_agent.py`): Uses the LLM to classify each
query as `qualitative`, `quantitative`, `complex`, or `ambiguous`, then routes
accordingly. For `complex` queries it calls both agents and merges the
answers into one clearly-labeled response. For `ambiguous` queries it asks
the user a clarifying question instead of guessing.

**Qualitative RAG Agent** (`agents/qualitative_agent.py`): Chunks and embeds
the sample enterprise docs (security policy, code review process, customer
complaint handling) using Sentence Transformers (local, no API key), stores
them in a persistent Chroma collection, retrieves the top-k relevant chunks
above a similarity threshold, and asks the LLM to answer using only that
context — with source citations and similarity scores returned alongside
the answer.

**Quantitative NL-to-SQL Agent** (`agents/quantitative_agent.py`): Sends the
schema + question to the LLM to generate a SQL query, validates it (SELECT-only,
blocks DROP/DELETE/UPDATE/INSERT/etc.), executes it against a sample SQLite
database (`monthly_revenue`, `customers` tables with ~2 years of synthetic
data across 4 regions), and returns a formatted table.

**LLM Client** (`llm_client.py`): Swappable abstraction over Gemini. Real
`GeminiClient` retries with exponential backoff and falls back across a model
chain (`gemini-3.6-flash` → `gemini-2.0-flash` → `gemini-1.5-flash`) if a
model is unavailable or quota-exhausted. If `GEMINI_API_KEY` isn't set,
`get_llm_client()` automatically returns a `MockLLMClient` so the rest of the
system can be built/tested/demoed without a live key.

## Setup

~~~bash
pip install -r requirements.txt
python data/build_sql_db.py          # builds data/enterprise.db
export GEMINI_API_KEY="your-key-here"  # optional — omit to run in mock mode
~~~

## Usage

Interactive mode:
~~~bash
python cli.py
~~~

Single query:
~~~bash
python cli.py --query "What is our company's security policy?"
python cli.py --query "What's our customer churn rate?"
python cli.py --query "Analyze our sales performance and recommend policy changes based on our customer success strategies"
~~~

## Sample Queries

| Type | Example |
|---|---|
| Qualitative | "Explain the code review process" |
| Qualitative | "How do we handle customer complaints?" |
| Quantitative | "Show me monthly revenue trends" |
| Quantitative | "Compare Q4 performance across regions" |
| Complex | "How does our employee satisfaction compare to industry standards and what policies might impact this?" |

## Testing

~~~bash
pytest tests/ -v
~~~

Tests run entirely against `MockLLMClient` — no API key or network calls
required (except Sentence Transformers' one-time model download, which is
cached after the first run).

## Known Limitations / Stretch Goals Not Yet Implemented

- No FastAPI/LangServe layer yet (Gold stretch goal)
- No structured JSON logging to file (currently stdout via `logging`)
- Manager agent's classification is single-shot; no multi-turn clarification loop

