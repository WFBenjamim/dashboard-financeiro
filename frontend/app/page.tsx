"use client";

import { useEffect, useMemo, useState } from "react";
import { EvolutionModal } from "@/components/EvolutionModal";
import { MonthFilter } from "@/components/MonthFilter";
import { fetchDashboardData } from "@/lib/api";
import { formatCurrencyText } from "@/lib/formatters";

const MONTHS = [
  { value: 1, label: "Jan" },
  { value: 2, label: "Fev" },
  { value: 3, label: "Mar" },
  { value: 4, label: "Abr" },
  { value: 5, label: "Mai" },
  { value: 6, label: "Jun" },
  { value: 7, label: "Jul" },
  { value: 8, label: "Ago" },
  { value: 9, label: "Set" },
  { value: 10, label: "Out" },
  { value: 11, label: "Nov" },
  { value: 12, label: "Dez" },
];

type DashboardData = Record<string, any>;

function cleanText(value: unknown): string {
  if (value === null || value === undefined) return "";
  let text = String(value);

  if (/[ÃÂâð]/.test(text)) {
    try {
      text = decodeURIComponent(escape(text));
    } catch {
      // Keep the original and repair the common sequences below.
    }
  }

  return text
    .replace(/Ã¡/g, "á")
    .replace(/Ã /g, "à")
    .replace(/Ã¢/g, "â")
    .replace(/Ã£/g, "ã")
    .replace(/Ã©/g, "é")
    .replace(/Ãª/g, "ê")
    .replace(/Ã­/g, "í")
    .replace(/Ã³/g, "ó")
    .replace(/Ã´/g, "ô")
    .replace(/Ãµ/g, "õ")
    .replace(/Ãº/g, "ú")
    .replace(/Ã§/g, "ç")
    .replace(/Ã/g, "Á")
    .replace(/Ã‰/g, "É")
    .replace(/ÃŠ/g, "Ê")
    .replace(/Ã‡/g, "Ç")
    .replace(/Âº/g, "º")
    .replace(/â€“/g, "–")
    .replace(/â€¢/g, "•")
    .replace(/â–²/g, "▲")
    .replace(/â–¼/g, "▼");
}

function normalizeKey(value: unknown): string {
  return cleanText(value)
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .trim();
}

