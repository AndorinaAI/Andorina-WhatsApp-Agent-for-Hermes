import os
import sys
import json
import subprocess
import shlex
from pathlib import Path

# Fix relative import
sys.path.append(str(Path(__file__).parent.parent))
from security.sec_types import ToolContract
from security.tool_guard import validate_tool_call

def _make_contract(status: str, error_code: str, payload: dict) -> ToolContract:
    """Helper para construir un ToolContract sin repetir las 4 claves de traza vacías."""
    return {
        "status":          status,
        "error_code":      error_code,
        "payload":         payload,
        "trace_id":        "",
        "tool_call_id":    "",
        "tool_chain_id":   "",
        "parent_trace_id": None,
    }

def execute_tool(command_line: str, role_config: dict = None, user_jid: str = None) -> ToolContract:
    """Executes a tool within a constrained subprocess environment."""
    
    # 1. Guard check
    validation = validate_tool_call(command_line, role_config, user_jid=user_jid)
    if validation["status"] != "OK":
        return validation
        
    try:
        parts = shlex.split(command_line)
    except Exception as e:
        return _make_contract("ERROR", "INTERNAL_ERROR", {"error": str(e)})

    # 2. Setup isolated environment
    safe_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": str(Path(__file__).parent.parent),  # Crucial for import common
        "HOME": os.environ.get("HOME", "/tmp"),
        "HERMES_HOME": os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    }
    
    # Ensure it's using the same python interpreter
    if parts[0] != sys.executable and not parts[0].endswith("python3"):
        parts.insert(0, sys.executable)
    else:
        parts[0] = sys.executable

    # 3. Execution with hard timeout
    import time
    from datetime import datetime
    start_t = time.time()
    try:
        proc = subprocess.run(
            parts,
            env=safe_env,
            capture_output=True,
            text=True,
            timeout=30  # Hard kill after 30 seconds
        )
        
        duration = time.time() - start_t
        log_dir = Path(__file__).parent.parent.parent / "logs" / "tools"
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "tool_execution.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(), "cmd": command_line, "duration": duration, "code": proc.returncode}) + "\n")

        
        try:
            # We expect the tool to output JSON compliant with ToolContract
            output_data = json.loads(proc.stdout)
            
            # Translate legacy sys.exit / {"ok": False} into V3.6 Contract
            if "status" not in output_data:
                if output_data.get("ok") is False:
                    return _make_contract("DENY", "FATAL", output_data)
                return _make_contract("OK", "NONE", output_data)
                
            return output_data
            
        except json.JSONDecodeError:
            # If it's not JSON, it might be a raw print or a crash
            if proc.returncode != 0:
                return _make_contract("ERROR", "FATAL", {"stderr": proc.stderr})
            return _make_contract("OK", "NONE", {"text": proc.stdout.strip()})
            
    except subprocess.TimeoutExpired:
        return _make_contract("ERROR", "TIMEOUT", {"error": "Execution exceeded 30 seconds"})
    except Exception as e:
        return _make_contract("ERROR", "INTERNAL_ERROR", {"error": str(e)})


if __name__ == "__main__":
    import argparse
    from security.rbac import load_rules, resolve_role, get_role_config
    sys.path.append(str(Path(__file__).parent.parent))
    from common import load_env
    
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["execute"])
    parser.add_argument("jid", help="JID of the user requesting execution")
    parser.add_argument("command", help="The full command line to execute")
    
    args = parser.parse_args()
    
    if args.cmd == "execute":
        rules = load_rules()
        env = load_env()
        role = resolve_role(args.jid, rules, env)
        role_config = get_role_config(role, rules)
        
        result = execute_tool(args.command, role_config, user_jid=args.jid)
        
        # Hermes Fallback Adapter
        if result.get("status") == "OK":
            result["ok"] = True
        else:
            result["ok"] = False
            
        print(json.dumps(result, ensure_ascii=False))
