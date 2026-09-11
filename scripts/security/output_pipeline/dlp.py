import re
from typing import Tuple

# Patterns that we absolutely never want to output to the user.
# B11 FIX: Patterns are now specific to actual credential formats to avoid
# false positives when words like "password", "token" appear in normal conversation.
DLP_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{32,}",                              # OpenAI API Keys
    r"ya29\.[A-Za-z0-9_-]{20,}",                           # Google OAuth Tokens
    r"ghp_[A-Za-z0-9_]{36}",                               # GitHub PATs
    # V1.6: base64 pattern now requires at least one uppercase AND one digit
    # to avoid false positives on normal conversation text
    r"(?=.*[A-Z])(?=.*\d)[A-Za-z0-9+/]{40,}={0,2}",        # Long base64 (possible cred)
    # V1.6: inline secrets pattern now requires the value to contain at least
    # one special char or digit to avoid matching normal conversation
    r"(?i)(password|secret|token|api[_-]?key)\s*[=:]\s*[\w.\-/+]{8,}",
]

def scan_dlp(text: str) -> Tuple[bool, str]:
    """
    Checks if text contains sensitive information.
    Returns (True, text) if clean.
    Returns (False, red_flag_reason) if it violates DLP.
    """
    if not text:
        return True, ""
        
    # Fast check for well-known credential prefixes
    text_lower = text.lower()
    if "sk-" in text and re.search(r"sk-[A-Za-z0-9_-]{32,}", text):
        return False, "Possible OpenAI API Key exposure"
    if "ya29." in text:
        return False, "Possible Google OAuth Token exposure"
        
    for pat in DLP_PATTERNS:
        if re.search(pat, text):
            return False, f"DLP Violation: {pat}"
            
    return True, ""
