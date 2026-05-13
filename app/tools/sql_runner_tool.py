from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from app.config.settings import Settings, get_settings
from app.db.engine import build_engine
from app.state.models import SQLRunResult


def _serialize_value(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "__float__") and value.__class__.__name__ == "Decimal":
        return float(value)
    return value


def run_sql(sql: str, settings: Settings | None = None, engine: Engine | None = None) -> SQLRunResult:
    """Execute a validated SELECT in a read-only PostgreSQL transaction."""
    settings = settings or get_settings()
    engine = engine or build_engine(settings)
    max_rows = settings.max_sql_rows

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text("SET LOCAL TRANSACTION READ ONLY"))
            connection.execute(text(f"SET LOCAL statement_timeout = {int(settings.sql_statement_timeout_ms)}"))
            connection.execute(text("SELECT set_config('search_path', :schema, true)"), {"schema": settings.postgres_schema})
            result = connection.execute(text(sql))
            rows = result.mappings().fetchmany(max_rows + 1)
            transaction.commit()
        except ProgrammingError as exc:
            transaction.rollback()
            if "UndefinedTable" in str(exc) or "does not exist" in str(exc):
                raise RuntimeError(
                    "La consulta referencia una tabla que PostgreSQL no encuentra en el schema configurado. "
                    f"Revisa POSTGRES_SCHEMA='{settings.postgres_schema}' y ejecuta scripts/check_database.py."
                ) from exc
            raise
        except Exception:
            transaction.rollback()
            raise

    columns = list(result.keys())
    truncated = len(rows) > max_rows
    serializable_rows = [
        {key: _serialize_value(value) for key, value in dict(row).items()} for row in rows[:max_rows]
    ]
    return SQLRunResult(columns=columns, rows=serializable_rows, row_count=len(serializable_rows), truncated=truncated)
