"""
code_ops.py
-------------

Utility functions for modifying code and dependency files.

This module collects operations that transform source code or configuration
files in a project. Unlike `code_modifier.py`, which focuses on AST‑based
transformations of individual Python files, these functions operate at a
coarser level: searching and replacing imports across a project or
updating dependency versions in requirements files. By separating these
concerns we avoid coupling our planner to the internal implementation
details of `code_modifier.py` and provide a clear API for common
operations.

Functions
---------
replace_library(project_root, old_lib, new_lib)
    Recursively search for Python files under `project_root` and replace
    occurrences of `old_lib` imports with `new_lib`. Returns a summary of
    scanned and modified files.

update_dependency(project_root, package, new_version)
    Update a dependency in the project's `requirements.txt`. If
    `new_version` is provided, pin the package to that version; otherwise
    remove any version specifier to allow installation of the latest
    release. Returns a summary of the change.
"""

from __future__ import annotations

import os
import re
from typing import Dict, Tuple


def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def replace_library(project_root: str, old_lib: str, new_lib: str) -> Dict[str, int]:
    """Replace import statements and usage of one library with another.

    This function walks through all `.py` files in `project_root` (excluding
    virtual environments or hidden directories) and performs a naive
    text‑based replacement of import statements and attribute references.

    It attempts to handle common patterns such as:

    * ``import requests`` -> ``import httpx``
    * ``from requests import ...`` -> ``from httpx import ...``
    * ``requests.get(...)`` -> ``httpx.get(...)``

    Note that this replacement is purely text‑based and does not parse
    Python syntax. It may replace occurrences inside comments or strings,
    which is acceptable for the MVP but should be improved in future
    versions.

    Parameters
    ----------
    project_root : str
        The root directory of the project whose code should be modified.
    old_lib : str
        The name of the library to be replaced (e.g. "requests").
    new_lib : str
        The name of the library to replace with (e.g. "httpx").

    Returns
    -------
    Dict[str, int]
        A dictionary with keys ``files_scanned`` and ``files_modified``.
    """
    files_scanned = 0
    files_modified = 0
    for root, dirs, files in os.walk(project_root):
        # Skip hidden directories and virtual environments to avoid
        # unintended modifications.
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "venv" and d != "__pycache__"]
        for file in files:
            if file.endswith(".py"):
                files_scanned += 1
                file_path = os.path.join(root, file)
                original = _read_file(file_path)
                modified = original
                # Replace import statements
                # ``import old_lib`` -> ``import new_lib``
                modified = re.sub(
                    rf"(^|\n)\s*import\s+{re.escape(old_lib)}(\s|$)",
                    lambda m: m.group(0).replace(old_lib, new_lib),
                    modified,
                    flags=re.MULTILINE,
                )
                # ``from old_lib import ...`` -> ``from new_lib import ...``
                modified = re.sub(
                    rf"(^|\n)\s*from\s+{re.escape(old_lib)}\s+import",
                    lambda m: m.group(0).replace(old_lib, new_lib),
                    modified,
                    flags=re.MULTILINE,
                )
                # Replace occurrences of ``old_lib.`` with ``new_lib.``
                modified = re.sub(
                    rf"\b{re.escape(old_lib)}\.",
                    f"{new_lib}.",
                    modified,
                )
                if modified != original:
                    files_modified += 1
                    _write_file(file_path, modified)
    return {"files_scanned": files_scanned, "files_modified": files_modified}


def update_dependency(project_root: str, package: str, new_version: str | None) -> Dict[str, str]:
    """Update or pin a dependency in the project's requirements file.

    This helper looks for a ``requirements.txt`` in ``project_root`` and
    modifies the specified package line. If ``new_version`` is provided,
    it sets ``package==new_version``. If ``None``, it removes any version
    constraint so that the latest version will be installed upon the next
    package installation.

    If the package is not found in the requirements file, a new line
    containing the package (with the optional version) is appended.

    Parameters
    ----------
    project_root : str
        Path to the root of the project.
    package : str
        The package name to update.
    new_version : Optional[str]
        A version specifier (e.g. "2.1.0") or ``None`` to remove the
        version pin.

    Returns
    -------
    Dict[str, str]
        A summary of the update: ``{ 'package': package, 'old_line': old_line, 'new_line': new_line }``.
    """
    requirements_path = os.path.join(project_root, "requirements.txt")
    summary: Dict[str, str] = {"package": package, "old_line": "", "new_line": ""}
    if not os.path.isfile(requirements_path):
        # If requirements.txt does not exist, create it with the package
        new_line = f"{package}=={new_version}" if new_version else package
        _write_file(requirements_path, new_line + "\n")
        summary["new_line"] = new_line
        return summary

    lines = _read_file(requirements_path).splitlines()
    found = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        # Compare package names ignoring extras and version constraints
        pkg_name = re.split(r"[\s\[\]=<>!~]", stripped)[0].lower()
        if pkg_name == package.lower():
            found = True
            summary["old_line"] = line
            if new_version:
                new_line = f"{package}=={new_version}"
            else:
                new_line = package
            summary["new_line"] = new_line
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    if not found:
        new_line = f"{package}=={new_version}" if new_version else package
        summary["new_line"] = new_line
        new_lines.append(new_line)
    # Write back to requirements.txt
    _write_file(requirements_path, "\n".join(new_lines) + "\n")
    return summary


