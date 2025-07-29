"""
prompt_parser.py
-----------------

Простой парсер естественно‑языковых запросов.  На вход получает
строку запроса и возвращает словарь с распознанным намерением и
дополнительными параметрами.

Этот модуль представляет собой MVP для вектора «Разум»: в будущем его
можно заменить на более сложную NLP‑модель, но пока достаточно
проверки по ключевым словам.
"""

from __future__ import annotations

from typing import Dict, Any


class PromptParser:
    """
    A simple natural language prompt parser that extracts the user's intent
    and relevant entities from a free‑form request.

    This parser uses a handful of regular expressions and keyword checks to
    recognise a small set of operations required in the MVP version of the
    SMITH agent. In the future this could be replaced with a more
    sophisticated NLP model, but for now it performs the following tasks:

    * Detects library replacement requests, e.g. "replace requests with httpx" or
      "замени requests на httpx", and returns the old and new library names.
    * Detects dependency update requests, e.g. "update pandas to 2.1.0" or
      "обнови pandas до версии 2.1.0". If no version is specified, the latest
      available version should be installed.
    * Detects test and linting requests.
    * Falls back to an unknown intent if nothing matches.
    """

    def parse(self, prompt: str) -> Dict[str, Any]:
        """Parse a natural language prompt into a structured intent.

        Parameters
        ----------
        prompt : str
            The user‑provided description of the task.

        Returns
        -------
        Dict[str, Any]
            A dictionary describing the recognised intent and any extracted
            entities (e.g. package names, versions).
        """
        import re

        text = prompt.strip().lower()

        # 1. Library replacement: "replace X with Y" or "замени X на Y"
        # Use a non‑greedy match to capture library names consisting of word
        # characters, dots or hyphens. This covers common Python package
        # naming conventions. The Russian version matches "замени ... на ...".
        replace_patterns = [
            r"replace\s+([\w\.\-]+)\s+with\s+([\w\.\-]+)",
            r"замени\s+([\w\.\-]+)\s+на\s+([\w\.\-]+)",
        ]
        for pattern in replace_patterns:
            m = re.search(pattern, text)
            if m:
                old_lib, new_lib = m.group(1), m.group(2)
                return {
                    "intent": "replace_library",
                    "old_lib": old_lib,
                    "new_lib": new_lib,
                }

        # 2. Dependency update: "update X [to version Y]" or "обнови X [до версии Y]"
        update_patterns = [
            r"update\s+([\w\.\-]+)(?:\s+to\s+(?:version\s+)?([\w\.\-]+))?",
            r"обнови\s+([\w\.\-]+)(?:\s+до\s+версии\s+([\w\.\-]+))?",
        ]
        for pattern in update_patterns:
            m = re.search(pattern, text)
            if m:
                package = m.group(1)
                version = m.group(2) if m.group(2) else None
                return {
                    "intent": "update_dependency",
                    "package": package,
                    "version": version,
                }

        # 3. Running tests: look for phrases like "run tests" or "запусти тесты"
        if re.search(r"run\s+tests", text) or re.search(r"запусти\s+тесты", text):
            return {"intent": "run_tests"}

        # 4. Linting: check for "lint", "lint the code" or the Russian "линт"
        if re.search(r"\blint\b", text) or "lint the code" in text or "линт" in text:
            return {"intent": "lint_code"}

        # 5. Add API endpoint: detect phrases like "add endpoint /users/{id}" or the Russian equivalent
        # We look for "add" or "добав" and a slash-delimited path. We also capture the framework
        # if the user mentions FastAPI or Flask explicitly.
        m_endpoint = re.search(r"(add|добав)\s+(?:an\s+)?endpoint\s+(/\S+)", text)
        if m_endpoint:
            path = m_endpoint.group(2)
            framework = "fastapi" if "fastapi" in text else ("flask" if "flask" in text else None)
            return {
                "intent": "add_endpoint",
                "path": path,
                "framework": framework,
            }

        # 6. Refactor GodObject: detect requests to refactor a god object class or file
        # Examples: "refactor GodObject.py", "Разбей GodObject.py", "refactor class GodObject"
        if ("refactor" in text or "рефактор" in text or "разбей" in text) and ("godobject" in text or "god object" in text):
            # Try to extract a filename with .py extension
            file_match = re.search(r"(\w+\.py)", text)
            file_name = file_match.group(1) if file_match else None
            return {
                "intent": "refactor_godobject",
                "file": file_name,
            }

        # Fallback: unknown intent
        return {"intent": "unknown"}