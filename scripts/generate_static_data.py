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
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import openpyxl

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
AVAILABLE_MONTHS = [1, 2, 3, 4]
# ──────────────────────────────────────────────────────────────────────────────


def month_file_key(months: list) -> str:
    """Converte lista de meses em chave de arquivo, ex: [1,2,3] -> '1-2-3'."""
    return "-".join(str(m) for m in sorted(months))


def _real_number(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if value is None:
        return 0.0
    text = str(value)
    digits = "".join(ch for ch in text if ch.isdigit() or ch in ",.-")
    if not digits:
        return 0.0
    try:
        return float(digits.replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def _has_existing_real_data(data: dict) -> bool:
    revenue = _real_number(data.get("revenue_mix", {}).get("value"))
    result = _real_number(data.get("net_result", {}).get("value"))
    expansions = data.get("revenue_mix", {}).get("expansions") or [{}]
    top_clients = expansions[0].get("items", [])
    return abs(revenue) > 0.01 or abs(result) > 0.01 or bool(top_clients)


def _is_suspect_real_data(data: dict) -> bool:
    data_quality = data.get("dataQuality", {})
    if data_quality.get("hasSuspectRealData"):
        return True

    revenue_mix = data.get("revenue_mix", {})
    cost_structure = data.get("cost_structure", {})
    net_result = data.get("net_result", {})
    budget = data.get("budget", {})
    expansions = revenue_mix.get("expansions") or [{}]
    top_clients = expansions[0].get("items", [])

    real_values_zero = (
        abs(_real_number(revenue_mix.get("value"))) < 0.01
        and abs(_real_number(net_result.get("value"))) < 0.01
        and abs(_real_number(cost_structure.get("total"))) < 0.01
    )
    revenue_breakdown_zero = (
        abs(_real_number(revenue_mix.get("contratual"))) < 0.01
        and abs(_real_number(revenue_mix.get("sucumbencia"))) < 0.01
        and abs(_real_number(revenue_mix.get("outras"))) < 0.01
        and not top_clients
    )
    has_period_budget = any(
        abs(_real_number(budget.get(key))) > 0.01
        for key in ("revenue", "costs", "result")
    )
    return real_values_zero and revenue_breakdown_zero and has_period_budget


def write_dashboard_json_safely(filename: Path, data: dict) -> bool:
    if _is_suspect_real_data(data) and filename.exists():
        try:
            existing = json.loads(filename.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}

        if _has_existing_real_data(existing):
            suspect_file = filename.with_name(f"{filename.stem}.suspect.json")
            suspect_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(
                "    [AVISO] Dados reais suspeitos/zerados. "
                f"Preservado {filename.name}; diagnostico salvo em {suspect_file.name}."
            )
            return False

    filename.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


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


def normalize_label(value) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return " ".join(text.lower().split())


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


def sum_totais_row(df: pd.DataFrame, label: str, columns: list[datetime]) -> float:
    expected = normalize_label(label)
    for row_label, row in df.iterrows():
        if normalize_label(row_label) == expected:
            return sum(to_number(row.get(col, 0)) for col in columns)
    return 0.0


def load_totais(selected_months: list[int], year: int = YEAR) -> dict[str, float]:
    wb = openpyxl.load_workbook(
        INFORMACOES_GERENCIAIS_FILE,
        read_only=True,
        data_only=True,
    )
    ws = wb["TOTAIS  20 E 21"]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]

    period_cols = []
    previous_cols = []
    for index, header_value in enumerate(header):
        if not hasattr(header_value, "year"):
            continue
        if header_value.year == year and header_value.month in selected_months:
            period_cols.append(index)
        if header_value.year == year - 1 and header_value.month in selected_months:
            previous_cols.append(index)

    print(f"Periodo selecionado {year} meses {selected_months}:")
    print(f"  Colunas {year}: {[header[index].strftime('%b/%Y') for index in period_cols]}")
    print(f"  Colunas {year - 1}: {[header[index].strftime('%b/%Y') for index in previous_cols]}")

    def sum_row(label: str, columns: list[int]) -> float:
        expected = normalize_label(label)
        for row in rows[1:]:
            if normalize_label(row[0]) == expected:
                values = [row[index] for index in columns if row[index] not in (None, "", "-")]
                return sum(float(value) for value in values if isinstance(value, (int, float)))
        return 0.0

    receita = sum_row("RECEITA", period_cols)
    custos = sum_row("CUSTOS E DESPESAS", period_cols)
    resultado = sum_row("RESULTADO IG", period_cols)
    impostos = sum_row("IMPOSTOS", period_cols)
    sucumbencia = sum_row("SUCUMBENCIA", period_cols)
    receita_2025 = sum_row("RECEITA", previous_cols)
    custos_2025 = sum_row("CUSTOS E DESPESAS", previous_cols)
    resultado_2025 = sum_row("RESULTADO IG", previous_cols)
    resultado_sem_sucumbencia = sum_row("RESULTADO SEM SUCUMBENCIAS", period_cols)

    return {
        "receita": receita,
        "custos": custos,
        "resultado": resultado,
        "impostos": impostos,
        "sucumbencia": sucumbencia,
        "receita_2025": receita_2025,
        "custos_2025": custos_2025,
        "resultado_2025": resultado_2025,
        "resultado_sem_sucumbencia": resultado_sem_sucumbencia,
        "variacao_receita": (receita - receita_2025) / receita_2025 if receita_2025 else 0.0,
        "variacao_custos": (custos - custos_2025) / custos_2025 if custos_2025 else 0.0,
    }


def build_cost_subtitle(selected_months: list[int], year: int = YEAR) -> str:
    variacao_custos = calculate_cost_variation(selected_months, year)
    if variacao_custos is None:
        return ""

    return f"{variacao_custos:+.1%}".replace(".", ",") + f" vs {year - 1}"


def calculate_cost_variation(selected_months: list[int], year: int = YEAR) -> float | None:
    df = load_totais_df()
    despesas_label = "custos e despesas"

    despesas_atual = sum_totais_row(
        df,
        despesas_label,
        [col for col in df.columns if col.year == year and col.month in selected_months],
    )
    despesas_anterior = sum_totais_row(
        df,
        despesas_label,
        [col for col in df.columns if col.year == year - 1 and col.month in selected_months],
    )

    if not despesas_anterior:
        return None

    return (despesas_atual - despesas_anterior) / despesas_anterior


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
    totais = load_totais(selected_months, year)
    budget = data.get("budget", {})
    resultado_orcado_periodo = float(budget.get("result") or data.get("net_result", {}).get("resultado_orcado") or 0.0)
    period_months = len(selected_months)

    resultado_real = totais["resultado"]
    resultado_sem_sucumb = totais["resultado_sem_sucumbencia"]

    resultado_2025 = totais["resultado_2025"]

    pct_vs_orcado = resultado_real / resultado_orcado_periodo if resultado_orcado_periodo else 0.0
    variacao_2025 = (resultado_real - resultado_2025) / abs(resultado_2025) if resultado_2025 else 0.0
    pct_ano = 0.0
    resultado_operacional = data["revenue_mix"]["value"] - (
        data["cost_structure"]["total"] - data["cost_structure"]["impostos"]
    )

    data["net_result"].update({
        "value": resultado_real,
        "sem_sucumbencia": resultado_sem_sucumb,
        "resultado_orcado_anual": resultado_orcado_periodo,
        "resultado_orcado": resultado_orcado_periodo,
        "meta_periodo_resultado": resultado_orcado_periodo,
        "meta_periodo_meses": period_months,
        "resultado_2025": resultado_2025,
        "pct_vs_orcado": pct_vs_orcado,
        "variacao_2025": variacao_2025,
        "pct_ano": pct_ano,
        "resultado_operacional": resultado_operacional,
    })


def enrich_revenue_and_cost_metrics(data: dict, selected_months: list[int], year: int = YEAR) -> None:
    budget = data.get("budget", {})
    cost_variation = calculate_cost_variation(selected_months, year)
    period_months = len(selected_months)
    meta_periodo_receita = float(budget.get("revenue") or data["revenue_mix"].get("meta_periodo_receita", 0))
    meta_periodo_custos = float(budget.get("costs") or data["cost_structure"].get("meta_periodo_custos", 0))
    cost_total = data["cost_structure"]["total"]

    data["revenue_mix"].update({
        "receita_orcada_anual": meta_periodo_receita,
        "receita_orcada_periodo": meta_periodo_receita,
        "meta_periodo_receita": meta_periodo_receita,
        "meta_periodo_meses": period_months,
        "pct_orcado": data["revenue_mix"]["value"] / meta_periodo_receita if meta_periodo_receita else 0.0,
        "variacao_2025": data["revenue_mix"].get("variacao_yoy", 0),
    })

    data["cost_structure"].update({
        "custo_orcado_anual": meta_periodo_custos,
        "custo_orcado_periodo": meta_periodo_custos,
        "meta_periodo_custos": meta_periodo_custos,
        "meta_periodo_meses": period_months,
        "pct_orcado_custos": cost_total / meta_periodo_custos if meta_periodo_custos else 0.0,
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
            write_dashboard_json_safely(filename, data)
        except Exception as exc:
            print(f"    [ERRO] {exc}")


def generate_evolution_jsons() -> None:
    df = load_totais_df()

    receita = next(row for row_label, row in df.iterrows() if normalize_label(row_label) == "receita")
    despesas = next(row for row_label, row in df.iterrows() if normalize_label(row_label) == "custos e despesas")
    resultado = next(row for row_label, row in df.iterrows() if normalize_label(row_label) == "resultado ig")

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
