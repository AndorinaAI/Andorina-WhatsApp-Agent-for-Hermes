import re
from typing import Tuple

# Patterns that we absolutely never want to output to the user
DLP_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{32,}",          # API Keys
    r"ya29\.[A-Za-z0-9_-]+",           # Google OAuth Tokens
    r"ghp_[A-Za-z0-9_]{36}",           # GitHub Tokens
    r"password|contraseña|secret|token", # Generic secrets
]

def scan_dlp(text: str) -> Tuple[bool, str]:
    """
    Checks if text contains sensitive information.
    Returns (True, text) if clean.
    Returns (False, red_flag_reason) if it violates DLP.
    """
    if not text:
        return True, ""
        
    text_lower = text.lower()
    
    # Fast check for simple secrets
    if "sk-" in text_lower or "ya29." in text_lower:
        return False, "Possible API Key exposure"
        
    for pat in DLP_PATTERNS:
        if re.search(pat, text_lower):
            return False, f"DLP Violation: {pat}"
            
    return True, ""
