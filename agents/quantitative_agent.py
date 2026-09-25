"""
Quantitative NL-to-SQL Agent.

Translates a natural language question into a SQL query against the sample
enterprise SQLite database, executes it, and returns tabular results.
"""
import os
import sqlite3
import logging
from tabulate import tabulate

import config

logger = logging.getLogger("quantitative_agent")

DB_PATH = config.SQL_DB_PATH

SCHEMA_DESCRIPTION = """
Table: monthly_revenue
  - month (TEXT, format 'YYYY-MM')
  - region (TEXT: 'North America', 'EMEA', 'APAC', 'LATAM')
  - revenue (REAL)

Table: customers
  - customer_id (INTEGER)
  - region (TEXT)
  - signup_month (TEXT, format 'YYYY-MM')
  - churn_month (TEXT, format 'YYYY-MM', NULL if still active)
  - plan (TEXT: 'Basic', 'Pro', 'Enterprise')
"""

# Basic safety net: only allow read-only queries.
FORBIDDEN_KEYWORDS = ["drop", "delete", "update", "insert", "alter", "attach", "pragma"]


class SQLSafetyError(Exception):
    pass


class QuantitativeAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(
                f"Database not found at {DB_PATH}. Run `python data/build_sql_db.py` first."
            )

    def _generate_sql(self, query: str) -> str:
        system_instruction = (
            "You translate natural language business questions into SQLite SQL queries. "
            "Return ONLY the raw SQL query, no markdown formatting, no explanation."
        )
        prompt = f"Schema:\n{SCHEMA_DESCRIPTION}\n\nQuestion: {query}\n\nSQL query:"
        sql = self.llm.generate(prompt, system_instruction=system_instruction)
        # strip markdown fences if the model added them anyway
        sql = sql.strip().strip("`").replace("sql\n", "", 1).strip()
        return sql

    def _validate_sql(self, sql: str):
        lowered = sql.lower()
        for kw in FORBIDDEN_KEYWORDS:
            if kw in lowered:
                raise SQLSafetyError(f"Query contains forbidden keyword: {kw}")
        if not lowered.strip().startswith("select"):
            raise SQLSafetyError("Only SELECT queries are permitted.")

    def _execute(self, sql: str) -> tuple[list[str], list[tuple]]:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            return columns, rows
        finally:
            conn.close()

    def answer(self, query: str) -> dict:
        sql = self._generate_sql(query)
        logger.info(f"Generated SQL: {sql}")

        try:
            self._validate_sql(sql)
            columns, rows = self._execute(sql)
        except (SQLSafetyError, sqlite3.Error) as e:
            return {
                "answer": f"I generated a query but it failed validation/execution: {e}",
                "generated_sql": sql,
                "agent": "quantitative",
                "error": str(e),
            }

        table_str = tabulate(rows, headers=columns, tablefmt="simple") if rows else "(no rows returned)"

        return {
            "answer": f"Query results:\n{table_str}",
            "generated_sql": sql,
            "columns": columns,
            "rows": rows,
            "agent": "quantitative",
        }

