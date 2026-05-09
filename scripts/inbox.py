#!/usr/bin/env python3
"""
🚀 Andoriña — Inbox Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━
Reads and lists incoming WhatsApp messages from the local log.
"""

import sys, json
from pathlib import Path

INBOX_FILE = Path.home() / '.hermes/skills/messaging/andorina/state/inbox.json'

def out(data):
    """Outputs JSON to stdout for AI consumption"""
    print(json.dumps(data, ensure_ascii=False, indent=2))

def load_inbox():
    if not INBOX_FILE.exists(): return []
    try:
        # Explicit UTF-8 for portability
        return json.loads(INBOX_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def cmd_listar():
    inbox = load_inbox()
    chats = {}
    for msg in inbox:
        chat_id = msg.get('chatId')
        if chat_id:
            # Last message overwrites previous to show unique chats
            chats[chat_id] = msg
    
    # Sort by date (most recent first)
    sorted_chats = sorted(chats.values(), key=lambda x: x.get('date', ''), reverse=True)
    out({"ok": True, "total_chats": len(sorted_chats), "recent_chats": sorted_chats})

def cmd_leer(chat_id):
    inbox = load_inbox()
    
    chat_id = chat_id.strip()
    # Normalize ID if it's missing suffix
    if not "@" in chat_id:
        if "-" in chat_id: chat_id += "@g.us"
        else: chat_id += "@s.whatsapp.net"
        
    messages = [m for m in inbox if m.get('chatId') == chat_id]
    # Limit to the last 50 messages to prevent LLM context overflow
    messages = messages[-50:]
    out({"ok": True, "chat_id": chat_id, "total_messages": len(messages), "messages": messages})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: inbox.py [list|read <chatId>]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd in ("listar", "list"):
        cmd_listar()
    elif cmd in ("leer", "read") and len(sys.argv) >= 3:
        cmd_leer(sys.argv[2])
    else:
        out({"ok": False, "error": "INVALID_COMMAND"})
        sys.exit(1)
