"""Common interface shared by the independent Cat / Sage / Judge agents.

This is intentionally the *only* thing the three agents share. Each agent
otherwise owns its own LLM client, prompt, and call signature, so they can
be developed, tested, and swapped independently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class AgentResult:
    """Uniform return value from any agent's ``act`` call.

    ``text`` is the human-readable output (an answer, a critique, a
    judge's reason). ``raw`` carries any extra structured data an agent
    wants to expose (e.g. Judge's verdict) without forcing a shared schema
    on every agent.
    """

    text: str
    raw: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Agent(Protocol):
    """Structural interface every agent (and every test double) satisfies."""

    name: str

    def act(self, **kwargs: Any) -> AgentResult: ...
