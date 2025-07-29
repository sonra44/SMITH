import argparse
import os

from .dynamic_planner import DynamicPlanner
from .plan_executor import PlanExecutor


# This class is now deprecated and will be removed later.
class Planner:
    pass


def main():
    """
    Main entry point for the SMITH Agent.
    This is now primarily for direct command-line execution of the agent logic,
    without the TUI.
    """
    parser = argparse.ArgumentParser(
        description="SMITH Agent: An AI orchestrator for development tasks."
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="The high-level task for the agent to perform.",
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="The absolute path to the project root directory.",
    )
    args = parser.parse_args()

    # Dynamic, step-by-step execution loop
    print(f'🧠 [Prompt Received]: "{args.prompt}"')
    smith_root = os.path.dirname(__file__)
    planner = DynamicPlanner(args.prompt, args.project_root)
    executor = PlanExecutor(args.project_root, smith_root)
    
    while not planner.is_finished():
        next_step = planner.get_next_step()
        if not next_step:
            print("✅ [Planner]: Задача выполнена.")
            break

        print(f"📝 [Next Step]: {next_step['description']}")
        result = executor.execute_step(next_step)
        planner.record_step_result(result)

        if result["status"] == "failed":
            print(f"🔥 [Step Failed]: {next_step['description']}")
            print(f"Error: {result.get('error', result.get('stderr', 'No specific error message.'))}")
            print("🛑 [Execution Halted]")
            break
        else:
            print(f"✅ [Step Succeeded]: {next_step['description']}")
            if result.get("stdout"):
                print(f"Stdout:\n{result['stdout']}")

    print("\n✨ [Agent Finished]")


if __name__ == "__main__":
    main()
