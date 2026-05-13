from typing import Literal

from langgraph.graph import END, StateGraph
from langsmith import traceable

from app.graph.guards import should_abort
from app.graph.nodes import (
    analyze_results_node,
    assemble_final_response_node,
    build_chart_node,
    classify_request_node,
    generate_sql_node,
    inspect_schema_node,
    run_sql_node,
    validate_sql_node,
)
from app.state.models import AgentState


def _continue_or_assemble(state: dict) -> Literal["continue", "assemble"]:
    parsed = AgentState.model_validate(state)
    if should_abort(parsed):
        return "assemble"
    return "continue"


def _after_validation(state: dict) -> Literal["continue", "assemble"]:
    parsed = AgentState.model_validate(state)
    if should_abort(parsed):
        return "assemble"
    if not parsed.validation or not parsed.validation.is_valid:
        return "assemble"
    return "continue"


def _after_analysis(state: dict) -> Literal["chart", "assemble"]:
    parsed = AgentState.model_validate(state)
    if should_abort(parsed):
        return "assemble"
    if parsed.generated_sql and parsed.generated_sql.needs_chart:
        return "chart"
    if parsed.intent == "analytical_query_with_chart":
        return "chart"
    return "assemble"


def build_workflow():
    graph = StateGraph(AgentState)
    graph.add_node("classify_request", classify_request_node)
    graph.add_node("inspect_schema", inspect_schema_node)
    graph.add_node("generate_sql", generate_sql_node)
    graph.add_node("validate_sql", validate_sql_node)
    graph.add_node("run_sql", run_sql_node)
    graph.add_node("analyze_results", analyze_results_node)
    graph.add_node("build_chart", build_chart_node)
    graph.add_node("assemble_final_response", assemble_final_response_node)

    graph.set_entry_point("classify_request")
    graph.add_conditional_edges("classify_request", _continue_or_assemble, {
        "continue": "inspect_schema",
        "assemble": "assemble_final_response",
    })
    graph.add_conditional_edges("inspect_schema", _continue_or_assemble, {
        "continue": "generate_sql",
        "assemble": "assemble_final_response",
    })
    graph.add_conditional_edges("generate_sql", _continue_or_assemble, {
        "continue": "validate_sql",
        "assemble": "assemble_final_response",
    })
    graph.add_conditional_edges("validate_sql", _after_validation, {
        "continue": "run_sql",
        "assemble": "assemble_final_response",
    })
    graph.add_conditional_edges("run_sql", _continue_or_assemble, {
        "continue": "analyze_results",
        "assemble": "assemble_final_response",
    })
    graph.add_conditional_edges("analyze_results", _after_analysis, {
        "chart": "build_chart",
        "assemble": "assemble_final_response",
    })
    graph.add_edge("build_chart", "assemble_final_response")
    graph.add_edge("assemble_final_response", END)
    return graph.compile()


@traceable(name="operational_analytics_agent", run_type="chain")
def run_agent(question: str) -> AgentState:
    workflow = build_workflow()
    initial_state = AgentState(question=question)
    result = workflow.invoke(initial_state)
    return AgentState.model_validate(result)
