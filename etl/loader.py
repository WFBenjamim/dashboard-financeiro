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

from config.settings import (
    PROFIT_ADVANCE_ADJUSTMENT_PCT,
    PROFIT_ADVANCE_ADJUSTMENT_PER_QUOTA,
    PROFIT_ADVANCE_MONTHLY_RESULT,
    PROFIT_ADVANCE_PAYMENT,
    PROFIT_ADVANCE_REFERENCE,
    PROFIT_ADVANCE_TOTAL_ADJUSTMENT,
    PROFIT_ADVANCE_TOTAL_QUOTAS,
)
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
ANTECIPACAO_FILE = DATA_DIR / "Antecipação Lucros.xlsx"

MONTH_LABELS = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr", 
    5: "mai", 6: "jun", 7: "jul", 8: "ago", 
    9: "set", 10: "out", 11: "nov", 12: "dez"
}


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
    prefix = "-" if value < 0 else ""
    if amount >= 1_000_000_000:
        return f"R$ {prefix}{_format_compact_number(amount / 1_000_000_000, 1)} B"
    if amount >= 1_000_000:
        return f"R$ {prefix}{_format_compact_number(amount / 1_000_000, 2)} M"
    if amount >= 1_000:
        return f"R$ {prefix}{_format_compact_number(amount / 1_000, 1)} mil"
    return f"R$ {prefix}{amount:.0f}".replace(".", ",")


def _format_currency_full(value: float) -> str:
    return _format_currency(value)


def _format_currency_precise(value: float) -> str:
    sign = "-" if value < 0 else ""
    formatted = f"{abs(float(value)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {sign}{formatted}"


def _format_compact_number(value: float, decimals: int) -> str:
    text = f"{value:.{decimals}f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def _format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def _format_signed_percent(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{_format_percent(value * 100)}"


def _format_count(value: float) -> str:
    return str(int(round(float(value))))


def _format_plain_decimal(value: float, decimals: int = 2) -> str:
    return f"{float(value):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_months_label(months: list[int], year: int) -> str:
    if not months:
        return f"{year}"

    month_labels = [MONTH_LABELS.get(month, str(month)) for month in months]
    year_suffix = str(year)[-2:]
    if len(month_labels) == 1:
        return f"{month_labels[0]}/{year_suffix}"
    return f"{', '.join(month_labels[:-1])} e {month_labels[-1]}/{year_suffix}"


def _normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip().lower()


@st.cache_data(show_spinner=False)
def _load_dashboard_template(file_mtime_ns: int) -> dict[str, Any]:
    return json.loads(TEMPLATE_FILE.read_text(encoding="utf-8"))


def _is_date_in_period(col_val, ano, selected_months):
    """Verifica se a data do Excel pertence ao ano e meses selecionados."""
    if pd.isna(col_val):
        return False
    try:
        if isinstance(col_val, (int, float)):
            # Formato numérico do Excel
            d = pd.to_datetime(col_val, origin="1899-12-30", unit="D")
        else:
            d = pd.to_datetime(col_val)
        return d.year == ano and d.month in selected_months
    except Exception:
        return False


def _sum_row_for_period(df: pd.DataFrame, label: str, header_row: int, ano: int, selected_months: list[int]) -> float:
    expected = _normalize_text(label)
    for i in range(len(df)):
        if _normalize_text(df.iloc[i, 0]) == expected:
            return sum(
                _to_float(df.iloc[i, j])
                for j in range(1, len(df.columns))
                if _is_date_in_period(df.iloc[header_row, j], ano, selected_months)
            )
    return 0.0


def _get_row_total_value(df: pd.DataFrame, label: str) -> float:
    expected = _normalize_text(label)
    for i in range(len(df)):
        if _normalize_text(df.iloc[i, 0]) == expected:
            for j in range(13, 0, -1):
                value = _to_float(df.iloc[i, j])
                if value:
                    return value
    return 0.0


