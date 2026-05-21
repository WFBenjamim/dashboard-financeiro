"use client";

import Image from "next/image";
import { Card } from "./Card";
import { TrendingDown } from "lucide-react";

interface CostCardProps {
  data: any;
}

export function CostCard({ data }: CostCardProps) {
  if (!data) return null;

  return (
    <Card className="flex flex-col h-full relative overflow-hidden group">
      <div className="absolute -right-6 -top-6 text-red-500/5 group-hover:text-red-500/10 transition-colors">
        <TrendingDown className="w-32 h-32" />
      </div>
      
      <div className="flex items-center gap-3 mb-4 relative z-10">
        <div className="p-2 rounded-lg bg-red-500/10 text-red-500">
          <Image className="gd-card-title-icon" src="/icones/custo.png" alt="" width={24} height={24} unoptimized aria-hidden="true" />
        </div>
        <h2 className="text-lg font-semibold text-[var(--foreground)]">{data.title}</h2>
      </div>

      <div className="mb-6 relative z-10">
        <div className="text-4xl font-bold tracking-tight text-[var(--foreground)]">{data.value}</div>
        <div className="text-sm text-[var(--text-muted)] mt-1">{data.subtitle}</div>
      </div>

      <div className="space-y-2 mt-auto relative z-10">
        {data.items?.map((item: any, i: number) => (
          <div key={i} className="flex items-center justify-between py-2 border-b border-[var(--border)] last:border-0">
            <span className="text-sm text-[var(--text-muted)]">{item.label}</span>
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-[var(--foreground)]">{item.value}</span>
              <span className="text-xs text-[var(--text-muted)] w-12 text-right">{item.share}</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
