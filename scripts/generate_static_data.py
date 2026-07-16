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
from utils.analysis_generator import generate_insights, generate_technical_analysis  # noqa: E402
from utils.dashboard_metrics import build_dashboard_metrics  # noqa: E402

OUTPUT_DIR = PROJECT_ROOT / "public" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GLOSAS_CONDENACOES_FILE = PROJECT_ROOT / "data" / "Glosas - Condena\u00e7\u00f5es - 2026.xlsx"
GLOSAS_CONDENACOES_FALLBACK_FILE = PROJECT_ROOT / "data" / "Glosas - Condenacoes - 2026.xlsx"
ORCAMENTO_FILE = PROJECT_ROOT / "data" / "Orçamento.xlsx"
INFORMACOES_GERENCIAIS_FILE = PROJECT_ROOT / "data" / "INFORMAÇÕES GERENCIAIS.xlsx"

# ─── Configuracao ─────────────────────────────────────────────────────────────
YEAR = 2026
# Apenas os meses que tem dados reais na planilha.
# Ajuste conforme os meses disponiveis no Orcamento.xlsx.
AVAILABLE_MONTHS = [1, 2, 3, 4, 5]
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
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def normalize_label(value) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return " ".join(text.lower().split())


def _month_label_to_number(value) -> int | None:
    month_map = {
        "jan": 1,
        "janeiro": 1,
        "fev": 2,
        "fevereiro": 2,
        "mar": 3,
        "marco": 3,
        "março": 3,
        "abr": 4,
        "abril": 4,
        "mai": 5,
        "maio": 5,
        "jun": 6,
        "junho": 6,
        "jul": 7,
        "julho": 7,
        "ago": 8,
        "agosto": 8,
        "set": 9,
        "setembro": 9,
        "out": 10,
        "outubro": 10,
        "nov": 11,
        "novembro": 11,
        "dez": 12,
        "dezembro": 12,
    }
    label = normalize_label(value)
    return month_map.get(label)


def _top_items_from_totals(totals: dict[str, float], limit: int = 5) -> list[dict[str, float | str | int]]:
    ranked = sorted(
        (
            {"position": index + 1, "name": name, "value": value}
            for index, (name, value) in enumerate(
                sorted(totals.items(), key=lambda item: abs(item[1]), reverse=True)
            )
            if abs(value) > 0.01
        ),
        key=lambda item: item["position"],
    )
    return ranked[:limit]


def _with_display_aliases(items: list[dict], aliases: dict[str, str]) -> list[dict]:
    return [
        {
            **item,
            "name": aliases.get(normalize_label(item.get("name")), item.get("name")),
        }
        for item in items
    ]


def _find_glosas_condenacoes_file() -> Path | None:
    for candidate in (GLOSAS_CONDENACOES_FILE, GLOSAS_CONDENACOES_FALLBACK_FILE):
        if candidate.exists():
            return candidate

    expected = normalize_label("Glosas - Condenacoes - 2026")
    for file_path in (PROJECT_ROOT / "data").glob("*.xlsx"):
        if normalize_label(file_path.stem) == expected:
            return file_path
    return None


def _is_month_header(value, month: int, year: int = YEAR) -> bool:
    if hasattr(value, "year") and hasattr(value, "month"):
        return value.year == year and value.month == month

    label = normalize_label(value)
    if not label:
        return False

    month_number = _month_label_to_number(label)
    if month_number == month:
        return True

    month_tokens = {
        1: ("jan", "janeiro"),
        2: ("fev", "fevereiro"),
        3: ("mar", "marco"),
        4: ("abr", "abril"),
        5: ("mai", "maio"),
        6: ("jun", "junho"),
        7: ("jul", "julho"),
        8: ("ago", "agosto"),
        9: ("set", "setembro"),
        10: ("out", "outubro"),
        11: ("nov", "novembro"),
        12: ("dez", "dezembro"),
    }
    return any(token in label for token in month_tokens.get(month, ())) and str(year) in label


