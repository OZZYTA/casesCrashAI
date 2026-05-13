# Agente de Analítica Operativa con LangGraph, PostgreSQL, Azure OpenAI y LangSmith

Proyecto base para el workshop técnico **"El agente no falló: falló el sistema alrededor del agente"**.

Este repositorio construye un agente real de analítica operativa: interpreta preguntas de negocio, inspecciona un esquema gobernado, genera SQL PostgreSQL de solo lectura, valida la consulta, ejecuta contra datos reales, analiza resultados y genera gráficas cuando aplica.

## Por qué esto sí es un agente real

No es un chatbot genérico ni un RAG básico. El modelo no responde solo desde memoria: participa dentro de un workflow con tools reales y contratos explícitos.

El flujo ideal es:

1. `classify_request`: identifica intención analítica con clasificación híbrida heurística + LLM si hay ambigüedad.
2. `get_schema_info`: expone solo tablas y columnas permitidas.
3. `generate_sql`: usa Azure OpenAI para producir SQL PostgreSQL de solo lectura.
4. `validate_sql`: aplica reglas de seguridad antes de tocar la base.
5. `run_sql`: ejecuta en PostgreSQL con transacción read-only y timeout.
6. `analyze_results`: convierte filas en hallazgos ejecutivos.
7. `build_chart`: genera HTML con Plotly si la intención lo requiere.
8. `assemble_final_response`: arma una respuesta trazable y depurable.

## Por qué LangGraph

LangGraph permite representar el sistema como un grafo explícito, no como una conversación abierta. Para este workshop eso importa porque:

- cada paso tiene responsabilidad clara,
- el estado es tipado y observable,
- las rutas de error son explícitas,
- se pueden limitar pasos y detectar repetición,
- es fácil introducir fallas controladas después sin desordenar toda la arquitectura.

## Estructura

```text
app/
  main.py
  graph/
    workflow.py
    nodes.py
    guards.py
  llm/
    azure_client.py
  tools/
    schema_tool.py
    sql_generator_tool.py
    sql_validator_tool.py
    sql_runner_tool.py
    result_analyzer_tool.py
    chart_tool.py
  db/
    engine.py
    models.py
    introspection.py
  prompts/
    system_prompts.py
    tool_prompts.py
  observability/
    tracing.py
    logging.py
  state/
    models.py
  config/
    settings.py
scripts/
  check_database.py
  run_demo.py
tests/
data/charts/
frontend/
  app.py
  theme.py
  styles.py
  components.py
  helpers.py
  sections/
```

## Setup local

Requisitos:

- Python 3.11+
- PostgreSQL accesible localmente o en red
- Azure OpenAI deployment de chat
- LangSmith opcional

Instalación:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configura `.env`:

```bash
AZURE_OPENAI_ENDPOINT=https://TU-RECURSO.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=...
AZURE_OPENAI_API_VERSION=2024-08-01-preview

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ops_analytics
POSTGRES_USER=postgres
POSTGRES_PASSWORD=...
POSTGRES_SCHEMA=public

LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=operational-analytics-agent
LANGSMITH_TRACING=false
```

Variables adicionales:

- `APP_LOG_LEVEL`: nivel de logs estructurados en consola.
- `POSTGRES_SCHEMA`: schema donde viven las tablas operativas. Por defecto `public`.
- `MAX_WORKFLOW_STEPS`: límite de pasos para evitar orquestación infinita.
- `MAX_SQL_ROWS`: máximo de filas devueltas por `run_sql`.
- `SQL_STATEMENT_TIMEOUT_MS`: timeout de queries en PostgreSQL.
- `CHART_OUTPUT_DIR`: carpeta para gráficas HTML.
- `CHART_TOP_N`: máximo de categorías visibles cuando una gráfica categórica tiene demasiados valores.

## Base de datos PostgreSQL

Este proyecto no carga CSV locales en runtime. Los CSV se usaron solo como referencia para definir el contrato de datos del agente. La fuente real debe ser una base PostgreSQL, por ejemplo Azure Database for PostgreSQL, configurada por `.env`.

El agente espera estas tablas en el schema definido por `POSTGRES_SCHEMA`:

- `branches`: sedes operativas con código, nombre, ciudad, región, fecha de apertura y estado activo.
- `categories`: categorías con dominio de negocio y bandera de seguimiento.
- `incidents`: tickets con sede, categoría, severidad, estado, fecha de reporte/resolución, usuarios afectados, horas de resolución, brecha de SLA, canal y resumen.

Puedes verificar que la base conectada cumple el contrato con:

```bash
python scripts/check_database.py
```

Ese script no crea ni modifica tablas; solo inspecciona PostgreSQL y reporta tablas/columnas faltantes frente al contrato gobernado.

Si ves un error como `relation "incidents" does not exist`, PostgreSQL sí recibió la consulta, pero no encontró esa tabla en el schema visible para el usuario. Ejecuta `python scripts/check_database.py` y revisa:

- que `POSTGRES_SCHEMA` sea el schema real donde están las tablas,
- que el usuario tenga permisos sobre ese schema,
- que los nombres físicos de tabla sean `branches`, `categories` e `incidents`.

## Ejecutar demo

```bash
python scripts/run_demo.py --question "¿Qué sede tuvo más incidentes críticos este mes?"
```

## Ejecutar frontend Streamlit

La demo ejecutiva vive en `frontend/` y consume la capa de servicio existente en `app/services/agent_service.py`; no reimplementa la lógica del agente.

```bash
streamlit run frontend/app.py
```

