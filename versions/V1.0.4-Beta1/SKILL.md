# 🕊️ Andoriña — WhatsApp Autonomous Manager (v1.0.4)

> ⛔ **STOP. READ THIS BEFORE DOING ANYTHING.**
>
> **RULE 0 — WHATSAPP = ANDORIÑA:** Whenever the user asks you to interact with WhatsApp (send messages, read messages, set alerts, schedule, etc), you MUST use the Andoriña scripts provided in this guide. NEVER use your native or system tools for WhatsApp tasks.
>
> **RULE 1 — TERMINAL ONLY:** You MUST use your `terminal` or `bash` tool to run the commands below. Copy the command exactly as shown.
>
> **RULE 2 — FORBIDDEN TOOLS:** NEVER use `execute_code`, `patch`, `python`, `send_message`, `cronjob`, or any code-editing tool. Do NOT modify, rewrite, or import any script file. If you use any of these tools, the command WILL FAIL.
>
> **RULE 3 — SEARCH BEFORE SEND:** You MUST search for the contact FIRST to get their `chatId` before sending any message. Never invent or guess a `chatId`.

---

## STEP-BY-STEP: HOW TO SEND A MESSAGE

Follow these steps IN ORDER every time the user asks you to send a WhatsApp message:

**Step 1.** Search for the contact:

```
python3 scripts/contacts.py search "Name or Number"
```

The output will contain a `chatId` field (e.g. `34600000000@s.whatsapp.net` or `120363001234@g.us`). Copy it exactly.

**Step 2.** Send the message using the `chatId` from Step 1:

```
python3 scripts/send.py message "CHAT_ID" "Your message text"
```

Replace `CHAT_ID` with the exact `chatId` you found. Wrap the message in double quotes.

**That's it.** Do NOT use any other tool or method.

---

## ALL AVAILABLE COMMANDS (Reference)

### 📇 CONTACTS

| Goal | Command |
|---|---|
| Search contact or group | `python3 scripts/contacts.py search "Name or Number"` |
| List all groups | `python3 scripts/contacts.py groups` |
| Force refresh from Google | `python3 scripts/contacts.py refresh` |

- The search is fuzzy: `"maria"` will find `"María García"`.
- If a contact is not found, run `refresh` and then search again.
- Group IDs end in `@g.us`. Contact IDs end in `@s.whatsapp.net`.

### ✉️ SEND TEXT

| Goal | Command |
|---|---|
| Send text message | `python3 scripts/send.py message "CHAT_ID" "Your message"` |
| Check bridge status | `python3 scripts/send.py status` |

- Replace `CHAT_ID` with the exact chatId from a contacts search.
- The message MUST be wrapped in double quotes.
- If the chatId is invalid, you will get `INVALID_CHAT_ID`.

### 📁 SEND FILES

| Goal | Command |
|---|---|
| Send image/doc/video | `python3 scripts/files.py "/absolute/path/to/file" "CHAT_ID"` |
| Send voice note (PTT) | `python3 scripts/files.py "/absolute/path/to/audio.mp3" "CHAT_ID" --voice` |

- The file MUST exist on disk. Use an absolute path.
- Any file type is supported (including unknown formats like `.xcf`). They will be delivered perfectly with their original filename.
- If you get `FILE_NOT_FOUND`, the path is wrong.

> **⚠️ FILE SEARCH PROTOCOL (Follow step-by-step!):**
>
> 1. Get the real folder path (language-dependent!):
>    `xdg-user-dir PICTURES` or `xdg-user-dir DOCUMENTS` or `xdg-user-dir DOWNLOAD`
> 2. Search for the file using the path from step 1:
>    `find /path/from/step1 -iname "filename.jpg"`
> 3. If not found, search broader:
>    `find ~ -maxdepth 3 -iname "*keyword*"`
> 4. For text files (`.txt`, `.md`, `.csv`), you CAN verify content:
>    `head -n 20 "/path/to/file.txt"`
> 5. For images, videos, Office docs (`.png`, `.jpg`, `.mp4`, `.docx`, `.pdf`), you CANNOT see the content. If the name is ambiguous or you find multiple files, ASK the user:
>    *"I cannot see the content of image/Office files. Please confirm if you want me to send [path]"*

### 📥 READ MESSAGES (INBOX)

| Goal | Command |
|---|---|
| List all recent chats | `python3 scripts/inbox.py list` |
| Read messages from a chat | `python3 scripts/inbox.py read "CHAT_ID"` |
| Read last N messages | `python3 scripts/inbox.py read "CHAT_ID" N` |
| Read ALL messages | `python3 scripts/inbox.py read "CHAT_ID" all` |

