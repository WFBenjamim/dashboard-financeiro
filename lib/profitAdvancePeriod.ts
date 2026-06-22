const MONTH_NAMES = [
  "JANEIRO",
  "FEVEREIRO",
  "MARÇO",
  "ABRIL",
  "MAIO",
  "JUNHO",
  "JULHO",
  "AGOSTO",
  "SETEMBRO",
  "OUTUBRO",
  "NOVEMBRO",
  "DEZEMBRO",
];

function formatMonthYear(date: Date) {
  return `${MONTH_NAMES[date.getMonth()]} / ${date.getFullYear()}`;
}

export function getProfitAdvancePeriodLabel(currentDate = new Date()) {
  const referenceDate = new Date(
    currentDate.getFullYear(),
    currentDate.getMonth() - 1,
    1,
  );
  const paymentDate = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth() + 2,
    1,
  );

  return `${formatMonthYear(referenceDate)} - PAGAMENTO EM ${formatMonthYear(paymentDate)}`;
}
