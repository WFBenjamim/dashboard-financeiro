"""
generate_static_data.py
-----------------------
Gera arquivos JSON estaticos com os dados do dashboard para todas as
combinacoes de meses disponiveis. Os arquivos sao salvos em
public/data/ e consumidos pelo app Next.js.

Como usar:
    python scripts/generate_static_data.py
"""

import itertools
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# Garante que o root do projeto esta no sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from etl.loader import get_dashboard_content, load_antecipacao_lucros  # noqa: E402

OUTPUT_DIR = PROJECT_ROOT / "public" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ORCAMENTO_FILE = PROJECT_ROOT / "data" / "Orçamento.xlsx"
INFORMACOES_GERENCIAIS_FILE = PROJECT_ROOT / "data" / "INFORMAÇÕES GERENCIAIS.xlsx"

# ─── Configuracao ─────────────────────────────────────────────────────────────
YEAR = 2026
# Apenas os meses que tem dados reais na planilha.
# Ajuste conforme os meses disponiveis no Orcamento.xlsx.
AVAILABLE_MONTHS = [1, 2, 3]
# ──────────────────────────────────────────────────────────────────────────────


def month_file_key(months: list) -> str:
    """Converte lista de meses em chave de arquivo, ex: [1,2,3] -> '1-2-3'."""
    return "-".join(str(m) for m in sorted(months))


def excel_date(value):
    if isinstance(value, datetime):
        return value
    try:
        if pd.isna(value):
            return None
        return datetime(1899, 12, 30) + timedelta(days=int(value))
    except Exception:
        return None


def to_number(value) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return float(value)


def load_totais_df() -> pd.DataFrame:
    df = pd.read_excel(
        INFORMACOES_GERENCIAIS_FILE,
        sheet_name="TOTAIS  20 E 21",
        header=0,
        index_col=0,
        engine="openpyxl",
    )
    df.columns = [excel_date(col) for col in df.columns]
    return df[[col for col in df.columns if col is not None]]


def build_cost_subtitle(selected_months: list[int], year: int = YEAR) -> str:
    variacao_custos = calculate_cost_variation(selected_months, year)
    if variacao_custos is None:
        return ""

    return f"{variacao_custos:+.1%}".replace(".", ",") + f" vs {year - 1}"


def calculate_cost_variation(selected_months: list[int], year: int = YEAR) -> float | None:
    df = load_totais_df()
    despesas_label = "CUSTOS E DESPESAS SEM INTERCOMPANY"
    despesas = df.loc[despesas_label]

    despesas_atual = sum(
        to_number(despesas.get(col, 0))
        for col in df.columns
        if col.year == year and col.month in selected_months
    )
    despesas_anterior = sum(
        to_number(despesas.get(col, 0))
        for col in df.columns
        if col.year == year - 1 and col.month in selected_months
    )

    if not despesas_anterior:
        return None

    return (despesas_atual - despesas_anterior) / despesas_anterior


def load_budget_totals() -> dict[str, float]:
    df_orc = pd.read_excel(
        ORCAMENTO_FILE,
        sheet_name="Resumo Orç 2026",
        header=2,
        engine="openpyxl",
    ).fillna("")
    total_row = df_orc[df_orc.iloc[:, 0].astype(str).str.strip() == "Total"]
    if total_row.empty:
        return {"receita": 0.0, "despesas": 0.0, "ml": 0.0}

    row = total_row.iloc[0]
    return {
        "receita": to_number(row.get("Receitas", 0)),
        "despesas": to_number(row.get("Despesas", 0)),
        "ml": to_number(row.get("ML", 0)),
    }