def load_recupera_glosas_breakdown(selected_months: list[int], year: int = YEAR) -> dict:
    file_path = _find_glosas_condenacoes_file()
    if not file_path:
        return {
            "available": False,
            "source": "Glosas - Condenacoes - 2026.xlsx",
            "sheet": "Resumo",
            "items": [],
            "total": 0.0,
            "message": "Planilha de detalhamento nao encontrada em data/.",
        }

    try:
        xl = pd.ExcelFile(file_path, engine="openpyxl")
        sheet_name = next((sheet for sheet in xl.sheet_names if normalize_label(sheet) == "resumo"), xl.sheet_names[0])
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine="openpyxl")
    except Exception as exc:
        return {
            "available": False,
            "source": file_path.name,
            "sheet": "Resumo",
            "items": [],
            "total": 0.0,
            "message": f"Nao foi possivel ler a planilha: {exc}",
        }

    header_row = -1
    month_columns: dict[int, int] = {}
    for row_index in range(len(df)):
        all_months = {
            month: column_index
            for column_index in range(len(df.columns))
            for month in range(1, 13)
            if _is_month_header(df.iloc[row_index, column_index], month, year)
        }
        detected = {
            month: column_index
            for column_index in range(len(df.columns))
            for month in selected_months
            if _is_month_header(df.iloc[row_index, column_index], month, year)
        }
        if detected and len(all_months) >= 3:
            header_row = row_index
            month_columns = detected
            break

    if header_row < 0 or not month_columns:
        return {
            "available": False,
            "source": file_path.name,
            "sheet": sheet_name,
            "items": [],
            "total": 0.0,
            "message": "Nao foram encontradas colunas mensais na aba Resumo.",
        }

    name_column = next(
        (
            column_index
            for column_index in range(len(df.columns))
            if normalize_label(df.iloc[header_row, column_index]) in {"centro de custo", "cliente", "item"}
        ),
        0,
    )

    totals: dict[str, float] = {}
    for row_index in range(header_row + 1, len(df)):
        cell = df.iloc[row_index, name_column]
        name = str(cell).strip() if cell is not None and not pd.isna(cell) else ""
        normalized_name = normalize_label(name)
        if normalized_name in {"total", "total geral"}:
            break
        if not normalized_name or normalized_name in {"bruno", "dif", "recupera"}:
            continue

        value = sum(
            to_number(df.iloc[row_index, column_index])
            for column_index in month_columns.values()
            if column_index < len(df.columns)
        )
        if abs(value) > 0.01:
            totals[name] = totals.get(name, 0.0) + value

    items = _top_items_from_totals(totals, limit=50)
    total = round(sum(float(item["value"]) for item in items), 2)
    return {
        "available": bool(items),
        "source": file_path.name,
        "sheet": sheet_name,
        "periodFilterable": True,
        "items": items,
        "total": total,
        "message": "" if items else "Sem dados detalhados para o periodo selecionado.",
    }


def _collect_sucumbencias_by_month(selected_months: list[int]) -> tuple[dict[str, dict[int, float]], dict]:
    xl = pd.ExcelFile(ORCAMENTO_FILE, engine="openpyxl")
    sheet_name = next((sheet for sheet in xl.sheet_names if normalize_label(sheet) == "sucumbencia"), None)
    if not sheet_name:
        return {}, {"source": "Orçamento.xlsx", "sheet": "Sucumbência", "periodFilterable": False}

    df = pd.read_excel(ORCAMENTO_FILE, sheet_name=sheet_name, header=None, engine="openpyxl")
    values: dict[str, dict[int, float]] = {}
    current_client = ""
    month_columns: dict[int, int] = {}

    for _, row in df.iterrows():
        first_cell = row.iloc[0]
        first_label = normalize_label(first_cell)
        detected_months = {
            month_number: column_index
            for column_index, month_number in (
                (column_index, _month_label_to_number(row.iloc[column_index]))
                for column_index in range(len(row))
            )
            if month_number is not None
        }

        if detected_months:
            current_client = str(first_cell).strip() if first_cell is not None and not pd.isna(first_cell) else ""
            month_columns = detected_months
            continue

        if not current_client or normalize_label(current_client) == "total" or first_label != "sucumbencia":
            continue

        monthly_values = values.setdefault(current_client, {})
        for month in selected_months:
            column_index = month_columns.get(month)
            if column_index is not None:
                monthly_values[month] = monthly_values.get(month, 0.0) + to_number(row.iloc[column_index])

    return values, {
        "source": "Orçamento.xlsx",
        "sheet": sheet_name,
        "nameColumn": "Cabeçalho do bloco do cliente",
        "valueColumns": "jan-dez na linha Sucumbência",
        "periodFilterable": True,
    }


