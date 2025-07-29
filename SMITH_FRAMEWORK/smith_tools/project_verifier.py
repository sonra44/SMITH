"""
project_verifier.py

SMITH Framework Tool - Hands Vector

A tool to run quality checks (tests, linting, type checking) on a project
and return a structured report.
"""

import argparse
import subprocess
import json
import sys
import os


class ProjectVerifier:
    """Runs various verification tools on a project directory."""

    def __init__(self, project_path):
        if not os.path.isdir(project_path):
            raise FileNotFoundError(
                f"Project directory not found: {project_path}"
            )
        self.project_path = project_path

    def _run_command(self, command):
        """A helper to run a command in the project directory."""
        try:
            process = subprocess.run(
                command,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return {
                "status": "succeeded" if process.returncode == 0 else "failed",
                "command": " ".join(command),
                "stdout": process.stdout.strip(),
                "stderr": process.stderr.strip(),
                "exit_code": process.returncode,
            }
        except FileNotFoundError:
            return {
                "status": "failed",
                "command": " ".join(command),
                "error": f"Command '{command[0]}' not found. Is it installed?",
                "exit_code": -1,
            }
        except Exception as e:
            return {
                "status": "failed",
                "command": " ".join(command),
                "error": f"An unexpected error occurred: {e}",
                "exit_code": -1,
            }

    def run_pytest(self):
        """Runs pytest and returns the results."""
        return self._run_command([sys.executable, "-m", "pytest"])

    def run_flake8(self):
        """Runs flake8 for linting and returns the results."""
        return self._run_command([sys.executable, "-m", "flake8", "."])

    def run_mypy(self):
        """Runs mypy for type checking and returns the results."""
        return self._run_command([sys.executable, "-m", "mypy", "."])


def main():
    """Main CLI handler for the project verifier."""
    parser = argparse.ArgumentParser(
        description="SMITH's Project Verifier. Runs quality checks on a project."
    )
    parser.add_argument(
        "project_path", help="The absolute path to the project directory."
    )
    parser.add_argument(
        "--tool",
        choices=["pytest", "flake8", "mypy", "all"],
        default="all",
        help="The tool to run.",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output the results in JSON format.",
    )
    args = parser.parse_args()
    try:
        verifier = ProjectVerifier(args.project_path)
        results = {}
        if args.tool in ["pytest", "all"]:
            results["pytest"] = verifier.run_pytest()
        if args.tool in ["flake8", "all"]:
            results["flake8"] = verifier.run_flake8()
        if args.tool in ["mypy", "all"]:
            results["mypy"] = verifier.run_mypy()
        if args.output_json:
            print(json.dumps(results, indent=2))
        else:
            for tool, result in results.items():
                print(f"--- Results for {tool} ---")
                if result.get("error"):
                    print(f"Error: {result['error']}")
                else:
                    print(f"Exit Code: {result['exit_code']}")
                    if result["stdout"]:
                        print(f"Stdout:\n{result['stdout']}")
                    if result["stderr"]:
                        print(f"Stderr:\n{result['stderr']}")
                print("=" * 30)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