def _month_columns_from_section(df: pd.DataFrame, section_label: str, selected_months: list[int]) -> tuple[int, list[int]]:
    month_labels = {
        1: "jan", 2: "fev", 3: "mar", 4: "abr",
        5: "mai", 6: "jun", 7: "jul", 8: "ago",
        9: "set", 10: "out", 11: "nov", 12: "dez",
    }
    selected_labels = {month_labels[month] for month in selected_months}

    for row_index in range(len(df)):
        label = str(df.iloc[row_index, 0]).strip().lower()
        if label == section_label.lower():
            columns = [
                column
                for column in range(1, len(df.columns))
                if str(df.iloc[row_index, column]).strip().lower() in selected_labels
            ]
            return row_index, columns

    return -1, []


def _sum_result_row(df: pd.DataFrame, header_row: int, columns: list[int]) -> float:
    if header_row < 0 or not columns:
        return 0.0

    for row_index in range(header_row + 1, len(df)):
        label = str(df.iloc[row_index, 0]).strip().lower()
        if label == "resultado":
            return sum(to_number(df.iloc[row_index, column]) for column in columns)
        if label in {"sucumbência", "sucumbencia", "total geral"}:
            break

    return 0.0


def enrich_net_result(data: dict, selected_months: list[int], year: int = YEAR) -> None:
    budget_totals = load_budget_totals()
    ml_orcado_anual = budget_totals["ml"]
    resultado_orcado_periodo = ml_orcado_anual / 12 * len(selected_months) if ml_orcado_anual else 0.0

    df_res = pd.read_excel(
        ORCAMENTO_FILE,
        sheet_name="Resultado - Sucumb - Sem Sucumb",
        header=None,
        engine="openpyxl",
    ).fillna("")
    total_header_row, total_columns = _month_columns_from_section(df_res, "Total Geral", selected_months)
    sem_sucumb_header_row, sem_sucumb_columns = _month_columns_from_section(df_res, "Sem Sucumbência", selected_months)
    resultado_real = _sum_result_row(df_res, total_header_row, total_columns)
    resultado_sem_sucumb = _sum_result_row(df_res, sem_sucumb_header_row, sem_sucumb_columns)

    df_tot = load_totais_df()
    resultado = df_tot.loc["RESULTADO SEM INTERCOMPANY"]
    resultado_2025 = sum(
        to_number(resultado.get(column, 0))
        for column in df_tot.columns
        if column.year == year - 1 and column.month in selected_months
    )

    pct_vs_orcado = resultado_real / resultado_orcado_periodo if resultado_orcado_periodo else 0.0
    variacao_2025 = (resultado_real - resultado_2025) / abs(resultado_2025) if resultado_2025 else 0.0
    pct_ano = resultado_real / ml_orcado_anual if ml_orcado_anual else 0.0
    resultado_operacional = data["revenue_mix"]["value"] - (
        data["cost_structure"]["total"] - data["cost_structure"]["impostos"]
    )

    data["net_result"].update({
        "value": resultado_real,
        "sem_sucumbencia": resultado_sem_sucumb,
        "resultado_orcado": resultado_orcado_periodo,
        "resultado_2025": resultado_2025,
        "pct_vs_orcado": pct_vs_orcado,
        "variacao_2025": variacao_2025,
        "pct_ano": pct_ano,
        "resultado_operacional": resultado_operacional,
    })


def enrich_revenue_and_cost_metrics(data: dict, selected_months: list[int], year: int = YEAR) -> None:
    budget_totals = load_budget_totals()
    cost_variation = calculate_cost_variation(selected_months, year)
    custo_orcado_anual = budget_totals["despesas"]
    cost_total = data["cost_structure"]["total"]

    data["revenue_mix"].update({
        "receita_orcada_anual": budget_totals["receita"] or data["revenue_mix"].get("receita_orcada", 0),
        "variacao_2025": data["revenue_mix"].get("variacao_yoy", 0),
    })

    data["cost_structure"].update({
        "custo_orcado_anual": custo_orcado_anual,
        "pct_orcado_custos": (
            cost_total / custo_orcado_anual * (12 / len(selected_months))
            if custo_orcado_anual and selected_months
            else 0.0
        ),
        "variacao_2025": cost_variation if cost_variation is not None else data["cost_structure"].get("variacao_custos_yoy", 0),
    })