def _collect_glosas_by_month(selected_months: list[int], year: int = YEAR) -> tuple[dict[str, dict[int, float]], dict]:
    df = pd.read_excel(
        INFORMACOES_GERENCIAIS_FILE,
        sheet_name="GLOSAS",
        header=0,
        engine="openpyxl",
    )
    period_columns = [
        column
        for column in df.columns
        if hasattr(column, "year") and column.year == year and column.month in selected_months
    ]
    if not period_columns:
        return {}, {"source": "INFORMAÇÕES GERENCIAIS.xlsx", "sheet": "GLOSAS", "periodFilterable": False}

    name_column = "Data" if "Data" in df.columns else df.columns[1]
    values: dict[str, dict[int, float]] = {}
    for _, row in df.iterrows():
        name = str(row.get(name_column, "")).strip()
        if not name or name.lower() == "nan":
            continue

        monthly_values = values.setdefault(name, {})
        for column in period_columns:
            monthly_values[column.month] = monthly_values.get(column.month, 0.0) + to_number(row.get(column, 0))

    return values, {
        "source": "INFORMAÇÕES GERENCIAIS.xlsx",
        "sheet": "GLOSAS",
        "nameColumn": str(name_column),
        "valueColumns": [column.strftime("%b/%Y") for column in period_columns],
        "periodFilterable": True,
    }


def _sum_monthly(values: dict[int, float], selected_months: list[int]) -> float:
    return sum(values.get(month, 0.0) for month in selected_months)


def load_okr_glosas(selected_months: list[int], year: int = YEAR) -> dict | None:
    try:
        df = pd.read_excel(INFORMACOES_GERENCIAIS_FILE, sheet_name="OKR", header=0, engine="openpyxl")
    except Exception:
        return None

    okr_values = []
    for _, row in df.iterrows():
        date_value = row.get("Ano")
        okr_value = row.get("OKR GLOSAS")
        if hasattr(date_value, "year") and date_value.year == year and date_value.month in selected_months:
            if okr_value is not None and not pd.isna(okr_value):
                okr_values.append(float(okr_value))

    if not okr_values:
        return None

    return {
        "source": "INFORMAÇÕES GERENCIAIS.xlsx",
        "sheet": "OKR",
        "column": "OKR GLOSAS",
        "value": sum(okr_values) / len(okr_values),
    }


