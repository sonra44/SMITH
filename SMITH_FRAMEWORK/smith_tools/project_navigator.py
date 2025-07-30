import argparse
import json
import os
import sys
from datetime import datetime, timezone
from .context_engine import analyze_code  # Use the refactored context_engine


class ProjectNavigator:
    """Simple wrapper to create project maps."""

    def create_project_map(self, directory_path: str):
        return create_project_map(directory_path)


def find_python_files(directory):
    """Recursively finds all Python files in a given directory, ignoring common virtualenv folders."""
    python_files = []
    exclude_dirs = set([".venv", "venv", "env", "__pycache__", ".git"])

    for root, dirs, files in os.walk(directory, topdown=True):
        # Exclude common virtual environment and cache directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def create_project_map(directory_path):
    """
    Analyzes a project directory and returns a structured map.
    Raises exceptions on failure.
    """
    if not os.path.isdir(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    py_files = find_python_files(directory_path)

    project_map = {
        "project_name": os.path.basename(os.path.normpath(directory_path)),
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        "files": {},
        "summary": {"total_files": len(py_files), "files_with_errors": 0},
    }

    for file_path in py_files:
        try:
            with open(file_path, "r", encoding="utf-8") as source_file:
                source_code = source_file.read()

            # Use the more advanced analyzer from context_engine
            analysis_result = analyze_code(source_code, file_name=file_path)

            # Use relative paths for portability
            relative_path = os.path.relpath(file_path, directory_path)
            project_map["files"][relative_path] = analysis_result

        except (ValueError, RuntimeError, FileNotFoundError) as e:
            project_map["summary"]["files_with_errors"] += 1
            relative_path = os.path.relpath(file_path, directory_path)
            project_map["files"][relative_path] = {"error": str(e)}

    return project_map


def main():
    """Main CLI handler for the project navigator."""
    parser = argparse.ArgumentParser(
        description="A tool to scan a project directory and create a JSON map of its structure."
    )
    parser.add_argument(
        "directory_path",
        type=str,
        help="The absolute path to the project directory to scan.",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="(Optional) The path to the output JSON file. Prints to stdout if not provided.",
    )

    args = parser.parse_args()

    try:
        print(f"Analyzing directory: {args.directory_path}...")
        project_map = create_project_map(args.directory_path)
        output_json = json.dumps(project_map, indent=2)

        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output_json)
                print(f"Analysis complete. Map saved to {args.output}")
                print(
                    f"Summary: {project_map['summary']['total_files']} files scanned, {project_map['summary']['files_with_errors']} failed to parse."
                )
            except IOError as e:
                raise RuntimeError(f"Error writing to output file: {e}")
        else:
            print(output_json)

    except (FileNotFoundError, RuntimeError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
