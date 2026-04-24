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


def _resolve_data_file(*candidate_names: str) -> Path:
    for candidate_name in candidate_names:
        candidate_path = DATA_DIR / candidate_name
        if candidate_path.exists():
            return candidate_path
    raise FileNotFoundError(
        f"Nenhum dos arquivos esperados foi encontrado em {DATA_DIR}: {', '.join(candidate_names)}"
    )


DATA_DIR = _runtime_root() / "data"
TEMPLATE_FILE = DATA_DIR / "dashboard_content.json"
INFO_FILE = _resolve_data_file("INFORMAÇÕES GERENCIAIS.xlsx", "INFORMAÇÕES GERENCIAIS - Copia.xlsx")
PERFORMANCE_FILE = DATA_DIR / "Faturamento Allan.xlsx"

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

    template["header"]["subtitle"] = "Período acumulado: 1º tri de 2026 • dados carregados via ETL"
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


def _resolve_date_columns(df: pd.DataFrame, mes: int, ano: int) -> list[int]:
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


def _sum_exact_terms(df: pd.DataFrame, text_column: str, terms: list[str], columns: list[int]) -> float:
    total = 0.0
    if not columns:
        return total

    launch = df[text_column].astype(str)
    for term in terms:
        target = _normalize_text(term)
        if target == "":
            continue
        matches = launch == target
        if not matches.any():
            continue
        for row_index in df.loc[matches].index:
            row = df.iloc[row_index]
            values = [_to_float(row.iloc[column]) for column in columns]
            total += sum(values)
    return total


def _sum_row_by_label(df: pd.DataFrame, label: str, columns: list[int], absolute: bool = False) -> float:
    row_index = _find_row_index_exact(df, label)
    if row_index is None:
        return 0.0

    value = _row_sum(df, row_index, columns)
    return abs(value) if absolute else value


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
    return _resolve_date_columns(df, mes, ano)


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


