"""
smith_agent_stage1.py
---------------------

Entry point for the SMITH agent's stage‑1 orchestrator. This script ties
together the prompt parser, dynamic planner and plan executor to form
a basic autonomous agent that can interpret simple natural language
requests, construct an execution plan with dependencies, and run the
necessary actions. Results of each run are appended to the
`.gemini/memory/reflections.log` file within the SMITH framework root.

Usage
-----
Run the agent with a prompt and project root:

```
python -m SMITH_FRAMEWORK.smith_tools.smith_agent_stage1 --prompt "update pandas to 2.0" --project-root /path/to/project
```

The SMITH root directory can be provided via the `SMITH_ROOT_DIR` environment
variable; otherwise a sensible default is used.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from .prompt_parser import PromptParser
from .dynamic_planner import DynamicPlanner
from .plan_executor import PlanExecutor


def _log_reflection(smith_root: str, prompt: str, plan: List[Dict[str, Any]], final_status: str, step_results: List[Dict[str, Any]]) -> None:
    """Append a run summary to the reflections log.

    Parameters
    ----------
    smith_root : str
        The root of the SMITH framework where the `.gemini/memory` folder resides.
    prompt : str
        The user prompt that initiated the run.
    plan : List[Dict[str, Any]]
        The plan that was executed.
    final_status : str
        The overall status of the run ("succeeded" or "failed").
    step_results : List[Dict[str, Any]]
        A list of result objects corresponding to each step in the plan.
    """
    memory_dir = os.path.join(smith_root, ".gemini", "memory")
    os.makedirs(memory_dir, exist_ok=True)
    log_path = os.path.join(memory_dir, "reflections.log")
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "plan": plan,
        "final_status": final_status,
        "step_results": step_results,
    }
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as exc:
        print(f"[WARNING] Could not write to reflections log: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SMITH Agent Stage‑1: parse prompt, plan actions, and execute."
    )
    parser.add_argument("--prompt", required=True, help="The task description for the agent.")
    parser.add_argument("--project-root", required=True, help="Absolute path to the project directory.")
    args = parser.parse_args()

    # Determine SMITH root directory; default to current working directory/SMITH_FRAMEWORK
    smith_root = os.getenv("SMITH_ROOT_DIR") or os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

    prompt = args.prompt
    project_root = args.project_root
    if not os.path.isdir(project_root):
        print(f"[ERROR] Provided project root does not exist or is not a directory: {project_root}")
        return

    # Generate or update project metadata (.project_meta.json) before parsing
    try:
        from .meta_generator import generate_metadata

        metadata = generate_metadata(project_root)
        meta_path = os.path.join(project_root, ".project_meta.json")
        with open(meta_path, "w", encoding="utf-8") as meta_file:
            json.dump(metadata, meta_file, indent=2)
        # Optionally notify the user
        print(f"📦 [Metadata]: Saved project metadata to {meta_path}")
    except Exception as meta_exc:
        print(f"[WARNING] Could not generate project metadata: {meta_exc}")

    # Parse the prompt into structured intent
    parser_obj = PromptParser()
    parsed = parser_obj.parse(prompt)
    if parsed.get("intent") == "unknown":
        print("🤔 [Planner]: I'm sorry, I couldn't understand the request.")
        return
    # Create a plan from the parsed intent
    planner = DynamicPlanner(parsed, project_root)
    plan = planner.create_plan()
    print("📝 [Plan Created]:")
    for idx, step in enumerate(plan, 1):
        desc = step.get("description", step.get("question", ""))
        deps = step.get("depends_on", [])
        print(f"  {idx}. {desc} (depends on: {deps if deps else 'none'})")

    # Execute the plan
    executor = PlanExecutor(project_root, smith_root)
    print("\n--- Execution ---")
    final_status, step_results = executor.execute_plan(plan)

    # Display results
    for step, result in zip(plan, step_results):
        status = result.get("status")
        desc = step.get("description", step.get("question", ""))
        if status == "succeeded":
            print(f"✅ [Step Succeeded]: {desc}")
            # Print additional information if available
            if "stdout" in result and result["stdout"]:
                print(f"Stdout:\n{result['stdout']}")
            if "stderr" in result and result["stderr"]:
                print(f"Stderr:\n{result['stderr']}")
            if "summary" in result:
                print(f"Summary: {result['summary']}")
        elif status == "failed":
            print(f"🔥 [Step Failed]: {desc}")
            print(f"Reason: {result.get('error', 'Unknown error')}\n")
        else:  # skipped or other status
            print(f"⚠️  [Step {status.capitalize()}]: {desc}")
            if result.get("error"):
                print(f"Reason: {result['error']}")

    # Log the run to the reflections log
    _log_reflection(smith_root, prompt, plan, final_status, step_results)

    # Final status message
    if final_status == "succeeded":
        print("\n✨ [Plan Executed Successfully]")
    else:
        print("\n❌ [Plan Execution Failed]")


if __name__ == "__main__":
    main()