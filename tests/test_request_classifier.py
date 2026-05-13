from app.tools.request_classifier_tool import classify_request


def test_heuristic_classifies_chart_request_without_llm() -> None:
    result = classify_request("Muéstrame una gráfica de incidentes por categoría")

    assert result.intent == "analytical_query_with_chart"
    assert result.method == "heuristic"
    assert result.confidence >= 0.9


def test_heuristic_classifies_comparative_request_without_llm() -> None:
    result = classify_request("Compara el crecimiento de incidentes entre enero y febrero")

    assert result.intent == "comparative_analysis"
    assert result.method == "heuristic"

