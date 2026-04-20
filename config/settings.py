from __future__ import annotations

import os


ANALYSIS_GENERATION_MODE = os.getenv("ANALYSIS_GENERATION_MODE", "template")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
