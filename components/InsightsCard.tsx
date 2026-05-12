"use client";

import { Card } from "./Card";
import { Lightbulb } from "lucide-react";

interface InsightsCardProps {
  insights: any[];
}

export function InsightsCard({ insights }: InsightsCardProps) {
  if (!insights || insights.length === 0) return null;

  return (
    <Card className="flex flex-col h-full bg-[var(--background)]">
      <div className="flex items-center gap-2 mb-4 text-[var(--accent)]">
        <Lightbulb className="w-5 h-5" />
        <h2 className="text-lg font-semibold text-[var(--foreground)]">Insights</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight: any, i: number) => (
          <div key={i} className="p-4 rounded-xl bg-[var(--card)] border border-[var(--border)] shadow-sm">
            <h3 className="font-semibold text-[var(--foreground)] mb-2 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--accent)]" />
              {insight.title}
            </h3>
            <p className="text-sm text-[var(--text-muted)] leading-relaxed">
              {insight.description}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
}
