"""Sage: reviews Cat's answer harshly and gives concrete feedback."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..llm import build_chat_model
from .base import AgentResult

SYSTEM_PROMPT = """\
You are Sage, a cold, rigorous, and unsparing critic. You are given a
user's question, Cat's answer to it, and Judge's reason for rejecting that
answer. Critique Cat's answer precisely: state exactly what is wrong,
missing, or irrelevant. Do not soften your tone and do not praise
unnecessarily. End with concrete, actionable guidance Cat can use to answer
better next time. Keep it under 120 words."""


class SageAgent:
    """Independent agent: owns its own LLM client and prompt."""

    name = "sage"

    def __init__(self, llm: Any = None) -> None:
        self._llm = llm or build_chat_model(temperature=0.3)

    def act(self, *, question: str, cat_answer: str, judge_reason: str) -> AgentResult:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"User's question: {question}\n\n"
                    f"Cat's answer: {cat_answer}\n\n"
                    f"Judge's reason for rejecting it: {judge_reason}\n\n"
                    "Critique Cat's answer and give feedback for improvement."
                )
            ),
        ]
        response = self._llm.invoke(messages)
        return AgentResult(text=response.content)
