"""SummaryFileExporter should turn accumulated spans into the summary file
once the session span itself ends."""

from __future__ import annotations

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from cat_sage.telemetry import SummaryFileExporter


def test_summary_file_written_when_session_span_ends(tmp_path):
    exporter = SummaryFileExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("test")

    summary_path = tmp_path / "summary.txt"

    with tracer.start_as_current_span("cat_sage.session") as session:
        session.set_attribute("session.question", "Why is the sky blue?")
        session.set_attribute("summary.file_path", str(summary_path))

        with tracer.start_as_current_span("cat_sage.round") as r1:
            r1.set_attribute("round.number", 1)
            r1.set_attribute("judge.verdict", "fail")
            r1.set_attribute("round.note", "cat rambled about naps")

        with tracer.start_as_current_span("cat_sage.round") as r2:
            r2.set_attribute("round.number", 2)
            r2.set_attribute("judge.verdict", "pass")
            r2.set_attribute("round.note", "cat nailed it")

        session.set_attribute("session.total_rounds", 2)
        session.set_attribute("session.outcome", "pass")

    assert summary_path.exists()
    content = summary_path.read_text(encoding="utf-8")
    assert "Question: Why is the sky blue?" in content
    assert "Round 1: judge=fail" in content
    assert "Round 2: judge=pass" in content
    assert "Total rounds: 2" in content
    assert "Outcome: pass" in content


def test_summary_skipped_without_file_path_attribute(tmp_path):
    exporter = SummaryFileExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("test")

    with tracer.start_as_current_span("cat_sage.session"):
        pass  # no summary.file_path attribute set

    assert list(tmp_path.iterdir()) == []
