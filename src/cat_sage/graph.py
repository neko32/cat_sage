"""LangGraph orchestration of the three independent agents.

This module holds no agent logic of its own -- it only wires Cat, Sage, and
Judge together as nodes and decides, via a conditional edge, whether to
respond, hand off to Sage for another round, or end in tears after five
failed rounds.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from .agents.base import Agent
from .conversation_log import ConversationLog
from .state import CatSageState, RoundRecord

MAX_ROUNDS = 5

CRY_MESSAGE = (
    "*Cat bursts into tears* \U0001f63f I tried my very best, five times over, "
    "and I still couldn't get it right. I'm sorry... I need a nap and a treat."
)


def _truncate(text: str, limit: int = 160) -> str:
    flat = " ".join(text.strip().splitlines())
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


def build_graph(
    *,
    cat: Agent,
    sage: Agent,
    judge: Agent,
    tracer: Any,
    log: ConversationLog,
):
    """Compile the Cat/Judge/Sage LangGraph state machine.

    ``tracer`` is any object exposing ``start_as_current_span`` (an
    OpenTelemetry ``Tracer`` in production, a fake in tests).
    """

    def cat_node(state: CatSageState) -> dict:
        result = cat.act(question=state["user_question"], sage_feedback=state.get("sage_feedback") or None)
        log.record(state["round"], "cat", result.text)
        return {"cat_answer": result.text}

    def judge_node(state: CatSageState) -> dict:
        result = judge.act(question=state["user_question"], cat_answer=state["cat_answer"])
        verdict = result.raw["verdict"]
        reason = result.raw["reason"]
        log.record(state["round"], "judge", reason, verdict=verdict)

        record: RoundRecord = {
            "round": state["round"],
            "cat_answer": state["cat_answer"],
            "judge_verdict": verdict,
            "judge_reason": reason,
            "sage_feedback": None,
        }

        with tracer.start_as_current_span("cat_sage.round") as span:
            span.set_attribute("round.number", state["round"])
            span.set_attribute("judge.verdict", verdict)
            span.set_attribute(
                "round.note",
                f'cat="{_truncate(state["cat_answer"])}" judge="{_truncate(reason)}"',
            )

        return {
            "judge_verdict": verdict,
            "judge_reason": reason,
            "history": state["history"] + [record],
        }

    def sage_node(state: CatSageState) -> dict:
        result = sage.act(
            question=state["user_question"],
            cat_answer=state["cat_answer"],
            judge_reason=state["judge_reason"],
        )
        log.record(state["round"], "sage", result.text)

        history = list(state["history"])
        if history:
            history[-1] = {**history[-1], "sage_feedback": result.text}

        return {"sage_feedback": result.text, "round": state["round"] + 1, "history": history}

    def respond_node(state: CatSageState) -> dict:
        return {"final_answer": state["cat_answer"], "outcome": "pass"}

    def cry_node(state: CatSageState) -> dict:
        log.record(state["round"], "cat", CRY_MESSAGE)
        return {"final_answer": CRY_MESSAGE, "outcome": "cry"}

    def route_after_judge(state: CatSageState) -> str:
        if state["judge_verdict"] == "pass":
            return "respond"
        if state["round"] >= MAX_ROUNDS:
            return "cry"
        return "sage"

    graph = StateGraph(CatSageState)
    graph.add_node("cat", cat_node)
    graph.add_node("judge", judge_node)
    graph.add_node("sage", sage_node)
    graph.add_node("respond", respond_node)
    graph.add_node("cry", cry_node)

    graph.set_entry_point("cat")
    graph.add_edge("cat", "judge")
    graph.add_conditional_edges(
        "judge",
        route_after_judge,
        {"respond": "respond", "sage": "sage", "cry": "cry"},
    )
    graph.add_edge("sage", "cat")
    graph.add_edge("respond", END)
    graph.add_edge("cry", END)

    return graph.compile()
