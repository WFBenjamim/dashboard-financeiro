"use client";

import { Card } from "./Card";
import { TrendingUp } from "lucide-react";

interface RevenueCardProps {
  data: any;
}

export function RevenueCard({ data }: RevenueCardProps) {
  if (!data) return null;

  return (
    <Card className="flex flex-col h-full relative overflow-hidden group">
      <div className="absolute -right-6 -top-6 text-[var(--accent)]/10 group-hover:text-[var(--accent)]/20 transition-colors">
        <TrendingUp className="w-32 h-32" />
      </div>
      
      <div className="flex items-center gap-3 mb-4 relative z-10">
        <div className="p-2 rounded-lg bg-[var(--accent)]/10 text-[var(--accent)]">
          <span className="text-xl">{data.icon || "💰"}</span>
        </div>
        <h2 className="text-lg font-semibold text-[var(--foreground)]">{data.title}</h2>
      </div>

      <div className="mb-6 relative z-10">
        <div className="text-4xl font-bold tracking-tight text-[var(--foreground)]">{data.value}</div>
        <div className="text-sm text-[var(--text-muted)] mt-1">{data.subtitle}</div>
      </div>

      <div className="space-y-3 mt-auto relative z-10">
        {data.rows?.map((row: any, i: number) => (
          <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
            <span className="text-sm font-medium text-[var(--foreground)]">{row.label}</span>
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-[var(--foreground)]">{row.value}</span>
              <span className="text-xs px-2 py-1 rounded bg-[var(--accent)]/10 text-[var(--accent)] font-medium">
                {row.share}
              </span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
