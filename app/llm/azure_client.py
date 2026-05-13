from langchain_openai import AzureChatOpenAI

from app.config.settings import Settings, get_settings


def build_azure_chat_model(settings: Settings | None = None, *, temperature: float = 0.0) -> AzureChatOpenAI:
    settings = settings or get_settings()
    if not settings.has_azure_openai:
        raise RuntimeError(
            "Azure OpenAI is not configured. Set AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT and AZURE_OPENAI_API_VERSION."
        )

    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key.get_secret_value() if settings.azure_openai_api_key else None,
        azure_deployment=settings.azure_openai_deployment,
        api_version=settings.azure_openai_api_version,
        temperature=temperature,
    )

