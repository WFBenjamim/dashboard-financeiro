const months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

interface MonthFilterProps {
  currentMonth: number;
  selectedMonths: number[];
  onChange: (months: number[]) => void;
}

export function MonthFilter({ currentMonth, selectedMonths, onChange }: MonthFilterProps) {
  function toggleMonth(month: number) {
    if (month > currentMonth) return;

    const isSelected = selectedMonths.includes(month);
    const nextMonths = isSelected
      ? selectedMonths.filter((item) => item !== month)
      : [...selectedMonths, month];

    onChange(nextMonths.sort((a, b) => a - b));
  }

  return (
    <div className="gd-month-filter" aria-label="Selecionar meses">
      {months.map((month) => {
        const isDisabled = month > currentMonth;
        const isSelected = selectedMonths.includes(month);

        return (
          <button
            key={month}
            type="button"
            className={[
              "gd-month-filter__button",
              isSelected ? "is-selected" : "",
              isDisabled ? "is-disabled" : "",
            ].filter(Boolean).join(" ")}
            disabled={isDisabled}
            onClick={() => toggleMonth(month)}
            aria-pressed={isSelected}
            title={`Mes ${month}`}
          >
            {month}
          </button>
        );
      })}
    </div>
  );
}
