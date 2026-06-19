"use client";

import Image from "next/image";
import { type ReactNode, useEffect, useState } from "react";
import CountUp from "react-countup";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { EvolutionDashboardSections } from "@/components/EvolutionModal";
import { FullscreenButton } from "@/components/FullscreenButton";
import { MonthFilter } from "@/components/MonthFilter";
import { ResultOpeningScreen } from "@/components/ResultOpeningScreen";
import { fetchDashboardData } from "@/lib/api";
import { formatCurrency, formatCurrencyText, parseCurrency } from "@/lib/formatters";

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

function availableMonthsUntil(month: number) {
  return Array.from({ length: month }, (_, index) => index + 1);
}

function OptionalSubline({ value }: { value: unknown }) {
  const text = cleanText(value);
  return text ? <div className="gd-subline">{text}</div> : null;
}

function OptionalCaption({ value }: { value: unknown }) {
  const text = cleanText(value);
  return text ? <div className="gd-margin-card__caption">{text}</div> : null;
}

function AnimatedCurrencyKpi({ value }: { value: unknown }) {
  const text = formatCurrencyText(cleanText(value));
  const parsed = parseCurrency(text);

  if (parsed === null) return <>{text}</>;

  return (
    <CountUp
      end={parsed}
      duration={1.35}
      formattingFn={(number) => formatCurrency(number)}
      redraw
    />
  );
}

function AnimatedNumberKpi({ value }: { value: unknown }) {
  const text = cleanText(value);
  const parsed = Number(text.replace(/\./g, "").replace(",", "."));

  if (!Number.isFinite(parsed)) return <>{text}</>;

  return (
    <CountUp
      end={parsed}
      duration={1.15}
      decimals={Number.isInteger(parsed) ? 0 : 1}
      decimal=","
      separator="."
      redraw
    />
  );
}

function AnimatedPercentKpi({ value }: { value: unknown }) {
  const text = cleanText(value);
  const parsed = Number(text.replace("%", "").replace(/\./g, "").replace(",", "."));

  if (!Number.isFinite(parsed)) return <>{text}</>;

  return (
    <CountUp
      end={parsed}
      duration={1.15}
      decimals={1}
      decimal=","
      suffix="%"
      redraw
    />
  );
}

