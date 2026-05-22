from __future__ import annotations

from typing import Any

from config.settings import ANALYSIS_GENERATION_MODE, LLM_PROVIDER
from utils.dashboard_metrics import (
    DashboardMetrics,
    build_dashboard_metrics,
    format_brl,
    format_percent,
)


def generate_technical_analysis(
    content: dict[str, Any],
    metrics: DashboardMetrics | None = None,
    mode: str | None = None,
) -> dict[str, Any]:
    """Gera a seção de análise técnica em modo template ou LLM."""
    selected_mode = (mode or ANALYSIS_GENERATION_MODE).strip().lower()
    resolved_metrics = metrics or build_dashboard_metrics(content)

    if selected_mode == "llm":
        return _generate_analysis_with_llm(content, resolved_metrics)

    return _generate_analysis_with_template(content, resolved_metrics)


def generate_insights(
    content: dict[str, Any],
    metrics: DashboardMetrics | None = None,
    mode: str | None = None,
) -> list[dict[str, str]]:
    """Gera os insights curtos do dashboard em modo template ou LLM."""
    selected_mode = (mode or ANALYSIS_GENERATION_MODE).strip().lower()
    resolved_metrics = metrics or build_dashboard_metrics(content)

    if selected_mode == "llm":
        return _generate_insights_with_llm(content, resolved_metrics)

    return _generate_insights_with_template(resolved_metrics)


def _generate_analysis_with_template(
    content: dict[str, Any],
    metrics: DashboardMetrics,
) -> dict[str, Any]:
    header = content["header"]
    technical_analysis = content.get("technical_analysis", {})
    period_label = header["subtitle"].split("•")[0].strip().rstrip(".")

    paragraphs = [
        _build_operational_paragraph(metrics),
        _build_interannual_paragraph(period_label, metrics),
        _build_net_result_paragraph(metrics),
        _build_people_costs_paragraph(metrics),
        _build_support_costs_paragraph(metrics),
        _build_client_risk_paragraph(metrics),
    ]

    return {
        "title": technical_analysis.get("title", "Análise técnica"),
        "paragraphs": paragraphs,
        "meta": {
            "mode": "template",
            "provider": None,
        },
    }


def _generate_analysis_with_llm(
    content: dict[str, Any],
    metrics: DashboardMetrics,
) -> dict[str, Any]:
    """Ponto de extensão para futura geração via provedor externo."""
    _ = LLM_PROVIDER
    analysis = _generate_analysis_with_template(content, metrics)
    analysis["meta"]["mode"] = "llm-fallback"
    analysis["meta"]["provider"] = LLM_PROVIDER
    return analysis


def _generate_insights_with_template(metrics: DashboardMetrics) -> list[dict[str, str]]:
    operating_pressure = abs(metrics.operating_result)
    tesoura_text = (
        f"Receita recua {format_percent(abs(metrics.revenue_change_pct))} enquanto custos avançam "
        f"{format_percent(metrics.cost_change_pct)}, pressionando {format_brl(operating_pressure)} no operacional."
        if metrics.operating_result < 0
        else
        f"Receita e custos seguem em direções distintas, mas ainda preservam resultado operacional de "
        f"{format_brl(metrics.operating_result)}."
    )

    people_mix = ", ".join(
        f"{item.label} {item.share}"
        for item in metrics.people_breakdown
    )

    top_group_risk = (
        "concentração elevada" if metrics.lead_client_share_pct >= 30 else
        "concentração relevante" if metrics.lead_client_share_pct >= 24 else
        "concentração moderada"
    )

    top_clients_description = (
        f"{metrics.lead_client_name} lidera um grupo que soma {format_brl(metrics.top_group_total)} "
        f"e mantém {top_group_risk} na frente comercial."
        if metrics.top_clients
        else "Sem faturamento por cliente no período selecionado."
    )

    return [
        {
            "tone": "red",
            "title": "Efeito tesoura",
            "description": tesoura_text,
        },
        {
            "tone": "yellow",
            "title": f"Pessoas representam {format_percent(metrics.people_share_pct)} dos custos",
            "description": (
                f"O gasto consolidado com Sócios, CLT e Estagiários soma {format_brl(metrics.people_cost_value)}, "
                f"representando {format_percent(metrics.people_share_pct)} do total de custos do período."
            ),
        },
        {
            "tone": "green",
            "title": "Estrutura de pessoas",
            "description": (
                f"A base segue concentrada em pessoas, com {people_mix}, o que reforça uma estrutura "
                f"mais rígida no curto prazo."
            ),
        },
        {
            "tone": "blue",
            "title": "Top 5 clientes",
            "description": top_clients_description,
        },
    ]


