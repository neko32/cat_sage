"""Independent agents: Cat, Sage, and Judge.

Each agent is its own class with its own LLM client instance, its own system
prompt, and its own input/output shape. They only share the ``Agent``
protocol defined in :mod:`cat_sage.agents.base`, which is what makes them
independently mockable/stubbable in tests and independently swappable at
runtime (e.g. pointing one agent at a different model later).
"""
