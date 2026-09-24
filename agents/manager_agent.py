"""
Manager Agent.

Classifies incoming queries as qualitative, quantitative, or complex
(needs both), routes to the appropriate agent(s), and merges/labels the
combined response. Falls back to a clarification question for genuinely
ambiguous queries.
"""
import logging

from agents.qualitative_agent import QualitativeAgent
from agents.quantitative_agent import QuantitativeAgent

logger = logging.getLogger("manager_agent")

CLASSIFY_SYSTEM_INSTRUCTION = """
You classify a user's business question into exactly one category:
- "qualitative": asks about policies, processes, procedures, explanations ("what is", "how do we", "explain")
- "quantitative": asks for numbers, metrics, trends, comparisons ("show me", "what's our churn rate", "compare")
- "complex": requires both a policy/process explanation AND numeric data to fully answer
- "ambiguous": genuinely unclear what's being asked, or missing key info needed to answer

Respond with ONLY one word: qualitative, quantitative, complex, or ambiguous.
"""


class ManagerAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.qualitative_agent = QualitativeAgent(llm_client)
        self.quantitative_agent = QuantitativeAgent(llm_client)

    def classify(self, query: str) -> str:
        result = self.llm.generate(query, system_instruction=CLASSIFY_SYSTEM_INSTRUCTION)
        result = result.strip().lower()
        if result not in ("qualitative", "quantitative", "complex", "ambiguous"):
            logger.warning(f"Unexpected classification '{result}', defaulting to 'ambiguous'")
            return "ambiguous"
        return result

    def handle_query(self, query: str) -> dict:
        classification = self.classify(query)
        logger.info(f"Query classified as: {classification}")

        if classification == "ambiguous":
            return {
                "classification": classification,
                "answer": (
                    "I'm not sure how to answer that as asked — could you clarify whether you're "
                    "looking for a policy/process explanation, specific numbers/metrics, or both?"
                ),
                "handled_by": [],
            }

        if classification == "qualitative":
            result = self.qualitative_agent.answer(query)
            return {
                "classification": classification,
                "answer": result["answer"],
                "sources": result.get("sources", []),
                "handled_by": ["qualitative"],
            }

        if classification == "quantitative":
            result = self.quantitative_agent.answer(query)
            return {
                "classification": classification,
                "answer": result["answer"],
                "generated_sql": result.get("generated_sql"),
                "handled_by": ["quantitative"],
            }

        # complex: query both agents and merge, clearly labeled
        qual_result = self.qualitative_agent.answer(query)
        quant_result = self.quantitative_agent.answer(query)

        merged_answer = (
            "This question needed both a policy/process lookup and numeric data. Here's the combined answer:\n\n"
            f"--- Qualitative (documentation) ---\n{qual_result['answer']}\n\n"
            f"--- Quantitative (data) ---\n{quant_result['answer']}"
        )

        return {
            "classification": classification,
            "answer": merged_answer,
            "sources": qual_result.get("sources", []),
            "generated_sql": quant_result.get("generated_sql"),
            "handled_by": ["qualitative", "quantitative"],
        }

