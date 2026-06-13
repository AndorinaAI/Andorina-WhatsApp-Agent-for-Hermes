#!/usr/bin/env python3
"""Patch whatsapp.py to add Sub-Soul + Inbox support for Andoriña.

Adds three things to Hermes' WhatsApp gateway adapter:
  1. _resolve_lid_to_phone method  — translates @lid JIDs to phone JIDs.
  2. Sub-Soul injection block      — uses the resolver before resolve_channel_prompt.
  3. Andoriña Inbox Writer block   — writes incoming messages to inbox.json
     directly (no hook dependency) so the GUI panel can display them.

Safe to run multiple times — each step is idempotent (skipped if already present).
"""
import re
import sys
from pathlib import Path


def find_whatsapp_py():
    """Locate whatsapp.py in Hermes installation."""
    candidates = [
        Path.home() / ".hermes" / "hermes-agent" / "gateway" / "platforms" / "whatsapp.py",
    ]
    import os
    hh = os.environ.get("HERMES_HOME")
    if hh:
        candidates.insert(0, Path(hh) / "hermes-agent" / "gateway" / "platforms" / "whatsapp.py")
    for c in candidates:
        if c.exists():
            return c
    return None


# ── Markers ──────────────────────────────────────────────────────────────────
METHOD_MARKER = "_resolve_lid_to_phone"
INJECT_MARKER = "# Sub-Soul injection via native Hermes channel_prompt path."
INBOX_MARKER  = "# ── Andoriña Inbox Writer ──"

# ── 1. _resolve_lid_to_phone method ──────────────────────────────────────────
METHOD_ANCHOR = '''\
    def _is_group_allowed(self, chat_id: str) -> bool:
        """Check whether a group chat should be processed."""
        if self._group_policy == "disabled":
            return False
        if self._group_policy == "allowlist":
            return chat_id in self._group_allow_from
        # "open" — all groups allowed
        return True'''

METHOD_REPLACEMENT = METHOD_ANCHOR + '''

    def _resolve_lid_to_phone(self, jid: str) -> str:
        """Translate a WhatsApp multi-device LID JID to a phone-number JID.

        WhatsApp's multi-device protocol identifies users with a numeric LID
        (Linked Identity Device) rather than their phone number, so incoming
        messages arrive with e.g. '212725569433687@lid' instead of
        '34681680435@s.whatsapp.net'.  The Node bridge saves reverse-mapping
        files (lid-mapping-{lid}_reverse.json) in the session directory;
        this method reads those files to resolve the phone number so that
        per-user channel_prompts (sub-souls) can be matched correctly.

        Falls back to returning the original JID unchanged when:
          - The JID does not end in '@lid'.
          - No mapping file exists for this LID.
          - The mapping file cannot be read or parsed.
        """
        import json as _json
        if not jid.endswith("@lid"):
            return jid
        lid_number = jid[:-4]  # strip '@lid'
        mapping_file = self._session_path / f"lid-mapping-{lid_number}_reverse.json"
        try:
            if mapping_file.exists():
                phone = _json.loads(mapping_file.read_text(encoding="utf-8"))
                if phone:
                    return f"{str(phone).strip()}@s.whatsapp.net"
        except Exception:
            pass
        return jid  # fallback: return as-is if no mapping found'''

# ── 2. Sub-Soul injection block ───────────────────────────────────────────────
OLD_INJECT_BLOCK = '''\
            # Sub-Soul injection via native Hermes channel_prompt path.
            # soul_sync.py writes channel_prompts to config.yaml keyed by JID.
            from gateway.platforms.base import resolve_channel_prompt
            _sender = data.get("senderId") or ""
            _chat = data.get("chatId") or ""
            _sender_key = _sender if "@" in _sender else f"{_sender}@s.whatsapp.net"
            _chat_key = _chat if "@" in _chat else f"{_chat}@s.whatsapp.net"
            
            # Cascade: 1) Group soul (chatId), 2) Individual soul (senderId)
            _channel_prompt = resolve_channel_prompt(self.config.extra, _chat_key)
            if not _channel_prompt and _sender_key != _chat_key:
                _channel_prompt = resolve_channel_prompt(self.config.extra, _sender_key)'''

NEW_INJECT_BLOCK = '''\
            # Sub-Soul injection via native Hermes channel_prompt path.
            # soul_sync.py writes channel_prompts to config.yaml keyed by JID.
            # WhatsApp multi-device sends @lid identifiers — resolve to phone
            # numbers so that per-user channel_prompts can be matched.
            from gateway.platforms.base import resolve_channel_prompt
            _sender = data.get("senderId") or ""
            _chat = data.get("chatId") or ""
            _sender_key = self._resolve_lid_to_phone(
                _sender if "@" in _sender else f"{_sender}@s.whatsapp.net"
            )
            _chat_key = self._resolve_lid_to_phone(
                _chat if "@" in _chat else f"{_chat}@s.whatsapp.net"
            )

            # Cascade: 1) Group soul (chatId), 2) Individual soul (senderId)
            _channel_prompt = resolve_channel_prompt(self.config.extra, _chat_key)
            if not _channel_prompt and _sender_key != _chat_key:
                _channel_prompt = resolve_channel_prompt(self.config.extra, _sender_key)'''

