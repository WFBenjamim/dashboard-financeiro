"use client";

import { useState } from "react";
import { Download, Moon, Sun, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";

interface HeaderProps {
  title: string;
  subtitle: string;
  year: number;
  months: number[];
  onPeriodChange: (year: number, months: number[]) => void;
  onExportPdf: () => void;
}

export function Header({ title, subtitle, year, months, onPeriodChange, onExportPdf }: HeaderProps) {
  const [isDark, setIsDark] = useState(true);

  const toggleTheme = () => {
    const html = document.documentElement;
    if (html.classList.contains("dark")) {
      html.classList.remove("dark");
      setIsDark(false);
    } else {
      html.classList.add("dark");
      setIsDark(true);
    }
  };

  return (
    <header className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 pb-6 border-b border-[var(--border)] gap-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">{title}</h1>
        <p className="text-[var(--text-muted)] mt-1">{subtitle}</p>
      </div>
      
      <div className="flex items-center gap-3">
        {/* Simple period selector for demo purposes */}
        <div className="flex items-center bg-[var(--card)] border border-[var(--border)] rounded-lg p-1">
          <Calendar className="w-4 h-4 mx-2 text-[var(--text-muted)]" />
          <select 
            value={year} 
            onChange={(e) => onPeriodChange(Number(e.target.value), months)}
            className="bg-transparent border-none text-sm outline-none cursor-pointer pr-2 text-[var(--foreground)]"
          >
            {[2024, 2025, 2026].map(y => <option key={y} value={y} className="bg-[var(--card)]">{y}</option>)}
          </select>
        </div>

        <button 
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-[var(--card)] border border-[var(--border)] hover:bg-[var(--card-hover)] transition-colors text-[var(--foreground)]"
          title="Alternar Tema"
        >
          {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        <button 
          onClick={onExportPdf}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-black font-medium rounded-lg hover:opacity-90 transition-opacity shadow-sm"
        >
          <Download className="w-4 h-4" />
          <span>Exportar PDF</span>
        </button>
      </div>
    </header>
  );
}
