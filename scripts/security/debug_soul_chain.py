#!/usr/bin/env python3
"""Quick diagnostic: verify the full Sub-Soul injection chain."""
import json, sys, os
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
CONFIG = HERMES_HOME / "config.yaml"
SKILL_STATE = HERMES_HOME / "skills" / "andorina" / "state"

print("=" * 60)
print("🔍 Sub-Soul Chain Diagnostic")
print("=" * 60)

# 1. guard_rules.json — what souls are assigned?
rules_file = SKILL_STATE / "guard_rules.json"
if rules_file.exists():
    rules = json.loads(rules_file.read_text())
    print("\n📋 guard_rules.json JID assignments:")
    for jid, entry in rules.get("jids", {}).items():
        soul = entry.get("custom_soul", "—")
        role = entry.get("role", "?")
        print(f"   {jid}: role={role}, custom_soul={soul!r}")
else:
    print("❌ guard_rules.json NOT FOUND")

# 2. config.yaml — what channel_prompts are written?
print(f"\n📄 config.yaml channel_prompts:")
if CONFIG.exists():
    import yaml
    with open(CONFIG) as f:
        cfg = yaml.safe_load(f) or {}
    wa = cfg.get("whatsapp", {})
    cp = wa.get("channel_prompts", {})
    if cp:
        for jid, text in cp.items():
            print(f"   ✅ {jid}: {len(text)} chars — starts with: {text[:80]!r}...")
    else:
        print("   ⚠️  No channel_prompts found under whatsapp:")
    
    # 3. Verify bridging: will Hermes put this in config.extra?
    print(f"\n🔗 Bridging check:")
    print(f"   whatsapp block type: {type(wa).__name__}")
    print(f"   'channel_prompts' in whatsapp block: {'channel_prompts' in wa}")
    if "channel_prompts" in wa and isinstance(wa["channel_prompts"], dict):
        print(f"   ✅ Hermes WILL bridge this into PlatformConfig.extra")
    else:
        print(f"   ❌ Hermes will NOT find channel_prompts")
else:
    print("   ❌ config.yaml NOT FOUND")

# 3. Simulate what orchestrator_hook returns for a test JID
test_jid = sys.argv[1] if len(sys.argv) > 1 else "34600000000@s.whatsapp.net"
print(f"\n🧪 Simulating orchestrator_hook for {test_jid}:")

sys.path.insert(0, str(HERMES_HOME / "skills" / "andorina" / "scripts"))
try:
    from common import load_env
    from security.orchestrator import build_snapshot
    env = load_env()
    snap = build_snapshot(test_jid, env)
    
    ctx = snap.get("context_only", "")
    si = snap.get("system_instruction", "")
    
    has_soul_in_ctx = "PERSONALITY" in ctx or "SOUL" in ctx
    has_soul_in_si = "PERSONALITY" in si or "SOUL" in si
    
    print(f"   mode: {snap['mode']}")
    print(f"   system_instruction length: {len(si)} chars")
    print(f"   context_only length: {len(ctx)} chars")
    print(f"   ⚠️  Soul in system_instruction: {'YES' if has_soul_in_si else 'no'}")
    print(f"   ✅ Soul in context_only: {'YES ← BUG!' if has_soul_in_ctx else 'no (correct)'}")
    print(f"\n   context_only preview:")
    for line in ctx.split("\n")[:5]:
        print(f"      {line}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("SUMMARY:")
print("  - channel_prompt goes to: ephemeral system prompt (authoritative)")
print("  - context_only goes to: user message (auxiliary context)")
print("  - If old personality persists: reset session with /new or orchestrator.py reset")
print("=" * 60)