def _get_table_value_by_labels(
    df: pd.DataFrame,
    row_label: str,
    column_label: str,
    header_row: int = 2,
) -> float:
    expected_row = _normalize_text(row_label)
    expected_col = _normalize_text(column_label)
    column_index = None

    for j in range(len(df.columns)):
        if _normalize_text(df.iloc[header_row, j]) == expected_col:
            column_index = j
            break

    if column_index is None:
        return 0.0

    for i in range(header_row + 1, len(df)):
        if _normalize_text(df.iloc[i, 0]) == expected_row:
            return _to_float(df.iloc[i, column_index])

    return 0.0


def _get_comparativo_2025_period(df: pd.DataFrame, selected_months: list[int]) -> float:
    """Busca o Realizado 2025 no bloco Receita - Com Sucumbencia.

    A aba Comparativo 26-25 do arquivo atual nao possui colunas mensais; por isso
    usamos o total anual da linha Total - Gondim proporcional ao periodo filtrado.
    Se a planilha ganhar granularidade mensal no futuro, este ponto fica isolado.
    """
    title_row = None
    title_col = None
    for i in range(len(df)):
        for j in range(len(df.columns)):
            if _normalize_text(df.iloc[i, j]) == "receita - com sucumbencia":
                title_row = i
                title_col = j
                break
        if title_row is not None:
            break

    if title_row is None or title_col is None:
        return 0.0

    header_row = title_row + 1
    label_col = None
    value_col = None
    for j in range(title_col, len(df.columns)):
        header = _normalize_text(df.iloc[header_row, j])
        if header == "carteira":
            label_col = j
        elif header == "realizado 2025":
            value_col = j

    if label_col is None or value_col is None:
        return 0.0

    annual_total = 0.0
    for i in range(header_row + 1, len(df)):
        label = _normalize_text(df.iloc[i, label_col])
        if label == "total - gondim":
            annual_total = _to_float(df.iloc[i, value_col])
            break

    if not annual_total:
        values = []
        for i in range(header_row + 1, len(df)):
            label = _normalize_text(df.iloc[i, label_col])
            if not label or label.startswith("total"):
                continue
            values.append(_to_float(df.iloc[i, value_col]))
        annual_total = sum(values)

    month_count = len({month for month in selected_months if 1 <= month <= 12})
    return annual_total * (month_count / 12) if month_count else 0.0


def _share(value: float, total: float) -> str:
    return _format_percent((value / total * 100) if total else 0.0)


