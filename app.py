from pathlib import Path

import streamlit as st

from components.dashboard_components import (
    load_css,
    render_dashboard,
    render_header_com_menu,
    render_modal_evolucao,
)
from utils.data_loader import get_dashboard_content


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
    content = get_dashboard_content()

    render_header_com_menu(content, logo_file=LOGO_FILE)

    render_modal_evolucao()

    render_dashboard(content, logo_file=LOGO_FILE)


if __name__ == "__main__":
    main()
