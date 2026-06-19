"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchEvolutionData, fetchProfitAdvanceData } from "@/lib/api";
import { formatCurrency } from "@/lib/formatters";

type EvolutionView = "annual" | "monthly" | "profitAdvance";

type EvolutionPoint = {
  label: string;
  year?: number;
  month_num?: number;
  receita: number;
  despesa: number;
  resultado: number;
};

type EvolutionPayload = {
  title: string;
  unit: string;
  data: EvolutionPoint[];
};

type ProfitAdvanceSummary = {
  resultadoMensal?: number;
  percentualAjusteMensalLucros?: number;
  totalAjusteMensalLucros?: number;
  totalQuotas?: number;
  ajusteMensalPorQuota?: number;
};

type ProfitAdvancePartnerRow = {
  index?: number;
  nivelSocietario?: string;
  level?: string;
  quotasServico?: number;
  quotas?: number;
  ajusteMensal?: number;
  adjustment?: number;
  antecipacaoFinal?: number;
  final?: number;
};

type ProfitAdvancePayload = {
  title?: string;
  summary?: ProfitAdvanceSummary;
  gan?: ProfitAdvancePartnerRow[];
  gaa?: ProfitAdvancePartnerRow[];
};

interface EvolutionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const MAX_VISIBLE_PROFIT_ADVANCE_ROWS = 13;

export function EvolutionModal({ open, onOpenChange }: EvolutionModalProps) {
  const [view, setView] = useState<EvolutionView>("annual");
  const [payload, setPayload] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const chartPayload = useMemo(
    () => view === "profitAdvance" ? null : normalizeEvolutionPayload(view, payload),
    [payload, view],
  );

  useEffect(() => {
    if (!open) return;

    let mounted = true;
    async function loadData() {
      setLoading(true);
      const data = view === "profitAdvance"
        ? await fetchProfitAdvanceData()
        : await fetchEvolutionData(view);

      if (mounted) {
        setPayload(data);
        setLoading(false);
      }
    }

    loadData();
    return () => {
      mounted = false;
    };
  }, [open, view]);

  if (!open) return null;

  return (
    <div className="gd-dialog-backdrop gd-dialog-backdrop--evolution" role="dialog" aria-modal="true">
      <div className="gd-evolution-dialog">
        <div className="gd-dialog__header">
          <h2>Análise de Evolução</h2>
          <button onClick={() => onOpenChange(false)} title="Fechar">×</button>
        </div>

        <div className="gd-evolution-tabs">
          <button className={view === "annual" ? "is-active" : ""} onClick={() => setView("annual")}>
            Evolução Anual
          </button>
          <button className={view === "monthly" ? "is-active" : ""} onClick={() => setView("monthly")}>
            Evolução Mensal
          </button>
          <button className={view === "profitAdvance" ? "is-active" : ""} onClick={() => setView("profitAdvance")}>
            Antecipação Lucros
          </button>
        </div>

        <div className="gd-chart-panel">
          {loading && <div className="gd-chart-state">Carregando dados...</div>}
          {!loading && view !== "profitAdvance" && chartPayload?.data.length ? <EvolutionChart chart={chartPayload} /> : null}
          {!loading && view === "profitAdvance" && payload?.summary && <ProfitAdvance data={payload} />}
          {!loading && view !== "profitAdvance" && !chartPayload?.data.length && (
            <div className="gd-chart-state">NÃ£o foi possÃ­vel carregar os dados de evoluÃ§Ã£o.</div>
          )}
          {!loading && view === "profitAdvance" && !payload?.summary && (
            <div className="gd-chart-state">Não foi possível carregar os dados de evolução.</div>
          )}
        </div>
      </div>
    </div>
  );
}

