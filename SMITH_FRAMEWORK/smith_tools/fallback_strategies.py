STRATEGIES = {
    "add endpoint": [
        {"action": "run_command", "command": "find . -name 'main.py' -o -name 'app.py'"},
        {"action": "modify_code", "operation": "add_endpoint", "template": "basic_endpoint"},
    ],
    "run tests": [
        {"action": "run_command", "command": "python -m pytest"},
        {"action": "analyze_output", "find": "FAILED|ERROR"},
    ],
}
