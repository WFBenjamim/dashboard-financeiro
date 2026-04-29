"""Formatador de números e valores monetários."""
from __future__ import annotations


def formatar_valor_compacto(valor: float) -> str:
    """
    Formata valor em reais compactos para milhares.
    
    Args:
        valor: Número a ser formatado
        
    Returns:
        String formatada (ex: "1.000.000,00", "840K", "500")
    """
    sinal = "-" if valor < 0 else ""
    valor_absoluto = abs(valor)

    if valor_absoluto >= 1_000_000:
        valor_formatado = f"{valor_absoluto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{sinal}{valor_formatado}"

    if valor_absoluto >= 1_000:
        return f"{sinal}{valor_absoluto / 1_000:.0f}K"

    return f"{sinal}{valor_absoluto:.0f}"


def formatar_valor_monetario(valor: float, usar_compacto: bool = True) -> str:
    """
    Formata valor monetário em reais.
    
    Args:
        valor: Valor a ser formatado
        usar_compacto: Se True, usa compactação para milhares e BRL completo a partir de 1 milhão. Se False, usa formato padrão.
        
    Returns:
        String formatada (ex: "R$ 1.000.000,00" ou "R$ 700K")
    """
    if usar_compacto:
        compacto = formatar_valor_compacto(valor)
        return f"R$ {compacto}"
    else:
        valor_formatado = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ -{valor_formatado}" if valor < 0 else f"R$ {valor_formatado}"
