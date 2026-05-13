from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from utils.number_formatter import formatar_valor_monetario


@dataclass(frozen=True)
class BreakdownMetric:
    label: str
    value: str
    share: str
    amount: float
    share_pct: float


@dataclass(frozen=True)
class ClientMetric:
    name: str
    value: str
    amount: float


@dataclass(frozen=True)
class DashboardMetrics:
    revenue_total: float
    cost_total: float
    operating_result: float
    revenue_change_pct: float
    cost_change_pct: float
    sucumbency_share_pct: float
    net_without_sucumbency: float
    people_share_pct: float
    socios_de_servico: BreakdownMetric
    taxes: BreakdownMetric
    correspondents: BreakdownMetric
    other_expenses: BreakdownMetric
    support_value: float
    support_share_pct: float
    people_breakdown: tuple[BreakdownMetric, ...]
    top_clients: tuple[ClientMetric, ...]
    top_group_total: float
    lead_client_name: str
    lead_client_share_pct: float


def build_dashboard_metrics(content: dict[str, Any]) -> DashboardMetrics:
    revenue = content["revenue_mix"]
    costs = content["cost_structure"]
    result = content["net_result"]
    people = content["people"]
    clients = content["top_clients"]["ranking"]

    revenue_total = parse_currency(revenue["value"])
    cost_total = parse_currency(costs["value"])
    operating_result = revenue_total - cost_total
    revenue_change_pct = float(revenue.get("comparison_pct", extract_primary_percent(revenue["subtitle"])))
    cost_total_anterior = float(costs.get("cost_total_anterior") or 0.0)
    cost_change_pct = (
        ((cost_total - cost_total_anterior) / cost_total_anterior) * 100
        if cost_total_anterior
        else extract_primary_percent(costs["subtitle"])
    )

    sucumbency_row = _find_item_by_label(revenue["rows"], "Sucumbência")
    sucumbency_share_pct = parse_percent(sucumbency_row["share"])
    net_without_sucumbency = extract_currency_from_text(result["subtitle"])

    socios_de_servico = _to_breakdown_metric(_find_item_by_label(costs["items"], "Sócios de Serviço"))
    clt_cost = _to_breakdown_metric(_find_item_by_label(costs["items"], "CLT"))
    people_share_pct = (
        (socios_de_servico.amount + clt_cost.amount) / cost_total * 100
        if cost_total
        else socios_de_servico.share_pct + clt_cost.share_pct
    )
    taxes = _to_breakdown_metric(_find_item_by_label(costs["items"], "Impostos"))
    correspondents = _to_breakdown_metric(_find_item_by_label(costs["items"], "Correspondentes"))
    other_expenses = _to_breakdown_metric(_find_item_by_label(costs["items"], "Outras Despesas"))

    people_breakdown = tuple(_to_breakdown_metric(item) for item in people["rows"])
    top_clients = tuple(_to_client_metric(item) for item in clients)

    top_group_total = sum(client.amount for client in top_clients)
    lead_client = top_clients[0]
    lead_client_share_pct = (lead_client.amount / top_group_total * 100) if top_group_total else 0.0

    return DashboardMetrics(
        revenue_total=revenue_total,
        cost_total=cost_total,
        operating_result=operating_result,
        revenue_change_pct=revenue_change_pct,
        cost_change_pct=cost_change_pct,
        sucumbency_share_pct=sucumbency_share_pct,
        net_without_sucumbency=net_without_sucumbency,
        people_share_pct=people_share_pct,
        socios_de_servico=socios_de_servico,
        taxes=taxes,
        correspondents=correspondents,
        other_expenses=other_expenses,
        support_value=correspondents.amount + other_expenses.amount,
        support_share_pct=correspondents.share_pct + other_expenses.share_pct,
        people_breakdown=people_breakdown,
        top_clients=top_clients,
        top_group_total=top_group_total,
        lead_client_name=lead_client.name,
        lead_client_share_pct=lead_client_share_pct,
    )


def parse_currency(value: str | int | float) -> float:
    if isinstance(value, (int, float)):
        return float(value)

    normalized = str(value).upper().replace("R$", "").replace(" ", "")
    if not any(char.isalpha() for char in normalized):
        return float(normalized.replace(".", "").replace(",", ".") if "," in normalized else normalized)

    sign = -1 if "-" in normalized else 1
    normalized = normalized.replace("-", "")

    multiplier = 1.0
    if normalized.endswith("B"):
        multiplier = 1_000_000_000.0
        normalized = normalized[:-1]
    elif normalized.endswith("MM"):
        multiplier = 1_000_000.0
        normalized = normalized[:-2]
    elif normalized.endswith("M"):
        multiplier = 1_000_000.0
        normalized = normalized[:-1]
    elif normalized.endswith("MIL"):
        multiplier = 1_000.0
        normalized = normalized[:-3]
    elif normalized.endswith("K"):
        multiplier = 1_000.0
        normalized = normalized[:-1]

    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif multiplier == 1.0:
        normalized = normalized.replace(".", "")

    return sign * float(normalized) * multiplier


def parse_percent(value: str) -> float:
    cleaned = value.replace("%", "").replace(".", "").replace(",", ".").strip()
    return float(cleaned)


def extract_currency_from_text(text: str) -> float:
    matches = re.findall(r"R\$\s*-?\s*[\d\.,]+(?:\s*(?:MM|M|MIL|K|B))?", text, flags=re.IGNORECASE)
    if not matches:
        return 0.0
    return parse_currency(matches[-1])


def extract_primary_percent(text: str) -> float:
    match = re.search(r"([▲▼+-]?)\s*(\d+(?:[.,]\d+)?)%", text)
    if not match:
        return 0.0

    marker = match.group(1)
    value = float(match.group(2).replace(",", "."))
    if marker in {"▼", "-"}:
        return -value
    return value


def format_brl(value: float) -> str:
    return formatar_valor_monetario(value)


def format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def normalize_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


def _find_item_by_label(items: list[dict[str, Any]], label: str) -> dict[str, Any]:
    expected = normalize_key(label)
    for item in items:
        if normalize_key(str(item.get("label", ""))) == expected:
            return item
    raise KeyError(f"Item '{label}' não encontrado.")


def _to_breakdown_metric(item: dict[str, str]) -> BreakdownMetric:
    return BreakdownMetric(
        label=item["label"],
        value=item["value"],
        share=item["share"],
        amount=parse_currency(item["value"]),
        share_pct=parse_percent(item["share"]),
    )


def _to_client_metric(item: dict[str, str]) -> ClientMetric:
    return ClientMetric(
        name=item["name"],
        value=item["value"],
        amount=parse_currency(item["value"]),
    )
