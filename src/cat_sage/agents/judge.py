"""Judge: LLM-as-judge, strictly decides pass/fail on Cat's answer."""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..llm import build_chat_model
from .base import AgentResult

SYSTEM_PROMPT = """\
You are Judge, an impartial and strict LLM-as-judge. You are given a
user's question and Cat's answer to it. Apply this rubric strictly:

- Correctness: every factual claim in the answer must be accurate. Any
  fabricated, invented, or unverifiable "fact" is an automatic fail.
- Relevance: the answer must directly and completely address the
  question, with no tangents, jokes, or unrelated asides mixed in.
- Sufficiency: the correct information must be clearly and cleanly
  presented, not buried in or diluted by irrelevant material.

Do not give credit for effort, confidence, or a partially-correct answer.
If a correct core answer is wrapped in significant irrelevant content
(non-sequiturs, unrelated commentary, padding), that still counts as
insufficient -- answer "fail". Only answer "pass" when the answer is
accurate, complete, and essentially free of material irrelevant to the
question.

Give a short, objective reason for your verdict, independent of tone or
confidence -- judge substance only."""


class JudgeVerdict(BaseModel):
    """Structured output schema Judge is constrained to produce."""

    verdict: Literal["pass", "fail"] = Field(description="Strict pass/fail verdict.")
    reason: str = Field(description="Short, objective reason for the verdict.")


class JudgeAgent:
    """Independent agent: owns its own LLM client, prompt, and output schema."""

    name = "judge"

    def __init__(self, llm: Any = None) -> None:
        base_llm = llm or build_chat_model(temperature=0.0)
        self._llm = base_llm.with_structured_output(JudgeVerdict)

    def act(self, *, question: str, cat_answer: str) -> AgentResult:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"User's question: {question}\n\nCat's answer: {cat_answer}"),
        ]
        result = self._llm.invoke(messages)
        return AgentResult(text=result.reason, raw={"verdict": result.verdict, "reason": result.reason})
