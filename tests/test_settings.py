from pydantic import SecretStr

from app.config.settings import Settings


def test_database_url_uses_postgres_settings() -> None:
    settings = Settings(
        POSTGRES_HOST="db",
        POSTGRES_PORT=5433,
        POSTGRES_DB="ops",
        POSTGRES_USER="agent",
        POSTGRES_PASSWORD=SecretStr("secret"),
    )

    assert settings.database_url == "postgresql+psycopg://agent:secret@db:5433/ops"


def test_azure_config_detection() -> None:
    missing = Settings(
        AZURE_OPENAI_ENDPOINT="",
        AZURE_OPENAI_API_KEY=None,
        AZURE_OPENAI_DEPLOYMENT="",
        AZURE_OPENAI_API_VERSION="",
    )
    configured = Settings(
        AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com/",
        AZURE_OPENAI_API_KEY=SecretStr("key"),
        AZURE_OPENAI_DEPLOYMENT="gpt-workshop",
        AZURE_OPENAI_API_VERSION="2024-08-01-preview",
    )

    assert missing.has_azure_openai is False
    assert configured.has_azure_openai is True
