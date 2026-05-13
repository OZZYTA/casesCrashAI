from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm.azure_client import build_azure_chat_model
from app.prompts.system_prompts import AGENT_ROLE_PROMPT
from app.prompts.tool_prompts import INTENT_CLASSIFICATION_PROMPT
from app.state.models import ClassificationResult
from app.tools.json_utils import parse_json_object


@dataclass(frozen=True)
class HeuristicSignal:
    intent: str
    confidence: float
    reason: str


CHART_TERMS = {
    "gráfica",
    "grafica",
    "gráfico",
    "grafico",
    "visualiza",
    "visualización",
    "visualizacion",
    "chart",
    "plot",
}

COMPARATIVE_TERMS = {
    "compara",
    "comparar",
    "comparación",
    "comparacion",
    "crecimiento",
    "variación",
    "variacion",
    "versus",
    " vs ",
    "diferencia",
    "evolución",
    "evolucion",
}


def classify_request(question: str, *, llm_threshold: float = 0.74) -> ClassificationResult:
    """Hybrid intent classification: fast heuristic first, LLM only for ambiguous cases."""
    heuristic = _classify_with_heuristic(question)
    if heuristic.confidence >= llm_threshold:
        return ClassificationResult(
            intent=heuristic.intent,
            confidence=heuristic.confidence,
            method="heuristic",
            reason=heuristic.reason,
        )
    return _classify_with_llm(question)


def _classify_with_heuristic(question: str) -> HeuristicSignal:
    q = f" {question.lower()} "
    has_chart = any(term in q for term in CHART_TERMS)
    has_compare = any(term in q for term in COMPARATIVE_TERMS)

    if has_chart:
        return HeuristicSignal(
            intent="analytical_query_with_chart",
            confidence=0.92,
            reason="La pregunta contiene señal explícita de visualización.",
        )
    if has_compare:
        return HeuristicSignal(
            intent="comparative_analysis",
            confidence=0.86,
            reason="La pregunta contiene señal explícita de comparación o variación.",
        )
    if any(term in q for term in ["qué", "que", "cuál", "cual", "cuánt", "resumen", "resume", "top", "ranking"]):
        return HeuristicSignal(
            intent="analytical_query",
            confidence=0.68,
            reason="La pregunta parece analítica, pero no tiene señal fuerte de gráfica o comparación.",
        )
    return HeuristicSignal(
        intent="analytical_query",
        confidence=0.45,
        reason="No hay suficiente señal heurística; se requiere clasificación LLM.",
    )


def _classify_with_llm(question: str) -> ClassificationResult:
    llm = build_azure_chat_model(temperature=0.0)
    prompt = INTENT_CLASSIFICATION_PROMPT.format(question=question)
    response = llm.invoke([SystemMessage(content=AGENT_ROLE_PROMPT), HumanMessage(content=prompt)])
    payload = parse_json_object(str(response.content))
    payload["method"] = "llm"
    return ClassificationResult.model_validate(payload)
