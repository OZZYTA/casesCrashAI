from app.graph.guards import register_step
from app.state.models import AgentState


def test_guard_allows_configured_second_generate_sql_call() -> None:
    state = AgentState(question="test")
    state = register_step(state, "generate_sql")
    state = register_step(state, "generate_sql")

    assert state.tool_call_counts["generate_sql"] == 2
    assert state.repeated_action_detected is False


def test_guard_blocks_third_generate_sql_call() -> None:
    state = AgentState(question="test")
    state = register_step(state, "generate_sql")
    state = register_step(state, "generate_sql")
    state = register_step(state, "generate_sql")

    assert state.repeated_action_detected is True
    assert any(not error.recoverable for error in state.errors)