@st.cache_data(show_spinner=False)
def get_extracted_data(ano: int, selected_months: list[int], file_mtime_ns: int | None = None) -> dict:
    """Extrai todos os dados necessários usando mapeamento exato da planilha Orçamento."""
    _ = file_mtime_ns
    f = str(ORCAMENTO_FILE)
    
    # --- 1. KPI AN (Margens) & 2. KPI AN (Pessoas) ---
    df_kpi = pd.read_excel(f, sheet_name="KPI AN", header=None, engine="openpyxl").fillna("")
    
    # Localizar a coluna "TOTAL" (última coluna)
    col_total_idx = None
    for j in range(len(df_kpi.columns)):
        if "TOTAL" in str(df_kpi.iloc[4, j]).upper():
            col_total_idx = j
            break
            
    mo, ml, pessoas = 0.0, 0.0, 0.0
    receita_kpi = 0.0
    resultado_kpi = 0.0
    
    if col_total_idx is not None:
        for i in range(len(df_kpi)):
            lbl = _normalize_text(df_kpi.iloc[i, 0])
            if "margem operacional" in lbl:
                mo = _to_float(df_kpi.iloc[i, col_total_idx])
            elif lbl == "receita":
                receita_kpi = _to_float(df_kpi.iloc[i, col_total_idx])
            elif lbl == "resultado":
                resultado_kpi = _to_float(df_kpi.iloc[i, col_total_idx])
            elif "quantidade de profissionais" in lbl:
                pessoas = _to_float(df_kpi.iloc[i, col_total_idx])
        
        if receita_kpi > 0:
            ml = resultado_kpi / receita_kpi

    # --- 3. Resumo -> Receita Total ---
    df_resumo = pd.read_excel(f, sheet_name="Resumo", header=None, engine="openpyxl").fillna("")
    receita_total = 0.0
    header_row_resumo = 2 # Linha com as datas no Resumo
    
    for i in range(len(df_resumo)):
        if _normalize_text(df_resumo.iloc[i, 0]) == "receita":
            for j in range(1, len(df_resumo.columns)):
                if _is_date_in_period(df_resumo.iloc[header_row_resumo, j], ano, selected_months):
                    receita_total += _to_float(df_resumo.iloc[i, j])
            break

    total_despesas = _sum_row_for_period(df_resumo, "TOTAL DESPESAS", header_row_resumo, ano, selected_months)
    correspondentes = _get_row_total_value(df_resumo, "Correspondentes")
    socios_servico = 0.0
    clt = 0.0

    df_resumo_orc = pd.read_excel(f, sheet_name="Resumo Orç 2026", header=None, engine="openpyxl").fillna("")
    receita_orcada_anual = _get_table_value_by_labels(df_resumo_orc, "Total", "Receitas")
    pct_orcado = (receita_total / receita_orcada_anual) if receita_orcada_anual else 0.0

    receita_2025_periodo = 0.0
    try:
        df_comparativo = pd.read_excel(f, sheet_name="Comparativo 26-25", header=None, engine="openpyxl").fillna("")
        receita_2025_periodo = _get_comparativo_2025_period(df_comparativo, selected_months)
    except Exception as exc:
        print(f"[ETL] Nao foi possivel ler Comparativo 26-25: {exc}")
    variacao_yoy = ((receita_total - receita_2025_periodo) / receita_2025_periodo) if receita_2025_periodo else 0.0

    # --- 4 & 5. Receita -> Faturamento por Cliente & Sucumbência ---
    df_receita = pd.read_excel(f, sheet_name="Receita", header=None, engine="openpyxl").fillna("")
    clientes = []
    sucumb = 0.0
    
    current_client = ""
    header_row_rec = -1
    
    for i in range(len(df_receita)):
        val0 = str(df_receita.iloc[i, 0]).strip()
        
        # Detecta início de bloco de cliente
        if "- FATURAMENTO" in val0.upper() and val0.upper() != "FATURAMENTO":
            current_client = val0.upper().replace("- FATURAMENTO", "").strip()
            # Procurar linha com datas logo abaixo
            for h in range(i+1, min(i+10, len(df_receita))):
                if df_receita.iloc[h, 1] != "" and df_receita.iloc[h, 1] != 0:
                    try:
                        if _is_date_in_period(df_receita.iloc[h, 1], ano, selected_months) or True:
                            header_row_rec = h
                            break
                    except:
                        pass
        
        # Extrai SUCUMBÊNCIAS daquele bloco
        if "SUCUMB" in val0.upper() and header_row_rec != -1:
            for j in range(1, len(df_receita.columns)):
                if _is_date_in_period(df_receita.iloc[header_row_rec, j], ano, selected_months):
                    sucumb += _to_float(df_receita.iloc[i, j])
                    
        # Extrai o TOTAL daquele bloco
        if val0.upper() == "TOTAL" and current_client and header_row_rec != -1:
            cliente_total = 0.0
            for j in range(1, len(df_receita.columns)):
                if _is_date_in_period(df_receita.iloc[header_row_rec, j], ano, selected_months):
                    cliente_total += _to_float(df_receita.iloc[i, j])
                    
            if cliente_total > 0 and current_client not in ["INTERCOMPANY"]:
                clientes.append((current_client, cliente_total))
            
            # Reseta as variáveis após fechar o bloco do cliente
            current_client = ""
            header_row_rec = -1

    clientes.sort(key=lambda x: x[1], reverse=True)
    top_5 = clientes[:5]
    outros = sum(x[1] for x in clientes[5:])
    
    ranking = [{"name": n, "value": _format_currency_full(v)} for n, v in top_5]
    if outros > 0:
        ranking.append({"name": "Outros", "value": _format_currency_full(outros)})

    # --- 6. Impostos -> Total ---
    df_impostos = pd.read_excel(f, sheet_name="Impostos", header=None, engine="openpyxl").fillna("")
    impostos = 0.0
    header_row_imp = 2
    
    for i in range(len(df_impostos)):
        if "impostos total" in _normalize_text(df_impostos.iloc[i, 0]):
            for j in range(1, len(df_impostos.columns)):
                if _is_date_in_period(df_impostos.iloc[header_row_imp, j], ano, selected_months):
                    impostos += _to_float(df_impostos.iloc[i, j])
            break

    outras_despesas = max(total_despesas - socios_servico - clt - correspondentes, 0.0)
    total_card_costs = total_despesas + impostos
    item_sum = impostos + socios_servico + clt + correspondentes + outras_despesas
    diff = total_card_costs - item_sum
    if abs(diff) > 0.01:
        print(f"[ETL] Diferença no card Estrutura de Custos: {diff:.2f}")
    
    return {
        "mo": mo,
        "ml": ml,
        "pessoas": pessoas,
        "receita_total": receita_total,
        "receita_orcada": receita_orcada_anual,
        "pct_orcado": pct_orcado,
        "receita_2025_periodo": receita_2025_periodo,
        "variacao_yoy": variacao_yoy,
        "sucumb": sucumb,
        "impostos": impostos,
        "top_5": ranking,
        "total_despesas": total_despesas,
        "socios_servico": socios_servico,
        "clt": clt,
        "correspondentes": correspondentes,
        "outras_despesas": outras_despesas,
        "clientes": clientes
    }


