"""Graph routing tests: cat -> judge -> (respond | sage -> cat) | cry.

All three agents are faked here -- these tests exercise only the LangGraph
wiring (routing, round counting, the 5-round cutoff, log recording), never
a real LLM.
"""

from __future__ import annotations

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

from cat_sage.agents.base import AgentResult
from cat_sage.conversation_log import ConversationLog
from cat_sage.graph import build_graph
from cat_sage.state import initial_state


class FakeCat:
    name = "cat"

    def __init__(self, answers: list[str]):
        self._answers = iter(answers)

    def act(self, **kwargs):
        return AgentResult(text=next(self._answers))


class FakeJudge:
    name = "judge"

    def __init__(self, verdicts: list[tuple[str, str]]):
        self._verdicts = iter(verdicts)

    def act(self, **kwargs):
        verdict, reason = next(self._verdicts)
        return AgentResult(text=reason, raw={"verdict": verdict, "reason": reason})


class FakeSage:
    name = "sage"

    def act(self, **kwargs):
        return AgentResult(text="Be more precise and address the actual question.")


def make_tracer():
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    return provider.get_tracer("test")


def test_pass_on_first_round_ends_immediately():
    cat = FakeCat(["Meow, the sky is basically a giant cat toy."])
    judge = FakeJudge([("pass", "Good enough")])
    log = ConversationLog()

    graph = build_graph(cat=cat, sage=FakeSage(), judge=judge, tracer=make_tracer(), log=log)
    result = graph.invoke(initial_state("Why is the sky blue?"))

    assert result["outcome"] == "pass"
    assert result["final_answer"] == "Meow, the sky is basically a giant cat toy."
    assert len(result["history"]) == 1
    assert result["history"][0]["judge_verdict"] == "pass"


def test_fail_then_pass_goes_through_sage_and_round_two():
    cat = FakeCat(["wrong answer", "better answer"])
    judge = FakeJudge([("fail", "off topic"), ("pass", "good")])
    log = ConversationLog()

    graph = build_graph(cat=cat, sage=FakeSage(), judge=judge, tracer=make_tracer(), log=log)
    result = graph.invoke(initial_state("What is 2+2?"))

    assert result["outcome"] == "pass"
    assert len(result["history"]) == 2
    assert result["history"][0]["sage_feedback"] is not None
    text = "\n".join(log.lines)
    assert "round1 cat: wrong answer" in text
    assert "round1 judge: [fail] off topic" in text
    assert "round1 sage:" in text
    assert "round2 cat: better answer" in text
    assert "round2 judge: [pass] good" in text


def test_five_failed_rounds_end_in_crying_cat():
    cat = FakeCat([f"answer {i}" for i in range(1, 6)])
    judge = FakeJudge([("fail", f"nope {i}") for i in range(1, 6)])
    log = ConversationLog()

    graph = build_graph(cat=cat, sage=FakeSage(), judge=judge, tracer=make_tracer(), log=log)
    result = graph.invoke(initial_state("What is the meaning of life?"))

    assert result["outcome"] == "cry"
    assert len(result["history"]) == 5
    assert "burst" in result["final_answer"].lower() or "tears" in result["final_answer"].lower()
    # Sage should have been consulted after rounds 1-4, but not after round 5.
    assert result["round"] == 5
