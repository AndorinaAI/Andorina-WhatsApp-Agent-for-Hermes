#!/usr/bin/env python3
"""
🩺 Andoriña — Patch Verifier
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verifies that the WhatsApp bridge (bridge.js) and adapter (whatsapp.py)
contain the expected Andoriña patches, including content markers.

Usage:
  python3 check_patches.py           # Human-readable output + auto-repair
  python3 check_patches.py --json    # JSON output for the GUI panel
  python3 check_patches.py --repair  # Force re-patch even if partially patched
"""

import os
import sys
import json
import subprocess
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
SKILL_DIR = Path(__file__).parent.absolute()

# ── Bridge.js markers ─────────────────────────────────────────────────────
# These are content strings that MUST be present in bridge.js after patching.
BRIDGE_MARKERS = {
    "health_endpoint":   "app.get('/health'",
    "groups_endpoint":   "app.get('/groups'",
    "mime_expansion":    "reqMimetype",
    "fromMe_inbox_fix":  "ANDORINA INBOX FIX v2",
}

# ── whatsapp.py markers ──────────────────────────────────────────────────
# These are content strings that MUST be present in whatsapp.py after patching.
WHATSAPP_MARKERS = {
    "inbox_writer":      "# ── Andoriña Inbox Writer ──",
    "webhook_dispatch":  "webhook.py",
    "hermes_home_env":   "HERMES_HOME",
}


def find_bridge_js() -> Path | None:
    """Locate the WhatsApp bridge.js inside the Hermes gateway."""
    # Standard locations — includes hermes-agent path used by current Hermes releases
    candidates = [
        # Hermes >= 2025: hermes-agent submodule layout
        HERMES_HOME / "hermes-agent" / "scripts" / "whatsapp-bridge" / "bridge.js",
        # Legacy / alternate layouts
        HERMES_HOME / "gateway" / "bridge.js",
        HERMES_HOME / "gateway" / "src" / "bridge.js",
        HERMES_HOME / "scripts" / "whatsapp-bridge" / "bridge.js",
    ]

    for c in candidates:
        if c.is_file():
            return c

    # Recursive search in hermes-agent/ and gateway/ as last resort
    for search_root in [
        HERMES_HOME / "hermes-agent",
        HERMES_HOME / "gateway",
    ]:
        if search_root.is_dir():
            for p in search_root.rglob("bridge.js"):
                if p.is_file():
                    return p

    return None


def find_whatsapp_py() -> Path | None:
    """Locate the WhatsApp adapter (whatsapp.py) inside the Hermes core."""
    candidates = [
        HERMES_HOME / "core" / "platforms" / "whatsapp.py",
        HERMES_HOME / "platforms" / "whatsapp.py",
    ]
    # Broader search
    for d in [HERMES_HOME / "core", HERMES_HOME]:
        if d.is_dir():
            for p in d.rglob("whatsapp.py"):
                if p not in candidates:
                    candidates.append(p)

    for c in candidates:
        if c.is_file():
            # Ensure it's the actual adapter, not our patcher
            content = c.read_text(encoding="utf-8", errors="replace")[:500]
            if "class WhatsApp" in content or "def send_message" in content or "platform" in content.lower():
                return c
    return None


def check_file(file_path: Path | None, markers: dict, file_label: str) -> dict:
    """Check a file for expected content markers."""
    result = {
        "file": str(file_path) if file_path else None,
        "exists": file_path is not None and file_path.is_file(),
        "markers": {},
        "all_ok": False,
    }

    if not result["exists"]:
        for name in markers:
            result["markers"][name] = False
        return result

    content = file_path.read_text(encoding="utf-8", errors="replace")
    all_ok = True
    for name, needle in markers.items():
        found = needle in content
        result["markers"][name] = found
        if not found:
            all_ok = False

    result["all_ok"] = all_ok
    return result


def run_repair(bridge_result: dict, whatsapp_result: dict) -> dict:
    """Run the patchers to fix missing patches."""
    repairs = []

    if not bridge_result["all_ok"]:
        patcher = SKILL_DIR / "patch_bridge.py"
        if patcher.is_file():
            try:
                env = os.environ.copy()
                env["HERMES_HOME"] = str(HERMES_HOME)
                r = subprocess.run(
                    [sys.executable, str(patcher)],
                    capture_output=True, text=True, timeout=30, env=env
                )
                repairs.append({
                    "target": "bridge.js",
                    "success": r.returncode == 0,
                    "output": r.stdout.strip() or r.stderr.strip(),
                })
            except Exception as e:
                repairs.append({"target": "bridge.js", "success": False, "output": str(e)})
        else:
            repairs.append({"target": "bridge.js", "success": False, "output": "patch_bridge.py not found"})

    if not whatsapp_result["all_ok"]:
        patcher = SKILL_DIR / "patch_whatsapp.py"
        if patcher.is_file():
            try:
                env = dict(os.environ)
                env["HERMES_HOME"] = str(HERMES_HOME)
                r = subprocess.run(
                    [sys.executable, str(patcher)],
                    capture_output=True, text=True, timeout=30, env=env
                )
                repairs.append({
                    "target": "whatsapp.py",
                    "success": r.returncode == 0,
                    "output": r.stdout.strip() or r.stderr.strip(),
                })
            except Exception as e:
                repairs.append({"target": "whatsapp.py", "success": False, "output": str(e)})
        else:
            repairs.append({"target": "whatsapp.py", "success": False, "output": "patch_whatsapp.py not found"})

    return {"repairs": repairs}


def main():
    is_json = "--json" in sys.argv
    force_repair = "--repair" in sys.argv

    bridge_path = find_bridge_js()
    whatsapp_path = find_whatsapp_py()

    bridge_result = check_file(bridge_path, BRIDGE_MARKERS, "bridge.js")
    whatsapp_result = check_file(whatsapp_path, WHATSAPP_MARKERS, "whatsapp.py")

    overall_ok = bridge_result["all_ok"] and whatsapp_result["all_ok"]

    if is_json:
        output = {
            "ok": overall_ok,
            "bridge": bridge_result,
            "whatsapp": whatsapp_result,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    # Human-readable output
    print("\n🩺 Andoriña — Patch Status")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    for label, result in [("bridge.js", bridge_result), ("whatsapp.py", whatsapp_result)]:
        if not result["exists"]:
            print(f"❌ {label}: NOT FOUND")
            continue
        status = "✅ OK" if result["all_ok"] else "⚠️  INCOMPLETE"
        print(f"{'✅' if result['all_ok'] else '⚠️'} {label}: {status}  ({result['file']})")
        for marker, found in result["markers"].items():
            icon = "  ✓" if found else "  ✗"
            print(f"  {icon} {marker}")
        print()

    if overall_ok and not force_repair:
        print("✨ All patches verified.\n")
        return

    # Auto-repair
    print("🔧 Running auto-repair...\n")
    repair_result = run_repair(bridge_result, whatsapp_result)
    for r in repair_result["repairs"]:
        icon = "✅" if r["success"] else "❌"
        print(f"  {icon} {r['target']}: {r['output']}")

    # Re-verify
    print("\n🔄 Re-verifying...")
    bridge_result2 = check_file(find_bridge_js(), BRIDGE_MARKERS, "bridge.js")
    whatsapp_result2 = check_file(find_whatsapp_py(), WHATSAPP_MARKERS, "whatsapp.py")

    if bridge_result2["all_ok"] and whatsapp_result2["all_ok"]:
        print("✨ All patches successfully applied.\n")
    else:
        print("⚠️  Some patches could not be applied. Check the output above.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
