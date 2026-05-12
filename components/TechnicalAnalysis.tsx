"use client";

import { Card } from "./Card";
import { FileText } from "lucide-react";

interface TechnicalAnalysisProps {
  data: any;
}

export function TechnicalAnalysis({ data }: TechnicalAnalysisProps) {
  if (!data) return null;

  return (
    <Card className="flex flex-col h-full bg-[var(--background)]">
      <div className="flex items-center gap-2 mb-4 text-[var(--accent)]">
        <FileText className="w-5 h-5" />
        <h2 className="text-lg font-semibold text-[var(--foreground)]">{data.title}</h2>
      </div>

      <div className="space-y-3">
        {data.paragraphs?.map((p: string, i: number) => (
          <p key={i} className="text-sm text-[var(--text-muted)] leading-relaxed">
            {p}
          </p>
        ))}
      </div>
    </Card>
  );
}
