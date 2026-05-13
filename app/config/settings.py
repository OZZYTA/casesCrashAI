from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: Optional[SecretStr] = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_deployment: str = Field(default="", alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(default="2024-08-01-preview", alias="AZURE_OPENAI_API_VERSION")

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="ops_analytics", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: Optional[SecretStr] = Field(default=None, alias="POSTGRES_PASSWORD")
    postgres_schema: str = Field(default="public", alias="POSTGRES_SCHEMA")

    langsmith_api_key: Optional[SecretStr] = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="operational-analytics-agent", alias="LANGSMITH_PROJECT")
    langsmith_tracing: bool = Field(default=True, alias="LANGSMITH_TRACING")
    langsmith_endpoint: str = Field(default="https://api.smith.langchain.com", alias="LANGSMITH_ENDPOINT")

    app_log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")
    max_workflow_steps: int = Field(default=10, alias="MAX_WORKFLOW_STEPS")
    max_sql_rows: int = Field(default=200, alias="MAX_SQL_ROWS")
    sql_statement_timeout_ms: int = Field(default=8000, alias="SQL_STATEMENT_TIMEOUT_MS")
    chart_output_dir: str = Field(default="data/charts", alias="CHART_OUTPUT_DIR")
    chart_top_n: int = Field(default=12, alias="CHART_TOP_N")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        password = self.postgres_password.get_secret_value() if self.postgres_password else ""
        return (
            f"postgresql+psycopg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def has_azure_openai(self) -> bool:
        return bool(
            self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.azure_openai_deployment
            and self.azure_openai_api_version
        )

    @model_validator(mode="after")
    def normalize_log_level(self) -> "Settings":
        self.app_log_level = self.app_log_level.upper()
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
