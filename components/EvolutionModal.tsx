"use client";

import { useEffect, useState } from "react";
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
          {!loading && view !== "profitAdvance" && payload?.data && <EvolutionChart chart={payload} />}
          {!loading && view === "profitAdvance" && payload?.summary && <ProfitAdvance data={payload} />}
          {!loading && !payload?.data && !payload?.summary && (
            <div className="gd-chart-state">Não foi possível carregar os dados de evolução.</div>
          )}
        </div>
      </div>
    </div>
  );
}

function EvolutionChart({ chart }: { chart: any }) {
  return (
    <>
      <div className="gd-chart-title">
        <strong>{chart.title}</strong>
        <span>{chart.unit}</span>
      </div>
      <ResponsiveContainer width="100%" height={390}>
        <LineChart data={chart.data} margin={{ top: 24, right: 28, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(226,232,240,0.12)" />
          <XAxis dataKey="label" stroke="rgba(226,232,240,0.68)" tick={{ fill: "rgba(226,232,240,0.68)" }} />
          <YAxis
            stroke="rgba(226,232,240,0.68)"
            tick={{ fill: "rgba(226,232,240,0.68)" }}
            tickFormatter={(value) => formatCurrency(Number(value) * 1_000_000)}
          />
          <Tooltip
            formatter={(value, name) => [formatCurrency(Number(value) * 1_000_000), String(name)]}
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

function ProfitAdvance({ data }: { data: ProfitAdvancePayload }) {
  const summary = data.summary || {};

  return (
    <div className="profit-advance-scroll">
      <section className="profit-advance" aria-label={data.title || "Antecipação mensal de distribuição de lucros"}>
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
