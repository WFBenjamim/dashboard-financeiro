from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from etl.loader import get_dashboard_content, load_antecipacao_lucros

app = FastAPI(title="Dashboard Financeiro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/dashboard")
def dashboard(year: int = 2026, months: str = "1,2,3"):
    selected_months = [int(m) for m in months.split(",")]
    return get_dashboard_content(year, selected_months)


@app.get("/api/evolution")
def evolution(view: str = "annual"):
    """Return chart-ready evolution data for the Next.js modal."""
    normalized_view = view.strip().lower()

    if normalized_view == "annual":
        return {
            "view": "annual",
            "title": "Evolução Anual: Receita vs Despesa vs Resultado",
            "unit": "R$ Milhões",
            "data": [
                {"label": "2022", "receita": 5.8, "despesa": 5.5, "resultado": 0.3},
                {"label": "2023", "receita": 6.2, "despesa": 6.0, "resultado": 0.2},
                {"label": "2024", "receita": 7.1, "despesa": 6.8, "resultado": 0.3},
                {"label": "2025", "receita": 8.5, "despesa": 6.8, "resultado": 1.7},
                {"label": "2026", "receita": 7.46, "despesa": 7.54, "resultado": -0.08},
            ],
        }

    if normalized_view == "monthly":
        return {
            "view": "monthly",
            "title": "Evolução Mensal (2026): Receita vs Despesa vs Resultado",
            "unit": "R$ Milhões",
            "data": [
                {"label": "Jan", "receita": 3.8, "despesa": 3.6, "resultado": 0.2},
                {"label": "Fev", "receita": 7.46, "despesa": 7.54, "resultado": -0.08},
                {"label": "Mar", "receita": 7.5, "despesa": 7.6, "resultado": -0.1},
                {"label": "Abr", "receita": 7.6, "despesa": 7.7, "resultado": -0.1},
                {"label": "Mai", "receita": 7.7, "despesa": 7.8, "resultado": -0.1},
                {"label": "Jun", "receita": 7.8, "despesa": 7.9, "resultado": -0.1},
                {"label": "Jul", "receita": 7.9, "despesa": 8.0, "resultado": -0.1},
                {"label": "Ago", "receita": 8.0, "despesa": 8.1, "resultado": -0.1},
                {"label": "Set", "receita": 8.1, "despesa": 8.2, "resultado": -0.1},
                {"label": "Out", "receita": 8.2, "despesa": 8.3, "resultado": -0.1},
                {"label": "Nov", "receita": 8.3, "despesa": 8.4, "resultado": -0.1},
                {"label": "Dez", "receita": 8.4, "despesa": 8.5, "resultado": -0.1},
            ],
        }

    raise HTTPException(status_code=400, detail="view must be 'annual' or 'monthly'")


@app.get("/api/profit-advance")
def profit_advance():
    return load_antecipacao_lucros()
