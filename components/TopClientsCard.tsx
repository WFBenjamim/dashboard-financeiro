"use client";

import { Card } from "./Card";

interface TopClientsCardProps {
  data: any;
}

export function TopClientsCard({ data }: TopClientsCardProps) {
  if (!data) return null;

  return (
    <Card className="flex flex-col h-full relative overflow-hidden group col-span-1 lg:col-span-2">
      <div className="flex items-center justify-between mb-6 relative z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[var(--accent)]/10 text-[var(--accent)]">
            <span className="text-xl">{data.icon || "🏆"}</span>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-[var(--foreground)]">{data.title}</h2>
            <div className="text-sm text-[var(--text-muted)]">{data.subtitle}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 relative z-10">
        {data.ranking?.map((client: any, i: number) => (
          <div key={i} className="flex flex-col p-4 rounded-xl bg-[var(--background)] border border-[var(--border)] relative overflow-hidden group/item hover:border-[var(--accent)] transition-colors">
            <div className="absolute -right-4 -bottom-4 text-6xl font-black text-[var(--border)] opacity-20 group-hover/item:text-[var(--accent)]/10 transition-colors pointer-events-none">
              {i + 1}
            </div>
            <span className="text-sm text-[var(--text-muted)] mb-2 truncate max-w-[90%]" title={client.name}>
              {client.name}
            </span>
            <span className="text-xl font-bold text-[var(--foreground)] mt-auto">
              {client.value}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}
