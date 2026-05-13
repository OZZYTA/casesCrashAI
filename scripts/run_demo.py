import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config.settings import get_settings
from app.observability.logging import configure_logging
from app.observability.tracing import configure_langsmith


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the operational analytics agent.")
    parser.add_argument("--question", required=True, help="Business question in natural language.")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.app_log_level)
    configure_langsmith(settings)

    from app.graph.workflow import run_agent

    state = run_agent(args.question)
    response = state.final_response

    print("\nQUESTION")
    print(args.question)
    print("\nSTEPS")
    for step in state.steps_taken:
        print(f"- {step}")
    print("\nSQL")
    print(response.sql if response and response.sql else "No SQL generated.")
    print("\nVALIDATION")
    if state.validation:
        print(f"valid={state.validation.is_valid}")
        for reason in state.validation.reasons:
            print(f"- {reason}")
    else:
        print("No validation result.")
    print("\nRESULT")
    if state.sql_result:
        print(f"rows={state.sql_result.row_count}, truncated={state.sql_result.truncated}")
        for row in state.sql_result.rows[:10]:
            print(row)
    else:
        print("No SQL result.")
    print("\nFINAL SUMMARY")
    if response:
        print(response.summary)
        for finding in response.findings:
            print(f"- {finding}")
        if response.chart_path:
            print(f"\nCHART\n{response.chart_path}")
        if response.errors:
            print("\nERRORS")
            for error in response.errors:
                print(f"- {error.tool_name}: {error.message}")


if __name__ == "__main__":
    main()