def get_dashboard_data(mes: int, ano: int, selected_months: list[int] | None = None) -> dict[str, Any]:
    """Orquestra o ETL a partir do Orçamento.xlsx e devolve a estrutura aninhada esperada pela interface."""
    mes = max(1, min(int(mes), 12))
    ano = int(ano)
    if not selected_months:
        selected_months = list(range(1, mes + 1))
        
    template = deepcopy(_load_dashboard_template(TEMPLATE_FILE.stat().st_mtime_ns))
    
    data = get_extracted_data(ano, selected_months, ORCAMENTO_FILE.stat().st_mtime_ns)
    
    receita_total = data["receita_total"]
    receita_orcada = data["receita_orcada"]
    pct_orcado = data["pct_orcado"]
    receita_2025_periodo = data["receita_2025_periodo"]
    variacao_yoy = data["variacao_yoy"]
    sucumb = data["sucumb"]
    contratuais = receita_total - sucumb if receita_total > sucumb else receita_total
    
    template["header"]["subtitle"] = f"Período acumulado: {_format_months_label(selected_months, ano)} • dados do Orçamento.xlsx"
    
    template["revenue_mix"] = {
        "icon": "💰",
        "title": "Mix de Receitas",
        "value": _format_currency(receita_total),
        "pct_orcado": pct_orcado,
        "receita_orcada": receita_orcada,
        "receita_2025_periodo": receita_2025_periodo,
        "variacao_yoy": variacao_yoy,
        "subtitle": f"{_format_percent(pct_orcado * 100)} do orçado anual • 2026  /  {_format_signed_percent(variacao_yoy)} vs 2025",
        "comparison_pct": 0,
        "rows": [
            {
                "label": "Contratuais", 
                "value": _format_currency(contratuais), 
                "share": _format_percent((contratuais/receita_total*100) if receita_total else 0)
            },
            {
                "label": "Sucumbência", 
                "value": _format_currency(sucumb), 
                "share": _format_percent((sucumb/receita_total*100) if receita_total else 0)
            }
        ],
        "expansions": [
            {
                "title": "Contratuais", 
                "items": [{"name": item["name"], "value": item["value"]} for item in data["top_5"][:5]]
            },
            {
                "title": "Sucumbência", 
                "items": []
            }
        ]
    }
    
    template["cost_structure"] = {
        "icon": "📉",
        "title": "Estrutura de Custos",
        "value": _format_currency(data["total_despesas"] + data["impostos"]),
        "subtitle": "Impostos e Despesas operacionais estimadas",
        "highlight": {
            "label": "Impostos", 
            "value": _share(data["impostos"], data["total_despesas"] + data["impostos"]), 
            "caption": "total de impostos no período"
        },
        "items": [
            {
                "label": "Impostos", 
                "value": _format_currency(data["impostos"]), 
                "share": _share(data["impostos"], data["total_despesas"] + data["impostos"]), 
                "details": []
            },
            {
                "label": "Sócios de Serviço", 
                "value": _format_currency(data["socios_servico"]), 
                "share": _share(data["socios_servico"], data["total_despesas"] + data["impostos"]), 
                "details": []
            },
            {
                "label": "CLT", 
                "value": _format_currency(data["clt"]), 
                "share": _share(data["clt"], data["total_despesas"] + data["impostos"]), 
                "details": []
            },
            {
                "label": "Correspondentes", 
                "value": _format_currency(data["correspondentes"]), 
                "share": _share(data["correspondentes"], data["total_despesas"] + data["impostos"]), 
                "details": []
            },
            {
                "label": "Outras Despesas", 
                "value": _format_currency(data["outras_despesas"]), 
                "share": _share(data["outras_despesas"], data["total_despesas"] + data["impostos"]), 
                "details": []
            }
        ]
    }
    
    template["net_result"] = {
        "icon": "📊",
        "title": "Resultado Líquido",
        "value": _format_currency(receita_total * data["ml"]),
        "subtitle": "Projeção via Margem Líquida"
    }
    
    template["margins"] = {
        "icon": "📈",
        "title": "Margens",
        "value": _format_percent(data["mo"] * 100),
        "subtitle": "Indicadores baseados no KPI AN",
        "metrics": [
            {
                "label": "Margem Operacional", 
                "value": _format_percent(data["mo"] * 100), 
                "caption": "KPI AN"
            },
            {
                "label": "Margem Líquida", 
                "value": _format_percent(data["ml"] * 100), 
                "caption": "KPI AN"
            }
        ]
    }
    
    template["people"] = {
        "icon": "👥",
        "title": "Pessoas",
        "value": _format_count(data["pessoas"]),
        "subtitle": "Quantidade de profissionais (KPI AN)",
        "rows": []
    }
    
    template["top_clients"] = {
        "icon": "🏆",
        "title": "Top 5 Clientes",
        "subtitle": f"Faturamento em {_format_months_label(selected_months, ano)}",
        "ranking": data["top_5"]
    }
    
    template["insights"] = []
    template["technical_analysis"] = {
        "title": "Análise técnica",
        "paragraphs": []
    }
    
    metrics = build_dashboard_metrics(template)
    template["technical_analysis"] = generate_technical_analysis(template, metrics=metrics)
    template["insights"] = generate_insights(template, metrics=metrics)
    return template


