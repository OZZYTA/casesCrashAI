from typing import Any

from app.config.settings import Settings, get_settings
from app.graph.guards import register_step, should_abort
from app.observability.logging import get_logger
from app.observability.tracing import traced_step
from app.state.models import AgentState, FinalResponse, ToolError
from app.tools.chart_tool import build_chart
from app.tools.request_classifier_tool import classify_request
from app.tools.result_analyzer_tool import analyze_results
from app.tools.schema_tool import get_schema_info
from app.tools.sql_generator_tool import generate_sql
from app.tools.sql_runner_tool import run_sql
from app.tools.sql_validator_tool import validate_sql


logger = get_logger(__name__)


def _state(raw_state: AgentState | dict[str, Any]) -> AgentState:
    return raw_state if isinstance(raw_state, AgentState) else AgentState.model_validate(raw_state)


def _dump(state: AgentState) -> dict[str, Any]:
    return state.model_dump()


def _record_error(state: AgentState, tool_name: str, exc: Exception, recoverable: bool = False) -> AgentState:
    state.errors.append(ToolError(tool_name=tool_name, message=str(exc), recoverable=recoverable))
    return state


def classify_request_node(raw_state: AgentState | dict[str, Any]) -> dict[str, Any]:
    state = register_step(_state(raw_state), "classify_request")
    if should_abort(state):
        return _dump(state)

    with traced_step("classify_request", question=state.question):
        state.classification = classify_request(state.question)
        state.intent = state.classification.intent
        logger.info(
            "request_classified",
            intent=state.intent,
            method=state.classification.method,
            confidence=state.classification.confidence,
            reason=state.classification.reason,
        )
    return _dump(state)


def inspect_schema_node(raw_state: AgentState | dict[str, Any]) -> dict[str, Any]:
    state = register_step(_state(raw_state), "inspect_schema")
    if should_abort(state):
        return _dump(state)

    try:
        with traced_step("inspect_schema"):
            state.schema_info = get_schema_info()
            logger.info("schema_loaded", allowed_tables=state.schema_info.allowed_tables)
    except Exception as exc:
        state = _record_error(state, "inspect_schema", exc)
    return _dump(state)


def generate_sql_node(raw_state: AgentState | dict[str, Any]) -> dict[str, Any]:
    state = register_step(_state(raw_state), "generate_sql")
    if should_abort(state) or not state.schema_info:
        return _dump(state)

    try:
        with traced_step("generate_sql"):
            state.generated_sql = generate_sql(state.question, state.schema_info)
            logger.info("sql_generated", sql=state.generated_sql.sql, needs_chart=state.generated_sql.needs_chart)
    except Exception as exc:
        state = _record_error(state, "generate_sql", exc)
    return _dump(state)


def validate_sql_node(raw_state: AgentState | dict[str, Any]) -> dict[str, Any]:
    state = register_step(_state(raw_state), "validate_sql")
    if should_abort(state) or not state.generated_sql:
        return _dump(state)

    try:
        with traced_step("validate_sql"):
            state.validation = validate_sql(state.generated_sql.sql)
            logger.info(
                "sql_validated",
                is_valid=state.validation.is_valid,
                reasons=state.validation.reasons,
                referenced_tables=state.validation.referenced_tables,
            )
    except Exception as exc:
        state = _record_error(state, "validate_sql", exc)
    return _dump(state)


def run_sql_node(raw_state: AgentState | dict[str, Any]) -> dict[str, Any]:
    state = register_step(_state(raw_state), "run_sql")
    if should_abort(state) or not state.validation or not state.validation.is_valid or not state.validation.safe_sql:
        return _dump(state)

    try:
        with traced_step("run_sql"):
            state.sql_result = run_sql(state.validation.safe_sql)
            logger.info("sql_executed", rows=state.sql_result.row_count, truncated=state.sql_result.truncated)
    except Exception as exc:
        state = _record_error(state, "run_sql", exc)
    return _dump(state)


def analyze_results_node(raw_state: AgentState | dict[str, Any]) -> dict[str, Any]:
    state = register_step(_state(raw_state), "analyze_results")
    if should_abort(state) or not state.sql_result or not state.validation or not state.validation.safe_sql:
        return _dump(state)

    try:
        with traced_step("analyze_results"):
            state.analysis = analyze_results(state.question, state.validation.safe_sql, state.sql_result)
            logger.info("results_analyzed", findings=len(state.analysis.key_findings))
    except Exception as exc:
        state = _record_error(state, "analyze_results", exc)
    return _dump(state)


def build_chart_node(raw_state: AgentState | dict[str, Any]) -> dict[str, Any]:
    state = register_step(_state(raw_state), "build_chart")
    if should_abort(state) or not state.sql_result:
        return _dump(state)

    try:
        with traced_step("build_chart"):
            chart_type = state.generated_sql.chart_type if state.generated_sql else "bar"
            state.chart = build_chart(state.question, state.sql_result, chart_type=chart_type)
            logger.info("chart_built", chart_path=state.chart.chart_path, chart_type=state.chart.chart_type)
    except Exception as exc:
        state = _record_error(state, "build_chart", exc, recoverable=True)
    return _dump(state)


def assemble_final_response_node(raw_state: AgentState | dict[str, Any]) -> dict[str, Any]:
    state = register_step(_state(raw_state), "assemble_final_response")
    settings: Settings = get_settings()

    with traced_step("assemble_final_response"):
        sql = state.validation.safe_sql if state.validation and state.validation.safe_sql else (
            state.generated_sql.sql if state.generated_sql else None
        )

        if state.analysis:
            summary = state.analysis.executive_summary
            findings = state.analysis.key_findings
        elif state.validation and not state.validation.is_valid:
            summary = "No ejecuté la consulta porque no pasó las reglas de seguridad SQL."
            findings = state.validation.reasons
        elif state.errors:
            summary = "El flujo no pudo completarse. Revisa los errores estructurados."
            findings = [error.message for error in state.errors]
        else:
            summary = "El flujo terminó sin resultados analizables."
            findings = []

        state.final_response = FinalResponse(
            question=state.question,
            sql=sql,
            summary=summary,
            findings=findings,
            chart_path=state.chart.chart_path if state.chart else None,
            errors=state.errors,
        )
        logger.info(
            "final_response_assembled",
            project=settings.langsmith_project,
            errors=len(state.errors),
            chart_path=state.final_response.chart_path,
        )
    return _dump(state)