def generate_dashboard_jsons() -> None:
    print(f"\n[Saida] Salvando em: {OUTPUT_DIR}\n")

    all_combinations = []
    for r in range(1, len(AVAILABLE_MONTHS) + 1):
        for combo in itertools.combinations(AVAILABLE_MONTHS, r):
            all_combinations.append(list(combo))

    for months in all_combinations:
        key = month_file_key(months)
        filename = OUTPUT_DIR / f"dashboard_{YEAR}_{key}.json"
        print(f"  -> dashboard_{YEAR}_{key}.json  (meses: {months})")
        try:
            data = get_dashboard_content(YEAR, months)
            cost_subtitle = build_cost_subtitle(months, YEAR)
            data["cost_subtitle"] = cost_subtitle
            data["cost_structure"]["subtitle"] = cost_subtitle
            data["cost_structure"]["cost_subtitle"] = cost_subtitle
            enrich_net_result(data, months, YEAR)
            enrich_revenue_and_cost_metrics(data, months, YEAR)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"    [ERRO] {exc}")


def generate_evolution_jsons() -> None:
    df = load_totais_df()

    receita_label = "RECEITA SEM INTERCOMPANY"
    despesas_label = "CUSTOS E DESPESAS SEM INTERCOMPANY"
    resultado_label = "RESULTADO SEM INTERCOMPANY"

    receita = df.loc[receita_label]
    despesas = df.loc[despesas_label]
    resultado = df.loc[resultado_label]

    month_labels = {
        1: "jan", 2: "fev", 3: "mar", 4: "abr",
        5: "mai", 6: "jun", 7: "jul", 8: "ago",
        9: "set", 10: "out", 11: "nov", 12: "dez",
    }

    monthly = []
    for col in df.columns:
        monthly.append({
            "month": f"{month_labels[col.month]}/{col.strftime('%y')}",
            "year": col.year,
            "month_num": col.month,
            "receita": round(to_number(receita.get(col, 0)), 2),
            "despesa": round(to_number(despesas.get(col, 0)), 2),
            "resultado": round(to_number(resultado.get(col, 0)), 2),
        })

    monthly_file = OUTPUT_DIR / "evolution_monthly.json"
    print("  -> evolution_monthly.json")
    with open(monthly_file, "w", encoding="utf-8") as f:
        json.dump(monthly, f, ensure_ascii=False, indent=2)

    annual_data = {}
    for col in df.columns:
        year = col.year
        if year not in annual_data:
            annual_data[year] = {"receita": 0.0, "despesa": 0.0, "resultado": 0.0}
        annual_data[year]["receita"] += to_number(receita.get(col, 0))
        annual_data[year]["despesa"] += to_number(despesas.get(col, 0))
        annual_data[year]["resultado"] += to_number(resultado.get(col, 0))

    annual = [
        {
            "year": year,
            "receita": round(values["receita"], 2),
            "despesa": round(values["despesa"], 2),
            "resultado": round(values["resultado"], 2),
        }
        for year, values in sorted(annual_data.items())
    ]

    annual_file = OUTPUT_DIR / "evolution_annual.json"
    print("  -> evolution_annual.json")
    with open(annual_file, "w", encoding="utf-8") as f:
        json.dump(annual, f, ensure_ascii=False, indent=2)


def generate_profit_advance_json() -> None:
    filename = OUTPUT_DIR / "profit_advance.json"
    print("  -> profit_advance.json")
    try:
        data = load_antecipacao_lucros()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"    [ERRO] {exc}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Gerador de Dados Estaticos - Dashboard Financeiro")
    print("=" * 60)

    print("\n[1/3] Gerando dados do dashboard por periodo...")
    generate_dashboard_jsons()

    print("\n[2/3] Gerando dados de evolucao...")
    generate_evolution_jsons()

    print("\n[3/3] Gerando dados de antecipacao de lucros...")
    generate_profit_advance_json()

    print("\n[OK] Concluido! Arquivos salvos em public/data/")