function parseShareValue(value: unknown): number {
  const text = cleanText(value).replace("%", "").trim();
  if (!text) return 0;
  return Number(text.replace(/\./g, "").replace(",", ".")) || 0;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function formatPercentMetric(value: unknown): string {
  if (!isFiniteNumber(value)) return "";
  return `${(value * 100).toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}

function formatSignedPercentMetric(value: unknown): string {
  const formatted = formatPercentMetric(value);
  return isFiniteNumber(value) && value > 0 ? `+${formatted}` : formatted;
}

function findInsight(insights: any[] | undefined, title: string) {
  const expected = normalizeKey(title);
  return (insights || []).find((insight) => normalizeKey(insight?.title).includes(expected));
}

export default function Dashboard() {
  const [showOpening, setShowOpening] = useState(true);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const year = 2026;
  const currentMonth = 5;
  const [months, setMonths] = useState<number[]>([]);

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      setLoading(true);
      const effectiveMonths = months.length ? months : availableMonthsUntil(currentMonth);
      const dashboardData = await fetchDashboardData(year, sortMonths(effectiveMonths).join(","));
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

  if (showOpening) {
    return <ResultOpeningScreen onEnter={() => setShowOpening(false)} />;
  }

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
          <p>Não foi possível carregar os dados do dashboard. Confira os arquivos em public/data.</p>
        </div>
      </main>
    );
  }

  const revenueInsight = findInsight(data.insights, "Top 5 clientes");
  const costInsight = findInsight(data.insights, "Pessoas representam") || findInsight(data.insights, "Sócios");
  const resultInsight = findInsight(data.insights, "Efeito tesoura");
  const peopleInsight = findInsight(data.insights, "Estrutura de pessoas");

  return (
    <main className="gd-app">
      <FullscreenButton />
      <div className="gd-shell">
        <div className="gd-logo-wrap">
          <Image className="gd-logo" src="/logo.png" alt="Logo Gondim" width={420} height={160} priority />
        </div>

        <Hero header={data.header} />

        <MonthFilter
          currentMonth={currentMonth}
          selectedMonths={months}
          onChange={(nextMonths) => setMonths(sortMonths(nextMonths))}
        />

        <section className="gd-top-section">
          <RevenueCard data={data.revenue_mix} insight={revenueInsight} topClients={data.top_clients} />
          <CostCard data={data.cost_structure} insight={costInsight} distribution={data.costDistribution} />
        </section>

        <section className="gd-kpi-row">
          <ResultCard data={data.net_result} insight={resultInsight} />
          <PeopleCard data={data.people} insight={peopleInsight} />
          <MarginsCard data={data.margins} />
        </section>

        <EvolutionDashboardSections />
      </div>
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
      <div className="gd-hero__band">DATA DE DIVULGAÇÃO: 22 DE JUNHO DE 2026</div>
    </section>
  );
}

function RevenueCard({ data, insight, topClients }: { data: any; insight?: any; topClients?: any }) {
  const [showRevenueView, setShowRevenueView] = useState(false);
  const rows = data?.rows || [];
  const receitaOrcadaPeriodo = data?.receita_orcada_periodo ?? data?.meta_periodo_receita ?? data?.receita_orcada_anual ?? data?.receita_orcada;
  const hasMetrics = isFiniteNumber(receitaOrcadaPeriodo)
    || isFiniteNumber(data?.variacao_2025)
    || isFiniteNumber(data?.pct_orcado);
  const contractualExpansion = (data?.expansions || []).find((expansion: any) =>
    normalizeKey(expansion?.title).includes("contratuais")
  );
  const contractualDetails = contractualExpansion?.items?.length
    ? contractualExpansion.items
    : (topClients?.ranking || []).filter((item: any) => normalizeKey(item?.name) !== "outros").slice(0, 5);
  const contractualItems = contractualDetails.slice(0, 5);

  useEffect(() => {
    if (!showRevenueView) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setShowRevenueView(false);
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [showRevenueView]);

  return (
    <article className="gd-card gd-card--blue">
      <div className="gd-card__header">
        <CardTitle icon="/icones/receita.png" title={data?.title || "Estrutura de Receita"} />
        <div className="gd-kpi"><AnimatedCurrencyKpi value={data?.value} /></div>
        {hasMetrics && (
          <MetricaGrid>
            <MetricaMini label="Orçado período" value={isFiniteNumber(receitaOrcadaPeriodo) ? formatCurrency(receitaOrcadaPeriodo) : ""} />
            <MetricaMini
              label="vs 2025"
              value={formatSignedPercentMetric(data?.variacao_2025)}
              tone={isFiniteNumber(data?.variacao_2025) && data.variacao_2025 < 0 ? "red" : "green"}
            />
            <MetricaMini
              label="% Orçado Periodo"
              value={formatPercentMetric(data?.pct_orcado)}
            />
          </MetricaGrid>
        )}
        {!!rows.length && (
          <div className="gd-card-actions">
            <button
              className="gd-secondary-action"
              type="button"
              onClick={() => setShowRevenueView(true)}
            >
              Ampliar visão
            </button>
          </div>
        )}
      </div>
      {!!rows.length && (
        <div className="gd-revenue-card-visual">
          <div className="gd-revenue-card-visual__heading">
            <strong>Composição da receita</strong>
            <span>Contratuais em destaque</span>
          </div>
          <RevenueDistributionChart rows={rows} contractualItems={contractualItems} compact />
        </div>
      )}
      <InsightNote insight={insight} />
      {!!rows.length && showRevenueView && (
        <RevenueDistributionModal
          rows={rows}
          contractualItems={contractualItems}
          periodLabel={data?.meta_periodo_meses ? `${data.meta_periodo_meses} meses selecionados` : "Período selecionado"}
          onClose={() => setShowRevenueView(false)}
        />
      )}
    </article>
  );
}

const REVENUE_DISTRIBUTION_COLORS = ["#38BDF8", "#A78BFA", "#22D3EE"];

function RevenueDistributionChart({
  rows,
  contractualItems,
  compact = false,
}: {
  rows: any[];
  contractualItems: any[];
  compact?: boolean;
}) {
  const chartItems = rows.map((row: any) => ({
    name: cleanText(row.label),
    value: parseCurrency(cleanText(row.value)) || 0,
    percent: parseShareValue(row.share) / 100,
  }));
  const contractual = chartItems.find((item) => normalizeKey(item.name).includes("contratuais")) || chartItems[0];
  const secondaryItems = chartItems.filter((item) => item !== contractual);

  return (
    <div className={`gd-revenue-chart${compact ? " gd-revenue-chart--compact" : ""}`}>
      <div className="gd-revenue-chart__main">
        <div className="gd-revenue-donut-column">
          <div className="gd-revenue-donut-stage">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartItems}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius="57%"
                  outerRadius="87%"
                  paddingAngle={2}
                  startAngle={90}
                  endAngle={-270}
                  minAngle={2}
                  stroke="rgba(15, 35, 75, 0.62)"
                  strokeWidth={2}
                  animationBegin={80}
                  animationDuration={800}
                  animationEasing="ease-out"
                >
                  {chartItems.map((item, index) => (
                    <Cell
                      key={item.name}
                      fill={REVENUE_DISTRIBUTION_COLORS[index % REVENUE_DISTRIBUTION_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip content={<RevenueDistributionTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="gd-revenue-donut-summary">
            <span>{contractual?.name || "Contratuais"}</span>
            <strong>{formatCurrency(contractual?.value || 0)}</strong>
            <em>{formatPercentMetric(contractual?.percent || 0)}</em>
          </div>
        </div>

        <div className="gd-contractual-panel">
          <div className="gd-contractual-panel__header">
            <span>Principais clientes contratuais</span>
            <strong>{formatCurrency(contractual?.value || 0)}</strong>
          </div>
          <div className="gd-contractual-ranking">
            {contractualItems.map((item: any, index: number) => (
              <div className="gd-contractual-ranking__row" key={`${cleanText(item.name)}-${index}`}>
                <span>{index + 1}</span>
                <strong>{cleanText(item.name)}</strong>
                <em>{formatCurrencyText(cleanText(item.value))}</em>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="gd-revenue-secondary">
        {secondaryItems.map((item, index) => (
          <div className="gd-revenue-secondary__item" key={item.name}>
            <span
              className="gd-revenue-secondary__swatch"
              data-color-index={(index + 1) % REVENUE_DISTRIBUTION_COLORS.length}
              aria-hidden="true"
            />
            <div>
              <span>{item.name}</span>
              <strong>{formatCurrency(item.value)}</strong>
            </div>
            <em>{formatPercentMetric(item.percent)}</em>
          </div>
        ))}
      </div>
    </div>
  );
}

function RevenueDistributionModal({
  rows,
  contractualItems,
  periodLabel,
  onClose,
}: {
  rows: any[];
  contractualItems: any[];
  periodLabel: string;
  onClose: () => void;
}) {
  return (
    <div className="gd-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="gd-modal gd-revenue-distribution"
        role="dialog"
        aria-modal="true"
        aria-labelledby="gd-revenue-distribution-title"
        onClick={(event) => event.stopPropagation()}
      >
        <button className="gd-modal__close" type="button" aria-label="Fechar" onClick={onClose}>
          ×
        </button>
        <div className="gd-modal__header">
          <h2 id="gd-revenue-distribution-title">Distribuição de Receita</h2>
          <p>{cleanText(periodLabel)}</p>
        </div>
        <div className="gd-revenue-distribution__body">
          <RevenueDistributionChart rows={rows} contractualItems={contractualItems} />
        </div>
      </div>
    </div>
  );
}

function RevenueDistributionTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const item = payload[0]?.payload || {};

  return (
    <div className="gd-chart-tooltip">
      <strong>{cleanText(item.name)}</strong>
      <span>{formatCurrency(Number(item.value || 0))}</span>
      <span>{formatPercentMetric(Number(item.percent || 0))}</span>
    </div>
  );
}

const COST_DISTRIBUTION_COLORS = [
  "#F59C27",
  "#FBBF24",
  "#FB7185",
  "#F97316",
  "#EF4444",
  "#FDBA74",
  "#E879F9",
  "#A78BFA",
  "#FDE68A",
  "#C084FC",
];

function CostCard({ data, insight, distribution }: { data: any; insight?: any; distribution?: any }) {
  const [showDistribution, setShowDistribution] = useState(false);
  const custoOrcadoPeriodo = data?.custo_orcado_periodo ?? data?.meta_periodo_custos ?? data?.custo_orcado_anual;
  const hasMetrics = isFiniteNumber(custoOrcadoPeriodo)
    || isFiniteNumber(data?.variacao_2025)
    || isFiniteNumber(data?.pct_orcado_custos);
  const hasDistribution = Boolean(distribution?.available && distribution?.items?.length);

  useEffect(() => {
    if (!showDistribution) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setShowDistribution(false);
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [showDistribution]);

  return (
    <article className="gd-card gd-card--gray">
      <div className="gd-card__header">
        <CardTitle icon="/icones/custo.png" title={data?.title || "Estrutura de Custos"} />
        <div className="gd-kpi"><AnimatedCurrencyKpi value={data?.value} /></div>
        {hasMetrics && (
          <MetricaGrid>
            <MetricaMini label="Orçado período" value={isFiniteNumber(custoOrcadoPeriodo) ? formatCurrency(custoOrcadoPeriodo) : ""} />
            <MetricaMini
              label="vs 2025"
              value={formatSignedPercentMetric(data?.variacao_2025)}
              tone={isFiniteNumber(data?.variacao_2025) && data.variacao_2025 > 0 ? "red" : "green"}
            />
            <MetricaMini
              label="% Orçado Periodo"
              value={formatPercentMetric(data?.pct_orcado_custos)}
              tone={isFiniteNumber(data?.pct_orcado_custos) && data.pct_orcado_custos > 1 ? "red" : "green"}
            />
          </MetricaGrid>
        )}
        {hasDistribution && (
          <div className="gd-card-actions">
            <button
              className="gd-secondary-action"
              type="button"
              onClick={() => setShowDistribution(true)}
            >
              Ampliar visão
            </button>
          </div>
        )}
      </div>
      {hasDistribution && (
        <div className="gd-cost-card-visual">
          <div className="gd-cost-card-visual__heading">
            <strong>Distribuição por grupo</strong>
            <span>{cleanText(distribution?.periodLabel || "Período selecionado")}</span>
          </div>
          <CostDistributionChart distribution={distribution} compact />
        </div>
      )}
      <InsightNote insight={insight} />
      {hasDistribution && showDistribution && (
        <CostDistributionModal
          distribution={distribution}
          onClose={() => setShowDistribution(false)}
        />
      )}
    </article>
  );
}

function CostDistributionChart({ distribution, compact = false }: { distribution: any; compact?: boolean }) {
  const items = distribution?.items || [];
  const total = Number(distribution?.total || 0);

  return (
    <div className={`gd-cost-chart${compact ? " gd-cost-chart--compact" : ""}`}>
      <div className="gd-donut-column">
        <div className="gd-donut-stage">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={items}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius="58%"
                outerRadius="86%"
                paddingAngle={1.5}
                startAngle={90}
                endAngle={-270}
                minAngle={1}
                stroke="rgba(77, 20, 12, 0.58)"
                strokeWidth={2}
                animationBegin={80}
                animationDuration={800}
                animationEasing="ease-out"
              >
                {items.map((item: any, index: number) => (
                  <Cell
                    key={cleanText(item.name)}
                    fill={COST_DISTRIBUTION_COLORS[index % COST_DISTRIBUTION_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip content={<CostDistributionTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="gd-donut-total">
          <span>Total</span>
          <strong>{formatCurrency(total)}</strong>
        </div>
      </div>

      <div className="gd-distribution-list">
        {items.map((item: any, index: number) => (
          <div className="gd-distribution-row" key={cleanText(item.name)}>
            <span
              className="gd-distribution-row__swatch"
              data-color-index={index % COST_DISTRIBUTION_COLORS.length}
              aria-hidden="true"
            />
            <span className="gd-distribution-row__name">{cleanText(item.name)}</span>
            <strong>{formatCurrency(Number(item.value || 0))}</strong>
            <span>{formatPercentMetric(Number(item.percent || 0))}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function CostDistributionModal({ distribution, onClose }: { distribution: any; onClose: () => void }) {
  return (
    <div className="gd-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="gd-modal gd-cost-distribution"
        role="dialog"
        aria-modal="true"
        aria-labelledby="gd-cost-distribution-title"
        onClick={(event) => event.stopPropagation()}
      >
        <button className="gd-modal__close" type="button" aria-label="Fechar" onClick={onClose}>
          ×
        </button>
        <div className="gd-modal__header">
          <h2 id="gd-cost-distribution-title">Distribuição de Custos</h2>
          <p>{cleanText(distribution?.periodLabel || "Período selecionado")}</p>
        </div>

        <div className="gd-cost-distribution__body">
          <CostDistributionChart distribution={distribution} />
        </div>
      </div>
    </div>
  );
}

function CostDistributionTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const item = payload[0]?.payload || {};

  return (
    <div className="gd-chart-tooltip">
      <strong>{cleanText(item.name)}</strong>
      <span>{formatCurrency(Number(item.value || 0))}</span>
      <span>{formatPercentMetric(Number(item.percent || 0))}</span>
    </div>
  );
}

function ResultCard({ data, insight }: { data: any; insight?: any }) {
  const hasMetrics = isFiniteNumber(data?.resultado_orcado)
    || isFiniteNumber(data?.variacao_2025)
    || isFiniteNumber(data?.pct_vs_orcado);

  return (
    <article className="gd-card gd-card--orange gd-card--compact">
      <CardTitle icon="/icones/liquido.png" title={data?.title || "Resultado Líquido"} />
      <div className="gd-kpi"><AnimatedCurrencyKpi value={data?.value} /></div>
      {hasMetrics && (
        <MetricaGrid>
          <MetricaMini label="Orçado" value={isFiniteNumber(data?.resultado_orcado) ? formatCurrency(data.resultado_orcado) : ""} />
          <MetricaMini
            label="vs 2025"
            value={formatSignedPercentMetric(data?.variacao_2025)}
            tone={isFiniteNumber(data?.variacao_2025) && data.variacao_2025 < 0 ? "red" : "green"}
          />
          <MetricaMini
            label="% Orçado Periodo"
            value={formatPercentMetric(data?.pct_vs_orcado)}
          />
        </MetricaGrid>
      )}
      <InsightNote insight={insight} />
    </article>
  );
}

function MetricaGrid({ children }: { children: ReactNode }) {
  return <div className="gd-result-mini-grid">{children}</div>;
}

function CardTitle({ icon, title }: { icon: string; title: unknown }) {
  return (
    <div className="gd-title">
      <Image className="gd-card-title-icon" src={icon} alt="" width={24} height={24} unoptimized aria-hidden="true" />
      <span>{cleanText(title)}</span>
    </div>
  );
}

function MetricaMini({ label, value, tone }: { label: string; value: string; tone?: "red" | "green" }) {
  return (
    <div className="gd-result-mini">
      <span>{label}</span>
      <strong className={tone ? `gd-result-mini__value--${tone}` : undefined}>{value}</strong>
    </div>
  );
}

function PeopleCard({ data, insight }: { data: any; insight?: any }) {
  return (
    <article className="gd-card gd-card--green gd-card--compact">
      <CardTitle icon="/icones/pessoas.png" title={data?.title || "Pessoas"} />
      <div className="gd-kpi"><AnimatedNumberKpi value={data?.value} /></div>
      <OptionalSubline value={data?.subtitle} />
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
      <InsightNote insight={insight} />
    </article>
  );
}

function MarginsCard({ data }: { data: any }) {
  const marginMetrics = (data?.metrics || []).map((metric: any) => {
    const isOperational = normalizeKey(metric.label).includes("operacional");
    const target = isOperational ? 0.35 : 0.17;
    const payloadValue = isOperational ? data?.operational : data?.net;
    const actual = isFiniteNumber(payloadValue)
      ? payloadValue
      : parseShareValue(metric.value) / 100;
    const attainment = target ? actual / target : 0;

    return {
      ...metric,
      actual,
      target,
      attainment,
    };
  });

  return (
    <article className="gd-card gd-card--purple gd-card--margins">
      <CardTitle icon="/icones/margens.png" title={data?.title || "Margens"} />
      <OptionalSubline value={data?.subtitle} />
      <div className="gd-margins-grid">
        {marginMetrics.map((metric: any) => (
          <div className="gd-margin-card" key={cleanText(metric.label)}>
            <div className="gd-margin-card__label">{cleanText(metric.label)}</div>
            <div className="gd-margin-card__value"><AnimatedPercentKpi value={metric.value} /></div>
            <div className="gd-margin-card__benchmarks">
              <div>
                <span>Meta acumulada</span>
                <strong>{formatPercentMetric(metric.target)}</strong>
              </div>
              <div>
                <span>Atingimento</span>
                <strong>{formatPercentMetric(metric.attainment)}</strong>
              </div>
            </div>
            <progress
              className="gd-margin-progress"
              max={1}
              value={Math.min(Math.max(metric.attainment, 0), 1)}
              aria-label={`Atingimento da meta de ${cleanText(metric.label)}`}
            />
            <OptionalCaption value={metric.caption} />
          </div>
        ))}
      </div>
    </article>
  );
}

function InsightNote({ insight }: { insight?: any }) {
  if (!insight) return null;

  return (
    <div className={`gd-card-insight gd-card-insight--${cleanText(insight.tone || "blue")}`}>
      <strong>{cleanText(insight.title)}</strong>
      <span>{cleanText(insight.description)}</span>
    </div>
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
