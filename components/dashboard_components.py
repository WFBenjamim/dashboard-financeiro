from __future__ import annotations

import base64
import re
from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Any

import streamlit as st

from utils.dashboard_metrics import normalize_key
from utils.number_formatter import formatar_valor_monetario
from utils.evolution_charts import create_grafico_evolucao_anual, create_grafico_evolucao_mensal


def _parse_valor_brl_e_formata(valor_str: str) -> str:
    """
    Extrai número de string formatada em BRL e retorna em formato compacto.
    Ex: "R$ 7.460.000,00" → "R$ 7,46M"
    """
    if not valor_str or not isinstance(valor_str, str):
        return valor_str

    if "R$" not in valor_str and not any(char.isdigit() for char in valor_str):
        return valor_str

    numero_str = valor_str.replace("R$", "").replace(" ", "").replace("\xa0", "")
    numero_str = numero_str.replace(".", "").replace(",", ".")

    try:
        numero = float(numero_str)
        return formatar_valor_monetario(numero, usar_compacto=True)
    except (ValueError, AttributeError):
        return valor_str


@st.cache_data(show_spinner=False)
def _read_css(css_file: str, css_mtime_ns: int) -> str:
    _ = css_mtime_ns
    return Path(css_file).read_text(encoding="utf-8")


def load_css(css_file: Path) -> None:
    """Carrega os estilos globais usados pelo dashboard."""
    css = _read_css(str(css_file), css_file.stat().st_mtime_ns)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_dashboard(content: dict[str, Any], logo_file: Path | None = None) -> None:
    """Renderiza o dashboard executivo completo."""
    logo_data_uri = _load_logo_data_uri(logo_file)
    html = _build_dashboard_html(content, logo_data_uri=logo_data_uri)
    st.markdown(html, unsafe_allow_html=True)


