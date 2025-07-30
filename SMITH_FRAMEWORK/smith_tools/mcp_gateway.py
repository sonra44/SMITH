"""
mcp_gateway.py (Master Control Program Gateway) - LIVE / ADC
-------------------------------------------------------------

This module is the sole interface between the SMITH agent's logic and the
underlying Large Language Model (LLM) API. This version uses Application
Default Credentials (ADC), inheriting the authentication from the environment
(e.g., the Gemini CLI session) instead of requiring a manual API key.
"""

import os
import json
import logging
import shutil
from datetime import datetime

# The official Google AI library
import google.generativeai as genai

class MCPGateway:
    """Gateway to the Gemini API or a local heuristic fallback."""

    def __init__(self):
        """Initializes the gateway and detects the operating mode."""
        env_flag = os.getenv("SMITH_NO_API", "false").lower() == "true"
        self.mode = "local" if env_flag else "live"
        if self.mode == "live":
            logging.info(
                "MCPGateway initialized. Relying on Application Default Credentials."
            )
        else:
            logging.info("MCPGateway running in LOCAL mode (no API calls).")
        self._analyzed = False

    def _cleanup_json_response(self, text: str) -> str:
        """Removes markdown fences and other clutter from the LLM's JSON response."""
        json_start = text.find('{')
        json_end = text.rfind('}')
        
        if json_start == -1 or json_end == -1:
            raise ValueError(f"Could not find a valid JSON object in the response: {text}")
            
        json_str = text[json_start : json_end + 1]
        return json_str

    def generate_step(self, system_prompt: str) -> dict:
        """Return the next step using either the live API or local heuristics."""
        if self.mode == "local":
            return self._heuristic_step(system_prompt)

        try:
            logging.info("Generating content with Gemini API...")
            model = genai.GenerativeModel("gemini-pro")

            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json"
            )

            response = model.generate_content(
                system_prompt, generation_config=generation_config
            )

            logging.info("Received response from Gemini API.")

            cleaned_json_str = self._cleanup_json_response(response.text)
            parsed_response = json.loads(cleaned_json_str)

            logging.info(f"Successfully parsed LLM response: {parsed_response}")
            return parsed_response

        except Exception as e:
            logging.error(
                f"An error occurred while interacting with the Gemini API: {e}"
            )
            return {
                "action": "finish_task",
                "parameters": {"reason": f"Failed to get next step from LLM: {e}"},
                "description": "Завершение задачи из-за ошибки API.",
            }

    def _heuristic_step(self, prompt: str) -> dict:
        """Very naive heuristic step generation for offline mode."""
        if not self._analyzed:
            self._analyzed = True
            return {
                "action": "run_command",
                "parameters": {"command": "ls -la && find . -name '*.py'"},
                "description": "Исследование структуры проекта",
            }

        lower = prompt.lower()
        if "add endpoint" in lower:
            return {
                "action": "modify_code",
                "parameters": {"operation": "add_endpoint", "path": "/autogen"},
                "description": "Добавляю новый endpoint",
            }
        if "refactor" in lower:
            return {
                "action": "modify_code",
                "parameters": {
                    "operation": "refactor_godobject",
                    "file": "GodObject.py",
                },
                "description": "Рефакторинг сложного файла",
            }
        if "fix" in lower or "исправ" in lower:
            return {
                "action": "verify_code",
                "parameters": {"tool": "pytest"},
                "description": "Запуск тестов для поиска ошибки",
            }
        return {
            "action": "run_command",
            "parameters": {"command": "ls -la"},
            "description": "Базовая навигация по проекту",
        }