- Default is last 50 messages.
- History starts recording from when the skill was installed. It is NOT retroactive.

### 🔔 ALERTS (Permanent Listening / Forwarding)

Use this when the user says "alert me", "warn me", "listen to", or "forward messages from".

| Goal | Command |
|---|---|
| Alert on ALL messages | `python3 scripts/alerts.py add "SOURCE_CHAT_ID" "OWNER"` |
| Alert on specific topics | `python3 scripts/alerts.py add "SOURCE_CHAT_ID" "OWNER" --keywords "word1, word2, word3"` |
| Forward to someone else | `python3 scripts/alerts.py add "SOURCE_CHAT_ID" "TARGET_CHAT_ID"` |
| Stop listening | `python3 scripts/alerts.py remove "SOURCE_CHAT_ID"` |
| List active alerts | `python3 scripts/alerts.py list` |

- `SOURCE_CHAT_ID` = the person/group you want to monitor. You MUST search for them first.
- `OWNER` = the special word that forwards to the admin. Write it exactly: `OWNER`.
- `--keywords` = comma-separated list. Be generous with synonyms, slang, and diminutives.
  - Example for "school": `"instituto, insti, colegio, cole, profe, profesor, examen, exámenes, nota, notas, clase, deberes, tarea"`
  - Example for "work": `"trabajo, curro, laburo, jefe, reunión, meeting, oficina, turno"`
- **CRITICAL:** You MUST search for the contact first to get their real `chatId`. NEVER guess an ID.

### 📅 SCHEDULE MESSAGES (AGENDA)

| Goal | Command |
|---|---|
| Schedule text | `python3 scripts/agenda.py auto-schedule "CHAT_ID" "TIME" "Message"` |
| Schedule file | `python3 scripts/agenda.py auto-schedule "CHAT_ID" "TIME" "/path/to/file"` |
| Schedule voice note | `python3 scripts/agenda.py auto-schedule "CHAT_ID" "TIME" "/path/to/audio.mp3" --voice` |
| List pending tasks | `python3 scripts/agenda.py list` |
| Cancel a task | `python3 scripts/agenda.py remove "MSG_ID"` |

**Time formats:**

| Format | Meaning | Example |
|---|---|---|
| `HH:MM` | Today at this hour | `"22:00"` |
| `DD HH:MM` | This month, day DD | `"25 09:30"` |
| `DD/MM HH:MM` | Specific date | `"15/06 18:00"` |

- Andoriña auto-avoids time collisions: if two tasks are at the same minute, it shifts one.
- If the message was not delivered on time, it stays in the agenda for retry (up to 60 minutes).

### 🩺 DIAGNOSTICS & REPAIR

| Goal | Command |
|---|---|
| Full system health check | `python3 scripts/diag.py` |
| Auto-repair bridge + QR | `python3 scripts/bridge_health.py` |

- If the user says "WhatsApp is not working", run `diag.py` first.
- If bridge is offline, run `bridge_health.py`. It will attempt auto-repair.

### 🛡️ SECURITY

| Goal | Command |
|---|---|
| View rate limit status | `python3 scripts/guard.py status` |
| Unblock a user | `python3 scripts/guard.py reset "34600000000"` |

- Replace the number with the actual phone number (digits only, no `+`).

### 🧹 CLEANUP

| Goal | Command |
|---|---|
| Delete logs, inbox, agenda | `python3 scripts/wipe_logs.py` |
| Wipe vector memory (Qdrant) | `python3 scripts/wipe_memory.py` |

- `wipe_logs.py` deletes chat history and scheduled tasks. WhatsApp session stays safe.
- `wipe_memory.py` erases the Qdrant vector database collections.

---

## PERSONA RULES (How to Behave)

1. **OWNER:** Speak naturally to the owner. They are your user.
2. **THIRD PARTIES:** When messaging anyone who is NOT the owner, introduce yourself according to your configured persona.
3. **LITERAL MODE:** If the owner says "Send literal", "Say exactly", or "Literal", send ONLY the exact text. No introductions, no extras.
4. **ID FIX:** If you see a phone number without `@`, add `@s.whatsapp.net`. If it contains `-`, add `@g.us`.

---

> **STUCK?** Read the source of any script to understand it:
> `cat scripts/<script_name>.py`
>
> **REMEMBER:** Use ONLY the `terminal` tool. NEVER use `execute_code`, `patch`, or `python` tools. NEVER modify any script.
