import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from security.output_pipeline.sanitizer import sanitize_output
from security.output_pipeline.dlp import scan_dlp
from security.output_pipeline.truncation import truncate_output
from security.output_pipeline.pagination import paginate_output
from security.output_pipeline.dlp_final import final_dlp_check

def run_pipeline(text: str, bypass_truncation: bool = False) -> dict:
    """
    Executes the secure output pipeline.
    Returns: {"status": "OK", "chunks": list} or {"status": "DENY", "error": str}
    """
    # 1. Sanitize
    text = sanitize_output(text)
    
    # 2. Initial DLP
    ok, reason = scan_dlp(text)
    if not ok:
        return {"status": "DENY", "error": reason}
        
    # 3. Truncation (unless specifically bypassed for trusted system msgs)
    if not bypass_truncation:
        text = truncate_output(text)
        
    # 4. Paginate
    chunks = paginate_output(text)
    
    # 5. Final DLP Pass
    ok, reason = final_dlp_check(chunks)
    if not ok:
        return {"status": "DENY", "error": f"Post-pagination DLP failure: {reason}"}
        
    return {"status": "OK", "chunks": chunks}
