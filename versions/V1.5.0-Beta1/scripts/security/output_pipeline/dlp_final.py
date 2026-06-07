from typing import Tuple
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from security.output_pipeline.dlp import scan_dlp

def final_dlp_check(chunks: list[str]) -> Tuple[bool, str]:
    """Double checks all generated chunks before they hit the transport layer."""
    for chunk in chunks:
        ok, reason = scan_dlp(chunk)
        if not ok:
            return False, reason
    return True, ""
