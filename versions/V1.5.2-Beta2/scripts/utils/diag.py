#!/usr/bin/env python3
"""
🩺 Andoriña — System Diagnosis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verifies the health of Qdrant, WhatsApp Bridge, and Configuration.
"""

import sys, json, urllib.request
from pathlib import Path

import os

# Paths
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
PROJECT_DIR = Path(__file__).parent.parent.parent.absolute()
STATE_DIR = PROJECT_DIR / "state"

# Import centralized env loading from common module
sys.path.append(str(Path(__file__).parent.parent))
from common import ENV_PATH, BRIDGE_URL

def out(msg, ok=True):
    symbol = "✅" if ok else "❌"
    print(f"{symbol} {msg}")

def check_memory():
    import subprocess
    provider = "Desconocido"
    is_ok = False
    try:
        cmd = os.environ.get("HERMES_CMD", "hermes")
        out = subprocess.check_output([cmd, "memory", "status"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if "Provider:" in line:
                provider = line.split(":", 1)[1].strip()
            if "Status:" in line:
                status_text = line.split(":", 1)[1].lower()
                if "available" in status_text or "online" in status_text or "ready" in status_text:
                    is_ok = True
        return provider, is_ok
    except Exception:
        return "Offline/Error", False

def check_bridge():
    try:
        with urllib.request.urlopen(f"{BRIDGE_URL}/health", timeout=2) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception: return None

def main():
    print("\n🩺 Diagnóstico del Sistema Andoriña")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    # 1. Memory
    provider, mem_ok = check_memory()
    out(f"Motor de Memoria ({provider}): " + ("Online" if mem_ok else "Offline"), mem_ok)
    
    # 2. Bridge
    b_data = check_bridge()
    if b_data:
        out(f"WhatsApp Bridge: Online (v{b_data.get('version', '1.x')})", True)
        status = b_data.get('status', 'Desconocido').lower()
        if status in ['open', 'connected']: status_es = "Conectado"
        else: status_es = status
        out(f"Conexión de WhatsApp: {status_es}", status in ['open', 'connected'])
    else:
        out(f"WhatsApp Bridge: Offline (Verifica el puerto en {BRIDGE_URL})", False)

    # 3. Contacts
    has_token = False
    if ENV_PATH.exists():
        has_token = "GOOGLE_CONTACTS_ACCESS_TOKEN" in ENV_PATH.read_text(encoding="utf-8")
    out("Contactos de Google Vinculados: " + ("Sí" if has_token else "No"), has_token)

    # 4. RBAC & Souls
    rules_file = STATE_DIR / "guard_rules.json"
    chatbot_file = STATE_DIR / "chatbot.json"
    away_file = STATE_DIR / "away.json"

    if rules_file.exists():
        rules = json.loads(rules_file.read_text(encoding="utf-8") or "{}")
        jids = len(rules.get("jids", {}))
        out(f"Reglas RBAC: Activas ({jids} contactos/grupos configurados)", True)
    else:
        out("Reglas RBAC: Faltantes (no se encontró guard_rules.json)", False)

    if chatbot_file.exists():
        c_data = json.loads(chatbot_file.read_text(encoding="utf-8") or "{}")
        chatbot_state = "Activado" if c_data.get("enabled", True) else "Desactivado"
        out(f"Motor de Chatbot Global: {chatbot_state}", c_data.get("enabled", True))
    else:
        out("Motor de Chatbot Global: Activado (Por Defecto)", True)

    if away_file.exists():
        a_data = json.loads(away_file.read_text(encoding="utf-8") or "{}")
        away_state = "Activado" if a_data.get("enabled", False) else "Desactivado"
        out(f"Auto-Responder Global (Away): {away_state}", a_data.get("enabled", False))
    else:
        out("Auto-Responder Global (Away): Desactivado", False)

    # 5. Local Storage
    notes_dir = STATE_DIR / "notes"
    souls_dir = STATE_DIR / "souls"
    agenda_file = STATE_DIR / "agenda.json"
    
    notes_count = len(list(notes_dir.glob("*.md"))) if notes_dir.exists() else 0
    souls_count = len(list(souls_dir.glob("*.md"))) if souls_dir.exists() else 0
    
    out(f"Almacenamiento Local: {notes_count} Notas, {souls_count} Souls Personalizadas", True)
    
    if agenda_file.exists():
        try:
            agenda_tasks = len(json.loads(agenda_file.read_text(encoding="utf-8") or "[]"))
            out(f"Cola de Agenda: {agenda_tasks} tareas pendientes", True)
        except:
            out("Cola de Agenda: Error al leer agenda.json", False)

    print("\n✨ Diagnóstico completado.\n")

if __name__ == "__main__":
    main()
