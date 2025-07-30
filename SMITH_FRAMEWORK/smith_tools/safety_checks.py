import os
import shutil
from datetime import datetime
import ast


def check_file_exists(file_path: str) -> bool:
    """Check that a Python file exists and is writable."""
    return (
        os.path.isfile(file_path)
        and file_path.endswith(".py")
        and os.access(file_path, os.W_OK)
    )


def create_backup(file_path: str) -> str:
    """Create a timestamped backup of the given file."""
    backup_dir = os.path.join(os.path.dirname(file_path), ".smith_backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(
        backup_dir, f"{os.path.basename(file_path)}.{timestamp}"
    )
    shutil.copy2(file_path, backup_path)
    return backup_path


def validate_python_syntax(code: str):
    """Validate Python syntax of the provided code string."""
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, str(e)
