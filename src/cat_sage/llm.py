"""LLM client factory for locally-hosted LM Studio models.

LM Studio exposes an OpenAI-compatible REST API, so every agent talks to it
through :class:`langchain_openai.ChatOpenAI` pointed at the local server. No
real API key is required; LM Studio ignores it, but the client still wants
some non-empty string.
"""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

DEFAULT_BASE_URL = "http://localhost:1234/v1"
DEFAULT_MODEL = "google/gemma-4-e4b"
DEFAULT_API_KEY = "lm-studio"


def build_chat_model(*, temperature: float = 0.7, model: str | None = None) -> ChatOpenAI:
    """Create a new, independent chat client for one agent.

    Each agent calls this on its own so agents never share a client
    instance -- only the environment-driven connection settings.
    """
    base_url = os.environ.get("LM_STUDIO_BASE_URL", DEFAULT_BASE_URL)
    api_key = os.environ.get("LM_STUDIO_API_KEY", DEFAULT_API_KEY)
    model_name = model or os.environ.get("LM_STUDIO_MODEL", DEFAULT_MODEL)
    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model_name,
        temperature=temperature,
    )
