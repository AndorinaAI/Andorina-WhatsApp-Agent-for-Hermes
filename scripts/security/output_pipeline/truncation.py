import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

def truncate_output(text: str) -> str:
    """Hard limit output length to prevent spam or token extraction attacks."""
    if not text:
        return ""
    # Lazy load to avoid crashing at import time if .env is missing
    try:
        from common import load_env as _load_env
        _max = int(_load_env().get("GUARD_MAX_CHARS_OUTPUT", 400))
    except Exception:
        _max = 400
    if len(text) > _max:
        return text[:_max - 3] + "..."
    return text
