from langchain_core.messages import HumanMessage, SystemMessage

from app.llm.azure_client import build_azure_chat_model
from app.prompts.system_prompts import AGENT_ROLE_PROMPT
from app.prompts.tool_prompts import SQL_GENERATION_PROMPT
from app.state.models import SQLGenerationResult, SchemaInfo
from app.tools.json_utils import parse_json_object


def generate_sql(question: str, schema_info: SchemaInfo) -> SQLGenerationResult:
    """Generate governed PostgreSQL SELECT using Azure OpenAI."""
    llm = build_azure_chat_model(temperature=0.0)
    prompt = SQL_GENERATION_PROMPT.format(
        question=question,
        schema_description=schema_info.description,
    )
    response = llm.invoke(
        [
            SystemMessage(content=AGENT_ROLE_PROMPT),
            HumanMessage(content=prompt),
        ]
    )
    payload = parse_json_object(str(response.content))
    return SQLGenerationResult.model_validate(payload)

