"""
plan_executor.py (v2 - Refactored for Interactive Mode)
------------------------------------------------------

The refactored plan executor is a simple, single-step execution engine.
It is designed to be called iteratively by a controlling agent, such as the one
orchestrated by interactive_cockpit.py. It executes one step at a time and
returns the result, leaving planning and state management to the caller.
"""

from __future__ import annotations

from typing import Dict, Any

# We still import the "hands" of the agent
from .project_verifier import ProjectVerifier
from .human_feedback_tool import HumanFeedbackTool
from . import code_ops


class PlanExecutor:
    """
    Executes a single step from a plan. This is a simplified, synchronous
    version designed for the interactive, step-by-step execution model.
    """

    def __init__(self, project_root: str, smith_root: str):
        """
        Initializes the executor.

        Parameters
        ----------
        project_root : str
            The path to the project directory where commands should be executed.
        smith_root : str
            The root of the SMITH framework; used to locate memory directories.
        """
        self.project_root = project_root
        self.smith_root = smith_root
        # Each executor gets its own set of tools to prevent state conflicts.
        self.verifier = ProjectVerifier(project_root)
        self.feedback_tool = HumanFeedbackTool()

    def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single step and catch any exceptions.

        This is the primary public method. It acts as a safe wrapper around the
        core execution logic.

        Parameters
        ----------
        step : Dict[str, Any]
            A dictionary describing the single action to perform.

        Returns
        -------
        Dict[str, Any]
            A result dictionary containing the status and any output or errors.
        """
        try:
            # The actual logic is in a private method.
            return self._execute_step_logic(step)
        except Exception as exc:
            # If anything unexpected happens, we report it gracefully.
            return {
                "status": "failed",
                "error": f"Unhandled exception in executor: {exc}",
            }

    def _execute_step_logic(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        The core logic for dispatching an action to the correct tool.
        """
        action = step.get("action")

        if not action:
            return {"status": "failed", "error": "Step is missing 'action' field."}

        # This is the main dispatcher logic. It maps an "action" string
        # to the actual Python function call from our tools.
        if action == "human_feedback":
            question = step.get("question") or step.get("description")
            confirmed = self.feedback_tool.request_confirmation(question)
            if confirmed:
                return {"status": "succeeded"}
            else:
                return {"status": "failed", "error": "Operation cancelled by user"}

        elif action == "modify_code":
            operation = step.get("operation")
            # This is a sub-dispatcher for code modification operations.
            if operation == "replace_library":
                summary = code_ops.replace_library(
                    self.project_root, step.get("old_lib"), step.get("new_lib")
                )
                return {"status": "succeeded", "summary": summary}
            elif operation == "update_dependency":
                summary = code_ops.update_dependency(
                    self.project_root, step.get("package"), step.get("version")
                )
                return {"status": "succeeded", "summary": summary}
            elif operation == "add_endpoint":
                summary = code_ops.add_fastapi_endpoint(
                    self.project_root, step.get("path"), step.get("framework")
                )
                return {"status": "succeeded", "summary": summary}
            elif operation == "refactor_godobject":
                summary = code_ops.refactor_godobject(self.project_root, step.get("file"))
                if summary.get("status") == "failed":
                    return {"status": "failed", "error": summary.get("error")}
                return {"status": "succeeded", "summary": summary}
            else:
                return {
                    "status": "failed",
                    "error": f"Unknown modify_code operation: {operation}",
                }

        elif action == "verify_code":
            tool = step.get("tool")
            # Sub-dispatcher for verification tools.
            if tool == "pytest":
                return self.verifier.run_pytest()
            elif tool == "flake8":
                return self.verifier.run_flake8()
            elif tool == "mypy":
                return self.verifier.run_mypy()
            else:
                return {
                    "status": "failed",
                    "error": f"Unknown verification tool: {tool}",
                }
        
        # The 'run_command' action was missing in the original file, but is required
        # by the dynamic_planner stub. We add it here.
        elif action == "run_command":
            import subprocess
            command = step.get("command")
            if not command:
                return {"status": "failed", "error": "run_command action requires a 'command'"}
            
            # We run the command in the project root directory.
            # Using shell=True for simplicity, but be aware of security implications.
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                return {"status": "succeeded", "stdout": result.stdout, "stderr": result.stderr}
            else:
                return {"status": "failed", "stdout": result.stdout, "stderr": result.stderr, "error": f"Command failed with exit code {result.returncode}"}

        else:
            # If the action is not recognized, we fail gracefully.
            return {
                "status": "failed",
                "error": f"Unknown action: {action}",
            }