def load_sucumbencias_glosas(selected_months: list[int], year: int = YEAR) -> dict:
    sucumbencias, sucumbencias_meta = _collect_sucumbencias_by_month(selected_months)
    glosas, glosas_meta = _collect_glosas_by_month(selected_months, year)

    key_to_name: dict[str, str] = {}
    for name in list(sucumbencias.keys()) + list(glosas.keys()):
        key_to_name.setdefault(normalize_label(name), name)

    monthly = []
    for month in sorted(selected_months):
        sucumbencias_total = sum(values.get(month, 0.0) for values in sucumbencias.values())
        glosas_total = sum(values.get(month, 0.0) for values in glosas.values())
        monthly.append({
            "month": month,
            "label": {
                1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
                7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez",
            }.get(month, str(month)),
            "sucumbencias": round(sucumbencias_total, 2),
            "glosas": round(glosas_total, 2),
            "diferenca": round(sucumbencias_total - glosas_total, 2),
        })

    ranking = []
    for key, name in key_to_name.items():
        sucumbencias_total = _sum_monthly(
            sucumbencias.get(name, sucumbencias.get(next((s for s in sucumbencias if normalize_label(s) == key), ""), {})),
            selected_months,
        )
        glosas_total = _sum_monthly(
            glosas.get(name, glosas.get(next((g for g in glosas if normalize_label(g) == key), ""), {})),
            selected_months,
        )
        if abs(sucumbencias_total) < 0.01 and abs(glosas_total) < 0.01:
            continue
        ranking.append({
            "name": name,
            "sucumbencias": round(sucumbencias_total, 2),
            "glosas": round(glosas_total, 2),
            "diferenca": round(sucumbencias_total - glosas_total, 2),
            "glosasPercent": glosas_total / sucumbencias_total if sucumbencias_total else None,
        })
    ranking.sort(key=lambda item: abs(item["glosas"]), reverse=True)
    ranking = ranking[:8]

    sucumbencias_total = sum(item["sucumbencias"] for item in monthly)
    glosas_total = sum(item["glosas"] for item in monthly)
    glosas_percent = glosas_total / sucumbencias_total if sucumbencias_total else None
    okr = load_okr_glosas(selected_months, year)

    summary = {
        "sucumbenciasTotal": round(sucumbencias_total, 2),
        "glosasTotal": round(glosas_total, 2),
        "diferenca": round(sucumbencias_total - glosas_total, 2),
        "glosasPercent": glosas_percent,
    }
    if okr:
        summary["okrGlosas"] = okr["value"]
        summary["okrAtingimento"] = glosas_percent / okr["value"] if glosas_percent is not None and okr["value"] else None

    sucumbencias_totals = {
        name: _sum_monthly(values, selected_months)
        for name, values in sucumbencias.items()
    }
    glosas_totals = {
        name: _sum_monthly(values, selected_months)
        for name, values in glosas.items()
    }
    recupera_breakdown = load_recupera_glosas_breakdown(selected_months, year)

    return {
        "title": "Balanço de Sucumbências x Glosas",
        "periodFilterable": sucumbencias_meta.get("periodFilterable") and glosas_meta.get("periodFilterable"),
        "summary": summary,
        "monthly": monthly,
        "ranking": ranking,
        "sources": {
            "sucumbencias": sucumbencias_meta,
            "glosas": glosas_meta,
            "okr": okr,
        },
        "topSucumbencias": {
            "title": "Top 5 Sucumbências",
            **sucumbencias_meta,
            "totalPeriod": round(sucumbencias_total, 2),
            "totalLabel": "Total de sucumbencia no periodo",
            "items": _with_display_aliases(
                _top_items_from_totals(sucumbencias_totals),
                {"valor legal": "RECUPERA"},
            ),
        },
        "topGlosas": {
            "title": "Top 5 Glosas",
            **glosas_meta,
            "totalPeriod": round(glosas_total, 2),
            "totalLabel": "Total de glosas no periodo",
            "recuperaBreakdown": recupera_breakdown,
            "items": _top_items_from_totals(glosas_totals),
        },
    }


def load_top_sucumbencias(selected_months: list[int]) -> dict:
    xl = pd.ExcelFile(ORCAMENTO_FILE, engine="openpyxl")
    sheet_name = next((sheet for sheet in xl.sheet_names if normalize_label(sheet) == "sucumbencia"), None)
    if not sheet_name:
        return {"source": "Orçamento.xlsx", "sheet": "Sucumbência", "periodFilterable": False, "items": []}

    df = pd.read_excel(ORCAMENTO_FILE, sheet_name=sheet_name, header=None, engine="openpyxl")
    totals: dict[str, float] = {}
    current_client = ""
    month_columns: dict[int, int] = {}

    for _, row in df.iterrows():
        first_cell = row.iloc[0]
        first_label = normalize_label(first_cell)

        row_months = {
            column_index: _month_label_to_number(row.iloc[column_index])
            for column_index in range(len(row))
        }
        detected_months = {
            month_number: column_index
            for column_index, month_number in row_months.items()
            if month_number is not None
        }
        if detected_months:
            current_client = str(first_cell).strip() if first_cell is not None and not pd.isna(first_cell) else ""
            month_columns = detected_months
            continue

        if current_client and normalize_label(current_client) != "total" and first_label == "sucumbencia":
            value = sum(
                to_number(row.iloc[column_index])
                for month in selected_months
                for column_index in [month_columns.get(month)]
                if column_index is not None
            )
            totals[current_client] = totals.get(current_client, 0.0) + value

    return {
        "title": "Top 5 Sucumbências",
        "source": "Orçamento.xlsx",
        "sheet": sheet_name,
        "nameColumn": "Cabeçalho do bloco do cliente",
        "valueColumns": "jan-dez na linha Sucumbência",
        "periodFilterable": True,
        "items": _top_items_from_totals(totals),
    }