# ── 3. Inbox Writer block (injected after sub-soul block, before return) ──────
INBOX_BLOCK = '''\

            # ── Andoriña Inbox Writer ────────────────────────────────────────────────────────
            # Write incoming messages directly to inbox.json so the GUI panel
            # can display them.  Replaces the broken hook approach
            # (message_received / whatsapp:message are not valid Hermes hooks).
            # Fully isolated: any exception here is swallowed so message
            # processing and sub-soul injection are never affected.
            try:
                import json as _json_inbox
                import fcntl as _fcntl
                import time as _time
                import os as _os_inbox
                from pathlib import Path as _Path

                _hermes_home = _Path(_os_inbox.environ.get("HERMES_HOME", str(_Path.home() / ".hermes")))
                _skill_base = _hermes_home / "skills" / "andorina"
                _inbox_file = _skill_base / "state" / "inbox.json"
                _lock_file  = _inbox_file.with_suffix(".lock")

                _sender_raw = self._resolve_lid_to_phone(data.get("senderId") or data.get("from") or "")
                _chat_raw   = self._resolve_lid_to_phone(data.get("chatId") or "")
                _ts = data.get("timestamp")
                if _ts:
                    try:
                        _ts_int = int(_ts)
                        if _ts_int > 20_000_000_000:
                            _ts_int //= 1000
                        _date_str = _time.strftime("%Y-%m-%dT%H:%M:%S", _time.localtime(_ts_int))
                    except Exception:
                        _date_str = _time.strftime("%Y-%m-%dT%H:%M:%S")
                else:
                    _date_str = _time.strftime("%Y-%m-%dT%H:%M:%S")

                _entry = {
                    "chatId":     _chat_raw,
                    "chatName":   data.get("chatName") or data.get("groupName") or "",
                    "from":       _sender_raw,
                    "senderName": data.get("senderName") or data.get("pushName") or "",
                    "text":       body or "",
                    "date":       _date_str,
                    "type":       data.get("mediaType") or "text",
                    "read":       False,
                }

                _inbox_file.parent.mkdir(parents=True, exist_ok=True)
                with open(_lock_file, "w") as _lf:
                    _fcntl.flock(_lf, _fcntl.LOCK_EX)
                    try:
                        _inbox = []
                        if _inbox_file.exists():
                            try:
                                _d = _json_inbox.loads(_inbox_file.read_text(encoding="utf-8"))
                                _inbox = _d if isinstance(_d, list) else []
                            except Exception:
                                _inbox = []

                        _merged = False
                        if _inbox and _entry["type"] == "text":
                            _last = _inbox[-1]
                            if (_last.get("chatId") == _entry["chatId"]
                                    and _last.get("from") == _entry["from"]
                                    and _last.get("type") == "text"):
                                try:
                                    from datetime import datetime as _dt
                                    _last_dt = _dt.strptime(_last["date"], "%Y-%m-%dT%H:%M:%S")
                                    _curr_dt = _dt.strptime(_entry["date"], "%Y-%m-%dT%H:%M:%S")
                                    if (_curr_dt - _last_dt).total_seconds() < 300:
                                        _last["text"] += "\\n" + _entry["text"]
                                        _last["date"] = _entry["date"]
                                        _last["read"] = False
                                        _merged = True
                                except Exception:
                                    pass

                        if not _merged:
                            _inbox.append(_entry)
                        if len(_inbox) > 500:
                            _inbox = _inbox[-500:]

                        _tmp = _inbox_file.with_suffix(".tmp")
                        _tmp.write_text(_json_inbox.dumps(_inbox, ensure_ascii=False, indent=2), encoding="utf-8")
                        _tmp.replace(_inbox_file)
                    finally:
                        _fcntl.flock(_lf, _fcntl.LOCK_UN)

                # ── Andoriña Alert Dispatcher ─────────────────────────────────────────
                # Call webhook.py to process semantic alerts and away-responder.
                # Runs as a detached subprocess — never blocks message processing.
                if not data.get("fromMe", False):
                    import subprocess as _sp
                    import sys as _sys_wh
                    _wh = _skill_base / "scripts" / "transport" / "webhook.py"
                    if _wh.exists():
                        _wh_payload = _json_inbox.dumps({
                            "event": "message_received",
                            "write_inbox": False,   # inbox already written above — skip duplicate write
                            "payload": {
                                "from":      _sender_raw,
                                "chatId":    _chat_raw,
                                "chatName":  data.get("chatName") or data.get("groupName") or "",
                                "senderId":  _sender_raw,
                                "text":      body or "",
                                "body":      body or "",
                                "pushName":  data.get("senderName") or data.get("pushName") or "",
                                "timestamp": data.get("timestamp"),
                                "fromMe":    False,
                                "type":      data.get("mediaType") or "text",
                            }
                        }).encode()
                        try:
                            _proc = _sp.Popen(
                                [_sys_wh.executable, str(_wh)],
                                stdin=_sp.PIPE, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL
                            )
                            _proc.stdin.write(_wh_payload)
                            _proc.stdin.close()
                        except Exception:
                            pass
                # ── End Alert Dispatcher ────────────────────────────────────────────

            except Exception:
                pass  # Never let inbox errors break message processing
            # ── End Inbox Writer ────────────────────────────────────────────────────────'''