def add_fastapi_endpoint(project_root: str, path: str, framework: str | None = None) -> Dict[str, str]:
    """Add a new API endpoint to a FastAPI or Flask project.

    For FastAPI projects this function tries to locate a common entry point
    (`main.py` or `app.py`) and append a new route definition. If no such
    file exists, it creates an `api_autogen.py` file in the project root.

    The generated handler returns a placeholder JSON payload. It is up to
    the user to customise the logic and integrate the router with the
    application instance.

    Parameters
    ----------
    project_root : str
        The root directory of the project.
    path : str
        The URL path for the new endpoint (e.g. `/users/{id}`).
    framework : Optional[str]
        Either 'fastapi' or 'flask'. If ``None``, defaults to FastAPI.

    Returns
    -------
    Dict[str, str]
        A summary containing the file modified/created and the path added.
    """
    framework = framework or "fastapi"
    # Determine target file
    candidate_files = ["main.py", "app.py"]
    target_file = None
    for fname in candidate_files:
        fpath = os.path.join(project_root, fname)
        if os.path.isfile(fpath):
            target_file = fpath
            break
    if target_file is None:
        target_file = os.path.join(project_root, "api_autogen.py")
    # Read existing content if file exists
    content = ""
    if os.path.isfile(target_file):
        content = _read_file(target_file)
    # Generate code depending on framework
    if framework == "fastapi":
        snippet = (
            "\n\n# Automatically generated endpoint\n"
            "from fastapi import APIRouter, Depends\n"
            "router = APIRouter()\n\n"
            f"@router.get(\"{path}\")\n"
            "async def autogenerated_endpoint():\n"
            "    return {\"detail\": \"This is a generated endpoint. Replace with your logic.\"}\n"
        )
    elif framework == "flask":
        snippet = (
            "\n\n# Automatically generated endpoint\n"
            "from flask import Blueprint, jsonify\n"
            "blueprint = Blueprint('autogen', __name__)\n\n"
            f"@blueprint.route(\"{path}\", methods=['GET'])\n"
            "def autogenerated_endpoint():\n"
            "    return jsonify({\"detail\": \"This is a generated endpoint. Replace with your logic.\"})\n"
        )
    else:
        raise ValueError(f"Unsupported framework: {framework}")
    new_content = content + snippet
    _write_file(target_file, new_content)
    return {"file": target_file, "path": path}


def refactor_godobject(project_root: str, file_name: str | None) -> Dict[str, Any]:
    """Naively split a 'GodObject' class file into three parts.

    This is a simplistic implementation intended for demonstration purposes.
    It does not perform a true refactoring based on responsibilities. Instead,
    it divides the original file's contents into three roughly equal parts and
    writes each part into a new file with a `_partN.py` suffix. The original
    file remains untouched.

    Parameters
    ----------
    project_root : str
        The root directory of the project.
    file_name : Optional[str]
        The name of the file containing the god object class. If ``None``,
        the function attempts to locate ``GodObject.py`` in the project root.

    Returns
    -------
    Dict[str, Any]
        A summary including the original file and the newly created files.
    """
    target = file_name or "GodObject.py"
    # Resolve absolute path
    # Attempt to locate the file case‑insensitively within the project root
    src_path = None
    # First, check the exact target and its lowercase variant
    candidate_paths = [
        os.path.join(project_root, target),
        os.path.join(project_root, target.lower()),
    ]
    for p in candidate_paths:
        if os.path.isfile(p):
            src_path = p
            break
    # If still not found, search the directory for a match ignoring case
    if src_path is None:
        for fname in os.listdir(project_root):
            if fname.lower() == target.lower() and fname.endswith(".py"):
                candidate = os.path.join(project_root, fname)
                if os.path.isfile(candidate):
                    src_path = candidate
                    break
    if src_path is None:
        return {
            "status": "failed",
            "error": f"GodObject file '{target}' not found in project root",
        }
    lines = _read_file(src_path).splitlines()
    # Determine chunk sizes for splitting into three parts
    total_lines = len(lines)
    chunk_size = max(1, total_lines // 3)
    new_files = []
    for idx in range(3):
        start = idx * chunk_size
        end = (idx + 1) * chunk_size if idx < 2 else total_lines
        part_lines = lines[start:end]
        new_name = f"{os.path.splitext(os.path.basename(src_path))[0]}_part{idx+1}.py"
        new_path = os.path.join(project_root, new_name)
        _write_file(new_path, "\n".join(part_lines) + "\n")
        new_files.append(new_name)
    return {
        "status": "succeeded",
        "original": os.path.basename(src_path),
        "new_files": new_files,
    }