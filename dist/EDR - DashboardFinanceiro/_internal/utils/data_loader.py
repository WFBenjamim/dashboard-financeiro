from __future__ import annotations

import json
import re
import unicodedata
from copy import deepcopy
from datetime import date, datetime
import os
import sys
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import streamlit as st

from utils.analysis_generator import generate_insights, generate_technical_analysis
from utils.dashboard_metrics import build_dashboard_metrics


def _runtime_root() -> Path:
    env_root = os.getenv("DASHBOARD_APP_ROOT")
    if env_root:
        return Path(env_root)

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


DATA_DIR = _runtime_root() / "data"
TEMPLATE_FILE = DATA_DIR / "dashboard_content.json"
ORCAMENTO_FILE = DATA_DIR / "Orçamento.xlsx"
INFO_FILE = DATA_DIR / "INFORMAÇÕES GERENCIAIS - Copia.xlsx"
FATURAMENTO_FILE = DATA_DIR / "Faturamento Allan.xlsx"

MONTH_LABELS = {
    1: "jan",
    2: "fev",
    3: "mar",
    4: "abr",
    5: "mai",
    6: "jun",
    7: "jul",
    8: "ago",
    9: "set",
    10: "out",
    11: "nov",
    12: "dez",
}


def get_dashboard_content() -> dict[str, Any]:
    """Carrega o dashboard usando o mês/ano atuais como padrão."""
    today = date.today()
    return get_dashboard_data(today.month, today.year)


def get_dashboard_data(mes: int, ano: int) -> dict[str, Any]:
    """Orquestra o ETL e devolve a estrutura aninhada esperada pela interface."""
    mes = max(1, min(int(mes), 12))
    ano = int(ano)

    template = deepcopy(_load_dashboard_template(TEMPLATE_FILE.stat().st_mtime_ns))

    kpis = load_kpis(mes, ano)
    headcount = load_headcount(ano)
    top_clientes = load_top_clientes(mes, ano)
    distribuicao_despesas = load_dre_distribution(mes, ano, kpis)

    template["header"]["subtitle"] = f"Período acumulado: {MONTH_LABELS[mes]} de {ano} • dados carregados via ETL"
    template["revenue_mix"] = kpis["revenue_mix"]
    template["cost_structure"] = distribuicao_despesas
    template["net_result"] = kpis["net_result"]
    template["margins"] = kpis["margins"]
    template["people"] = headcount
    template["top_clients"] = top_clientes
    template["insights"] = []
    template["technical_analysis"] = {
        "title": "Análise técnica",
        "paragraphs": [],
    }

    metrics = build_dashboard_metrics(template)
    template["technical_analysis"] = generate_technical_analysis(template, metrics=metrics)
    template["insights"] = generate_insights(template, metrics=metrics)
    return template


