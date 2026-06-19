"use client";

import { FullscreenButton } from "@/components/FullscreenButton";

type ResultOpeningScreenProps = {
  onEnter: () => void;
};

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

function getReferencePeriod() {
  const today = new Date();
  const referenceDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
  const meetingNumber = referenceDate.getMonth() + 1;
  const month = MONTH_NAMES[referenceDate.getMonth()];
  const year = referenceDate.getFullYear();

  return {
    ordinal: `${meetingNumber}º`,
    period: `${month} DE ${year}`,
  };
}

export function ResultOpeningScreen({ onEnter }: ResultOpeningScreenProps) {
  const { ordinal, period } = getReferencePeriod();

  function handleKeyDown(event: React.KeyboardEvent<HTMLElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onEnter();
    }
  }

  return (
    <main
      className="result-opening"
      onClick={onEnter}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-label="Entrar no dashboard"
    >
      <FullscreenButton />
      <div className="result-opening__content">
        <div className="result-opening__ordinal">{ordinal}</div>
        <div className="result-opening__title">ENCONTRO DE DIVULGAÇÃO DE RESULTADOS</div>
        <div className="result-opening__period">{period}</div>
      </div>
    </main>
  );
}
