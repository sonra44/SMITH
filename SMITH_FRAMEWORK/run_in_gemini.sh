#!/bin/bash
# Проверяем, что мы в Gemini CLI
if [ -z "$GEMINI_SESSION" ]; then
    echo "Error: Not in Gemini CLI session"
    echo "Please run this script from within Gemini CLI"
    exit 1
fi

export SMITH_MODE="gemini_cli"
python -m smith_tools.smith_agent "$@"
