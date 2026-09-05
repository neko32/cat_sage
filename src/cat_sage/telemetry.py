"""OpenTelemetry wiring for Cat & Sage.

Every session opens one root span (``cat_sage.session``) and one child span
per round (``cat_sage.round``) carrying the round number and a short note.
:class:`SummaryFileExporter` accumulates every span it sees and, once the
session span itself ends, writes a human-readable summary file next to it.
"""

from __future__ import annotations

from pathlib import Path

from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.trace import Tracer

SESSION_SPAN_NAME = "cat_sage.session"
ROUND_SPAN_NAME = "cat_sage.round"


class SummaryFileExporter(SpanExporter):
    """Collects round spans and flushes a summary file when the session ends."""

    def __init__(self) -> None:
        self._round_spans: list[ReadableSpan] = []

    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            if span.name == ROUND_SPAN_NAME:
                self._round_spans.append(span)
            elif span.name == SESSION_SPAN_NAME:
                self._write_summary(span)
        return SpanExportResult.SUCCESS

    def _write_summary(self, session_span: ReadableSpan) -> None:
        attrs = session_span.attributes or {}
        file_path = attrs.get("summary.file_path")
        if not file_path:
            return
        path = Path(str(file_path))
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = [f"Question: {attrs.get('session.question', '')}"]
        rounds = sorted(
            self._round_spans,
            key=lambda s: (s.attributes or {}).get("round.number", 0),
        )
        for span in rounds:
            a = span.attributes or {}
            lines.append(
                f"Round {a.get('round.number')}: judge={a.get('judge.verdict')} "
                f'note="{a.get("round.note", "")}"'
            )
        lines.append(f"Total rounds: {attrs.get('session.total_rounds', '')}")
        lines.append(f"Outcome: {attrs.get('session.outcome', '')}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def shutdown(self) -> None:  # pragma: no cover - nothing to release
        return None


def build_tracer(exporter: SpanExporter | None = None) -> tuple[Tracer, SpanExporter]:
    """Build a fresh tracer + exporter pair for one session.

    A fresh :class:`TracerProvider` per session keeps sessions from leaking
    accumulated round spans into each other via a shared exporter instance.
    """
    provider = TracerProvider()
    exporter = exporter or SummaryFileExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("cat_sage")
    return tracer, exporter
