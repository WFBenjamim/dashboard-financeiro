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

interface EvolutionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

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
          {!loading && view === "profitAdvance" && payload?.companies && <ProfitAdvance data={payload} />}
          {!loading && !payload?.data && !payload?.companies && (
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

function ProfitAdvance({ data }: { data: any }) {
  return (
    <section className="ga-shell-next">
      <header className="ga-hero-next">
        <h3>{data.title}</h3>
        <p>{data.subtitle}</p>
      </header>

      <div className="ga-summary-next">
        {(data.metrics || []).map((metric: any) => (
          <div className="ga-summary-card" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </div>
        ))}
      </div>

      <div className="ga-company-grid">
        {(data.companies || []).map((company: any) => (
          <article className="ga-company-panel" key={company.short_name}>
            <div className="ga-company-head">
              <span>{company.short_name}</span>
              <h4>{company.company_name}</h4>
            </div>
            <div className="ga-table-next">
              <div className="ga-table-head">
                <span>Nível Societário</span>
                <span>Quotas</span>
                <span>Ajuste Mensal</span>
                <span>Antecipação Final</span>
              </div>
              {(company.rows || []).map((row: any) => (
                <div className="ga-table-row" key={`${company.short_name}-${row.index}`}>
                  <span>{row.level}</span>
                  <span>{row.quotas_formatted}</span>
                  <span>{row.adjustment_formatted}</span>
                  <strong>{row.final_formatted}</strong>
                </div>
              ))}
              <div className="ga-table-row ga-table-row--total">
                <span>Total</span>
                <span>{company.totals?.quotas_formatted}</span>
                <span>{company.totals?.adjustment_formatted}</span>
                <strong>{company.totals?.final_formatted}</strong>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
