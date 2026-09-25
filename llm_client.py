"""
LLM client abstraction.

Two implementations behind the same interface:
  - GeminiClient: calls the real Gemini API via google-genai, with retry/backoff
    and model fallback (mirrors the pattern from python-day-2-lab-2).
  - MockLLMClient: returns deterministic canned responses so the rest of the
    system (routing, retrieval, SQL execution) can be built and tested without
    a working API key.

Set GEMINI_API_KEY in the environment to use the real client. If it's unset,
get_llm_client() automatically falls back to the mock so you're never blocked.
"""
import logging
from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import config

logger = logging.getLogger("llm_client")

# Ordered fallback chain — if the first model is unavailable/quota-exhausted,
# try the next one. Update this list if Google renames/deprecates models again.
MODEL_FALLBACK_CHAIN = [config.DEFAULT_MODEL, "gemini-3.8-flash", "gemini-2.5-flash"]


class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_instruction: str = "") -> str:
        """Return a text completion for the given prompt."""
        raise NotImplementedError


class QuotaExceededError(Exception):
    pass


class GeminiClient(LLMClient):
    def __init__(self, api_key: str | None = None):
        from google import genai  # imported here so mock mode never requires the package at import time

        self.api_key = api_key or config.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        self.client = genai.Client(api_key=self.api_key)
        self._working_model = None

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _call_model(self, model: str, prompt: str, system_instruction: str) -> str:
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config={"system_instruction": system_instruction} if system_instruction else None,
        )
        return response.text

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        # Try the last known-working model first, then walk the fallback chain.
        chain = [self._working_model] + MODEL_FALLBACK_CHAIN if self._working_model else MODEL_FALLBACK_CHAIN
        last_error = None
        for model in dict.fromkeys(chain):  # dedupe, preserve order
            try:
                result = self._call_model(model, prompt, system_instruction)
                self._working_model = model
                return result
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                last_error = e
                continue
        raise QuotaExceededError(f"All models in fallback chain failed. Last error: {last_error}")


class MockLLMClient(LLMClient):
    """
    Deterministic mock so agents can be built/tested without a live API key.
    Recognizes a few patterns to return plausible fake responses; otherwise
    returns a generic canned answer.
    """

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        lower = prompt.lower()

        if "classify" in system_instruction.lower() or "classify" in lower[:200]:
            if any(w in lower for w in ["revenue", "churn", "compare", "performance", "trend", "how many", "average"]):
                if any(w in lower for w in ["polic", "process", "explain", "handle"]):
                    return "complex"
                return "quantitative"
            return "qualitative"

        if "generate sql" in lower or "sql query" in system_instruction.lower():
            return "SELECT region, SUM(revenue) as total_revenue FROM monthly_revenue GROUP BY region;"

        return (
            "[MOCK RESPONSE] This is a placeholder answer generated because no GEMINI_API_KEY "
            "is set. The retrieval/SQL pipeline ran correctly — swap in a real key to get real "
            "generated answers."
        )


def get_llm_client() -> LLMClient:
    api_key = config.GEMINI_API_KEY
    if api_key:
        try:
            return GeminiClient(api_key=api_key)
        except Exception as e:
            logger.warning(f"Falling back to MockLLMClient — GeminiClient init failed: {e}")
            return MockLLMClient()
    logger.info("GEMINI_API_KEY not set — using MockLLMClient. Set the env var to use real Gemini.")
    return MockLLMClient()

