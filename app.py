from pathlib import Path
from datetime import date

import streamlit as st

from components.dashboard_components import (
    TOP_CLIENTS_MONTHS_KEY,
    TOP_CLIENTS_YEAR_KEY,
    init_top_clients_filter_state,
    load_css,
    render_dashboard_bottom,
    render_dashboard_top,
    render_header_com_menu,
    render_modal_evolucao,
    render_top_clients_filter,
)
from etl.loader import get_dashboard_content


BASE_DIR = Path(__file__).resolve().parent
CSS_FILE = BASE_DIR / "assets" / "css" / "styles.css"
LOGO_FILE = BASE_DIR / "assets" / "images" / "logo.png"


def main() -> None:
    """Renderiza o dashboard financeiro executivo."""
    st.set_page_config(
        page_title="Encontro de Divulgação de Resultados - Gondim | 2026 (EDR)",
        page_icon=":briefcase:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    with st.sidebar:
        if st.button("🔄 Recarregar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    load_css(CSS_FILE)
    today = date.today()
    default_year = today.year
    default_months = [1, 2, 3]

    init_top_clients_filter_state(default_year, default_months)
    selected_year = int(st.session_state[TOP_CLIENTS_YEAR_KEY])
    selected_months = [int(month) for month in st.session_state[TOP_CLIENTS_MONTHS_KEY]]

    content = get_dashboard_content(selected_year=selected_year, selected_months=selected_months)

    render_header_com_menu(content, logo_file=LOGO_FILE)

    render_dashboard_top(content, logo_file=LOGO_FILE)

    render_top_clients_filter(content, default_year, default_months)

    render_modal_evolucao()

    render_dashboard_bottom(content)


if __name__ == "__main__":
    main()
