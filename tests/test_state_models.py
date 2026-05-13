from app.state.models import AnalysisResult, SQLGenerationResult


def test_sql_generation_accepts_string_assumption() -> None:
    result = SQLGenerationResult.model_validate(
        {
            "sql": "SELECT category_name, count(*) AS total FROM categories GROUP BY category_name",
            "rationale": "Agrupa incidentes por categoría.",
            "assumptions": "Se asume que no hay filtro temporal.",
            "needs_chart": True,
            "chart_type": "bar",
        }
    )

    assert result.assumptions == ["Se asume que no hay filtro temporal."]


def test_sql_generation_accepts_empty_chart_type() -> None:
    result = SQLGenerationResult.model_validate(
        {
            "sql": "SELECT category_name, count(*) AS total FROM categories GROUP BY category_name",
            "rationale": "Agrupa incidentes por categoría.",
            "assumptions": [],
            "needs_chart": False,
            "chart_type": "",
        }
    )

    assert result.chart_type is None


def test_analysis_result_accepts_string_caveat() -> None:
    result = AnalysisResult.model_validate(
        {
            "executive_summary": "Payments concentra más incidentes.",
            "key_findings": ["Payments lidera el ranking."],
            "caveats": "El análisis no incluye tendencias temporales.",
        }
    )

    assert result.caveats == ["El análisis no incluye tendencias temporales."]


def test_analysis_result_accepts_string_finding() -> None:
    result = AnalysisResult.model_validate(
        {
            "executive_summary": "Payments concentra más incidentes.",
            "key_findings": "Payments lidera el ranking.",
            "caveats": [],
        }
    )

    assert result.key_findings == ["Payments lidera el ranking."]