def _generate_insights_with_llm(
    content: dict[str, Any],
    metrics: DashboardMetrics,
) -> list[dict[str, str]]:
    _ = content
    _ = LLM_PROVIDER
    return _generate_insights_with_template(metrics)


def _build_operational_paragraph(metrics: DashboardMetrics) -> str:
    if metrics.operating_result < 0:
        return (
            f"No acumulado do período, a receita somou {format_brl(metrics.revenue_total)} e ficou "
            f"{format_percent(abs(metrics.revenue_change_pct))} abaixo da base comparativa, enquanto a "
            f"estrutura de custos alcançou {format_brl(metrics.cost_total)} após avanço de "
            f"{format_percent(metrics.cost_change_pct)}. Esse descompasso levou o resultado operacional "
            f"a uma pressão estimada de {format_brl(abs(metrics.operating_result))}."
        )

    return (
        f"No acumulado do período, a receita somou {format_brl(metrics.revenue_total)} e a estrutura "
        f"de custos atingiu {format_brl(metrics.cost_total)}, produzindo resultado operacional positivo "
        f"de {format_brl(metrics.operating_result)}. O ritmo entre receita e despesas segue relativamente equilibrado."
    )


def _build_interannual_paragraph(period_label: str, metrics: DashboardMetrics) -> str:
    spread = abs(metrics.cost_change_pct - metrics.revenue_change_pct)
    mismatch = (
        "um descolamento relevante entre receita e custos"
        if spread >= 10
        else "um descompasso mais moderado entre receita e custos"
    )
    return (
        f"A comparação interanual de {period_label.lower()} deve ser lida com cautela, mas já evidencia "
        f"{mismatch}. Como o painel observa um recorte parcial do ano, o efeito de base, sazonalidade e "
        f"timing de reconhecimento das linhas pode ampliar ou suavizar a fotografia do período."
    )


def _build_net_result_paragraph(metrics: DashboardMetrics) -> str:
    if metrics.net_without_sucumbency < 0:
        return (
            f"Sem a contribuição da sucumbência, o resultado líquido ficaria em "
            f"{format_brl(metrics.net_without_sucumbency)}, o que reforça a dependência dessa linha "
            f"não recorrente para amortecer a pressão operacional. Hoje ela representa "
            f"{format_percent(metrics.sucumbency_share_pct)} do mix de receitas."
        )

    return (
        f"Mesmo sem considerar a sucumbência, o resultado líquido permaneceria em "
        f"{format_brl(metrics.net_without_sucumbency)}, sugerindo que a geração recorrente ainda se sustenta "
        f"com menor dependência de receitas extraordinárias."
    )


def _build_people_costs_paragraph(metrics: DashboardMetrics) -> str:
    intensity = (
        "muito elevado" if metrics.people_share_pct >= 65 else
        "relevante" if metrics.people_share_pct >= 50 else
        "moderado"
    )
    return (
        f"O principal vetor de rigidez está na estrutura de pessoas: o desembolso com essa frente responde "
        f"por {format_percent(metrics.people_share_pct)} do total de custos, patamar {intensity}. Em paralelo, "
        f"a linha de Sócios concentra {metrics.socios_de_servico.share}, o que reforça a necessidade de disciplina sobre capacidade, "
        f"alocação e produtividade."
    )


def _build_support_costs_paragraph(metrics: DashboardMetrics) -> str:
    return (
        f"Na camada complementar, correspondentes somam {metrics.correspondents.value} "
        f"({metrics.correspondents.share}) e outras despesas atingem {metrics.other_expenses.value} "
        f"({metrics.other_expenses.share}). Juntas, essas rubricas representam {format_brl(metrics.support_value)} "
        f"e {format_percent(metrics.support_share_pct)} dos custos, oferecendo espaço para ajustes táticos sem "
        f"alterar a espinha dorsal da operação."
    )


def _build_client_risk_paragraph(metrics: DashboardMetrics) -> str:
    if not metrics.top_clients:
        return "Na frente comercial, não há faturamento por cliente no período selecionado."

    client_names = ", ".join(client.name for client in metrics.top_clients[:5])
    concentration = (
        "um nível elevado de concentração comercial"
        if metrics.lead_client_share_pct >= 30
        else "um nível relevante de concentração comercial"
    )
    return (
        f"Na frente comercial, o faturamento segue concentrado no top 5 clientes, formado por {client_names}, "
        f"que juntos somam {format_brl(metrics.top_group_total)}. A liderança de {metrics.lead_client_name}, "
        f"com {format_percent(metrics.lead_client_share_pct)} desse bloco, sinaliza {concentration} e mantém a "
        f"diversificação da carteira como agenda prioritária."
    )
