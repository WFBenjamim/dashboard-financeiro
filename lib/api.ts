/**
 * Camada de acesso a dados.
 *
 * O app Next.js usa os snapshots JSON em /public/data por padrão, o que funciona
 * localmente e no Vercel sem depender do backend Python legado. Se um backend
 * for criado no futuro, defina NEXT_PUBLIC_API_URL para buscar dados por API.
 */

type JsonData = any;

const API_BASE = process.env.NEXT_PUBLIC_API_URL;

async function fetchStatic(path: string): Promise<JsonData> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Static JSON not found: ${path} (${res.status})`);
  return res.json();
}

async function fetchAPI(path: string): Promise<JsonData> {
  if (!API_BASE) throw new Error("NEXT_PUBLIC_API_URL is not configured");

  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error: ${path} (${res.status})`);
  return res.json();
}

/** Converte "1,2,3" em "1-2-3" para montar o nome do arquivo. */
function monthsToFileKey(months: string): string {
  return months
    .split(",")
    .map((m) => m.trim())
    .sort((a, b) => Number(a) - Number(b))
    .join("-");
}

export async function fetchDashboardData(year: number, months: string) {
  try {
    const key = monthsToFileKey(months);
    return API_BASE
      ? await fetchAPI(`/api/dashboard?year=${year}&months=${months}`)
      : await fetchStatic(`/data/dashboard_${year}_${key}.json`);
  } catch (error) {
    console.error("[fetchDashboardData]", error);
    return null;
  }
}

export async function fetchEvolutionData(view: "annual" | "monthly") {
  try {
    return API_BASE
      ? await fetchAPI(`/api/evolution?view=${view}`)
      : await fetchStatic(`/data/evolution_${view}.json`);
  } catch (error) {
    console.error("[fetchEvolutionData]", error);
    return null;
  }
}

export async function fetchProfitAdvanceData() {
  try {
    return API_BASE
      ? await fetchAPI("/api/profit-advance")
      : await fetchStatic("/data/profit_advance.json");
  } catch (error) {
    console.error("[fetchProfitAdvanceData]", error);
    return null;
  }
}