def _resolve_named_column(df: pd.DataFrame, expected_names: list[str]) -> Any:
    expected = {_normalize_text(name) for name in expected_names}
    for column in df.columns:
        if _normalize_text(column) in expected:
            return column

    raise KeyError(f"Nenhuma das colunas esperadas foi encontrada: {', '.join(expected_names)}")


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
    """Carrega os KPIs principais a partir da tabela TOTAIS 20 E 21 e da DRE."""
    totais_df = _read_excel_sheet(str(INFO_FILE), "TOTAIS  20 E 21", header=0).fillna(0)
    dre_df = _read_excel_sheet(str(INFO_FILE), "DRE", header=0).fillna(0)
    dre_df, text_column = _prepare_dre_dataframe(dre_df)

    total_columns = _resolve_date_columns(totais_df, mes, ano)
    dre_columns = _resolve_dre_columns(dre_df, mes, ano)

    total_receita = _sum_row_by_label(totais_df, "RECEITA SEM INTERCOMPANY", total_columns)
    total_costs = _sum_row_by_label(totais_df, "CUSTOS E DESPESAS SEM INTERCOMPANY", total_columns)
    total_result_signed = _sum_row_by_label(totais_df, "RESULTADO SEM INTERCOMPANY", total_columns)
    total_orcado = _sum_row_by_label(totais_df, "TOTAL ORÇADO", total_columns)

    contratuais = abs(_sum_exact_terms(dre_df, text_column, ["Clientes - Honorários Contratuais"], dre_columns))
    sucumbencia = abs(_sum_exact_terms(dre_df, text_column, ["Clientes - Honorários de Sucumbência"], dre_columns))
    result_without_sucumbency = total_result_signed - sucumbencia

    revenue_attainment = (total_receita / total_orcado * 100) if total_orcado else 0.0
    revenue_share_sucumbencia = (sucumbencia / total_receita * 100) if total_receita else 0.0
    margins_value = (total_result_signed / total_receita * 100) if total_receita else 0.0

    return {
        "revenue_mix": {
            "icon": "💰",
            "title": "Mix de Receitas",
            "value": _format_currency(total_receita),
            "subtitle": f"▾ {revenue_share_sucumbencia:.1f}% sucumbência • {revenue_attainment:.0f}% do orçado",
            "rows": [
                {
                    "label": "Contratuais",
                    "value": _format_currency(contratuais),
                    "share": _format_percent((contratuais / total_receita * 100) if total_receita else 0.0),
                },
                {
                    "label": "Sucumbência",
                    "value": _format_currency(sucumbencia),
                    "share": _format_percent(revenue_share_sucumbencia),
                },
            ],
            "expansions": [
                {
                    "title": "Contratuais",
                    "items": [{"name": item["name"], "value": item["value"]} for item in load_top_clientes(mes, ano)["ranking"][:5]],
                },
                {
                    "title": "Sucumbência",
                    "items": [],
                },
            ],
        },
        "net_result": {
            "icon": "📊",
            "title": "Resultado Líquido",
            "value": _format_currency(total_result_signed),
            "subtitle": f"Resultado líquido sem sucumbência: {_format_currency(result_without_sucumbency)}",
        },
        "margins": {
            "icon": "📈",
            "title": "Margens",
            "value": _format_percent(margins_value),
            "subtitle": f"Resultado estimado: {_format_currency(total_result_signed)}",
        },
        "cost_totals": {
            "direct_costs": total_costs,
            "taxes": 0.0,
            "rateio": 0.0,
            "total": total_costs,
        },
        "_raw": {
            "revenue_total": total_receita,
            "cost_total": total_costs,
            "net_result": total_result_signed,
            "direct_costs": total_costs,
            "taxes": 0.0,
            "rateio": 0.0,
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
    """Carrega o top 5 da tabela Performance por faturamento acumulado no período."""
    df = _read_excel_sheet(str(PERFORMANCE_FILE), "Faturamento 2025", header=None).fillna(0)
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

    total = _to_float(kpis.get("_raw", {}).get("cost_total", 0.0))

    socios_servico = abs(_sum_exact_terms(df, text_column, ["Custo Operacional - Jurídico"], columns))
    clt = abs(_sum_exact_terms(df, text_column, ["Pessoal Adm"], columns))
    correspondentes = abs(_sum_exact_terms(df, text_column, ["Custo Operacional - Correspondentes"], columns))
    impostos = abs(_sum_exact_terms(df, text_column, ["Impostos e Taxas - Normais"], columns))
    outras = max(total - (socios_servico + clt + correspondentes + impostos), 0.0)
    personnel_share = ((socios_servico + clt) / total * 100) if total else 0.0

    items = [
        _build_item(
            "Sócios de Serviço",
            socios_servico,
            total,
            details=[
                {"name": "Jurídico", "value": _format_currency(abs(_sum_exact_terms(df, text_column, ["Custo Operacional - Jurídico"], columns)))},
                {"name": "Processos Trabalhistas", "value": _format_currency(abs(_sum_exact_terms(df, text_column, ["Custo Operacional - Processos Trabalhistas"], columns)))},
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
            details=[{"name": "Impostos e Taxas - Normais", "value": _format_currency(impostos)}],
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
                {"name": "Condenações + Glosas", "value": _format_currency(abs(_sum_exact_terms(df, text_column, ["Condenações + Glosas"], columns)))},
                {"name": "Comunicação", "value": _format_currency(abs(_sum_exact_terms(df, text_column, ["Comunicação"], columns)))},
                {"name": "Consumo de Material", "value": _format_currency(abs(_sum_exact_terms(df, text_column, ["Consumo de Material"], columns)))},
                {"name": "Despesas Gerais", "value": _format_currency(abs(_sum_exact_terms(df, text_column, ["Despesas Gerais"], columns)))},
                {"name": "Equipamentos", "value": _format_currency(abs(_sum_exact_terms(df, text_column, ["Equipamentos"], columns)))},
                {"name": "Localização / Ocupação", "value": _format_currency(abs(_sum_exact_terms(df, text_column, ["Localização / Ocupação"], columns)))},
                {"name": "Prestadores de Serviço", "value": _format_currency(abs(_sum_exact_terms(df, text_column, ["Prestadores de Serviço"], columns)))},
                {"name": "Marketing", "value": _format_currency(abs(_sum_exact_terms(df, text_column, ["Marketing"], columns)))},
                {"name": "Vendas e Marketing", "value": _format_currency(abs(_sum_exact_terms(df, text_column, ["Vendas e Marketing"], columns)))},
            ],
        ),
    ]

    return {
        "icon": "📉",
        "title": "Estrutura de Custos",
        "value": _format_currency(total),
        "subtitle": "Consolidação do DRE por centro de custo",
        "highlight": {
            "label": "Despesa com pessoas",
            "value": _format_percent(personnel_share),
            "caption": "principal grupo de custo",
        },
        "items": items,
    }


def _build_antecipacao_sheet_payload(df: pd.DataFrame, sheet_name: str, company_name: str, short_name: str) -> dict[str, Any]:
    index_column = _resolve_named_column(df, ["índice", "indice"])
    level_column = _resolve_named_column(df, ["nível societário", "nivel societario"])
    base_column = _resolve_named_column(df, ["antecipação mensal de distribuição de lucros", "antecipacao mensal de distribuicao de lucros"])
    quotas_column = _resolve_named_column(df, ["quotas de serviço", "quotas de servico"])
    adjustment_column = _resolve_named_column(df, ["ajuste mensal"])
    final_column = _resolve_named_column(df, ["antecipação mensal de distribuição de lucros final", "antecipacao mensal de distribuicao de lucros final"])

    rows: list[dict[str, Any]] = []
    totals = {
        "base": 0.0,
        "quotas": 0.0,
        "ajuste": 0.0,
        "final": 0.0,
    }

    for _, row in df.iterrows():
        level_value = row[level_column]
        if pd.isna(level_value) or not str(level_value).strip():
            continue

        index_value = _to_float(row[index_column])
        base_value = _to_float(row[base_column])
        quotas_value = _to_float(row[quotas_column])
        adjustment_value = _to_float(row[adjustment_column])
        final_value = _to_float(row[final_column])

        rows.append(
            {
                "index": int(round(index_value)),
                "level": str(level_value).strip(),
                "base": base_value,
                "quotas": int(round(quotas_value)),
                "adjustment": adjustment_value,
                "final": final_value,
            }
        )
        totals["base"] += base_value
        totals["quotas"] += quotas_value
        totals["ajuste"] += adjustment_value
        totals["final"] += final_value

    return {
        "company_name": company_name,
        "short_name": short_name,
        "sheet_name": sheet_name,
        "rows": rows,
        "row_count": len(rows),
        "totals": totals,
    }


@st.cache_data(show_spinner=False)
def load_antecipacao_lucros() -> dict[str, Any]:
    """Carrega as tabelas de antecipação de lucros para o menu hamburguer."""
    sheets = [
        ("Antecipação Lucros GAN", "Gondim Advogados", "GAN"),
        ("Antecipação Lucros GAA", "Gondim Gestão e Tecnologia", "GAA"),
    ]

    companies: list[dict[str, Any]] = []
    totals = {
        "companies": 0,
        "rows": 0,
        "base": 0.0,
        "quotas": 0.0,
        "ajuste": 0.0,
        "final": 0.0,
    }

    for sheet_name, company_name, short_name in sheets:
        df = _read_excel_sheet(str(INFO_FILE), sheet_name, header=0).dropna(how="all")
        payload = _build_antecipacao_sheet_payload(df, sheet_name, company_name, short_name)
        companies.append(payload)
        totals["companies"] += 1
        totals["rows"] += payload["row_count"]
        totals["base"] += payload["totals"]["base"]
        totals["quotas"] += payload["totals"]["quotas"]
        totals["ajuste"] += payload["totals"]["ajuste"]
        totals["final"] += payload["totals"]["final"]

    return {
        "title": "AJUSTE / ANTECIPAÇÃO MENSAL DE DISTRIBUIÇÃO DE LUCROS",
        "subtitle": "FEVEREIRO / 2026 - PAGAMENTO EM ABRIL / 2026",
        "source": INFO_FILE.name,
        "metrics": [
            {
                "label": "Empresas",
                "value": str(totals["companies"]),
                "caption": "painéis carregados",
            },
            {
                "label": "Sócios",
                "value": str(totals["rows"]),
                "caption": "linhas da planilha",
            },
            {
                "label": "Base mensal",
                "value": totals["base"],
                "caption": "antecipação bruta",
            },
            {
                "label": "Ajuste mensal",
                "value": totals["ajuste"],
                "caption": "efeito do rateio",
            },
            {
                "label": "Final projetado",
                "value": totals["final"],
                "caption": "valor consolidado",
            },
        ],
        "companies": companies,
        "totals": totals,
    }
