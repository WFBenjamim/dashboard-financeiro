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
from pathlib import Path

# Garante que o root do projeto esta no sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from etl.loader import get_dashboard_content, load_antecipacao_lucros  # noqa: E402

OUTPUT_DIR = PROJECT_ROOT / "public" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
    # Dados de evolucao sao estaticos (definidos em main.py)
    annual = {
        "view": "annual",
        "title": "Evolucao Anual: Receita vs Despesa vs Resultado",
        "unit": "R$ Milhoes",
        "data": [
            {"label": "2022", "receita": 5.8, "despesa": 5.5, "resultado": 0.3},
            {"label": "2023", "receita": 6.2, "despesa": 6.0, "resultado": 0.2},
            {"label": "2024", "receita": 7.1, "despesa": 6.8, "resultado": 0.3},
            {"label": "2025", "receita": 8.5, "despesa": 6.8, "resultado": 1.7},
            {"label": "2026", "receita": 7.46, "despesa": 7.54, "resultado": -0.08},
        ],
    }
    monthly = {
        "view": "monthly",
        "title": "Evolucao Mensal (2026): Receita vs Despesa vs Resultado",
        "unit": "R$ Milhoes",
        "data": [
            {"label": "Jan", "receita": 3.8, "despesa": 3.6, "resultado": 0.2},
            {"label": "Fev", "receita": 7.46, "despesa": 7.54, "resultado": -0.08},
            {"label": "Mar", "receita": 7.5, "despesa": 7.6, "resultado": -0.1},
            {"label": "Abr", "receita": 7.6, "despesa": 7.7, "resultado": -0.1},
            {"label": "Mai", "receita": 7.7, "despesa": 7.8, "resultado": -0.1},
            {"label": "Jun", "receita": 7.8, "despesa": 7.9, "resultado": -0.1},
            {"label": "Jul", "receita": 7.9, "despesa": 8.0, "resultado": -0.1},
            {"label": "Ago", "receita": 8.0, "despesa": 8.1, "resultado": -0.1},
            {"label": "Set", "receita": 8.1, "despesa": 8.2, "resultado": -0.1},
            {"label": "Out", "receita": 8.2, "despesa": 8.3, "resultado": -0.1},
            {"label": "Nov", "receita": 8.3, "despesa": 8.4, "resultado": -0.1},
            {"label": "Dez", "receita": 8.4, "despesa": 8.5, "resultado": -0.1},
        ],
    }

    for name, data in [("annual", annual), ("monthly", monthly)]:
        filename = OUTPUT_DIR / f"evolution_{name}.json"
        print(f"  -> evolution_{name}.json")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"    [ERRO] {exc}")


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
