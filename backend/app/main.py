from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.routes import auth, data_transfer, expenses, incomes, recurring_expenses, stats
from app.core.config import get_settings
from app.db.session import engine

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(expenses.router, prefix=settings.api_prefix)
app.include_router(incomes.router, prefix=settings.api_prefix)
app.include_router(recurring_expenses.router, prefix=settings.api_prefix)
app.include_router(stats.router, prefix=settings.api_prefix)
app.include_router(data_transfer.router, prefix=settings.api_prefix)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/database")
def database_health_check() -> dict:
    with engine.connect() as connection:
        inspector = inspect(connection)
        tables = sorted(inspector.get_table_names())
        database = connection.execute(text("SELECT DATABASE()")).scalar()

    return {
        "status": "ok",
        "database": database,
        "tables": tables,
        "required_tables_ready": all(
            table in tables for table in ["users", "expenses", "monthly_incomes", "alembic_version"]
        ),
    }


@app.get("/health/routes")
def routes_health_check() -> dict:
    routes = []
    for route in app.routes:
        methods = sorted(method for method in (route.methods or []) if method not in {"HEAD", "OPTIONS"})
        if not methods:
            continue
        routes.append({"path": route.path, "methods": methods})

    return {"status": "ok", "routes": routes}
