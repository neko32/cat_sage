"""OpenTelemetry wiring for Cat & Sage.

Every session opens one root span (``cat_sage.session``) and one child span
per round (``cat_sage.round``) carrying the round number and a short note.
:class:`SummaryFileExporter` accumulates every span it sees and, once the
session span itself ends, writes a human-readable summary file next to it.
"""

from __future__ import annotations

import json
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


class JsonFileExporter(SpanExporter):
    """Collects every span (raw) and writes the full span tree as JSON once
    the session span ends -- the un-curated counterpart to
    :class:`SummaryFileExporter`, useful for debugging or feeding into
    another tracing tool.
    """

    def __init__(self) -> None:
        self._spans: list[ReadableSpan] = []

    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            self._spans.append(span)
            if span.name == SESSION_SPAN_NAME:
                self._write_json(span)
        return SpanExportResult.SUCCESS

    def _write_json(self, session_span: ReadableSpan) -> None:
        attrs = session_span.attributes or {}
        file_path = attrs.get("spans.file_path")
        if not file_path:
            return
        path = Path(str(file_path))
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [self._span_to_dict(span) for span in self._spans]
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _span_to_dict(span: ReadableSpan) -> dict:
        ctx = span.get_span_context()
        parent = span.parent
        return {
            "name": span.name,
            "trace_id": format(ctx.trace_id, "032x") if ctx else None,
            "span_id": format(ctx.span_id, "016x") if ctx else None,
            "parent_span_id": format(parent.span_id, "016x") if parent else None,
            "start_time_ns": span.start_time,
            "end_time_ns": span.end_time,
            "duration_ns": (span.end_time - span.start_time if span.start_time and span.end_time else None),
            "attributes": dict(span.attributes or {}),
            "status": span.status.status_code.name if span.status else None,
        }

    def shutdown(self) -> None:  # pragma: no cover - nothing to release
        return None


def build_tracer(exporters: list[SpanExporter] | None = None) -> tuple[Tracer, list[SpanExporter]]:
    """Build a fresh tracer + exporters set for one session.

    Defaults to both :class:`SummaryFileExporter` (human-readable) and
    :class:`JsonFileExporter` (raw span dump). A fresh :class:`TracerProvider`
    per session keeps sessions from leaking accumulated round spans into
    each other via shared exporter instances.
    """
    provider = TracerProvider()
    exporters = exporters if exporters is not None else [SummaryFileExporter(), JsonFileExporter()]
    for exporter in exporters:
        provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("cat_sage")
    return tracer, exporters
