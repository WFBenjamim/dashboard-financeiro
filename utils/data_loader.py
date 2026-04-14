from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from utils.analysis_generator import generate_insights, generate_technical_analysis
from utils.dashboard_metrics import build_dashboard_metrics


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "dashboard_content.json"


def get_dashboard_content() -> dict[str, Any]:
    """Carrega o conteúdo do dashboard e monta os textos automáticos."""
    return _load_dashboard_content(str(DATA_FILE), DATA_FILE.stat().st_mtime_ns)


@st.cache_data(show_spinner=False)
def _load_dashboard_content(data_file: str, file_mtime_ns: int) -> dict[str, Any]:
    _ = file_mtime_ns
    content = json.loads(Path(data_file).read_text(encoding="utf-8"))
    metrics = build_dashboard_metrics(content)
    content["technical_analysis"] = generate_technical_analysis(content, metrics=metrics)
    content["insights"] = generate_insights(content, metrics=metrics)
    return content
