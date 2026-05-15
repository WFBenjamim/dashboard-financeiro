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
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"    [ERRO] {exc}")


def generate_evolution_jsons() -> None:
    df = pd.read_excel(
        INFORMACOES_GERENCIAIS_FILE,
        sheet_name="TOTAIS  20 E 21",
        header=0,
        index_col=0,
        engine="openpyxl",
    )

    def excel_date(value):
        if isinstance(value, datetime):
            return value
        try:
            if pd.isna(value):
                return None
            return datetime(1899, 12, 30) + timedelta(days=int(value))
        except Exception:
            return None

    cols_parsed = [excel_date(col) for col in df.columns]
    df.columns = cols_parsed
    df = df[[col for col in df.columns if col is not None]]

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

    def to_number(value) -> float:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)

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
