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

# The official Google AI library
import google.generativeai as genai

class MCPGateway:
    """A live gateway to the Gemini API using the environment's auth."""

    def __init__(self):
        """
        Initializes the gateway.
        It relies on the `google-generativeai` library to automatically find
        the necessary credentials from the execution environment.
        """
        # We don't configure a key. The library will find it automatically.
        logging.info("MCPGateway initialized. Relying on Application Default Credentials.")

    def _cleanup_json_response(self, text: str) -> str:
        """Removes markdown fences and other clutter from the LLM's JSON response."""
        json_start = text.find('{')
        json_end = text.rfind('}')
        
        if json_start == -1 or json_end == -1:
            raise ValueError(f"Could not find a valid JSON object in the response: {text}")
            
        json_str = text[json_start : json_end + 1]
        return json_str

    def generate_step(self, system_prompt: str) -> dict:
        """
        Takes a system prompt, sends it to the Gemini API, and returns a
        structured step dictionary.
        """
        try:
            logging.info("Generating content with Gemini API...")
            model = genai.GenerativeModel('gemini-pro')
            
            # We still request a JSON response type.
            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json"
            )

            response = model.generate_content(system_prompt, generation_config=generation_config)
            
            logging.info("Received response from Gemini API.")
            
            cleaned_json_str = self._cleanup_json_response(response.text)
            parsed_response = json.loads(cleaned_json_str)
            
            logging.info(f"Successfully parsed LLM response: {parsed_response}")
            return parsed_response

        except Exception as e:
            logging.error(f"An error occurred while interacting with the Gemini API: {e}")
            return {
                "action": "finish_task",
                "parameters": {
                    "reason": f"Failed to get next step from LLM: {e}"
                },
                "description": "Завершение задачи из-за ошибки API."
            }
