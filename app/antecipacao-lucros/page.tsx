"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { FullscreenButton } from "@/components/FullscreenButton";
import { ProfitAdvanceStandalone } from "@/components/ProfitAdvanceStandalone";

export default function ProfitAdvancePage() {
  return (
    <main className="profit-advance-page">
      <FullscreenButton />
      <header className="profit-advance-page__header">
        <Link className="profit-advance-page__back" href="/">
          <ArrowLeft aria-hidden="true" size={18} />
          <span>Voltar</span>
        </Link>
        <h1>Antecipação de Lucros</h1>
      </header>
      <section className="profit-advance-page__content">
        <ProfitAdvanceStandalone />
      </section>
    </main>
  );
}
