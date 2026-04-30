"""Gráficos de evolução anual e mensal usando Plotly."""
from __future__ import annotations

import plotly.graph_objects as go

from utils.number_formatter import formatar_valor_monetario


def _format_million_values(values: list[float]) -> list[str]:
    return [formatar_valor_monetario(value * 1_000_000) for value in values]


def create_grafico_evolucao_anual() -> go.Figure:
    """
    Cria gráfico de evolução anual com linhas de Receita, Despesa e Resultado.
    
    Returns:
        Figura Plotly com dados de 2022-2026
    """
    anos = [2022, 2023, 2024, 2025, 2026]
    
    # Dados simulados (em milhões)
    receita = [5.8, 6.2, 7.1, 8.5, 7.46]
    despesa = [5.5, 6.0, 6.8, 6.8, 7.54]
    resultado = [0.3, 0.2, 0.3, 1.7, -0.08]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=anos,
        y=receita,
        mode='lines+markers',
        name='Receita',
        line=dict(color='#3B82F6', width=3),
        marker=dict(size=8),
        customdata=_format_million_values(receita),
        hovertemplate='%{fullData.name}: %{customdata}<extra></extra>',
    ))
    
    fig.add_trace(go.Scatter(
        x=anos,
        y=despesa,
        mode='lines+markers',
        name='Despesa',
        line=dict(color='#EF4444', width=3),
        marker=dict(size=8),
        customdata=_format_million_values(despesa),
        hovertemplate='%{fullData.name}: %{customdata}<extra></extra>',
    ))
    
    fig.add_trace(go.Scatter(
        x=anos,
        y=resultado,
        mode='lines+markers',
        name='Resultado',
        line=dict(color='#FBBF24', width=3),
        marker=dict(size=8),
        customdata=_format_million_values(resultado),
        hovertemplate='%{fullData.name}: %{customdata}<extra></extra>',
    ))
    
    fig.update_layout(
        title='Evolução Anual: Receita vs Despesa vs Resultado',
        xaxis_title='Ano',
        yaxis_title='Valor (R$ Milhões)',
        height=400,
        hovermode='x unified',
        template='plotly_dark',
        plot_bgcolor='rgba(30, 30, 35, 0.5)',
        paper_bgcolor='rgba(18, 19, 22, 0.8)',
        font=dict(family='Manrope, sans-serif', size=12, color='#f8fafc'),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
        ),
        margin=dict(l=50, r=50, t=60, b=50),
    )
    fig.update_xaxes(type='category', tickmode='array', tickvals=[str(ano) for ano in anos], ticktext=[str(ano) for ano in anos])
    
    return fig


def create_grafico_evolucao_mensal() -> go.Figure:
    """
    Cria gráfico de evolução mensal com linhas de Receita, Despesa e Resultado.
    
    Returns:
        Figura Plotly com dados de jan-dez (período acumulado até fev)
    """
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
             'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    # Dados simulados (em milhões, acumulado até fevereiro)
    receita = [3.8, 7.46, 7.5, 7.6, 7.7, 7.8,
               7.9, 8.0, 8.1, 8.2, 8.3, 8.4]
    despesa = [3.6, 7.54, 7.6, 7.7, 7.8, 7.9,
               8.0, 8.1, 8.2, 8.3, 8.4, 8.5]
    resultado = [0.2, -0.08, -0.1, -0.1, -0.1, -0.1,
                 -0.1, -0.1, -0.1, -0.1, -0.1, -0.1]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=meses,
        y=receita,
        mode='lines+markers',
        name='Receita',
        line=dict(color='#3B82F6', width=3),
        marker=dict(size=8),
        customdata=_format_million_values(receita),
        hovertemplate='%{fullData.name}: %{customdata}<extra></extra>',
    ))
    
    fig.add_trace(go.Scatter(
        x=meses,
        y=despesa,
        mode='lines+markers',
        name='Despesa',
        line=dict(color='#EF4444', width=3),
        marker=dict(size=8),
        customdata=_format_million_values(despesa),
        hovertemplate='%{fullData.name}: %{customdata}<extra></extra>',
    ))
    
    fig.add_trace(go.Scatter(
        x=meses,
        y=resultado,
        mode='lines+markers',
        name='Resultado',
        line=dict(color='#FBBF24', width=3),
        marker=dict(size=8),
        customdata=_format_million_values(resultado),
        hovertemplate='%{fullData.name}: %{customdata}<extra></extra>',
    ))
    
    fig.update_layout(
        title='Evolução Mensal (2026): Receita vs Despesa vs Resultado',
        xaxis_title='Mês',
        yaxis_title='Valor (R$ Milhões)',
        height=400,
        hovermode='x unified',
        template='plotly_dark',
        plot_bgcolor='rgba(30, 30, 35, 0.5)',
        paper_bgcolor='rgba(18, 19, 22, 0.8)',
        font=dict(family='Manrope, sans-serif', size=12, color='#f8fafc'),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
        ),
        margin=dict(l=50, r=50, t=60, b=50),
    )
    
    return fig
