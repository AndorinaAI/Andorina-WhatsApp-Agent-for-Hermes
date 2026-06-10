import re

def sanitize_output(text: str) -> str:
    """Removes invisible characters and normalizes spaces."""
    if not text:
        return ""
    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Normalize multiple spaces (but preserve newlines)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()
