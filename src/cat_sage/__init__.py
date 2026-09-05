"""Cat & Sage: a multi-agent LangGraph POC.

Three independent agents collaborate to answer a user's question:

- ``CatAgent`` gives confident but tangential/wrong answers.
- ``JudgeAgent`` (LLM-as-judge) decides pass/fail on Cat's answer.
- ``SageAgent`` critiques a failing answer so Cat can try again.

The loop runs for up to five rounds; if Judge never passes Cat's answer,
the session ends with Cat crying.
"""

__all__ = ["__version__"]
__version__ = "0.1.0"
