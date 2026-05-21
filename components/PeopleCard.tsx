"use client";

import Image from "next/image";
import { Card } from "./Card";
import { Users } from "lucide-react";

interface PeopleCardProps {
  data: any;
}

export function PeopleCard({ data }: PeopleCardProps) {
  if (!data) return null;

  return (
    <Card className="flex flex-col h-full relative overflow-hidden group">
      <div className="absolute -right-6 -top-6 text-[var(--accent)]/5 group-hover:text-[var(--accent)]/10 transition-colors">
        <Users className="w-32 h-32" />
      </div>
      
      <div className="flex items-center gap-3 mb-6 relative z-10">
        <div className="p-2 rounded-lg bg-[var(--accent)]/10 text-[var(--accent)]">
          <Image className="gd-card-title-icon" src="/icones/pessoas.png" alt="" width={24} height={24} unoptimized aria-hidden="true" />
        </div>
        <h2 className="text-lg font-semibold text-[var(--foreground)]">{data.title}</h2>
      </div>

      <div className="mb-2 relative z-10">
        <div className="text-5xl font-bold tracking-tight text-[var(--foreground)]">{data.value}</div>
      </div>
      <div className="text-sm text-[var(--text-muted)] relative z-10">{data.subtitle}</div>
    </Card>
  );
}
