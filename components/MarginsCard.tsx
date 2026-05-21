"use client";

import Image from "next/image";
import { Card } from "./Card";
import { LineChart } from "lucide-react";

interface MarginsCardProps {
  data: any;
}

export function MarginsCard({ data }: MarginsCardProps) {
  if (!data) return null;

  return (
    <Card className="flex flex-col h-full relative overflow-hidden group">
      <div className="absolute -right-6 -top-6 text-[var(--accent)]/5 group-hover:text-[var(--accent)]/10 transition-colors">
        <LineChart className="w-32 h-32" />
      </div>
      
      <div className="flex items-center gap-3 mb-6 relative z-10">
        <div className="p-2 rounded-lg bg-[var(--accent)]/10 text-[var(--accent)]">
          <Image className="gd-card-title-icon" src="/icones/margens.png" alt="" width={24} height={24} unoptimized aria-hidden="true" />
        </div>
        <h2 className="text-lg font-semibold text-[var(--foreground)]">{data.title}</h2>
      </div>

      <div className="grid grid-cols-2 gap-4 mt-auto relative z-10">
        {data.metrics?.map((metric: any, i: number) => (
          <div key={i} className="p-4 rounded-xl bg-[var(--background)] border border-[var(--border)] text-center flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-[var(--foreground)] mb-1">{metric.value}</span>
            <span className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">{metric.label}</span>
            <span className="text-[10px] text-[var(--text-muted)] opacity-70 mt-1">{metric.caption}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}
