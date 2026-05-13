import sys
from pathlib import Path

from langsmith import Client
from langsmith.utils import LangSmithError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config.settings import get_settings  # noqa: E402
from app.observability.logging import configure_logging  # noqa: E402
from app.observability.tracing import configure_langsmith  # noqa: E402


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)
    configure_langsmith(settings)

    if not settings.langsmith_tracing:
        print("LangSmith tracing está apagado: LANGSMITH_TRACING=false")
        raise SystemExit(0)

    if not settings.langsmith_api_key:
        print("Falta LANGSMITH_API_KEY en .env")
        raise SystemExit(1)

    try:
        client = Client(
            api_key=settings.langsmith_api_key.get_secret_value(),
            api_url=settings.langsmith_endpoint,
        )
        project = client.read_project(project_name=settings.langsmith_project)
    except LangSmithError as exc:
        print("No pude validar LangSmith con la configuración actual.")
        print(f"Endpoint: {settings.langsmith_endpoint}")
        print(f"Project: {settings.langsmith_project}")
        print("Revisa que la API key pertenezca al mismo workspace donde existe el proyecto.")
        print(f"Detalle técnico: {exc}")
        raise SystemExit(1) from exc

    print("LangSmith OK")
    print(f"Project: {project.name}")
    print(f"Project ID: {project.id}")


if __name__ == "__main__":
    main()
