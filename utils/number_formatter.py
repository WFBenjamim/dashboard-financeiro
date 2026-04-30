"""Formatadores de numeros e valores monetarios."""
from __future__ import annotations


def _format_compact_number(valor: float, casas_decimais: int) -> str:
    texto = f"{valor:.{casas_decimais}f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def formatar_valor_compacto(valor: float) -> str:
    """
    Formata valor numerico no padrao executivo brasileiro.

    Args:
        valor: Numero a ser formatado

    Returns:
        String formatada (ex: "12,5 mil", "12,16 M", "1,2 B")
    """
    sinal = "-" if valor < 0 else ""
    valor_absoluto = abs(float(valor))

    if valor_absoluto >= 1_000_000_000:
        return f"{sinal}{_format_compact_number(valor_absoluto / 1_000_000_000, 1)} B"

    if valor_absoluto >= 1_000_000:
        return f"{sinal}{_format_compact_number(valor_absoluto / 1_000_000, 2)} M"

    if valor_absoluto >= 1_000:
        return f"{sinal}{_format_compact_number(valor_absoluto / 1_000, 1)} mil"

    return f"{sinal}{valor_absoluto:.0f}"


def formatar_valor_monetario(valor: float, usar_compacto: bool = True) -> str:
    """
    Formata valor monetario em reais no padrao executivo brasileiro.

    Args:
        valor: Valor a ser formatado
        usar_compacto: Se True, usa compactacao executiva. Se False, usa formato BRL completo.

    Returns:
        String formatada (ex: "R$ 12,5 mil" ou "R$ 12,16 M")
    """
    if usar_compacto:
        return f"R$ {formatar_valor_compacto(valor)}"

    valor_formatado = f"{abs(float(valor)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ -{valor_formatado}" if valor < 0 else f"R$ {valor_formatado}"