def get_dashboard_content(
    selected_year: int | None = None,
    selected_months: list[int] | None = None,
) -> dict[str, Any]:
    """Carrega o dashboard usando o período selecionado como padrão."""
    today = date.today()
    ano = int(selected_year or today.year)
    months = selected_months if selected_months is not None else list(range(1, today.month + 1))
    return get_dashboard_data(max(months) if months else today.month, ano, selected_months=months)


def load_antecipacao_lucros() -> dict[str, Any]:
    """Carrega a aba de ajuste/antecipação mensal de lucros."""
    if not ANTECIPACAO_FILE.exists():
        return {
            "title": "AJUSTE / ANTECIPAÇÃO MENSAL DE DISTRIBUIÇÃO DE LUCROS",
            "subtitle": "Planilha de antecipação não encontrada.",
            "source": ANTECIPACAO_FILE.name,
            "metrics": [],
            "companies": [],
            "totals": {}
        }

    companies_config = [
        {
            "sheet_name": "Antecipação Lucros GAN",
            "short_name": "GAN",
            "company_name": "GONDIM ADVOGADOS",
        },
        {
            "sheet_name": "Antecipação Lucros GAA",
            "fallback_sheet_name": "Antecipação Lucros GAT",
            "short_name": "GAA",
            "company_name": "GONDIM GESTÃO E TECNOLOGIA",
        },
    ]

    workbook = pd.ExcelFile(ANTECIPACAO_FILE)
    companies = []
    total_adjustment = 0.0
    total_quotas = 0.0
    total_final = 0.0

    for config in companies_config:
        sheet_name = config["sheet_name"]
        if sheet_name not in workbook.sheet_names:
            sheet_name = config.get("fallback_sheet_name", sheet_name)
        if sheet_name not in workbook.sheet_names:
            continue

        df = pd.read_excel(ANTECIPACAO_FILE, sheet_name=sheet_name, header=0, engine="openpyxl").fillna("")
        rows = []
        company_base = 0.0
        company_adjustment = 0.0
        company_final = 0.0
        company_quotas = 0.0

        for index, row in df.iterrows():
            level = str(row.iloc[1]).strip()
            if not level:
                continue

            base = _to_float(row.iloc[2])
            quotas = _to_float(row.iloc[3])
            adjustment = _to_float(row.iloc[4])
            final = _to_float(row.iloc[5])

            company_base += base
            company_quotas += quotas
            company_adjustment += adjustment
            company_final += final

            rows.append({
                "index": int(index) + 1,
                "level": level,
                "base": base,
                "quotas": quotas,
                "adjustment": adjustment,
                "final": final,
                "base_formatted": _format_currency(base),
                "adjustment_formatted": _format_currency(adjustment),
                "final_formatted": _format_currency(final),
                "quotas_formatted": _format_plain_decimal(quotas),
            })

        total_quotas += company_quotas
        total_adjustment += company_adjustment
        total_final += company_final

        companies.append({
            **config,
            "sheet_name": sheet_name,
            "rows": rows,
            "totals": {
                "base": company_base,
                "quotas": company_quotas,
                "adjustment": company_adjustment,
                "final": company_final,
                "base_formatted": _format_currency(company_base),
                "adjustment_formatted": _format_currency(company_adjustment),
                "final_formatted": _format_currency(company_final),
                "quotas_formatted": _format_plain_decimal(company_quotas),
            }
        })

    summary_result = PROFIT_ADVANCE_MONTHLY_RESULT
    summary_adjustment_pct = PROFIT_ADVANCE_ADJUSTMENT_PCT
    summary_adjustment = PROFIT_ADVANCE_TOTAL_ADJUSTMENT
    summary_quotas = PROFIT_ADVANCE_TOTAL_QUOTAS
    summary_adjustment_per_quota = PROFIT_ADVANCE_ADJUSTMENT_PER_QUOTA

    return {
        "title": "AJUSTE / ANTECIPAÇÃO MENSAL DE DISTRIBUIÇÃO DE LUCROS",
        "subtitle": f"Referência: {PROFIT_ADVANCE_REFERENCE} • Pagamento: {PROFIT_ADVANCE_PAYMENT}",
        "source": ANTECIPACAO_FILE.name,
        "metrics": [
            {"label": "Resultado Mensal", "value": _format_currency_precise(summary_result), "raw_value": summary_result},
            {"label": "% Ajuste Mensal", "value": _format_percent(summary_adjustment_pct), "raw_value": summary_adjustment_pct},
            {"label": "Total de Ajuste", "value": _format_currency_precise(summary_adjustment), "raw_value": summary_adjustment},
            {"label": "Total de Quotas", "value": _format_plain_decimal(summary_quotas), "raw_value": summary_quotas},
            {"label": "Ajuste por Quota", "value": _format_plain_decimal(summary_adjustment_per_quota, 4), "raw_value": summary_adjustment_per_quota},
        ],
        "companies": companies,
        "totals": {
            "result": summary_result,
            "adjustment_pct": summary_adjustment_pct,
            "adjustment": summary_adjustment,
            "quotas": summary_quotas,
            "adjustment_per_quota": summary_adjustment_per_quota,
            "table_final": total_final,
            "table_adjustment": total_adjustment,
            "table_quotas": total_quotas,
        }
    }
