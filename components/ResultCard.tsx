"use client";

import { Card } from "./Card";
import { BarChart3 } from "lucide-react";

interface ResultCardProps {
  data: any;
}

export function ResultCard({ data }: ResultCardProps) {
  if (!data) return null;

  return (
    <Card className="flex flex-col h-full bg-gradient-to-br from-[var(--card)] to-[var(--background)] relative overflow-hidden group border-[var(--accent)]/30">
      <div className="absolute -right-6 -top-6 text-[var(--accent)]/5 group-hover:text-[var(--accent)]/10 transition-colors">
        <BarChart3 className="w-40 h-40" />
      </div>
      
      <div className="flex items-center gap-3 mb-6 relative z-10">
        <div className="p-2 rounded-lg bg-[var(--accent)]/10 text-[var(--accent)]">
          <span className="text-xl">{data.icon || "📊"}</span>
        </div>
        <h2 className="text-lg font-semibold text-[var(--foreground)]">{data.title}</h2>
      </div>

      <div className="mb-2 relative z-10">
        <div className="text-5xl font-bold tracking-tight text-[var(--foreground)]">{data.value}</div>
      </div>
      <div className="text-sm text-[var(--text-muted)] relative z-10 mb-6">{data.subtitle}</div>

      <div className="mt-auto relative z-10 p-4 rounded-xl bg-[var(--accent)]/10 border border-[var(--accent)]/20 flex items-center justify-between">
        <span className="text-sm font-medium text-[var(--foreground)]">Margem Líquida Adotada</span>
        <span className="text-sm font-bold text-[var(--accent)]">{data.value} (Projeção)</span>
      </div>
    </Card>
  );
}
