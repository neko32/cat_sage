# Cat & Sage — Design

## Concept

Three independent agents collaborate to answer a user's question:

- **Cat** answers confidently, but the answer is usually tangential, off-topic,
  or just plain wrong.
- **Judge** (LLM-as-judge) strictly decides `pass` / `fail` on whether Cat's
  answer sufficiently and correctly addresses the question. A correct core
  answer wrapped in irrelevant padding (jokes, tangents, non-sequiturs)
  still fails -- Judge does not give partial credit. See the rubric in
  [`agents/judge.py`](../src/cat_sage/agents/judge.py).
- **Sage** is called in only when Judge fails Cat. Sage reviews Cat's answer
  coldly and rigorously, and gives concrete feedback so Cat can try again.

The loop repeats for up to **5 rounds**. If Judge never passes Cat within
5 rounds, the session ends with Cat crying.

## Why three *independent* agents, not one prompt-switched client

Each agent (`CatAgent`, `SageAgent`, `JudgeAgent`) owns:

- its own LLM client instance,
- its own system prompt,
- its own input/output shape.

They only share a minimal structural interface, `Agent` (see
[`agents/base.py`](../src/cat_sage/agents/base.py)):

```python
class Agent(Protocol):
    name: str
    def act(self, **kwargs) -> AgentResult: ...
```

This keeps the three agents genuinely decoupled: any agent can be swapped,
pointed at a different model, or replaced with a mock/stub in tests without
touching the others or the orchestration graph.

## Graph (LangGraph)

```
START ─▶ cat ─▶ judge ─┬─ pass ───────────────▶ respond ─▶ END
                        │
                        ├─ fail, round < 5 ───▶ sage ─▶ cat  (round += 1, loop)
                        │
                        └─ fail, round == 5 ──▶ cry ─────────▶ END
```

`graph.py` holds no agent logic — it only wires the three agents together
as LangGraph nodes and routes based on Judge's verdict and the round
counter. See [`graph.py`](../src/cat_sage/graph.py).

### State

```python
class CatSageState(TypedDict):
    user_question: str
    round: int
    cat_answer: str
    judge_verdict: Literal["pass", "fail"]
    judge_reason: str
    sage_feedback: str
    history: list[RoundRecord]
    final_answer: str | None
    outcome: Literal["pass", "cry"] | None
```

## LLM backend

All three agents talk to a locally-hosted [LM Studio](https://lmstudio.ai/)
model through its OpenAI-compatible REST API, via `langchain_openai.ChatOpenAI`.
No real API key is required. Connection details are environment-driven
(see [`.env.example`](../.env.example)):

| Variable             | Default                        |
|----------------------|---------------------------------|
| `LM_STUDIO_BASE_URL` | `http://localhost:1234/v1`      |
| `LM_STUDIO_MODEL`    | `google/gemma-4-e4b`            |
| `LM_STUDIO_API_KEY`  | `lm-studio` (ignored by LM Studio) |

## Telemetry (OpenTelemetry)

Each session opens one root span, `cat_sage.session`, and one child span per
round, `cat_sage.round`, carrying `round.number`, `judge.verdict`, and a
short `round.note`. A custom exporter, `SummaryFileExporter`
(see [`telemetry.py`](../src/cat_sage/telemetry.py)), accumulates every span
it sees and, once the session span ends, writes a human-readable summary
file:

```
Question: Why is the sky blue?
Round 1: judge=fail note="cat="...", judge="..."
Round 2: judge=pass note="cat="...", judge="..."
Total rounds: 2
Outcome: pass
```

## Output files

Every session writes two files under `C:\tmp\`:

- `cat_sage_{slug}_{timestamp}.txt` — the telemetry summary above.
- `cat_sage_{slug}_{timestamp}_conversation.txt` — the full round-by-round
  conversation log, in exactly this format:

  ```
  round1 cat: xxx
  round1 judge: [fail] yyy
  round1 sage: zzz
  round2 cat: aaa
  round2 judge: [pass] bbb
  ```

`{slug}` is a filesystem-safe one-line summary derived directly from the
first few words of the user's question (see `slugify` in
[`cli.py`](../src/cat_sage/cli.py)) — no extra LLM call is spent on it.

## Testing policy (POC scope)

This is a proof-of-concept intended for a LinkedIn write-up, so the usual
90% coverage / strict TDD bar for this team is intentionally relaxed for
this project. What *is* covered:

- **`test_agents.py`** — each agent tested independently against a fake LLM
  (no LM Studio dependency).
- **`test_graph.py`** — the LangGraph routing logic (pass / fail+retry /
  5-round cutoff) tested against fake Cat/Sage/Judge agents.
- **`test_telemetry.py`** — `SummaryFileExporter` produces the expected
  summary file from a real OpenTelemetry span tree.

Static analysis: `ruff check` + `ruff format --check`, both clean.

## Running it

```bash
pip install -e ".[dev]"
python -m cat_sage.cli "Why is the sky blue?"
```

or with no argument, it prompts interactively.
