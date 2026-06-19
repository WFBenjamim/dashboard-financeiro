"use client";

import { useEffect, useState } from "react";
import { ProfitAdvance } from "@/components/EvolutionModal";
import { fetchProfitAdvanceData } from "@/lib/api";

export function ProfitAdvanceStandalone() {
  const [payload, setPayload] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function loadData() {
      const data = await fetchProfitAdvanceData();
      if (mounted) {
        setPayload(data);
        setLoading(false);
      }
    }

    void loadData();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return <div className="gd-chart-state">Carregando dados...</div>;
  }

  if (!payload?.summary) {
    return <div className="gd-chart-state">Não foi possível carregar os dados de antecipação de lucros.</div>;
  }

  return <ProfitAdvance data={payload} />;
}
