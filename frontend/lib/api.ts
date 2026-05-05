/**
 * api.ts
 * ------
 * Camada de acesso a dados.
 *
 * Em modo ESTÁTICO (build para GitHub Pages):
 *   NEXT_PUBLIC_STATIC=true  →  lê arquivos JSON pré-gerados em /public/data/
 *
 * Em modo DESENVOLVIMENTO:
 *   NEXT_PUBLIC_STATIC não definido  →  chama localhost:8000 (FastAPI)
 */

const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const USE_STATIC = process.env.NEXT_PUBLIC_STATIC === "true";
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ─── helpers ────────────────────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function fetchStatic(path: string): Promise<any> {
  const res = await fetch(`${BASE_PATH}${path}`);
  if (!res.ok) throw new Error(`Static JSON not found: ${path} (${res.status})`);
  return res.json();
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function fetchAPI(path: string): Promise<any> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error: ${path} (${res.status})`);
  return res.json();
}

/** Converte "1,2,3" → "1-2-3" (formato do nome do arquivo). */
function monthsToFileKey(months: string): string {
  return months
    .split(",")
    .map((m) => m.trim())
    .sort((a, b) => Number(a) - Number(b))
    .join("-");
}

// ─── funções públicas ────────────────────────────────────────────────────────

export async function fetchDashboardData(year: number, months: string) {
  try {
    if (USE_STATIC) {
      const key = monthsToFileKey(months);
      return await fetchStatic(`/data/dashboard_${year}_${key}.json`);
    }
    return await fetchAPI(`/api/dashboard?year=${year}&months=${months}`);
  } catch (error) {
    console.error("[fetchDashboardData]", error);
    return null;
  }
}

export async function fetchEvolutionData(view: "annual" | "monthly") {
  try {
    if (USE_STATIC) {
      return await fetchStatic(`/data/evolution_${view}.json`);
    }
    return await fetchAPI(`/api/evolution?view=${view}`);
  } catch (error) {
    console.error("[fetchEvolutionData]", error);
    return null;
  }
}

export async function fetchProfitAdvanceData() {
  try {
    if (USE_STATIC) {
      return await fetchStatic("/data/profit_advance.json");
    }
    return await fetchAPI("/api/profit-advance");
  } catch (error) {
    console.error("[fetchProfitAdvanceData]", error);
    return null;
  }
}