def _build_dashboard_html(content: dict[str, Any], logo_data_uri: str | None = None) -> str:
    header = content["header"]
    revenue = content["revenue_mix"]
    costs = content["cost_structure"]
    result = content["net_result"]
    margins = content["margins"]
    people = content["people"]
    clients = content["top_clients"]

    # Formata valores dos KPIs principais
    revenue_value_formatted = _parse_valor_brl_e_formata(revenue["value"])
    costs_value_formatted = _parse_valor_brl_e_formata(costs["value"])
    result_value_formatted = _parse_valor_brl_e_formata(result["value"])
    margins_value_formatted = _parse_valor_brl_e_formata(margins["value"])
    people_value_formatted = people["value"]
    highlight_value_formatted = _parse_valor_brl_e_formata(costs["highlight"]["value"])
    highlight_caption = costs["highlight"].get("caption") or "principal grupo de custo"

    revenue_expansions = {
        normalize_key(item["title"]): item["items"]
        for item in revenue["expansions"]
    }
    revenue_rows = "".join(
        _build_revenue_row(
            label=row["label"],
            value=row["value"],
            share=row["share"],
            items=revenue_expansions.get(normalize_key(row["label"])),
        )
        for row in revenue["rows"]
    )
    cost_cards_reorganizados = _render_custos_reorganizados(
        costs=costs,
        highlight_value_formatted=highlight_value_formatted,
        highlight_caption=highlight_caption,
    )
    people_rows = "".join(
        _build_people_row(row["label"], row["value"], row["share"])
        for row in people["rows"]
    )
    client_rows = "".join(
        _build_client_row(index, client["name"], client["value"])
        for index, client in enumerate(clients["ranking"], start=1)
    )
    insights = "".join(
        _build_insight_card(item["tone"], item["title"], item["description"])
        for item in content["insights"]
    )
    analysis = "".join(
        f"<p>{escape(paragraph)}</p>" for paragraph in content["technical_analysis"]["paragraphs"]
    )
    logo_html = _build_logo_html(logo_data_uri)

    html = dedent(
        f"""
        <div class="gd-shell">
        {logo_html}
        <div class="gd-hero">
        <div class="gd-hero__inner">
        <h1>{escape(header["title"])}</h1>
        <p class="gd-hero__subtitle">{escape(header["subtitle"])}</p>
        </div>
        <div class="gd-hero__band">{escape(header["band"])}</div>
        </div>
        <div class="gd-top-section">
        <div class="gd-top-column">
        <div class="gd-card gd-card--blue">
        <div class="gd-card__header">
        <div class="gd-title">{escape(revenue["icon"])} {escape(revenue["title"])}</div>
        <div class="gd-kpi">{escape(revenue_value_formatted)}</div>
        <div class="gd-subline">{escape(revenue["subtitle"])}</div>
        </div>
        <div class="gd-surface">
        <div class="gd-revenue-list">
        {revenue_rows}
        </div>
        </div>
        </div>
        <div class="gd-card gd-card--orange gd-card--compact">
        <div class="gd-title">{escape(result["icon"])} {escape(result["title"])}</div>
        <div class="gd-kpi">{escape(result_value_formatted)}</div>
        <div class="gd-subline">{escape(result["subtitle"])}</div>
        </div>
        <div class="gd-card gd-card--green">
        <div class="gd-title">{escape(people["icon"])} {escape(people["title"])}</div>
        <div class="gd-kpi">{escape(people_value_formatted)}</div>
        <div class="gd-subline">{escape(people["subtitle"])}</div>
        <div class="gd-list">{people_rows}</div>
        </div>
        </div>
        <div class="gd-top-column">
        <div class="gd-card gd-card--gray">
        <div class="gd-card__header">
        <div class="gd-title">{escape(costs["icon"])} {escape(costs["title"])}</div>
        <div class="gd-kpi">{escape(costs_value_formatted)}</div>
        <div class="gd-subline">{escape(costs["subtitle"])}</div>
        </div>
        {cost_cards_reorganizados}
        </div>
        <div class="gd-card gd-card--purple gd-card--compact">
        <div class="gd-title">{escape(margins["icon"])} {escape(margins["title"])}</div>
        <div class="gd-kpi">{escape(margins_value_formatted)}</div>
        <div class="gd-subline">{escape(margins["subtitle"])}</div>
        </div>
        <div class="gd-card gd-card--yellow">
        <div class="gd-title">{escape(clients["icon"])} {escape(clients["title"])}</div>
        <div class="gd-subline">{escape(clients["subtitle"])}</div>
        <div class="gd-list gd-list--spaced">{client_rows}</div>
        </div>
        </div>
        </div>
        <div class="gd-bottom-section">
        <div class="gd-insights">
        {insights}
        </div>
        <div class="gd-technical">
        <h2>{escape(content["technical_analysis"]["title"])}</h2>
        {analysis}
        </div>
        </div>
        </div>
        """
    ).strip()
    return "\n".join(line for line in html.splitlines() if line.strip())


def _build_logo_html(logo_data_uri: str | None) -> str:
    if not logo_data_uri:
        return ""

    return (
        "<div class='gd-logo-wrap'>"
        f"<img class='gd-logo' src='{logo_data_uri}' alt='Logo Gondim'>"
        "</div>"
    )


def _build_revenue_row(
    label: str,
    value: str,
    share: str,
    items: list[dict[str, str]] | None = None,
) -> str:
    formatted_value = _parse_valor_brl_e_formata(value)
    content = (
        f"<span class='gd-revenue-line__label'>{escape(label)}</span>"
        "<span class='gd-revenue-line__metrics'>"
        f"<strong>{escape(formatted_value)}</strong>"
        f"<span>{escape(share)}</span>"
        "</span>"
    )

    if not items:
        return f"<div class='gd-revenue-line gd-revenue-line--static'>{content}</div>"

    formatted_items = [
        {
            **item,
            "value": _parse_valor_brl_e_formata(item.get("value", ""))
        }
        for item in items
    ]

    return (
        "<details class='gd-revenue-line'>"
        "<summary class='gd-revenue-line__summary'>"
        f"{content}"
        "</summary>"
        "<div class='gd-revenue-line__content'>"
        f"{_build_detail_rows(formatted_items)}"
        "</div>"
        "</details>"
    )


