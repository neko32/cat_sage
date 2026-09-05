"""Command-line entrypoint for the Cat & Sage POC."""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from .agents.cat import CatAgent
from .agents.judge import JudgeAgent
from .agents.sage import SageAgent
from .conversation_log import ConversationLog
from .graph import build_graph
from .state import initial_state
from .telemetry import build_tracer

OUTPUT_DIR = Path(r"C:\tmp")


def slugify(text: str, max_words: int = 8, max_len: int = 60) -> str:
    """Filesystem-safe one-line summary derived from the question itself."""
    words = re.findall(r"[A-Za-z0-9]+", text.lower())[:max_words]
    slug = "_".join(words) if words else "session"
    return slug[:max_len].strip("_") or "session"


def run(question: str, *, output_dir: Path = OUTPUT_DIR) -> dict:
    tracer, _exporter = build_tracer()
    cat, sage, judge = CatAgent(), SageAgent(), JudgeAgent()
    log = ConversationLog()

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    slug = slugify(question)
    summary_path = output_dir / f"cat_sage_{slug}_{timestamp}.txt"
    conversation_path = output_dir / f"cat_sage_{slug}_{timestamp}_conversation.txt"

    graph = build_graph(cat=cat, sage=sage, judge=judge, tracer=tracer, log=log)

    with tracer.start_as_current_span("cat_sage.session") as session_span:
        session_span.set_attribute("session.question", question)
        session_span.set_attribute("summary.file_path", str(summary_path))
        final_state = graph.invoke(initial_state(question), config={"recursion_limit": 50})
        session_span.set_attribute("session.total_rounds", len(final_state["history"]))
        session_span.set_attribute("session.outcome", final_state["outcome"] or "")

    log.save(conversation_path)

    print(f"\n=== Final answer ===\n{final_state['final_answer']}\n")
    print(f"Telemetry summary written to: {summary_path}")
    print(f"Conversation log written to: {conversation_path}")

    return final_state


def _force_utf8_stdio() -> None:
    """Windows consoles often default to cp932; LLM output can contain
    characters (em dashes, curly quotes, emoji) that codec can't encode."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    _force_utf8_stdio()
    load_dotenv()  # picks up .env next to pyproject.toml, if present
    parser = argparse.ArgumentParser(prog="cat-sage", description="Cat & Sage multi-agent POC")
    parser.add_argument("question", nargs="*", help="The question to ask Cat")
    args = parser.parse_args()
    question = " ".join(args.question) if args.question else input("Ask Cat something: ")
    run(question)


if __name__ == "__main__":
    main()
