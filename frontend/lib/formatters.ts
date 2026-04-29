export function formatCurrency(value: number): string {
  const amount = Math.abs(Number(value) || 0);
  const prefix = value < 0 ? "-" : "";

  if (amount >= 1_000_000_000) {
    return `R$ ${prefix}${formatCompactNumber(amount / 1_000_000_000, 1)} B`;
  }

  if (amount >= 1_000_000) {
    return `R$ ${prefix}${formatCompactNumber(amount / 1_000_000, 2)} M`;
  }

  if (amount >= 1_000) {
    return `R$ ${prefix}${formatCompactNumber(amount / 1_000, 1)} mil`;
  }

  return `R$ ${prefix}${Math.round(amount).toLocaleString("pt-BR")}`;
}

export function parseCurrency(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string" || !value.includes("R$")) return null;

  const normalized = value
    .toUpperCase()
    .replace("R$", "")
    .trim();

  const sign = normalized.includes("-") ? -1 : 1;
  const withoutSign = normalized.replace("-", "").trim();
  let multiplier = 1;
  let numeric = withoutSign;

  if (numeric.endsWith("B")) {
    multiplier = 1_000_000_000;
    numeric = numeric.slice(0, -1);
  } else if (numeric.endsWith("MM")) {
    multiplier = 1_000_000;
    numeric = numeric.slice(0, -2);
  } else if (numeric.endsWith("M")) {
    multiplier = 1_000_000;
    numeric = numeric.slice(0, -1);
  } else if (numeric.endsWith("MIL")) {
    multiplier = 1_000;
    numeric = numeric.slice(0, -3);
  } else if (numeric.endsWith("K")) {
    multiplier = 1_000;
    numeric = numeric.slice(0, -1);
  }

  numeric = numeric.trim();
  const decimal = numeric.includes(",")
    ? numeric.replace(/\./g, "").replace(",", ".")
    : numeric.replace(/\./g, "");
  const parsed = Number(decimal);

  return Number.isFinite(parsed) ? sign * parsed * multiplier : null;
}

export function formatCurrencyText(value: unknown): string {
  const parsed = parseCurrency(value);
  return parsed === null ? String(value ?? "") : formatCurrency(parsed);
}

function formatCompactNumber(value: number, decimals: number): string {
  return value
    .toLocaleString("pt-BR", {
      minimumFractionDigits: 0,
      maximumFractionDigits: decimals,
    });
}