function sortMonths(months: number[]) {
  return [...months].sort((a, b) => a - b);
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState(2026);
  const [months, setMonths] = useState([1, 2, 3]);
  const currentMonth = 3;
  const [periodOpen, setPeriodOpen] = useState(false);
  const [evolutionOpen, setEvolutionOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      setLoading(true);
      const dashboardData = await fetchDashboardData(year, sortMonths(months).join(","));
      if (isMounted) {
        setData(dashboardData);
        setLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [year, months]);

  const yearOptions = useMemo(() => [year - 1, year, year + 1], [year]);

  if (loading) {
    return (
      <main className="gd-app gd-app--centered">
        <div className="gd-loader" />
        <p>Carregando dados financeiros...</p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="gd-app gd-app--centered">
        <div className="gd-error">
          <h1>Erro de conexão</h1>
          <p>Não foi possível carregar os dados. Confirme se o backend FastAPI está rodando na porta 8000.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="gd-app">
      <button className="gd-evolution-fab" onClick={() => setEvolutionOpen(true)} title="Abrir evolução">
        ☰
      </button>

      <div className="gd-shell">
        <div className="gd-logo-wrap">
          <img className="gd-logo" src="/logo.png" alt="Logo Gondim" />
        </div>

        <Hero header={data.header} />

        <MonthFilter
          currentMonth={currentMonth}
          selectedMonths={months}
          onChange={(nextMonths) => setMonths(sortMonths(nextMonths))}
        />

        <section className="gd-top-section">
          <div className="gd-top-column">
            <RevenueCard data={data.revenue_mix} />
            <ResultCard data={data.net_result} />
            <PeopleCard data={data.people} />
          </div>
          <div className="gd-top-column gd-top-column--right">
            <CostCard data={data.cost_structure} />
            <MarginsCard data={data.margins} />
          </div>
        </section>

        <TopClientsCard
          data={data.top_clients}
          year={year}
          months={months}
          yearOptions={yearOptions}
          isOpen={periodOpen}
          onOpen={() => setPeriodOpen(true)}
          onClose={() => setPeriodOpen(false)}
          onApply={(newYear, newMonths) => {
            setYear(newYear);
            setMonths(sortMonths(newMonths));
            setPeriodOpen(false);
          }}
        />

        <Insights insights={data.insights} />
        <TechnicalAnalysis data={data.technical_analysis} />
      </div>

      <EvolutionModal open={evolutionOpen} onOpenChange={setEvolutionOpen} />
    </main>
  );
}

function Hero({ header }: { header: any }) {
  return (
    <section className="gd-hero">
      <div className="gd-hero__inner">
        <h1>{cleanText(header?.title || "Encontro de Divulgação de Resultados – Gondim | 2026 (EDR)")}</h1>
        <p className="gd-hero__subtitle">{cleanText(header?.subtitle || "Período acumulado")}</p>
      </div>
      <div className="gd-hero__band">{cleanText(header?.band || "Data de divulgação: 27 de março de 2026")}</div>
    </section>
  );
}

function RevenueCard({ data }: { data: any }) {
  const rows = data?.rows || [];
  const expansions = new Map(
    (data?.expansions || []).map((item: any) => [normalizeKey(item.title), item.items || []])
  );

  return (
    <article className="gd-card gd-card--blue">
      <div className="gd-card__header">
        <div className="gd-title">💰 {cleanText(data?.title || "Mix de Receitas")}</div>
        <div className="gd-kpi">{formatCurrencyText(cleanText(data?.value))}</div>
        <div className="gd-subline">{cleanText(data?.subtitle)}</div>
      </div>
      <div className="gd-surface">
        <div className="gd-revenue-list">
          {rows.map((row: any) => (
            <RevenueRow
              key={cleanText(row.label)}
              row={row}
              items={(expansions.get(normalizeKey(row.label)) as any[]) || []}
            />
          ))}
        </div>
      </div>
    </article>
  );
}

function RevenueRow({ row, items }: { row: any; items: any[] }) {
  const content = (
    <>
      <span className="gd-revenue-line__label">{cleanText(row.label)}</span>
      <span className="gd-revenue-line__metrics">
        <strong>{formatCurrencyText(cleanText(row.value))}</strong>
        <span>{cleanText(row.share)}</span>
      </span>
    </>
  );

  if (!items.length) {
    return <div className="gd-revenue-line gd-revenue-line--static">{content}</div>;
  }

  return (
    <details className="gd-revenue-line">
      <summary className="gd-revenue-line__summary">{content}</summary>
      <DetailRows items={items} />
    </details>
  );
}

function CostCard({ data }: { data: any }) {
  const items = data?.items || [];
  const special = items.filter((item: any) => {
    const label = normalizeKey(item.label);
    return label.includes("socios de servico") || label === "clt";
  });
  const remaining = items.filter((item: any) => !special.includes(item));

  return (
    <article className="gd-card gd-card--gray">
      <div className="gd-card__header">
        <div className="gd-title">📉 {cleanText(data?.title || "Estrutura de Custos")}</div>
        <div className="gd-kpi">{formatCurrencyText(cleanText(data?.value))}</div>
        <div className="gd-subline">{cleanText(data?.subtitle)}</div>
      </div>
      <div className="gd-cost-layout">
        <div className="gd-cost-layout__left">
          <div className="gd-cost gd-cost--highlight">
            <div className="gd-cost__label">{cleanText(data?.highlight?.label || "Impostos")}</div>
            <div className="gd-cost__value gd-cost__value--xl">{cleanText(data?.highlight?.value || "0,0%")}</div>
            <div className="gd-cost__caption">{cleanText(data?.highlight?.caption || "principal grupo de custo")}</div>
          </div>
          <div className="gd-cost-list">
            {special.map((item: any) => (
              <CostItem key={cleanText(item.label)} item={item} />
            ))}
          </div>
        </div>
        <div className="gd-cost-layout__right">
          <div className="gd-cost-list">
            {remaining.map((item: any) => (
              <CostItem key={cleanText(item.label)} item={item} />
            ))}
          </div>
        </div>
      </div>
    </article>
  );
}

function CostItem({ item }: { item: any }) {
  const details = item?.details || [];
  const head = (
    <>
      <div className="gd-cost-rect__head">
        <span className="gd-cost-rect__label">{cleanText(item.label)}</span>
        <span className="gd-cost-rect__share">{cleanText(item.share)}</span>
      </div>
      <div className="gd-cost-rect__value">{formatCurrencyText(cleanText(item.value))}</div>
    </>
  );

  if (!details.length) {
    return <div className="gd-cost-rect">{head}</div>;
  }

  return (
    <details className="gd-cost-rect gd-cost-rect--expandable">
      <summary className="gd-cost-rect__summary">{head}</summary>
      <DetailRows items={details} />
    </details>
  );
}

function ResultCard({ data }: { data: any }) {
  return (
    <article className="gd-card gd-card--orange gd-card--compact">
      <div className="gd-title">📊 {cleanText(data?.title || "Resultado Líquido")}</div>
      <div className="gd-kpi">{formatCurrencyText(cleanText(data?.value))}</div>
      <div className="gd-subline">{cleanText(data?.subtitle)}</div>
    </article>
  );
}

function PeopleCard({ data }: { data: any }) {
  return (
    <article className="gd-card gd-card--green gd-card--compact">
      <div className="gd-title">👥 {cleanText(data?.title || "Pessoas")}</div>
      <div className="gd-kpi">{cleanText(data?.value)}</div>
      <div className="gd-subline">{cleanText(data?.subtitle)}</div>
      {!!data?.rows?.length && (
        <div className="gd-list">
          {data.rows.map((row: any) => (
            <div className="gd-row" key={cleanText(row.label)}>
              <span className="gd-row__label">{cleanText(row.label)}</span>
              <span className="gd-row__value-group">
                <strong>{cleanText(row.value)}</strong>
                <span className="gd-pill gd-pill--inline">{cleanText(row.share)}</span>
              </span>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

function MarginsCard({ data }: { data: any }) {
  return (
    <article className="gd-card gd-card--purple gd-card--margins">
      <div className="gd-title">📈 {cleanText(data?.title || "Margens")}</div>
      <div className="gd-subline">{cleanText(data?.subtitle)}</div>
      <div className="gd-margins-grid">
        {(data?.metrics || []).map((metric: any) => (
          <div className="gd-margin-card" key={cleanText(metric.label)}>
            <div className="gd-margin-card__label">{cleanText(metric.label)}</div>
            <div className="gd-margin-card__value">{cleanText(metric.value)}</div>
            <div className="gd-margin-card__caption">{cleanText(metric.caption)}</div>
          </div>
        ))}
      </div>
    </article>
  );
}

function TopClientsCard({
  data,
  year,
  months,
  yearOptions,
  isOpen,
  onOpen,
  onClose,
  onApply,
}: {
  data: any;
  year: number;
  months: number[];
  yearOptions: number[];
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  onApply: (year: number, months: number[]) => void;
}) {
  return (
    <section className="gd-top-clients-row">
      <article className="gd-card gd-card--yellow">
        <div className="gd-card-inline-header">
          <div className="gd-title">🏆 {cleanText(data?.title || "Top 5 Clientes")}</div>
          <button className="gd-period-button" onClick={onOpen} title="Alterar período">
            +
          </button>
        </div>
        <div className="gd-subline">{cleanText(data?.subtitle)}</div>
        <div className="gd-list gd-list--spaced">
          {(data?.ranking || []).map((client: any, index: number) => (
            <div className="gd-row gd-row--client" key={`${client.name}-${index}`}>
              <strong>{index + 1}. {cleanText(client.name)}</strong>
              <span>{formatCurrencyText(cleanText(client.value))}</span>
            </div>
          ))}
        </div>
      </article>
      {isOpen && (
        <PeriodDialog
          year={year}
          months={months}
          yearOptions={yearOptions}
          onClose={onClose}
          onApply={onApply}
        />
      )}
    </section>
  );
}

function PeriodDialog({
  year,
  months,
  yearOptions,
  onClose,
  onApply,
}: {
  year: number;
  months: number[];
  yearOptions: number[];
  onClose: () => void;
  onApply: (year: number, months: number[]) => void;
}) {
  const [draftYear, setDraftYear] = useState(year);
  const [draftMonths, setDraftMonths] = useState(months);

  function toggleMonth(month: number) {
    setDraftMonths((current) =>
      current.includes(month)
        ? current.filter((item) => item !== month)
        : sortMonths([...current, month])
    );
  }

  return (
    <div className="gd-dialog-backdrop" role="dialog" aria-modal="true">
      <div className="gd-dialog">
        <div className="gd-dialog__header">
          <h2>Selecionar período</h2>
          <button onClick={onClose} title="Fechar">×</button>
        </div>
        <div className="gd-period-form">
          <label>
            <span>Ano</span>
            <select value={draftYear} onChange={(event) => setDraftYear(Number(event.target.value))}>
              {yearOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <div className="gd-month-grid">
            {MONTHS.map((month) => (
              <label key={month.value} className="gd-month-option">
                <input
                  type="checkbox"
                  checked={draftMonths.includes(month.value)}
                  onChange={() => toggleMonth(month.value)}
                />
                <span>{month.label}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="gd-dialog__actions">
          <button onClick={onClose}>Cancelar</button>
          <button
            className="gd-dialog__primary"
            disabled={!draftMonths.length}
            onClick={() => onApply(draftYear, draftMonths)}
          >
            Carregar
          </button>
        </div>
      </div>
    </div>
  );
}

function Insights({ insights }: { insights: any[] }) {
  if (!insights?.length) return null;

  return (
    <section className="gd-insights">
      {insights.map((insight: any, index: number) => (
        <article className={`gd-insight gd-insight--${cleanText(insight.tone || "blue")}`} key={`${insight.title}-${index}`}>
          <div className="gd-insight__title">{cleanText(insight.title)}</div>
          <div className="gd-insight__description">{cleanText(insight.description)}</div>
        </article>
      ))}
    </section>
  );
}

function TechnicalAnalysis({ data }: { data: any }) {
  return (
    <section className="gd-technical">
      <h2>{cleanText(data?.title || "Análise técnica")}</h2>
      {(data?.paragraphs || []).map((paragraph: string, index: number) => (
        <p key={index}>{cleanText(paragraph)}</p>
      ))}
    </section>
  );
}

function DetailRows({ items }: { items: any[] }) {
  return (
    <div className="gd-detail-rows">
      {items.map((item: any, index: number) => (
        <div className="gd-mini-row" key={`${item.name}-${index}`}>
          <span className="gd-mini-row__label">{index + 1}. {cleanText(item.name)}</span>
          <strong className="gd-mini-row__value">{formatCurrencyText(cleanText(item.value))}</strong>
        </div>
      ))}
    </div>
  );
}
