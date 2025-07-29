#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
meta_generator.py

SMITH Framework Tool - Memory Vector

Generates and maintains a .project_meta.json file in a project's root,
containing essential information for the agent to quickly orient itself.
"""

import argparse
import json
import os
import sys
from . import project_navigator  # Reuse the navigator to get file structure


def generate_metadata(project_path):
    """Generates metadata for a given project path."""
    if not os.path.isdir(project_path):
        raise FileNotFoundError(f"Project directory not found: {project_path}")

    # Use the project_navigator to get a map of the project
    project_map = project_navigator.create_project_map(project_path)

    # Basic metadata
    metadata = {
        "project_name": project_map["project_name"],
        "agent_version": "SMITH 3.2",  # Version of the agent that generated the meta
        "last_updated": project_map["analysis_timestamp"],
        "file_summary": project_map["summary"],
        "detected_tools": {},
    }

    # Heuristics to detect common tools and configurations
    if os.path.exists(os.path.join(project_path, "requirements.txt")):
        metadata["detected_tools"]["pip"] = "requirements.txt"
    if os.path.exists(os.path.join(project_path, "pyproject.toml")):
        metadata["detected_tools"]["poetry_or_pip"] = "pyproject.toml"
    if os.path.exists(os.path.join(project_path, ".git")):
        metadata["detected_tools"]["git"] = ".git directory"
    if os.path.exists(os.path.join(project_path, "tests")) or os.path.exists(
        os.path.join(project_path, "test")
    ):
        metadata["detected_tools"]["pytest"] = "tests/ or test/ directory"

    return metadata


def main():
    """Main CLI handler."""
    parser = argparse.ArgumentParser(
        description="Generates a .project_meta.json file for a project."
    )
    parser.add_argument(
        "project_path", help="The absolute path to the project directory."
    )
    parser.add_argument(
        "--output-dir",
        help="(Optional) Directory to save the file in. Defaults to project_path.",
    )

    args = parser.parse_args()

    try:
        print(f"Generating metadata for {args.project_path}...")
        metadata = generate_metadata(args.project_path)

        output_dir = args.output_dir or args.project_path
        output_path = os.path.join(output_dir, ".project_meta.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        print(f"Successfully generated and saved metadata to {output_path}")

    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