# ── Return MessageEvent patterns ──────────────────────────────────────────────
RETURN_PATTERN = re.compile(
    r'(            return MessageEvent\(\n'
    r'                text=body,\n'
    r'                message_type=msg_type,\n'
    r'                source=source,\n'
    r'                raw_message=data,\n'
    r'                message_id=data\.get\("messageId"\),\n'
    r'                media_urls=cached_urls,\n'
    r'                media_types=media_types,\n'
    r'            \))'
)

RETURN_WITH_CHANNEL = re.compile(
    r'(            return MessageEvent\(\n'
    r'                text=body,\n'
    r'                message_type=msg_type,\n'
    r'                source=source,\n'
    r'                raw_message=data,\n'
    r'                message_id=data\.get\("messageId"\),\n'
    r'                media_urls=cached_urls,\n'
    r'                media_types=media_types,\n'
    r'                channel_prompt=_channel_prompt,\n'
    r'            \))'
)


def patch(dry_run=False):
    wp = find_whatsapp_py()
    if not wp:
        print("❌ whatsapp.py not found")
        return False

    content = wp.read_text(encoding="utf-8")
    changed = False

    # ── 1. Add _resolve_lid_to_phone method if missing ───────────────────────
    if METHOD_MARKER not in content:
        if METHOD_ANCHOR not in content:
            print("⚠️  Could not find _is_group_allowed anchor — skipping method injection")
        else:
            if dry_run:
                print("[dry-run] Would inject _resolve_lid_to_phone method")
            else:
                content = content.replace(METHOD_ANCHOR, METHOD_REPLACEMENT, 1)
                changed = True
                print("✓ _resolve_lid_to_phone method injected")
    else:
        print("✓ _resolve_lid_to_phone already present")

    # ── 2. Upgrade stale inject block (old → new, with LID resolution) ────────
    if OLD_INJECT_BLOCK in content:
        if dry_run:
            print("[dry-run] Would upgrade inject block to LID-aware version")
        else:
            content = content.replace(OLD_INJECT_BLOCK, NEW_INJECT_BLOCK, 1)
            changed = True
            print("✓ Inject block upgraded to LID-aware version")

    # ── 3. Add inject block + channel_prompt if totally missing ───────────────
    if INJECT_MARKER not in content:
        m = RETURN_WITH_CHANNEL.search(content)
        if m:
            if dry_run:
                print("[dry-run] Would inject sub-soul block before existing MessageEvent return")
            else:
                new_return = NEW_INJECT_BLOCK + "\n\n" + m.group(1)
                content = content[:m.start()] + new_return + content[m.end():]
                changed = True
                print("✓ Sub-soul inject block added")
        else:
            m2 = RETURN_PATTERN.search(content)
            if m2:
                if dry_run:
                    print("[dry-run] Would inject block and add channel_prompt to MessageEvent")
                else:
                    new_return_inner = m2.group(1).replace(
                        "                media_types=media_types,\n            )",
                        "                media_types=media_types,\n                channel_prompt=_channel_prompt,\n            )"
                    )
                    new_return = NEW_INJECT_BLOCK + "\n\n" + new_return_inner
                    content = content[:m2.start()] + new_return + content[m2.end():]
                    changed = True
                    print("✓ Sub-soul inject block + channel_prompt added to MessageEvent")
            else:
                print("⚠️  Could not find MessageEvent return pattern — manual check needed")
    else:
        print("✓ Sub-Soul injection block already present")

    # ── 4. Add Inbox Writer block before return MessageEvent ──────────────────
    if INBOX_MARKER not in content:
        m_ret = RETURN_WITH_CHANNEL.search(content)
        if m_ret:
            if dry_run:
                print("[dry-run] Would inject Inbox Writer before return MessageEvent")
            else:
                new_return = INBOX_BLOCK + "\n\n" + m_ret.group(1)
                content = content[:m_ret.start()] + new_return + content[m_ret.end():]
                changed = True
                print("✓ Inbox Writer block injected")
        else:
            print("⚠️  Could not find patched MessageEvent return — inbox writer not injected")
    else:
        print("✓ Inbox Writer already present")

    if not changed:
        print("✓ whatsapp.py already fully patched — nothing to do")
        return True

    if not dry_run:
        backup = wp.with_suffix(".py.bak")
        if not backup.exists():
            import shutil
            shutil.copy2(wp, backup)
            print(f"  (backup: {backup})")
        wp.write_text(content, encoding="utf-8")
        print(f"✓ whatsapp.py patched successfully ({wp})")

    return True


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    ok = patch(dry_run=dry)
    sys.exit(0 if ok else 1)
