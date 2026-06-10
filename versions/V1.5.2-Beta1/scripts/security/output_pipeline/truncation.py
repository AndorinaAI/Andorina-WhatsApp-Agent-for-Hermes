import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from common import load_env

_env = load_env()
MAX_CHARS_OUTPUT = int(_env.get("GUARD_MAX_CHARS_OUTPUT", 400))

def truncate_output(text: str) -> str:
    """Hard limit output length to prevent spam or token extraction attacks."""
    if not text:
        return ""
    if len(text) > MAX_CHARS_OUTPUT:
        return text[:MAX_CHARS_OUTPUT - 3] + "..."
    return text
