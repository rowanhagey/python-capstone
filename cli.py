"""
CLI entry point for the Multi-Agent RAG System.

Usage:
    python cli.py
    python cli.py --query "What is our company's security policy?"
"""
import sys
import argparse
import logging

from agents.manager_agent import ManagerAgent
from llm_client import get_llm_client
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger("cli")


BANNER = """
==============================================
 Enterprise Documentation RAG System
 Type a question, or 'exit' / 'quit' to leave.
==============================================
"""


def print_result(result: dict):
    print(f"\n[classified as: {result['classification']}] [handled by: {', '.join(result['handled_by']) or 'clarification needed'}]")
    print("-" * 60)
    print(result["answer"])
    if result.get("sources"):
        print("\nSources:")
        for s in result["sources"]:
            print(f"  - {s['document']} (chunk {s['chunk']}, similarity {s['similarity']})")
    if result.get("generated_sql"):
        print(f"\nGenerated SQL: {result['generated_sql']}")
    print("-" * 60)


def run_single_query(manager: ManagerAgent, query: str):
    try:
        result = manager.handle_query(query)
        print_result(result)
    except Exception as e:
        logger.error(f"Error handling query: {e}")
        print(f"\nSomething went wrong processing that query: {e}")


def run_interactive(manager: ManagerAgent):
    print(BANNER)
    while True:
        try:
            query = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
        if not query:
            continue
        if query.lower() in ("exit", "quit"):
            print("Exiting.")
            break
        run_single_query(manager, query)


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent RAG System CLI")
    parser.add_argument("--query", "-q", type=str, help="Run a single query and exit")
    args = parser.parse_args()

    logger.info("Initializing agents (this may take a moment on first run — indexing docs)...")
    llm_client = get_llm_client()
    manager = ManagerAgent(llm_client)
    logger.info("Ready.")

    if args.query:
        run_single_query(manager, args.query)
    else:
        run_interactive(manager)


if __name__ == "__main__":
    sys.exit(main() or 0)

