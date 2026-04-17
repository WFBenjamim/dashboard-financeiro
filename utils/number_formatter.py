"""Formatador de números e valores monetários."""
from __future__ import annotations


def formatar_valor_compacto(valor: float) -> str:
    """
    Formata valor em formato compacto (M/K).
    
    Args:
        valor: Número a ser formatado
        
    Returns:
        String formatada (ex: "7,46M", "840K", "500")
    """
    sinal = "-" if valor < 0 else ""
    valor_absoluto = abs(valor)

    if valor_absoluto >= 1_000_000:
        texto = f"{valor_absoluto / 1_000_000:.2f}".replace(".", ",")
        if texto.endswith(",00"):
            texto = texto[:-3]
        return f"{sinal}{texto}M"

    if valor_absoluto >= 1_000:
        return f"{sinal}{valor_absoluto / 1_000:.0f}K"

    return f"{sinal}{valor_absoluto:.0f}"


def formatar_valor_monetario(valor: float, usar_compacto: bool = True) -> str:
    """
    Formata valor monetário em reais.
    
    Args:
        valor: Valor a ser formatado
        usar_compacto: Se True, usa formato M/K. Se False, usa formato padrão.
        
    Returns:
        String formatada (ex: "R$ 7,46M" ou "R$ 7.460.000,00")
    """
    if usar_compacto:
        compacto = formatar_valor_compacto(valor)
        return f"R$ {compacto}"
    else:
        valor_formatado = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ -{valor_formatado}" if valor < 0 else f"R$ {valor_formatado}"


def formatar_percentual(percentual: float) -> str:
    """
    Formata um percentual.
    
    Args:
        percentual: Valor entre 0 e 100
        
    Returns:
        String formatada (ex: "12,5%")
    """
    return f"{percentual:.1f}%".replace(".", ",")