@st.cache_data(show_spinner=False)
def _load_dashboard_template(file_mtime_ns: int) -> dict[str, Any]:
    _ = file_mtime_ns
    return json.loads(TEMPLATE_FILE.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def _read_excel_sheet(file_path: str, sheet_name: str, header: int | None = 0) -> pd.DataFrame:
    return pd.read_excel(file_path, sheet_name=sheet_name, header=header, engine="openpyxl")


@st.cache_data(show_spinner=False)
def _read_csv_file(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)


def _normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip().lower()


def _to_float(value: Any) -> float:
    if value is None or pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return 0.0

    text = text.replace("R$", "").replace("%", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")

    text = re.sub(r"[^0-9\-\.]+", "", text)
    if text in {"", "-", "."}:
        return 0.0

    try:
        return float(text)
    except ValueError:
        return 0.0


def _format_currency(value: float) -> str:
    amount = abs(float(value))
    if amount >= 1_000_000:
        compact = f"{amount / 1_000_000:.2f}".replace(".", ",")
        if compact.endswith(",00"):
            compact = compact[:-3]
        prefix = "-" if value < 0 else ""
        return f"R$ {prefix}{compact}M"
    if amount >= 1_000:
        prefix = "-" if value < 0 else ""
        return f"R$ {prefix}{amount / 1_000:.0f}K"

    prefix = "-" if value < 0 else ""
    return f"R$ {prefix}{amount:.0f}"


def _format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def _format_count(value: float) -> str:
    return str(int(round(float(value))))


def _find_row_index(df: pd.DataFrame, term: str, start_row: int = 0) -> int | None:
    target = _normalize_text(term)
    for idx in range(start_row, len(df)):
        row = df.iloc[idx].tolist()
        for cell in row:
            if target and target in _normalize_text(cell):
                return idx
    return None


def _find_row_index_exact(df: pd.DataFrame, term: str, start_row: int = 0) -> int | None:
    target = _normalize_text(term)
    for idx in range(start_row, len(df)):
        row = df.iloc[idx].tolist()
        for cell in row:
            if _normalize_text(cell) == target:
                return idx
    return None


def _month_columns_from_header(header_row: Iterable[Any], mes: int) -> list[int]:
    columns: list[int] = []
    for idx, value in enumerate(header_row):
        normalized = _normalize_text(value)
        if normalized in MONTH_LABELS.values():
            month_number = next(number for number, label in MONTH_LABELS.items() if label == normalized)
            if month_number <= mes:
                columns.append(idx)
    return columns


def _date_columns_upto(df: pd.DataFrame, mes: int, ano: int) -> list[int]:
    columns: list[int] = []
    for idx, col in enumerate(df.columns):
        column_date: datetime | None = None
        if isinstance(col, datetime):
            column_date = col
        elif isinstance(col, date):
            column_date = datetime.combine(col, datetime.min.time())
        elif isinstance(col, str):
            parsed = pd.to_datetime(col, errors="coerce")
            if not pd.isna(parsed):
                column_date = parsed.to_pydatetime()

        if column_date and column_date.year == ano and column_date.month <= mes:
            columns.append(idx)
    return columns


def _row_sum(df: pd.DataFrame, row_index: int, columns: list[int]) -> float:
    if row_index is None:
        return 0.0
    row = df.iloc[row_index]
    values = [_to_float(row.iloc[column]) for column in columns]
    return float(sum(values))


def _last_significant_value(row: pd.Series) -> float:
    for value in reversed(row.tolist()):
        numeric = _to_float(value)
        if abs(numeric) > 1e-6:
            return numeric
    return 0.0


def _sum_terms(df: pd.DataFrame, terms: list[str], columns: list[int]) -> float:
    total = 0.0
    for term in terms:
        row_index = _find_row_index(df, term)
        total += abs(_row_sum(df, row_index, columns))
    return total


def _sum_terms_with_sign(df: pd.DataFrame, terms: list[str], columns: list[int]) -> float:
    total = 0.0
    for term in terms:
        row_index = _find_row_index(df, term)
        total += _row_sum(df, row_index, columns)
    return total


def _resolve_dre_text_column(df: pd.DataFrame) -> str:
    for column in df.columns:
        if _normalize_text(column) == "lancamento":
            return column
    raise KeyError("Coluna de lançamento não encontrada na planilha DRE")


def _prepare_dre_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    prepared = df.copy()
    text_column = _resolve_dre_text_column(prepared)
    prepared[text_column] = prepared[text_column].astype(str).str.strip().str.lower().map(_normalize_text)
    return prepared, text_column


def _resolve_dre_columns(df: pd.DataFrame, mes: int, ano: int) -> list[int]:
    columns = _date_columns_upto(df, mes, ano)
    if columns:
        return columns

    available_years = sorted(
        {
            column.year
            for column in df.columns
            if isinstance(column, datetime) or isinstance(column, date)
        }
    )
    if not available_years:
        return []

    return _date_columns_upto(df, mes, available_years[-1])


def _sum_dre_terms(df: pd.DataFrame, text_column: str, terms: list[str], columns: list[int]) -> float:
    if not columns:
        return 0.0

    launch = df[text_column].astype(str)
    mask = pd.Series(False, index=df.index)
    for term in terms:
        mask = mask | launch.str.contains(_normalize_text(term), na=False, regex=False)

    if not mask.any():
        return 0.0

    total = 0.0
    for _, row in df.loc[mask].iterrows():
        values = [_to_float(value) for value in row.iloc[columns].fillna(0).tolist()]
        total += sum(values)
    return total


def _build_item(label: str, value: float, total: float, details: list[dict[str, str]] | None = None, color_highlight: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {
        "label": label,
        "value": _format_currency(value),
        "share": _format_percent((abs(value) / total * 100) if total else 0.0),
        "details": details or [],
    }
    if color_highlight:
        item["color_highlight"] = color_highlight
    return item


@st.cache_data(show_spinner=False)
def load_kpis(mes: int, ano: int) -> dict[str, Any]:
    """Carrega os KPIs principais a partir das planilhas de orçamento e resultado."""
    resultado_df = _read_excel_sheet(str(ORCAMENTO_FILE), "Resultado - Sucumb - Sem Sucumb", header=None).fillna(0)
    kpi_df = _read_excel_sheet(str(ORCAMENTO_FILE), "KPI AN", header=None).fillna(0)

    sem_header = _find_row_index_exact(resultado_df, "Sem Sucumbência")
    suc_header = _find_row_index_exact(resultado_df, "Sucumbência")
    total_header = _find_row_index_exact(resultado_df, "Total - Gondim")

    sem_cols = _month_columns_from_header(resultado_df.iloc[sem_header].tolist(), mes) if sem_header is not None else []
    suc_cols = _month_columns_from_header(resultado_df.iloc[suc_header].tolist(), mes) if suc_header is not None else []

    sem_receita = _last_significant_value(resultado_df.iloc[_find_row_index_exact(resultado_df, "Receita", sem_header or 0)])
    suc_receita = _last_significant_value(resultado_df.iloc[_find_row_index_exact(resultado_df, "Receita", suc_header or 0)])
    total_receita = abs(sem_receita) + abs(suc_receita)

    total_result_signed = _last_significant_value(kpi_df.iloc[_find_row_index_exact(kpi_df, "Resultado")])
    total_result = abs(total_result_signed)

    row_total_revenue = _last_significant_value(kpi_df.iloc[_find_row_index_exact(kpi_df, "Receita")])
    row_direct_costs = abs(_last_significant_value(kpi_df.iloc[_find_row_index_exact(kpi_df, "Despesas Diretas")]))
    row_taxes = abs(_last_significant_value(kpi_df.iloc[_find_row_index_exact(kpi_df, "Impostos")]))
    row_rateio = abs(_last_significant_value(kpi_df.iloc[_find_row_index_exact(kpi_df, "Rateio")]))
    row_margin = _last_significant_value(kpi_df.iloc[_find_row_index_exact(kpi_df, "Margem Operacional (%MC)")])
    row_result = _last_significant_value(kpi_df.iloc[_find_row_index_exact(kpi_df, "Resultado")])

    revenue_attainment = (total_receita / row_total_revenue * 100) if row_total_revenue else 0.0

    return {
        "revenue_mix": {
            "icon": "💰",
            "title": "Origem de Receitas",
            "value": _format_currency(total_receita),
            "subtitle": f"▾ {abs((suc_receita / total_receita * 100) if total_receita else 0.0):.1f}% sucumbência • {revenue_attainment:.0f}% do orçado",
            "rows": [
                {
                    "label": "Contratuais",
                    "value": _format_currency(sem_receita),
                    "share": _format_percent((abs(sem_receita) / total_receita * 100) if total_receita else 0.0),
                },
                {
                    "label": "Sucumbência",
                    "value": _format_currency(suc_receita),
                    "share": _format_percent((abs(suc_receita) / total_receita * 100) if total_receita else 0.0),
                },
            ],
            "expansions": [
                {
                    "title": "Contratuais",
                    "items": [{"name": item["name"], "value": item["value"]} for item in load_top_clientes(mes, ano)["ranking"][:5]],
                },
                {
                    "title": "Sucumbência",
                    "items": _build_month_expansion(resultado_df, suc_header, "Receita", mes),
                },
            ],
        },
        "net_result": {
            "icon": "📊",
            "title": "Resultado Líquido",
            "value": _format_currency(total_result_signed),
            "subtitle": f"Resultado líquido sem sucumbência: {_format_currency(total_result)}",
        },
        "margins": {
            "icon": "📈",
            "title": "Margens",
            "value": _format_percent(row_margin * 100 if abs(row_margin) <= 1 else row_margin),
            "subtitle": f"Resultado estimado: {_format_currency(row_result)}",
        },
        "cost_totals": {
            "direct_costs": row_direct_costs,
            "taxes": row_taxes,
            "rateio": row_rateio,
        },
        "_raw": {
            "revenue_total": row_total_revenue,
            "net_result": total_result_signed,
            "direct_costs": row_direct_costs,
            "taxes": row_taxes,
            "rateio": row_rateio,
        },
    }


def _build_month_expansion(df: pd.DataFrame, header_row: int | None, row_label: str, mes: int) -> list[dict[str, str]]:
    if header_row is None:
        return []

    month_cols = _month_columns_from_header(df.iloc[header_row].tolist(), mes)
    row_index = _find_row_index_exact(df, row_label, header_row)
    if row_index is None:
        return []

    row = df.iloc[row_index]
    items: list[dict[str, str]] = []
    for column in month_cols:
        month_label = _normalize_text(df.iloc[header_row].iloc[column])
        items.append({"name": month_label.title(), "value": _format_currency(_to_float(row.iloc[column]))})
    total_value = abs(_row_sum(df, row_index, month_cols))
    items.append({"name": "Total", "value": _format_currency(total_value)})
    return items


@st.cache_data(show_spinner=False)
def load_headcount(ano: int) -> dict[str, Any]:
    """Carrega headcount de sócios, celetistas e estagiários."""
    df = _read_excel_sheet(str(INFO_FILE), "Pessoas", header=0).fillna(0)
    year_column = _resolve_year_column(df, ano)

    def _get_funtion_value(function_name: str) -> float:
        mask = (
            df["Tipo"].astype(str).map(_normalize_text) == "total"
        ) & (
            df["Função"].astype(str).map(_normalize_text) == _normalize_text(function_name)
        )
        subset = df.loc[mask]
        if subset.empty:
            return 0.0
        return _to_float(subset.iloc[0][year_column])

    socios = _get_funtion_value("Sócios")
    celetistas = _get_funtion_value("Celetistas")
    estagiarios = _get_funtion_value("Estagiários")
    total = _get_funtion_value("Total")

    return {
        "icon": "👥",
        "title": "Pessoas",
        "value": _format_count(total),
        "subtitle": "Estrutura de equipe",
        "rows": [
            {"label": "Sócios", "value": _format_count(socios), "share": _format_percent((socios / total * 100) if total else 0.0)},
            {"label": "CLTs", "value": _format_count(celetistas), "share": _format_percent((celetistas / total * 100) if total else 0.0)},
            {"label": "Estagiários", "value": _format_count(estagiarios), "share": _format_percent((estagiarios / total * 100) if total else 0.0)},
        ],
    }


def _resolve_year_column(df: pd.DataFrame, ano: int) -> Any:
    for column in df.columns:
        if _normalize_text(column) == str(ano):
            return column

    numeric_years = [column for column in df.columns if str(column).isdigit()]
    if numeric_years:
        return sorted(numeric_years, key=lambda item: int(str(item)))[-1]

    return df.columns[-1]


@st.cache_data(show_spinner=False)
def load_top_clientes(mes: int, ano: int) -> dict[str, Any]:
    """Carrega o top 5 de clientes por faturamento acumulado no período."""
    df = _read_excel_sheet(str(FATURAMENTO_FILE), "Faturamento 2025", header=None).fillna(0)
    section_headers = [idx for idx in range(len(df)) if _normalize_text(df.iloc[idx, 1] if len(df.columns) > 1 else "") == "carteiras"]
    if not section_headers:
        return {
            "icon": "🏆",
            "title": "Top 5 Clientes",
            "subtitle": "Faturamento acumulado no período",
            "ranking": [],
        }

    header_row = section_headers[-1]
    month_columns = [column for column in range(2, min(14, len(df.columns))) if column - 1 <= mes]

    clientes: list[tuple[str, float]] = []
    for idx in range(header_row + 1, len(df)):
        row = df.iloc[idx]
        nome = row.iloc[1] if len(row) > 1 else 0
        if not isinstance(nome, str) or not nome.strip():
            continue
        if _normalize_text(nome) in {"carteiras", "total geral"}:
            continue

        faturamento = sum(_to_float(row.iloc[column]) for column in month_columns)
        if faturamento > 0:
            clientes.append((nome.strip(), faturamento))

    clientes.sort(key=lambda item: item[1], reverse=True)
    top_5 = clientes[:5]
    outros_total = sum(valor for _, valor in clientes[5:])

    ranking = [{"name": nome, "value": _format_currency(valor)} for nome, valor in top_5]
    if outros_total > 0:
        ranking.append({"name": "Outros", "value": _format_currency(outros_total)})

    return {
        "icon": "🏆",
        "title": "Top 5 Clientes",
        "subtitle": "Faturamento acumulado no período",
        "ranking": ranking,
    }


@st.cache_data(show_spinner=False)
def load_dre_distribution(mes: int, ano: int, kpis: dict[str, Any]) -> dict[str, Any]:
    """Monta a distribuição de despesas a partir do DRE e dos KPIs consolidados."""
    df = _read_excel_sheet(str(INFO_FILE), "DRE", header=0).fillna(0)
    df, text_column = _prepare_dre_dataframe(df)
    columns = _resolve_dre_columns(df, mes, ano)

    socios_servico_raw = abs(_sum_dre_terms(df, text_column, ["juridico", "processos trabalhistas"], columns))
    clt_raw = abs(_sum_dre_terms(df, text_column, ["pessoal adm"], columns))
    correspondentes_raw = abs(_sum_dre_terms(df, text_column, ["correspondentes"], columns))
    impostos_raw = abs(_sum_dre_terms(df, text_column, ["imposto"], columns))
    outras_raw = abs(
        _sum_dre_terms(
            df,
            text_column,
            [
                "condenações + glosas",
                "comunicação",
                "consumo de material",
                "despesas gerais",
                "equipamentos",
                "localização / ocupação",
                "prestadores de serviço",
                "marketing",
                "vendas e marketing",
            ],
            columns,
        )
    )

    socios_servico = socios_servico_raw
    clt = clt_raw
    correspondentes = correspondentes_raw
    outras = outras_raw
    impostos = impostos_raw
    total = socios_servico + clt + correspondentes + outras + impostos
    personnel_share = ((socios_servico + clt) / total * 100) if total else 0.0

    items = [
        _build_item(
            "Sócios de Serviço",
            socios_servico,
            total,
            details=[
                {"name": "Jurídico", "value": _format_currency(abs(_sum_dre_terms(df, text_column, ["juridico"], columns)))} ,
                {"name": "Processos Trabalhistas", "value": _format_currency(abs(_sum_dre_terms(df, text_column, ["processos trabalhistas"], columns)))} ,
            ],
            color_highlight="green",
        ),
        _build_item(
            "CLT",
            clt,
            total,
            details=[{"name": "Pessoal Adm", "value": _format_currency(clt)}],
            color_highlight="purple",
        ),
        _build_item(
            "Impostos",
            impostos,
            total,
            details=[{"name": "Impostos", "value": _format_currency(impostos)}],
        ),
        _build_item(
            "Correspondentes",
            correspondentes,
            total,
            details=[{"name": "Custo Operacional - Correspondentes", "value": _format_currency(correspondentes)}],
            color_highlight="blue",
        ),
        _build_item(
            "Outras Despesas",
            outras,
            total,
            details=[
                {"name": "Condenações + Glosas", "value": _format_currency(abs(_sum_dre_terms(df, text_column, ["condenações + glosas"], columns)))} ,
                {"name": "Comunicação", "value": _format_currency(abs(_sum_dre_terms(df, text_column, ["comunicação"], columns)))} ,
                {"name": "Consumo de Material", "value": _format_currency(abs(_sum_dre_terms(df, text_column, ["consumo de material"], columns)))} ,
                {"name": "Despesas Gerais", "value": _format_currency(abs(_sum_dre_terms(df, text_column, ["despesas gerais"], columns)))} ,
                {"name": "Equipamentos", "value": _format_currency(abs(_sum_dre_terms(df, text_column, ["equipamentos"], columns)))} ,
                {"name": "Localização / Ocupação", "value": _format_currency(abs(_sum_dre_terms(df, text_column, ["localização / ocupação"], columns)))} ,
                {"name": "Prestadores de Serviço", "value": _format_currency(abs(_sum_dre_terms(df, text_column, ["prestadores de serviço"], columns)))} ,
                {"name": "Marketing", "value": _format_currency(abs(_sum_dre_terms(df, text_column, ["marketing"], columns)))} ,
                {"name": "Vendas e Marketing", "value": _format_currency(abs(_sum_dre_terms(df, text_column, ["vendas e marketing"], columns)))} ,
            ],
        ),
    ]

    return {
        "icon": "📉",
        "title": "Distribuição de Despesas",
        "value": _format_currency(total),
        "subtitle": "Consolidação do DRE por centro de custo",
        "highlight": {
            "label": "Despesa com pessoas",
            "value": _format_percent(personnel_share),
            "caption": "principal grupo de custo",
        },
        "items": items,
    }
