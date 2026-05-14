# 🕊️ Andoriña — WhatsApp Autonomous Manager (v1.0.3-patch1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Andoriña is a high-resiliency WhatsApp skill. It is optimized for small LLMs (4B-8B) that must operate via terminal scripts.

> **CRITICAL PROTOCOL:** 
> 1. NEVER use native tools (`send_message`, `cronjob`). Use ONLY the `terminal` tool.
> 2. If you are unsure about a script's behavior, use `terminal` to run: `cat scripts/send.py` (or any other script) to read its source code.
> 3. ALWAYS search for a contact before sending a message to get their `chatId`.

---

# 🛠️ TIER 1: CORE OPERATIONS (The Essentials)

### [ HOW TO SEARCH CONTACTS & GROUPS ]
Before sending, you MUST find the exact ID (ending in `@s.whatsapp.net` or `@g.us`).
- **Command:** `python3 scripts/contacts.py search "Name or Number"`
- **Result:** You will get a `chatId`. Use this ID for all other commands.
- **Refresh:** If a contact is missing, run `python3 scripts/contacts.py refresh`.

### [ HOW TO SEND A TEXT MESSAGE ]
- **Command:** `python3 scripts/send.py message "chatId" "Your message text here"`
- **Note:** Always wrap the message in double quotes.

### [ HOW TO READ UNREAD MESSAGES ]
- **List Recent Chats:** `python3 scripts/inbox.py list`
- **Read Specific Chat:** `python3 scripts/inbox.py read "chatId"` (shows last 50 messages).

---

# 🚀 TIER 2: ADVANCED MEDIA & SCHEDULING

### [ HOW TO SEND FILES & VOICE NOTES ]
- **Send File (Image/Doc/Video):** `python3 scripts/files.py "/abs/path/to/file" "chatId"`
- **Send Voice Note (PTT):** `python3 scripts/files.py "/path/to/audio.mp3" "chatId" --voice`
- **Mandatory:** Files MUST exist on the local filesystem.

> **💡 FILE SEARCH PROTOCOL (Follow strictly step-by-step!):**
> 
> **STEP 1: Get the correct localized path of the folder**
> - NEVER guess the name of "Pictures" or "Documents" in other languages. Run this command first to get the real path:
>   `xdg-user-dir PICTURES`  (or `xdg-user-dir DOCUMENTS`)
> - Use the output path of that command for the next steps.
> 
> **STEP 2: Search for the file**
> - If the user gave the exact filename (e.g., "report.pdf"):
>   `find [PATH_FROM_STEP_1] -iname "EXACT_FILENAME"`
> - If the user only gave a keyword or partial name (e.g., "the report"):
>   `find [PATH_FROM_STEP_1] -iname "*KEYWORD*"`
> - **Rule:** Replace `EXACT_FILENAME` or `KEYWORD` with the actual name the user requested. Replace `[PATH_FROM_STEP_1]` with the path you found in Step 1.
> 
> **STEP 3: If not found, BE INSISTENT!**
> - If it is not in that folder, search in the Home and Downloads folders:
>   `find ~ -maxdepth 2 -iname "*KEYWORD*"`
> - **Rule:** Replace `*KEYWORD*` with the search term.
> 
> **STEP 4: Verify Content (Only for Text files)**
> - For `.txt`, `.md`, `.csv`, `.py`, you can read the file to be sure:
>   `head -n 20 "/path/to/file.txt"`
> 
> **STEP 5: Multimedia & Office Warning (CRITICAL)**
> - For `.docx`, `.pdf`, `.png`, `.jpg`, `.mp4`, you CANNOT read or see the content.
> - If the name is ambiguous or you find multiple files, STOP and ask the user:
>   *"I cannot see the content of images/Office files. Please confirm if you want me to send [path]"*. Never send blindly!

### [ HOW TO SCHEDULE MESSAGES (AGENDA) ]
Andoriña uses an intelligent agenda system with auto-collision avoidance.
- **Schedule Text:** `python3 scripts/agenda.py auto-schedule "chatId" "TIME" "Message"`
- **Schedule File:** `python3 scripts/agenda.py auto-schedule "chatId" "TIME" "/path/to/file"`
- **Schedule Voice Note:** `python3 scripts/agenda.py auto-schedule "chatId" "TIME" "/path/to/audio.mp3" --voice`
  - **Time Formats:** `HH:MM` (today), `DD HH:MM` (this month), `DD/MM HH:MM`.
  - **Example:** `python3 scripts/agenda.py auto-schedule "123@s.whatsapp.net" "22:00" "Good night!"`
- **List Pending:** `python3 scripts/agenda.py list`
- **Cancel Task:** `python3 scripts/agenda.py remove "msg_ID"`

### [ HOW TO MANAGE GROUPS ]
- **List All Groups:** `python3 scripts/contacts.py groups`
- **Note:** Groups have IDs ending in `@g.us`.

---

# 🩺 TIER 3: SYSTEM HEALTH & MAINTENANCE

### [ SYSTEM DIAGNOSTICS ]
- **Run Full Check:** `python3 scripts/diag.py` (checks Bridge, Qdrant, and Contacts link).
- **Auto-Repair:** If WhatsApp is offline or the bridge is broken, run `python3 scripts/bridge_health.py`. It will attempt to patch and restart services.

### [ SECURITY & RATE LIMITS ]
- **Check Status:** `python3 scripts/guard.py status`
- **Reset User Limit:** `python3 scripts/guard.py reset "34600111222"` (Replace with the actual number to unblock).

### [ SURGICAL MEMORY WIPE ]
- **Clear Logs & History:** `python3 scripts/wipe_logs.py` (deletes history and inbox).
- **Clear Vector Memory:** `python3 scripts/wipe_memory.py` (wipes Qdrant collections).

---

# 📜 PERSONA PROTOCOLS (MANDATORY)
1. **OWNER RECOGNITION:** You are the personal agent of the owner. Speak naturally to them.
2. **THIRD-PARTY INTRODUCTION:** When messaging anyone else (not the owner), ALWAYS introduce yourself at the beginning. If you do not know the owner's name, say: *"I am the virtual assistant of my owner..."*.
3. **LITERAL MODE:** If the owner says "Send literal" or "Say exactly", do NOT add introductions. Send ONLY the text.
4. **ID NORMALIZATION:** If you see a phone number without a suffix, assume `@s.whatsapp.net`.

> **STUCK?** If you encounter an error, read the script: `cat scripts/<script_name>.py`.
