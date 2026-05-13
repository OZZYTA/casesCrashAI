import json
import sys
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config.settings import get_settings
from app.db.engine import build_engine
from app.db.introspection import inspect_database_contract
from app.observability.logging import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)
    try:
        report = inspect_database_contract(build_engine(settings), settings=settings)
    except SQLAlchemyError as exc:
        print("No pude conectarme a PostgreSQL con la configuración actual.")
        print(f"Host: {settings.postgres_host}")
        print(f"Port: {settings.postgres_port}")
        print(f"Database: {settings.postgres_db}")
        print(f"Schema: {settings.postgres_schema}")
        print(f"User: {settings.postgres_user}")
        print("\nRevisa que .env tenga los datos reales de Azure PostgreSQL y que tu IP esté permitida.")
        print(f"\nDetalle técnico: {exc}")
        raise SystemExit(1) from exc

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
