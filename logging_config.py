"""
Structured JSON logging setup.

Every log record is emitted as one JSON object per line (JSONL), suitable
for ingestion by log aggregators. Captures the fields the rubric asks for:
incoming query, selected agent, retrieved sources, generated SQL,
execution time, and errors — via the `extra={...}` kwarg on normal
logging calls, e.g.:

    logger.info("query handled", extra={"event": "query_handled", "query": q, "agent": "qualitative"})
"""
import json
import logging
import os
import time

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.jsonl")

# Standard LogRecord attributes we don't want duplicated in the "extra" payload.
_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()) | {"message", "asctime"}


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Pull in any extra fields passed via logger.info(msg, extra={...})
        for key, value in record.__dict__.items():
            if key not in _RESERVED:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging(level=logging.INFO):
    os.makedirs(LOG_DIR, exist_ok=True)

    json_handler = logging.FileHandler(LOG_FILE)
    json_handler.setFormatter(JSONFormatter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers if setup_logging() is called more than once
    # (e.g. once by cli.py, once by a test import).
    root.handlers.clear()
    root.addHandler(json_handler)
    root.addHandler(console_handler)


class Timer:
    """Small context manager for measuring execution time in seconds."""
    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = round(time.perf_counter() - self._start, 4)

