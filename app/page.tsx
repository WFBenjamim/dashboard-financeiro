"use client";

import Image from "next/image";
import { type ReactNode, useEffect, useState } from "react";
import CountUp from "react-countup";
import { EvolutionDashboardSections } from "@/components/EvolutionModal";
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
  const [months, setMonths] = useState([1, 2, 3]);
  const currentMonth = 3;

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
  const costInsight = findInsight(data.insights, "Sócios de Serviço");
  const resultInsight = findInsight(data.insights, "Efeito tesoura");
  const peopleInsight = findInsight(data.insights, "Estrutura de pessoas");

  return (
    <main className="gd-app">
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
          <RevenueCard data={data.revenue_mix} insight={revenueInsight} />
          <CostCard data={data.cost_structure} insight={costInsight} />
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
      <div className="gd-hero__band">{cleanText(header?.band || "DATA DE DIVULGAÇÃO: 22 DE MAIO DE 2026")}</div>
    </section>
  );
}

function RevenueCard({ data, insight }: { data: any; insight?: any }) {
  const rows = data?.rows || [];
  const expansions = new Map(
    (data?.expansions || []).map((item: any) => [normalizeKey(item.title), item.items || []])
  );
  const receitaOrcadaAnual = data?.receita_orcada_anual ?? data?.receita_orcada;
  const hasMetrics = isFiniteNumber(receitaOrcadaAnual)
    || isFiniteNumber(data?.variacao_2025)
    || isFiniteNumber(data?.pct_orcado);

  return (
    <article className="gd-card gd-card--blue">
      <div className="gd-card__header">
        <div className="gd-title">💰 {cleanText(data?.title || "Mix de Receitas")}</div>
        <div className="gd-kpi"><AnimatedCurrencyKpi value={data?.value} /></div>
        <OptionalSubline value={data?.subtitle} />
        {hasMetrics && (
          <MetricaGrid>
            <MetricaMini label="Orçado anual" value={isFiniteNumber(receitaOrcadaAnual) ? formatCurrency(receitaOrcadaAnual) : ""} />
            <MetricaMini
              label="vs 2025"
              value={formatSignedPercentMetric(data?.variacao_2025)}
              tone={isFiniteNumber(data?.variacao_2025) && data.variacao_2025 < 0 ? "red" : "green"}
            />
            <MetricaMini label="% do orçado" value={formatPercentMetric(data?.pct_orcado)} />
          </MetricaGrid>
        )}
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
      <InsightNote insight={insight} />
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

function CostCard({ data, insight }: { data: any; insight?: any }) {
  const items = data?.items || [];
  const fallbackHighlight = [...items].sort((a: any, b: any) => parseShareValue(b?.share) - parseShareValue(a?.share))[0];
  const highlight = data?.highlight || fallbackHighlight || {};
  const special = items.filter((item: any) => {
    const label = normalizeKey(item.label);
    return label.includes("socios de servico") || label === "clt";
  });
  const remaining = items.filter((item: any) => !special.includes(item));
  const hasMetrics = isFiniteNumber(data?.custo_orcado_anual)
    || isFiniteNumber(data?.variacao_2025)
    || isFiniteNumber(data?.pct_orcado_custos);

  return (
    <article className="gd-card gd-card--gray">
      <div className="gd-card__header">
        <div className="gd-title">📉 {cleanText(data?.title || "Estrutura de Custos")}</div>
        <div className="gd-kpi"><AnimatedCurrencyKpi value={data?.value} /></div>
        <OptionalSubline value={data?.subtitle} />
        {hasMetrics && (
          <MetricaGrid>
            <MetricaMini label="Orçado anual" value={isFiniteNumber(data?.custo_orcado_anual) ? formatCurrency(data.custo_orcado_anual) : ""} />
            <MetricaMini
              label="vs 2025"
              value={formatSignedPercentMetric(data?.variacao_2025)}
              tone={isFiniteNumber(data?.variacao_2025) && data.variacao_2025 > 0 ? "red" : "green"}
            />
            <MetricaMini
              label="% do orçado"
              value={formatPercentMetric(data?.pct_orcado_custos)}
              tone={isFiniteNumber(data?.pct_orcado_custos) && data.pct_orcado_custos > 1 ? "red" : "green"}
            />
          </MetricaGrid>
        )}
      </div>
      <div className="gd-cost-layout">
        <div className="gd-cost-layout__left">
          <div className="gd-cost gd-cost--highlight">
            <div className="gd-cost__label">{cleanText(highlight?.label || "Principal grupo")}</div>
            <div className="gd-cost__value gd-cost__value--xl">{cleanText(highlight?.value || highlight?.share || "0,0%")}</div>
            {cleanText(highlight?.caption || (fallbackHighlight ? "principal grupo de custo" : "")) && (
              <div className="gd-cost__caption">
                {cleanText(highlight?.caption || (fallbackHighlight ? "principal grupo de custo" : ""))}
              </div>
            )}
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
      <InsightNote insight={insight} />
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

function ResultCard({ data, insight }: { data: any; insight?: any }) {
  const hasMetrics = isFiniteNumber(data?.resultado_orcado)
    || isFiniteNumber(data?.variacao_2025)
    || isFiniteNumber(data?.pct_vs_orcado);

  return (
    <article className="gd-card gd-card--orange gd-card--compact">
      <div className="gd-title">📊 {cleanText(data?.title || "Resultado Líquido")}</div>
      <div className="gd-kpi"><AnimatedCurrencyKpi value={data?.value} /></div>
      {isFiniteNumber(data?.sem_sucumbencia) && (
        <div className="gd-result-submetric">
          Resultado sem sucumbência: {formatCurrency(data.sem_sucumbencia)}
        </div>
      )}
      {hasMetrics && (
        <MetricaGrid>
          <MetricaMini label="Orçado" value={isFiniteNumber(data?.resultado_orcado) ? formatCurrency(data.resultado_orcado) : ""} />
          <MetricaMini
            label="vs 2025"
            value={formatSignedPercentMetric(data?.variacao_2025)}
            tone={isFiniteNumber(data?.variacao_2025) && data.variacao_2025 < 0 ? "red" : "green"}
          />
          <MetricaMini label="% Orçado" value={formatPercentMetric(data?.pct_vs_orcado)} />
        </MetricaGrid>
      )}
      {!isFiniteNumber(data?.sem_sucumbencia) && <OptionalSubline value={data?.subtitle} />}
      <InsightNote insight={insight} />
    </article>
  );
}

function MetricaGrid({ children }: { children: ReactNode }) {
  return <div className="gd-result-mini-grid">{children}</div>;
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
      <div className="gd-title">👥 {cleanText(data?.title || "Pessoas")}</div>
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
  return (
    <article className="gd-card gd-card--purple gd-card--margins">
      <div className="gd-title">📈 {cleanText(data?.title || "Margens")}</div>
      <OptionalSubline value={data?.subtitle} />
      <div className="gd-margins-grid">
        {(data?.metrics || []).map((metric: any) => (
          <div className="gd-margin-card" key={cleanText(metric.label)}>
            <div className="gd-margin-card__label">{cleanText(metric.label)}</div>
            <div className="gd-margin-card__value"><AnimatedPercentKpi value={metric.value} /></div>
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