def _build_cost_card(item: dict[str, Any]) -> str:
    details = item.get("details", [])
    formatted_value = _parse_valor_brl_e_formata(item.get("value", ""))
    color_highlight = item.get("color_highlight", "")

    highlight_class = ""
    if color_highlight == "green":
        highlight_class = " gd-cost-rect--highlight-green"
    elif color_highlight == "purple":
        highlight_class = " gd-cost-rect--highlight-purple"
    elif color_highlight == "blue":
        highlight_class = " gd-cost-rect--highlight-blue"

    content = (
        "<div class='gd-cost-rect__head'>"
        f"<div class='gd-cost-rect__label'>{escape(item['label'])}</div>"
        f"<div class='gd-cost-rect__share'>{escape(item['share'])}</div>"
        "</div>"
        f"<div class='gd-cost-rect__value'>{escape(formatted_value)}</div>"
    )

    if not details:
        return f"<div class='gd-cost-rect{highlight_class}'>{content}</div>"

    formatted_details = [
        {
            **detail,
            "value": _parse_valor_brl_e_formata(detail.get("value", ""))
        }
        for detail in details
    ]

    return (
        f"<details class='gd-cost-rect gd-cost-rect--expandable{highlight_class}'>"
        "<summary class='gd-cost-rect__summary'>"
        f"{content}"
        "</summary>"
        "<div class='gd-cost-rect__content'>"
        f"{_build_detail_rows(formatted_details)}"
        "</div>"
        "</details>"
    )


def _build_detail_rows(items: list[dict[str, str]]) -> str:
    return "".join(
        (
            "<div class='gd-mini-row'>"
            f"<span class='gd-mini-row__label'>{index}. {escape(item['name'])}</span>"
            f"<strong class='gd-mini-row__value'>{escape(item['value'])}</strong>"
            "</div>"
        )
        for index, item in enumerate(items, start=1)
    )


def _render_custos_reorganizados(
    costs: dict[str, Any],
    highlight_value_formatted: str,
    highlight_caption: str,
) -> str:
    """
    Renderiza cards de custo reorganizados:
    - Card de destaque à esquerda
    - Sócios de Serviço e CLT abaixo dele, em coluna
    - Demais cards à direita
    """
    especiais = []
    restantes = []

    for item in costs["items"]:
        if item["label"] in ["Sócios de Serviço", "CLT"]:
            especiais.append(item)
        else:
            restantes.append(item)

    especiais_html = "".join(_build_cost_card(item) for item in especiais)
    restantes_html = "".join(_build_cost_card(item) for item in restantes)

    return dedent(
        f"""
        <div class="gd-cost-layout">
        <div class="gd-cost-layout__left">
        <div class="gd-cost gd-cost--highlight">
        <div class="gd-cost__label">{escape(costs["highlight"]["label"])}</div>
        <div class="gd-cost__value gd-cost__value--xl">{escape(highlight_value_formatted)}</div>
        <div class="gd-cost__caption">{escape(highlight_caption)}</div>
        </div>
        <div class="gd-cost-list gd-cost-list--special">
        {especiais_html}
        </div>
        </div>
        <div class="gd-cost-layout__right">
        <div class="gd-cost-list gd-cost-list--main">
        {restantes_html}
        </div>
        </div>
        </div>
        """
    ).strip()


def _build_people_row(label: str, value: str, share: str) -> str:
    return (
        "<div class='gd-row'>"
        f"<span class='gd-row__label'>{escape(label)}</span>"
        "<div class='gd-row__value-group'>"
        f"<strong>{escape(value)}</strong>"
        f"<span class='gd-pill gd-pill--inline'>{escape(share)}</span>"
        "</div>"
        "</div>"
    )


def _build_client_row(index: int, name: str, value: str) -> str:
    formatted_value = _parse_valor_brl_e_formata(value)
    return (
        "<div class='gd-row gd-row--client'>"
        f"<strong>{index}. {escape(name)}</strong>"
        f"<span>{escape(formatted_value)}</span>"
        "</div>"
    )


def _build_insight_card(tone: str, title: str, description: str) -> str:
    return (
        f"<div class='gd-insight gd-insight--{escape(tone)}'>"
        f"<div class='gd-insight__title'>{escape(title)}</div>"
        f"<div class='gd-insight__description'>{escape(description)}</div>"
        "</div>"
    )


