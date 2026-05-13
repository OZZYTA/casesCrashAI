from pathlib import Path
from uuid import uuid4

import pandas as pd
import plotly.express as px

from app.config.settings import Settings, get_settings
from app.state.models import ChartResult, SQLRunResult


def build_chart(
    question: str,
    result: SQLRunResult,
    chart_type: str | None = "bar",
    settings: Settings | None = None,
) -> ChartResult:
    """Build a Plotly chart from query results and write it as local HTML."""
    settings = settings or get_settings()
    if result.row_count == 0 or len(result.columns) < 2:
        return ChartResult(message="No hay suficientes datos tabulares para construir una gráfica.")

    output_dir = Path(settings.chart_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(result.rows)
    if df.empty:
        return ChartResult(message="La consulta no devolvió filas para graficar.")

    numeric_cols = [col for col in result.columns if pd.api.types.is_numeric_dtype(df[col])]
    if not numeric_cols:
        return ChartResult(
            message="No se encontró una métrica numérica para graficar. Ajusta la consulta para incluir conteos, sumas o promedios."
        )

    temporal_cols = [col for col in result.columns if _looks_temporal(col, df[col])]
    dimension_cols = [col for col in result.columns if col not in numeric_cols]

    x_col = temporal_cols[0] if temporal_cols else (dimension_cols[0] if dimension_cols else result.columns[0])
    y_col = numeric_cols[0]
    inferred_type = _choose_chart_type(chart_type, x_col, df[x_col], len(df))

    truncated_for_chart = False
    message = "Gráfica generada correctamente."
    if inferred_type in {"bar", "pie"} and len(df) > settings.chart_top_n:
        df = df.sort_values(y_col, ascending=False).head(settings.chart_top_n)
        truncated_for_chart = True
        message = f"Gráfica generada con top {settings.chart_top_n} categorías por {y_col}."

    title = question[:90]
    if inferred_type == "line":
        df = df.sort_values(x_col)
        fig = px.line(df, x=x_col, y=y_col, markers=True, title=title)
    elif inferred_type == "pie":
        fig = px.pie(df, names=x_col, values=y_col, title=title)
    else:
        fig = px.bar(df, x=x_col, y=y_col, text_auto=True, title=title)

    fig.update_layout(template="plotly_white", margin=dict(l=40, r=30, t=70, b=80))
    output_path = output_dir / f"chart_{uuid4().hex[:10]}.html"
    fig.write_html(output_path, include_plotlyjs="cdn")
    return ChartResult(
        chart_path=str(output_path.resolve()),
        chart_type=inferred_type,
        x_column=x_col,
        y_column=y_col,
        truncated_for_chart=truncated_for_chart,
        message=message,
    )


def _looks_temporal(column_name: str, series: pd.Series) -> bool:
    lowered = column_name.lower()
    if any(token in lowered for token in ["date", "fecha", "month", "mes", "week", "semana", "_at", "period"]):
        return True
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    return False


def _choose_chart_type(requested_type: str | None, x_col: str, x_series: pd.Series, row_count: int) -> str:
    if _looks_temporal(x_col, x_series):
        return "line"
    if requested_type == "pie" and row_count <= 8:
        return "pie"
    if requested_type == "line":
        return "line"
    return "bar"
