"""Each agent is tested independently, with a fake LLM standing in for
LM Studio -- no network/local-server dependency in unit tests."""

from __future__ import annotations

from types import SimpleNamespace

from cat_sage.agents.cat import CatAgent
from cat_sage.agents.judge import JudgeAgent
from cat_sage.agents.sage import SageAgent


class FakeChatModel:
    def __init__(self, content: str):
        self.content = content
        self.last_messages = None

    def invoke(self, messages):
        self.last_messages = messages
        return SimpleNamespace(content=self.content)


class FakeStructuredModel:
    def __init__(self, verdict: str, reason: str):
        self.verdict = verdict
        self.reason = reason
        self.last_messages = None

    def invoke(self, messages):
        self.last_messages = messages
        return SimpleNamespace(verdict=self.verdict, reason=self.reason)


class FakeJudgeLLM:
    def __init__(self, structured: FakeStructuredModel):
        self._structured = structured

    def with_structured_output(self, schema):
        return self._structured


def test_cat_agent_returns_llm_text():
    agent = CatAgent(llm=FakeChatModel("meow, the answer is a nap"))
    result = agent.act(question="What is 2+2?")
    assert result.text == "meow, the answer is a nap"


def test_cat_agent_includes_sage_feedback_when_retrying():
    llm = FakeChatModel("second try")
    agent = CatAgent(llm=llm)
    agent.act(question="What is 2+2?", sage_feedback="Be more precise")
    joined = " ".join(m.content for m in llm.last_messages)
    assert "Be more precise" in joined


def test_cat_agent_omits_feedback_on_first_attempt():
    llm = FakeChatModel("first try")
    agent = CatAgent(llm=llm)
    agent.act(question="What is 2+2?")
    joined = " ".join(m.content for m in llm.last_messages)
    assert "criticism" not in joined.lower()


def test_sage_agent_returns_critique_referencing_inputs():
    llm = FakeChatModel("This answer is wrong because it ignores the question.")
    agent = SageAgent(llm=llm)
    result = agent.act(question="Q", cat_answer="A", judge_reason="off topic")
    assert "wrong" in result.text
    joined = " ".join(m.content for m in llm.last_messages)
    assert "off topic" in joined


def test_judge_agent_returns_structured_verdict():
    structured = FakeStructuredModel("pass", "Answer is correct and on point")
    agent = JudgeAgent(llm=FakeJudgeLLM(structured))
    result = agent.act(question="Q", cat_answer="A")
    assert result.raw["verdict"] == "pass"
    assert result.raw["reason"] == "Answer is correct and on point"
    assert result.text == "Answer is correct and on point"


def test_judge_agent_fail_verdict():
    structured = FakeStructuredModel("fail", "Answer does not address the question")
    agent = JudgeAgent(llm=FakeJudgeLLM(structured))
    result = agent.act(question="Q", cat_answer="A")
    assert result.raw["verdict"] == "fail"
