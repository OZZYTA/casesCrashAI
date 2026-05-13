from app.config.settings import Settings, get_settings
from app.state.models import AgentState, ToolError


class WorkflowGuardError(RuntimeError):
    pass


STEP_CALL_LIMITS: dict[str, int] = {
    "classify_request": 1,
    "inspect_schema": 1,
    "generate_sql": 2,
    "validate_sql": 2,
    "run_sql": 1,
    "analyze_results": 1,
    "build_chart": 1,
    "assemble_final_response": 1,
}


def register_step(state: AgentState, step_name: str, settings: Settings | None = None) -> AgentState:
    settings = settings or get_settings()
    if len(state.steps_taken) >= settings.max_workflow_steps:
        state.errors.append(
            ToolError(
                tool_name="workflow_guard",
                message=f"Se alcanzó el límite de pasos del workflow ({settings.max_workflow_steps}).",
                recoverable=False,
            )
        )
        return state

    state.steps_taken.append(step_name)
    state.tool_call_counts[step_name] = state.tool_call_counts.get(step_name, 0) + 1
    max_calls = STEP_CALL_LIMITS.get(step_name, 1)

    if state.steps_taken[:-1] and state.steps_taken[-2] == step_name:
        state.errors.append(
            ToolError(
                tool_name="workflow_guard",
                message=f"Acción repetida consecutiva detectada: {step_name}.",
                recoverable=True,
                details={"step": step_name, "call_count": state.tool_call_counts[step_name], "max_calls": max_calls},
            )
        )

    if state.tool_call_counts[step_name] > max_calls:
        state.repeated_action_detected = True
        state.errors.append(
            ToolError(
                tool_name="workflow_guard",
                message=(
                    f"El step {step_name} excedió el máximo configurado "
                    f"({state.tool_call_counts[step_name]}/{max_calls})."
                ),
                recoverable=False,
                details={"step": step_name, "call_count": state.tool_call_counts[step_name], "max_calls": max_calls},
            )
        )
    return state


def should_abort(state: AgentState) -> bool:
    return bool(state.repeated_action_detected or any(not error.recoverable for error in state.errors))