export function EvolutionDashboardSections() {
  const [annualPayload, setAnnualPayload] = useState<any>(null);
  const [monthlyPayload, setMonthlyPayload] = useState<any>(null);
  const [profitPayload, setProfitPayload] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const annualChart = useMemo(
    () => normalizeEvolutionPayload("annual", annualPayload),
    [annualPayload],
  );
  const monthlyChart = useMemo(
    () => normalizeEvolutionPayload("monthly", monthlyPayload),
    [monthlyPayload],
  );

  useEffect(() => {
    let mounted = true;

    async function loadData() {
      setLoading(true);
      const [annual, monthly, profit] = await Promise.all([
        fetchEvolutionData("annual"),
        fetchEvolutionData("monthly"),
        fetchProfitAdvanceData(),
      ]);

      if (mounted) {
        setAnnualPayload(annual);
        setMonthlyPayload(monthly);
        setProfitPayload(profit);
        setLoading(false);
      }
    }

    loadData();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <>
      <section className="gd-evolution-section" aria-label="Evolução financeira">
        <article className="gd-dashboard-chart-card">
          <div className="gd-dashboard-section-title">Evolução Anual</div>
          <div className="gd-chart-panel">
            {loading && <div className="gd-chart-state">Carregando dados...</div>}
            {!loading && annualChart?.data.length ? <EvolutionChart chart={annualChart} height={360} /> : null}
            {!loading && !annualChart?.data.length && (
              <div className="gd-chart-state">Não foi possível carregar os dados de evolução anual.</div>
            )}
          </div>
        </article>

        <article className="gd-dashboard-chart-card">
          <div className="gd-dashboard-section-title">Evolução Mensal</div>
          <div className="gd-chart-panel">
            {loading && <div className="gd-chart-state">Carregando dados...</div>}
            {!loading && monthlyChart?.data.length ? <EvolutionChart chart={monthlyChart} height={360} /> : null}
            {!loading && !monthlyChart?.data.length && (
              <div className="gd-chart-state">Não foi possível carregar os dados de evolução mensal.</div>
            )}
          </div>
        </article>
      </section>

      <section className="gd-profit-section" aria-label="Antecipação de lucros">
        <article className="gd-dashboard-chart-card gd-dashboard-chart-card--profit">
          <div className="gd-dashboard-section-heading">
            <div className="gd-dashboard-section-title">Antecipação de Lucros</div>
            <Link className="gd-secondary-action" href="/antecipacao-lucros">
              Ampliar visão
            </Link>
          </div>
          <div className="gd-chart-panel gd-profit-inline">
            {loading && <div className="gd-chart-state">Carregando dados...</div>}
            {!loading && profitPayload?.summary && <ProfitAdvance data={profitPayload} />}
            {!loading && !profitPayload?.summary && (
              <div className="gd-chart-state">Não foi possível carregar os dados de antecipação de lucros.</div>
            )}
          </div>
        </article>
      </section>
    </>
  );
}

function normalizeEvolutionPayload(view: EvolutionView, payload: any): EvolutionPayload | null {
  if (!payload) return null;

  const rawData = Array.isArray(payload) ? payload : payload.data;
  if (!Array.isArray(rawData)) return null;

  const data = rawData.map((item: any) => ({
    label: String(item.label ?? item.month ?? item.year ?? ""),
    year: typeof item.year === "number" ? item.year : Number(item.year) || undefined,
    month_num: typeof item.month_num === "number" ? item.month_num : Number(item.month_num) || undefined,
    receita: Number(item.receita || 0),
    despesa: Number(item.despesa || 0),
    resultado: Number(item.resultado || 0),
  }));

  const sortedData = view === "monthly"
    ? data
        .sort((a, b) => Number(a.year || 0) - Number(b.year || 0) || Number(a.month_num || 0) - Number(b.month_num || 0))
        .slice(-24)
    : data.sort((a, b) => Number(a.year || a.label) - Number(b.year || b.label));

  return {
    title: view === "monthly"
      ? "Evolucao Mensal: Receita vs Despesa vs Resultado"
      : "Evolucao Anual: Receita vs Despesa vs Resultado",
    unit: "R$",
    data: sortedData,
  };
}

function EvolutionChart({ chart, height = 390 }: { chart: EvolutionPayload; height?: number }) {
  return (
    <>
      <div className="gd-chart-title">
        <strong>{chart.title}</strong>
        <span>{chart.unit}</span>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chart.data} margin={{ top: 24, right: 28, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(226,232,240,0.12)" />
          <XAxis dataKey="label" stroke="rgba(226,232,240,0.68)" tick={{ fill: "rgba(226,232,240,0.68)" }} />
          <YAxis
            stroke="rgba(226,232,240,0.68)"
            tick={{ fill: "rgba(226,232,240,0.68)" }}
            tickFormatter={(value) => formatCurrency(Number(value))}
          />
          <Tooltip
            formatter={(value, name) => [formatCurrency(Number(value)), String(name)]}
            contentStyle={{
              background: "#0f172a",
              border: "1px solid rgba(148,163,184,0.22)",
              borderRadius: 14,
              color: "#f8fafc",
            }}
          />
          <Legend />
          <Line type="monotone" dataKey="receita" name="Receita" stroke="#60a5fa" strokeWidth={3} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="despesa" name="Despesa" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="resultado" name="Resultado" stroke="#fbbf24" strokeWidth={3} dot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </>
  );
}

const brCurrency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const brNumber = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });
const brPercent = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});
const brQuota = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 4, maximumFractionDigits: 4 });

