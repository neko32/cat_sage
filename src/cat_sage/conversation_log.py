"""Plain-text conversation log in the exact format requested:

round1 cat: xxx
round1 judge: [fail] yyy
round1 sage: zzz
round2 cat: aaa
round2 judge: [pass] bbb
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConversationLog:
    lines: list[str] = field(default_factory=list)

    def record(self, round_no: int, speaker: str, text: str, *, verdict: str | None = None) -> None:
        flat = " ".join(text.strip().splitlines())
        if speaker == "judge" and verdict:
            self.lines.append(f"round{round_no} judge: [{verdict}] {flat}")
        else:
            self.lines.append(f"round{round_no} {speaker}: {flat}")

    def as_text(self) -> str:
        return "\n".join(self.lines) + ("\n" if self.lines else "")

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.as_text(), encoding="utf-8")
