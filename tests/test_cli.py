"""
CLI interface tests.

Tests print_result() formatting and run_single_query()/run_interactive()
behavior directly against a mocked ManagerAgent, rather than spawning
subprocesses — faster and avoids depending on stdin/stdout plumbing.
"""
from unittest.mock import MagicMock
import pytest

import cli


def test_print_result_shows_classification_and_answer(capsys):
    result = {
        "classification": "qualitative",
        "handled_by": ["qualitative"],
        "answer": "This is the answer.",
        "sources": [],
    }
    cli.print_result(result)
    captured = capsys.readouterr()
    assert "classified as: qualitative" in captured.out
    assert "handled by: qualitative" in captured.out
    assert "This is the answer." in captured.out


def test_print_result_shows_sources_when_present(capsys):
    result = {
        "classification": "qualitative",
        "handled_by": ["qualitative"],
        "answer": "answer text",
        "sources": [{"document": "security_policy", "chunk": 0, "similarity": 0.72}],
    }
    cli.print_result(result)
    captured = capsys.readouterr()
    assert "Sources:" in captured.out
    assert "security_policy" in captured.out
    assert "0.72" in captured.out


def test_print_result_shows_generated_sql_when_present(capsys):
    result = {
        "classification": "quantitative",
        "handled_by": ["quantitative"],
        "answer": "Query results:\n...",
        "generated_sql": "SELECT * FROM monthly_revenue;",
    }
    cli.print_result(result)
    captured = capsys.readouterr()
    assert "Generated SQL: SELECT * FROM monthly_revenue;" in captured.out


def test_print_result_shows_clarification_needed_when_no_agent_handled_it(capsys):
    result = {
        "classification": "ambiguous",
        "handled_by": [],
        "answer": "Could you clarify?",
    }
    cli.print_result(result)
    captured = capsys.readouterr()
    assert "clarification needed" in captured.out


def test_run_single_query_calls_manager_and_prints_result(capsys):
    mock_manager = MagicMock()
    mock_manager.handle_query.return_value = {
        "classification": "qualitative",
        "handled_by": ["qualitative"],
        "answer": "mocked answer",
        "sources": [],
    }
    cli.run_single_query(mock_manager, "Explain the code review process")
    mock_manager.handle_query.assert_called_once_with("Explain the code review process")
    captured = capsys.readouterr()
    assert "mocked answer" in captured.out


def test_run_single_query_handles_exceptions_gracefully(capsys):
    mock_manager = MagicMock()
    mock_manager.handle_query.side_effect = RuntimeError("something broke")
    # should not raise
    cli.run_single_query(mock_manager, "some query")
    captured = capsys.readouterr()
    assert "something went wrong" in captured.out.lower()


def test_run_interactive_exits_on_exit_command(monkeypatch, capsys):
    mock_manager = MagicMock()
    inputs = iter(["exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    cli.run_interactive(mock_manager)  # should return cleanly, not loop forever
    mock_manager.handle_query.assert_not_called()


def test_run_interactive_skips_blank_input_then_exits(monkeypatch):
    mock_manager = MagicMock()
    mock_manager.handle_query.return_value = {
        "classification": "qualitative", "handled_by": ["qualitative"], "answer": "ok", "sources": [],
    }
    inputs = iter(["", "  ", "What is our security policy?", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    cli.run_interactive(mock_manager)
    mock_manager.handle_query.assert_called_once_with("What is our security policy?")


def test_run_interactive_handles_keyboard_interrupt(monkeypatch):
    mock_manager = MagicMock()
    def raise_interrupt(_):
        raise KeyboardInterrupt()
    monkeypatch.setattr("builtins.input", raise_interrupt)
    cli.run_interactive(mock_manager)  # should not propagate the exception

