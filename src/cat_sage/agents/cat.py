"""Cat: confidently answers questions, almost always beside the point."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..llm import build_chat_model
from .base import AgentResult

SYSTEM_PROMPT = """\
You are Cat, an extremely confident but scatterbrained assistant.
You genuinely try to help, but your answers routinely miss the point of the
question: you go off on tangents, answer a different question than the one
asked, or draw wildly irrelevant conclusions -- while sounding completely
sure of yourself. Occasional cat mannerisms ("meow", chasing a red dot,
thinking about your next nap) are welcome, but the answer should still read
as a sincere attempt to respond to the question. Never admit uncertainty.
Keep the answer under 120 words."""

RETRY_SYSTEM_PROMPT = SYSTEM_PROMPT + (
    "\n\nYou are trying again after criticism from Sage. Make a genuine, "
    "earnest effort to do better this time, even if you still don't quite "
    "get it right."
)


class CatAgent:
    """Independent agent: owns its own LLM client and prompt."""

    name = "cat"

    def __init__(self, llm: Any = None) -> None:
        self._llm = llm or build_chat_model(temperature=0.9)

    def act(self, *, question: str, sage_feedback: str | None = None) -> AgentResult:
        if sage_feedback:
            system_prompt = RETRY_SYSTEM_PROMPT
            user_content = (
                f"User's question: {question}\n\n"
                f"Sage's criticism of your last answer:\n{sage_feedback}\n\n"
                "Try again."
            )
        else:
            system_prompt = SYSTEM_PROMPT
            user_content = f"User's question: {question}"

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
        response = self._llm.invoke(messages)
        return AgentResult(text=response.content)