function getRowLevel(row: ProfitAdvancePartnerRow) {
  return row.nivelSocietario || row.level || "";
}

export function ProfitAdvance({ data }: { data: ProfitAdvancePayload }) {
  const summary = data.summary || {};

  return (
    <div className="profit-advance-scroll">
      <section className="profit-advance" aria-label={data.title || "Antecipação mensal de distribuição de lucros"}>
        <div className="profit-advance__period-text">
          ABRIL / 2026 - PAGAMENTO EM JUNHO / 2026
        </div>
        <div className="profit-advance__summary-value profit-advance__summary-value--resultado">
          {brCurrency.format(Number(summary.resultadoMensal || 0))}
        </div>
        <div className="profit-advance__summary-value profit-advance__summary-value--percentual">
          {brPercent.format(Number(summary.percentualAjusteMensalLucros || 0))}
        </div>
        <div className="profit-advance__summary-value profit-advance__summary-value--total-ajuste">
          {brCurrency.format(Number(summary.totalAjusteMensalLucros || 0))}
        </div>
        <div className="profit-advance__summary-value profit-advance__summary-value--total-quotas">
          {brNumber.format(Number(summary.totalQuotas || 0))}
        </div>
        <div className="profit-advance__summary-value profit-advance__summary-value--ajuste-quota">
          {brQuota.format(Number(summary.ajusteMensalPorQuota || 0))}
        </div>

        <ProfitAdvanceTable variant="gan" rows={data.gan || []} />
        <ProfitAdvanceTable variant="gaa" rows={data.gaa || []} />
      </section>
    </div>
  );
}

function ProfitAdvanceTable({ variant, rows }: { variant: "gan" | "gaa"; rows: ProfitAdvancePartnerRow[] }) {
  const visibleRows = rows.slice(0, MAX_VISIBLE_PROFIT_ADVANCE_ROWS);

  return (
    <div className={`profit-advance__table profit-advance__table--${variant}`}>
      {visibleRows.map((row, index) => (
        <div className="profit-advance__row" key={`${variant}-${row.index || index}`}>
          <span className="profit-advance__cell profit-advance__cell--level">{getRowLevel(row)}</span>
          <span className="profit-advance__cell">{brNumber.format(Number(row.quotasServico ?? row.quotas ?? 0))}</span>
          <span className="profit-advance__cell">{brCurrency.format(Number(row.ajusteMensal ?? row.adjustment ?? 0))}</span>
          <span className="profit-advance__cell profit-advance__cell--final">
            {brCurrency.format(Number(row.antecipacaoFinal ?? row.final ?? 0))}
          </span>
        </div>
      ))}
    </div>
  );
}
