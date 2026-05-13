SQL_GENERATION_PROMPT = """\
Genera SQL PostgreSQL de solo lectura para responder la pregunta.

Pregunta:
{question}

Esquema permitido:
{schema_description}

Reglas obligatorias:
- Devuelve una única sentencia SELECT.
- No uses DELETE, UPDATE, INSERT, TRUNCATE, DROP, ALTER, CREATE, GRANT ni REVOKE.
- No uses múltiples statements ni punto y coma.
- No uses SELECT *.
- Usa solo tablas permitidas.
- Usa aliases claros.
- Limita resultados detallados con LIMIT cuando no sean agregados.
- Para "este mes", usa date_trunc('month', reported_at) = date_trunc('month', CURRENT_DATE).
- Para "último trimestre", usa reported_at >= CURRENT_DATE - INTERVAL '3 months'.
- Para severidad crítica usa severity_level = 'critical'; para alta usa severity_level IN ('high', 'critical') si el usuario habla de severidad alta en sentido amplio.
- Si se pide crecimiento entre meses, calcula conteos por mes y variación porcentual con NULLIF para evitar división por cero.
- Incluye columnas con nombres ejecutivos y fáciles de graficar.

Decide también si conviene gráfica:
- needs_chart true para comparaciones, rankings, series temporales o distribución por categoría/sede.
- chart_type: bar para rankings/distribuciones, line para series temporales, pie solo para composición simple.

Devuelve JSON estricto con estas llaves:
sql, rationale, assumptions, needs_chart, chart_type
"""


INTENT_CLASSIFICATION_PROMPT = """\
Clasifica la intención de esta pregunta de analítica operativa.

Pregunta:
{question}

Clases permitidas:
- analytical_query: pregunta analítica general sobre datos operativos.
- comparative_analysis: comparación entre periodos, sedes, categorías, severidades o crecimiento.
- analytical_query_with_chart: el usuario pide explícitamente una gráfica, visualización o mostrar datos visualmente.

Reglas:
- No expliques paso a paso.
- Usa analytical_query_with_chart si pide gráfica, gráfico, visualización, plot, chart, tendencia visual o "muéstrame" con intención visual.
- Usa comparative_analysis si pide comparar, crecimiento, variación, versus, ranking entre periodos o diferencias.
- Si no hay señal clara de comparación o gráfica, usa analytical_query.

Devuelve JSON estricto con estas llaves:
intent, confidence, reason
"""
