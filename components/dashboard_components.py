from __future__ import annotations

import base64
from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Any

import streamlit as st

from utils.dashboard_metrics import normalize_key


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
    cost_cards = "".join(_build_cost_card(item) for item in costs["items"])
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
        <div class="gd-grid gd-grid--primary">
        <div class="gd-card gd-card--blue">
        <div class="gd-card__header">
        <div class="gd-title">{escape(revenue["icon"])} {escape(revenue["title"])}</div>
        <div class="gd-kpi">{escape(revenue["value"])}</div>
        <div class="gd-subline">{escape(revenue["subtitle"])}</div>
        </div>
        <div class="gd-surface">
        <div class="gd-revenue-list">
        {revenue_rows}
        </div>
        </div>
        </div>
        <div class="gd-card gd-card--gray">
        <div class="gd-card__header">
        <div class="gd-title">{escape(costs["icon"])} {escape(costs["title"])}</div>
        <div class="gd-kpi">{escape(costs["value"])}</div>
        <div class="gd-subline">{escape(costs["subtitle"])}</div>
        </div>
        <div class="gd-cost-layout">
        <div class="gd-cost gd-cost--highlight">
        <div class="gd-cost__label">{escape(costs["highlight"]["label"])}</div>
        <div class="gd-cost__value gd-cost__value--xl">{escape(costs["highlight"]["value"])}</div>
        </div>
        <div class="gd-cost-list">
        {cost_cards}
        </div>
        </div>
        </div>
        </div>
        <div class="gd-grid gd-grid--secondary">
        <div class="gd-card gd-card--orange gd-card--compact">
        <div class="gd-title">{escape(result["icon"])} {escape(result["title"])}</div>
        <div class="gd-kpi">{escape(result["value"])}</div>
        <div class="gd-subline">{escape(result["subtitle"])}</div>
        </div>
        <div class="gd-card gd-card--purple gd-card--compact">
        <div class="gd-title">{escape(margins["icon"])} {escape(margins["title"])}</div>
        <div class="gd-kpi">{escape(margins["value"])}</div>
        <div class="gd-subline">{escape(margins["subtitle"])}</div>
        </div>
        </div>
        <div class="gd-grid gd-grid--secondary">
        <div class="gd-card gd-card--green">
        <div class="gd-title">{escape(people["icon"])} {escape(people["title"])}</div>
        <div class="gd-kpi">{escape(people["value"])}</div>
        <div class="gd-subline">{escape(people["subtitle"])}</div>
        <div class="gd-list">{people_rows}</div>
        </div>
        <div class="gd-card gd-card--yellow">
        <div class="gd-title">{escape(clients["icon"])} {escape(clients["title"])}</div>
        <div class="gd-subline">{escape(clients["subtitle"])}</div>
        <div class="gd-list gd-list--spaced">{client_rows}</div>
        </div>
        </div>
        <div class="gd-insights">
        {insights}
        </div>
        <div class="gd-technical">
        <h2>{escape(content["technical_analysis"]["title"])}</h2>
        {analysis}
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
    content = (
        f"<span class='gd-revenue-line__label'>{escape(label)}</span>"
        "<span class='gd-revenue-line__metrics'>"
        f"<strong>{escape(value)}</strong>"
        f"<span>{escape(share)}</span>"
        "</span>"
    )

    if not items:
        return f"<div class='gd-revenue-line gd-revenue-line--static'>{content}</div>"

    return (
        "<details class='gd-revenue-line'>"
        "<summary class='gd-revenue-line__summary'>"
        f"{content}"
        "</summary>"
        "<div class='gd-revenue-line__content'>"
        f"{_build_detail_rows(items)}"
        "</div>"
        "</details>"
    )


def _build_cost_card(item: dict[str, Any]) -> str:
    details = item.get("details", [])
    content = (
        "<div class='gd-cost-rect__head'>"
        f"<div class='gd-cost-rect__label'>{escape(item['label'])}</div>"
        f"<div class='gd-cost-rect__share'>{escape(item['share'])}</div>"
        "</div>"
        f"<div class='gd-cost-rect__value'>{escape(item['value'])}</div>"
    )

    if not details:
        return f"<div class='gd-cost-rect'>{content}</div>"

    return (
        "<details class='gd-cost-rect gd-cost-rect--expandable'>"
        "<summary class='gd-cost-rect__summary'>"
        f"{content}"
        "</summary>"
        "<div class='gd-cost-rect__content'>"
        f"{_build_detail_rows(details)}"
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
    return (
        "<div class='gd-row gd-row--client'>"
        f"<strong>{index}. {escape(name)}</strong>"
        f"<span>{escape(value)}</span>"
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
