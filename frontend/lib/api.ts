export async function fetchDashboardData(year: number, months: string) {
  try {
    const res = await fetch(`http://localhost:8000/api/dashboard?year=${year}&months=${months}`, { cache: "no-store" });
    if (!res.ok) {
      throw new Error("Failed to fetch dashboard data");
    }
    return res.json();
  } catch (error) {
    console.error("Error fetching dashboard data:", error);
    return null;
  }
}

export async function fetchEvolutionData(view: "annual" | "monthly") {
  try {
    const res = await fetch(`http://localhost:8000/api/evolution?view=${view}`, { cache: "no-store" });
    if (!res.ok) {
      throw new Error("Failed to fetch evolution data");
    }
    return res.json();
  } catch (error) {
    console.error("Error fetching evolution data:", error);
    return null;
  }
}

export async function fetchProfitAdvanceData() {
  try {
    const res = await fetch("http://localhost:8000/api/profit-advance", { cache: "no-store" });
    if (!res.ok) {
      throw new Error("Failed to fetch profit advance data");
    }
    return res.json();
  } catch (error) {
    console.error("Error fetching profit advance data:", error);
    return null;
  }
}
