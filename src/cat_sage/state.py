"""Shared state schema passed between LangGraph nodes."""

from __future__ import annotations

from typing import Literal, TypedDict

Verdict = Literal["pass", "fail"]
Outcome = Literal["pass", "cry"]


class RoundRecord(TypedDict):
    """Everything that happened in a single Cat -> Judge (-> Sage) round."""

    round: int
    cat_answer: str
    judge_verdict: Verdict
    judge_reason: str
    sage_feedback: str | None


class CatSageState(TypedDict):
    """LangGraph state threaded through cat / judge / sage / respond / cry nodes."""

    user_question: str
    round: int
    cat_answer: str
    judge_verdict: Verdict
    judge_reason: str
    sage_feedback: str
    history: list[RoundRecord]
    final_answer: str | None
    outcome: Outcome | None


def initial_state(question: str) -> CatSageState:
    """Build the starting state for a new session."""
    return CatSageState(
        user_question=question,
        round=1,
        cat_answer="",
        judge_verdict="fail",
        judge_reason="",
        sage_feedback="",
        history=[],
        final_answer=None,
        outcome=None,
    )