def _load_logo_data_uri(logo_file: Path | None) -> str | None:
    if not logo_file or not logo_file.exists():
        return None

    encoded = _read_logo_base64(str(logo_file), logo_file.stat().st_mtime_ns)
    suffix = logo_file.suffix.lower()
    mime_type = "image/png" if suffix == ".png" else "image/jpeg"
    return f"data:{mime_type};base64,{encoded}"


@st.cache_data(show_spinner=False)
def _read_logo_base64(logo_file: str, logo_mtime_ns: int) -> str:
    _ = logo_mtime_ns
    return base64.b64encode(Path(logo_file).read_bytes()).decode("ascii")


def render_header_com_menu(content: dict[str, Any], logo_file: Path | None = None) -> None:
    """Renderiza o botão fixo do menu de evolução."""
    _ = content
    _ = logo_file
    menu_html = """
    <style>
    .gd-evolution-fab {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 10000;
    }

    .gd-evolution-fab button,
    .gd-evolution-fab a {
        appearance: none;
        border: 1px solid rgba(251, 191, 36, 0.45);
        border-radius: 14px;
        width: 3rem;
        height: 3rem;
        background: linear-gradient(135deg, #FBBF24 0%, #F59E0B 100%);
        color: #1f1300;
        font-size: 1.4rem;
        font-weight: 800;
        box-shadow: 0 10px 24px rgba(251, 191, 36, 0.24);
        cursor: pointer;
        transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
    }

    .gd-evolution-fab button:hover,
    .gd-evolution-fab a:hover {
        transform: translateY(-1px) scale(1.04);
        box-shadow: 0 14px 28px rgba(251, 191, 36, 0.34);
        filter: brightness(1.03);
    }

    .gd-evolution-fab a {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
    }
    </style>
    """
    st.markdown(menu_html, unsafe_allow_html=True)
    if "gd_show_evolution_dialog" not in st.session_state:
        st.session_state.gd_show_evolution_dialog = False
    if "gd_evolution_tab" not in st.session_state:
        st.session_state.gd_evolution_tab = "anual"

    if st.button("☰", key="gd_evolution_menu_button", help="Abrir evolução"):
        st.session_state.gd_show_evolution_dialog = True


def render_modal_evolucao() -> None:
    """Abre um dialog nativo com os gráficos de evolução."""
    if not st.session_state.get("gd_show_evolution_dialog", False):
        return

    @st.dialog("Análise de Evolução", width="large", dismissible=False, icon="📈")
    def _dialog() -> None:
        st.markdown(
            "<div style='margin-bottom: 0.75rem; color: rgba(248,250,252,0.72);'>"
            "Escolha a visão que deseja analisar.</div>",
            unsafe_allow_html=True,
        )

        btn_anual, btn_mensal, btn_close = st.columns([1.1, 1.1, 0.45], gap="small")

        with btn_anual:
            if st.button(
                "Evolução Anual",
                key="evolucao_btn_anual",
                use_container_width=True,
                type="primary" if st.session_state.gd_evolution_tab == "anual" else "secondary",
            ):
                st.session_state.gd_evolution_tab = "anual"
                st.rerun()

        with btn_mensal:
            if st.button(
                "Evolução Mensal",
                key="evolucao_btn_mensal",
                use_container_width=True,
                type="primary" if st.session_state.gd_evolution_tab == "mensal" else "secondary",
            ):
                st.session_state.gd_evolution_tab = "mensal"
                st.rerun()

        with btn_close:
            if st.button("✕", key="evolucao_btn_close", use_container_width=True):
                st.session_state.gd_show_evolution_dialog = False
                st.session_state.gd_evolution_tab = "anual"
                st.rerun()

        st.write("")

        if st.session_state.gd_evolution_tab == "anual":
            st.plotly_chart(create_grafico_evolucao_anual(), use_container_width=True, key="grafico_evolucao_anual_dialog")
        else:
            st.plotly_chart(create_grafico_evolucao_mensal(), use_container_width=True, key="grafico_evolucao_mensal_dialog")

    _dialog()

