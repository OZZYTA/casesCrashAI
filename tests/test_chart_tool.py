from app.config.settings import Settings
from app.state.models import SQLRunResult
from app.tools.chart_tool import build_chart


def test_chart_tool_returns_metadata_for_bar_chart(tmp_path) -> None:
    result = SQLRunResult(
        columns=["categoria", "total_incidentes"],
        rows=[
            {"categoria": "Payments", "total_incidentes": 10},
            {"categoria": "Network", "total_incidentes": 8},
        ],
        row_count=2,
    )
    settings = Settings(CHART_OUTPUT_DIR=str(tmp_path))

    chart = build_chart("Incidentes por categoría", result, chart_type="bar", settings=settings)

    assert chart.chart_path is not None
    assert chart.chart_type == "bar"
    assert chart.x_column == "categoria"
    assert chart.y_column == "total_incidentes"
    assert chart.truncated_for_chart is False


def test_chart_tool_limits_many_categories(tmp_path) -> None:
    result = SQLRunResult(
        columns=["categoria", "total_incidentes"],
        rows=[{"categoria": f"Cat {index}", "total_incidentes": index} for index in range(20)],
        row_count=20,
    )
    settings = Settings(CHART_OUTPUT_DIR=str(tmp_path), CHART_TOP_N=5)

    chart = build_chart("Incidentes por categoría", result, chart_type="bar", settings=settings)

    assert chart.chart_path is not None
    assert chart.truncated_for_chart is True
    assert "top 5" in chart.message
