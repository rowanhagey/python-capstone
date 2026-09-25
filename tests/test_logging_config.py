import json
import logging
import os

from logging_config import JSONFormatter, Timer


def test_json_formatter_produces_valid_json():
    record = logging.LogRecord(
        name="test_logger", level=logging.INFO, pathname="", lineno=0,
        msg="hello world", args=(), exc_info=None,
    )
    formatter = JSONFormatter()
    output = formatter.format(record)
    parsed = json.loads(output)  # raises if not valid JSON
    assert parsed["message"] == "hello world"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"


def test_json_formatter_includes_extra_fields():
    record = logging.LogRecord(
        name="test_logger", level=logging.INFO, pathname="", lineno=0,
        msg="query handled", args=(), exc_info=None,
    )
    record.event = "query_classified"
    record.query = "What is our churn rate?"
    record.execution_time_sec = 0.123
    formatter = JSONFormatter()
    parsed = json.loads(formatter.format(record))
    assert parsed["event"] == "query_classified"
    assert parsed["query"] == "What is our churn rate?"
    assert parsed["execution_time_sec"] == 0.123


def test_json_formatter_includes_exception_info():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        record = logging.LogRecord(
            name="test_logger", level=logging.ERROR, pathname="", lineno=0,
            msg="something failed", args=(), exc_info=sys.exc_info(),
        )
    formatter = JSONFormatter()
    parsed = json.loads(formatter.format(record))
    assert "exception" in parsed
    assert "ValueError" in parsed["exception"]


def test_timer_measures_elapsed_time():
    import time
    with Timer() as t:
        time.sleep(0.05)
    assert t.elapsed >= 0.04  # allow small scheduling slack
    assert isinstance(t.elapsed, float)

