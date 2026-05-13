import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm.azure_client import build_azure_chat_model
from app.prompts.system_prompts import AGENT_ROLE_PROMPT, ANALYSIS_PROMPT
from app.state.models import AnalysisResult, SQLRunResult
from app.tools.json_utils import parse_json_object


def analyze_results(question: str, sql: str, result: SQLRunResult) -> AnalysisResult:
    """Convert tabular query output into executive business findings."""
    if result.row_count == 0:
        return AnalysisResult(
            executive_summary="No se encontraron datos para responder con los filtros aplicados.",
            key_findings=[],
            caveats=["El resultado de la consulta está vacío; revisa periodo, severidad o alcance solicitado."],
        )

    llm = build_azure_chat_model(temperature=0.0)
    rows_json = json.dumps(result.rows[:50], ensure_ascii=False, default=str)
    prompt = ANALYSIS_PROMPT.format(question=question, sql=sql, rows=rows_json)
    response = llm.invoke([SystemMessage(content=AGENT_ROLE_PROMPT), HumanMessage(content=prompt)])
    payload = parse_json_object(str(response.content))
    return AnalysisResult.model_validate(payload)

