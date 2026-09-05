# Cat & Sage 🐱🧙

A small multi-agent LangGraph proof-of-concept about accountability between AI agents.

- **Cat** answers your question — confidently, and usually beside the point.
- **Judge** (LLM-as-judge) strictly rules the answer `pass` or `fail`.
- **Sage** steps in only on `fail`, critiques Cat's answer coldly, and gives
  concrete feedback so Cat can try again.

The loop runs for up to 5 rounds. If Judge never passes Cat, the session
ends with Cat in tears.

```
START ─▶ cat ─▶ judge ─┬─ pass ───────────────▶ respond ─▶ END
                        ├─ fail, round < 5 ───▶ sage ─▶ cat  (loop)
                        └─ fail, round == 5 ──▶ cry ─────────▶ END
```

Cat, Sage, and Judge are three genuinely independent agents (own LLM client,
own prompt, own I/O shape) sharing only a minimal `Agent` protocol — not one
client with swapped prompts. See [`docs/design.md`](docs/design.md) for the
full write-up.

## Requirements

- Python >= 3.11
- [LM Studio](https://lmstudio.ai/) running locally with an OpenAI-compatible
  server enabled (default `http://localhost:1234/v1`) and a chat model loaded
  (default expected: `google/gemma-4-e4b`)

## Quick start

`scripts/run.ps1` (Windows) and `scripts/run.sh` (Linux/macOS/Git Bash) both
create the virtualenv on first use, install the project, seed `.env` from
`.env.example` if missing, and forward all arguments to the CLI:

```powershell
scripts\run.ps1 "Why is the sky blue?"
```

```bash
scripts/run.sh "Why is the sky blue?"
```

## Manual setup

```bash
python -m venv .venv
.venv\Scripts\activate        # or: source .venv/Scripts/activate
pip install -e ".[dev]"
copy .env.example .env        # adjust if your LM Studio setup differs
```

## Run

```bash
python -m cat_sage.cli "Why is the sky blue?"
```

Each run prints the final answer and writes two files under `C:\tmp\`:

- `cat_sage_{slug}_{timestamp}.txt` — an OpenTelemetry-derived summary of
  every round (round number, verdict, note).
- `cat_sage_{slug}_{timestamp}_conversation.txt` — the full round-by-round
  transcript:

  ```
  round1 cat: xxx
  round1 judge: [fail] yyy
  round1 sage: zzz
  round2 cat: aaa
  round2 judge: [pass] bbb
  ```

## Test

```bash
pytest
ruff check .
ruff format --check .
```

All tests run against fake agents/LLMs — no LM Studio connection required.

## Project layout

```
src/cat_sage/
├── state.py            # shared LangGraph state schema
├── graph.py             # orchestration only — no agent logic
├── agents/
│   ├── base.py          # the Agent protocol every agent implements
│   ├── cat.py
│   ├── sage.py
│   └── judge.py
├── llm.py                # LM Studio (OpenAI-compatible) client factory
├── telemetry.py           # OpenTelemetry spans -> summary file
├── conversation_log.py     # round-by-round transcript writer
└── cli.py                  # entrypoint
```

## Status

Proof-of-concept — test coverage is intentionally scoped to the graph's
routing logic and each agent's contract, not exhaustive edge cases.