def load_top_glosas(selected_months: list[int], year: int = YEAR) -> dict:
    df = pd.read_excel(
        INFORMACOES_GERENCIAIS_FILE,
        sheet_name="GLOSAS",
        header=0,
        engine="openpyxl",
    )

    period_columns = [
        column
        for column in df.columns
        if hasattr(column, "year") and column.year == year and column.month in selected_months
    ]
    if not period_columns:
        return {"source": "INFORMAÇÕES GERENCIAIS.xlsx", "sheet": "GLOSAS", "periodFilterable": False, "items": []}

    name_column = "Data" if "Data" in df.columns else df.columns[1]
    totals: dict[str, float] = {}
    for _, row in df.iterrows():
        name = str(row.get(name_column, "")).strip()
        if not name or name.lower() == "nan":
            continue
        value = sum(to_number(row.get(column, 0)) for column in period_columns)
        totals[name] = totals.get(name, 0.0) + value

    return {
        "title": "Top 5 Glosas",
        "source": "INFORMAÇÕES GERENCIAIS.xlsx",
        "sheet": "GLOSAS",
        "nameColumn": str(name_column),
        "valueColumns": [column.strftime("%b/%Y") for column in period_columns],
        "periodFilterable": True,
        "items": _top_items_from_totals(totals),
    }


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
    period_months = len(selected_months) or 1

    return {
        "receita": receita,
        "custos": custos,
        "resultado": resultado,
        "impostos": impostos,
        "sucumbencia": sucumbencia,
        "receita_media_periodo": receita / period_months,
        "custos_media_periodo": custos / period_months,
        "resultado_media_periodo": resultado / period_months,
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


def enrich_net_result(data: dict, selected_months: list[int], year: int = YEAR, totais: dict[str, float] | None = None) -> None:
    totais = totais or load_totais(selected_months, year)
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
        "averagePeriod": totais["resultado_media_periodo"],
        "previousYearPeriod": resultado_2025,
        "media_periodo": totais["resultado_media_periodo"],
        "periodo_2025": resultado_2025,
        "pct_vs_orcado": pct_vs_orcado,
        "variacao_2025": variacao_2025,
        "pct_ano": pct_ano,
        "resultado_operacional": resultado_operacional,
    })


def enrich_revenue_and_cost_metrics(data: dict, selected_months: list[int], year: int = YEAR, totais: dict[str, float] | None = None) -> None:
    totais = totais or load_totais(selected_months, year)
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
        "averagePeriod": totais["receita_media_periodo"],
        "previousYearPeriod": totais["receita_2025"],
        "media_periodo": totais["receita_media_periodo"],
        "faturamento_2025": totais["receita_2025"],
        "pct_orcado": data["revenue_mix"]["value"] / meta_periodo_receita if meta_periodo_receita else 0.0,
        "variacao_2025": data["revenue_mix"].get("variacao_yoy", 0),
    })

    data["cost_structure"].update({
        "custo_orcado_anual": meta_periodo_custos,
        "custo_orcado_periodo": meta_periodo_custos,
        "meta_periodo_custos": meta_periodo_custos,
        "meta_periodo_meses": period_months,
        "averagePeriod": totais["custos_media_periodo"],
        "previousYearPeriod": totais["custos_2025"],
        "media_periodo": totais["custos_media_periodo"],
        "despesas_2025": totais["custos_2025"],
        "pct_orcado_custos": meta_periodo_custos / cost_total if cost_total else 0.0,
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
            totais = load_totais(months, YEAR)
            enrich_net_result(data, months, YEAR, totais=totais)
            enrich_revenue_and_cost_metrics(data, months, YEAR, totais=totais)
            sucumbencias_glosas = load_sucumbencias_glosas(months, YEAR)
            data["topSucumbencias"] = sucumbencias_glosas.pop("topSucumbencias")
            data["topGlosas"] = sucumbencias_glosas.pop("topGlosas")
            data["sucumbenciasGlosas"] = sucumbencias_glosas
            metrics = build_dashboard_metrics(data)
            data["technical_analysis"] = generate_technical_analysis(data, metrics=metrics)
            data["insights"] = generate_insights(data, metrics=metrics)
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