La interfaz muestra:

- panel de consulta abierto, sin preguntas precargadas,
- respuesta ejecutiva del agente,
- puntos clave del análisis,
- gráfica Plotly cuando el backend genera `chart_path`,
- datos de soporte en una sección secundaria cuando hay resultados tabulares.

La UI principal evita exponer detalles internos del agente; esos detalles quedan para consola, logs, LangSmith o herramientas de depuración.

Más ejemplos:

```bash
python scripts/run_demo.py --question "Compárame las categorías con mayor crecimiento entre enero y febrero"
python scripts/run_demo.py --question "¿Qué sede concentra más incidentes de severidad alta?"
python scripts/run_demo.py --question "Resume los hallazgos más importantes de los tickets del último trimestre"
python scripts/run_demo.py --question "Muéstrame una gráfica de los incidentes por categoría"
```

La salida imprime pregunta, pasos, SQL generado, validación, resultado, resumen final y ruta de gráfica cuando exista.

## Gobernanza de datos

El agente solo ve un contrato controlado de esquema en `app/tools/schema_tool.py`. No introspecta toda la base ni expone tablas arbitrarias al modelo. Ese contrato incluye tablas permitidas, columnas, relaciones y descripciones de negocio para que Azure OpenAI genere SQL con contexto suficiente sin conocer objetos no gobernados.

`validate_sql` bloquea:

- `DELETE`, `UPDATE`, `INSERT`, `TRUNCATE`, `DROP`, `ALTER`, `CREATE`, `GRANT`, `REVOKE`,
- múltiples statements o `;`,
- tablas fuera del allowlist,
- `SELECT *`,
- consultas no agregadas sin `LIMIT`.

`run_sql` agrega defensa en ejecución:

- transacción `READ ONLY`,
- `statement_timeout`,
- máximo de filas serializadas.

## Observabilidad con LangSmith

`app/observability/tracing.py` configura LangSmith desde `.env`. Si `LANGSMITH_API_KEY` está vacío, el sistema sigue funcionando localmente y desactiva tracing remoto.

Cuando está configurado, LangSmith registra llamadas del modelo y el flujo LangChain/LangGraph. Además, los logs estructurados muestran paso, duración, errores, SQL y rutas de salida relevantes.

Para validar credenciales antes de correr el agente:

```bash
python scripts/check_langsmith.py
```

Un `403 Forbidden` normalmente significa que `LANGSMITH_API_KEY` no pertenece al workspace/proyecto configurado en `LANGSMITH_PROJECT`, o que la key no tiene permisos de escritura.

## Cómo decide el flujo y las tools

El LLM no elige libremente qué tool llamar. LangGraph define el flujo y cada nodo llama una tool concreta:

- `classify_request` usa `request_classifier_tool.py`.
- `inspect_schema` usa `schema_tool.py`.
- `generate_sql` usa `sql_generator_tool.py`.
- `validate_sql` usa `sql_validator_tool.py`.
- `run_sql` usa `sql_runner_tool.py`.
- `analyze_results` usa `result_analyzer_tool.py`.
- `build_chart` usa `chart_tool.py`.

La clasificación inicial es híbrida: primero aplica señales rápidas y explicables; si la señal no es suficiente, usa Azure OpenAI con un prompt corto y salida estructurada.

## Cómo evita loops de tool calling

Este diseño evita dejar al modelo decidir indefinidamente qué tool llamar. El grafo es finito y explícito.

Mecanismos:

- `MAX_WORKFLOW_STEPS` limita pasos globales.
- `register_step` registra cada nodo ejecutado.
- Se detecta repetición inmediata de acción.
- Los límites por step están centralizados en `STEP_CALL_LIMITS` dentro de `app/graph/guards.py`.
- Algunos steps pueden repetirse de forma controlada, por ejemplo `generate_sql` y `validate_sql` admiten hasta 2 llamadas.
- Los errores no recuperables saltan a `assemble_final_response`.
- La validación SQL fallida corta antes de ejecutar PostgreSQL.

Esto hace que una falla de orquestación sea detectable y explicable, no un comportamiento silencioso.

## Capa de servicio para UI

Para conectar un front o API sin acoplarse a LangGraph directamente, usa:

```python
from app.services.agent_service import execute_agent

payload = execute_agent("Muéstrame una gráfica de incidentes por categoría")
```

La respuesta es un `dict` serializable con intención, clasificación, pasos, SQL, validación, resultado, análisis, gráfica y errores.

## Prompts

Los prompts viven en:

- `app/prompts/system_prompts.py`
- `app/prompts/tool_prompts.py`

Están separados para poder auditarlos en vivo. Incluyen reglas de seguridad SQL, ambigüedad temporal, resultados vacíos, decisión de gráfica y formato ejecutivo.

## Tests

```bash
pytest
```

Los tests actuales cubren validación SQL y configuración. No requieren Azure OpenAI ni PostgreSQL.

## Preparado para fallas futuras

Esta versión implementa el flujo sano. Para el workshop puedes introducir fallas controladas en puntos aislados:

- falla por contexto: modificar `schema_tool.py` para ocultar o describir mal columnas,
- falla por contrato de tool: cambiar modelos Pydantic en `state/models.py`,
- falla por ausencia de validación: saltar `validate_sql` en `workflow.py`,
- falla por orquestación: relajar `guards.py` o agregar ciclos al grafo,
- falla por manejo de errores: convertir errores no recuperables en recuperables en `nodes.py`.

La separación por módulos permite romper una capa sin convertir el proyecto en una demo artificial.
