from __future__ import annotations

import os


ANALYSIS_GENERATION_MODE = os.getenv("ANALYSIS_GENERATION_MODE", "template")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5-mini")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
