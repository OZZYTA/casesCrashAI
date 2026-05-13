import os
from contextlib import contextmanager
from time import perf_counter
from typing import Any, Iterator

from app.config.settings import Settings
from app.observability.logging import get_logger


logger = get_logger(__name__)


def configure_langsmith(settings: Settings) -> None:
    """Enable LangSmith when credentials exist, otherwise keep local execution intact."""
    enabled = bool(settings.langsmith_tracing and settings.langsmith_api_key)
    tracing_value = "true" if enabled else "false"
    os.environ["LANGSMITH_TRACING"] = tracing_value
    os.environ["LANGCHAIN_TRACING_V2"] = tracing_value
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
    if settings.langsmith_api_key:
        api_key = settings.langsmith_api_key.get_secret_value()
        os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ["LANGCHAIN_API_KEY"] = api_key

    logger.info(
        "langsmith_configured",
        enabled=enabled,
        project=settings.langsmith_project,
        endpoint=settings.langsmith_endpoint,
    )


@contextmanager
def traced_step(step_name: str, **context: Any) -> Iterator[None]:
    start = perf_counter()
    logger.info("step_started", step=step_name, **context)
    try:
        yield
        duration_ms = round((perf_counter() - start) * 1000, 2)
        logger.info("step_finished", step=step_name, duration_ms=duration_ms)
    except Exception as exc:
        duration_ms = round((perf_counter() - start) * 1000, 2)
        logger.exception("step_failed", step=step_name, duration_ms=duration_ms, error=str(exc))
        raise
