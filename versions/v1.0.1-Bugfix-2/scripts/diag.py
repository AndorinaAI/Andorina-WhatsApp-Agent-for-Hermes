#!/usr/bin/env python3
"""
🩺 Andoriña — System Diagnosis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verifies the health of Qdrant, WhatsApp Bridge, and Configuration.
"""

import sys, json, urllib.request
from pathlib import Path

# Paths
ENV_FILE = Path.home() / ".hermes" / ".env"
BRIDGE_URL = "http://localhost:3000"

# Load dynamic configuration
if ENV_FILE.exists():
    try:
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "WHATSAPP_BRIDGE_URL" in line and "=" in line:
                BRIDGE_URL = line.partition("=")[2].strip()
    except: pass

def out(msg, ok=True):
    symbol = "✅" if ok else "❌"
    print(f"{symbol} {msg}")

def check_qdrant():
    try:
        # Standard Qdrant port
        with urllib.request.urlopen("http://localhost:6333/", timeout=2) as r:
            return r.getcode() == 200
    except: return False

def check_bridge():
    try:
        with urllib.request.urlopen(f"{BRIDGE_URL}/health", timeout=2) as r:
            return json.loads(r.read().decode('utf-8'))
    except: return None

def main():
    print("\n🩺 Andoriña System Diagnosis")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    # 1. Qdrant
    q_ok = check_qdrant()
    out("Qdrant Memory Engine: " + ("Online" if q_ok else "Offline"), q_ok)
    
    # 2. Bridge
    b_data = check_bridge()
    if b_data:
        out(f"WhatsApp Bridge: Online (v{b_data.get('version', '1.x')})", True)
        status = b_data.get('status', 'Unknown')
        out(f"WhatsApp Connection: {status}", status == 'connected')
    else:
        out(f"WhatsApp Bridge: Offline (Check port at {BRIDGE_URL})", False)

    # 3. Contacts
    has_token = False
    if ENV_FILE.exists():
        has_token = "GOOGLE_CONTACTS_ACCESS_TOKEN" in ENV_FILE.read_text(encoding="utf-8")
    out("Google Contacts Linked: " + ("Yes" if has_token else "No"), has_token)

    print("\n✨ Diagnosis complete.\n")

if __name__ == "__main__":
    main()
