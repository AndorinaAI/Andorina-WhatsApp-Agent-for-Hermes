#!/usr/bin/env python3
"""
🚀 Andoriña — Setup Assistant (v1.0.3-patch1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys, os, re, subprocess, json, time
from pathlib import Path

# ── Colors ───────────────────────────────────────────────────
CYAN    = "\033[38;5;51m"
WHITE   = "\033[1;37m"
GRAY    = "\033[38;5;244m"
GREEN   = "\033[38;5;76m"
YELLOW  = "\033[38;5;226m"
RED     = "\033[38;5;196m"
MAGENTA = "\033[38;5;201m"
DIM     = "\033[2m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

# ── Paths ────────────────────────────────────────────────────
SOURCE_DIR  = Path(__file__).parent

LOGO = f"""{CYAN}
      @@@@@@@@@@@@@@@@@@@@@@@ @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@ @%@@@@@@@@@@@@@@@@@@@@@@@@@@@@%+#@@@@@
      @@@@@@@@@@@@@@@@@@@@ #@=%@@@@@@@@@@@@@@@@@@@@@@@%+ +-@@@@@@@
      @@@@@@@@@@@@@@@@@@@  @ @#@@@@@@@@@@@@@@@@@@@%+  +@@-@@@@@@@@
      @@@@@@@@@@@@@@@@@@  @ +@*@@@@@@@@@@@@@@@%-   +@@@+:@@@@@@@@@
      @@@@@@@@@@@@@@@@@  #  @ @@@@@@@@@@@@#-   :#@@%-- @@@@@@@@@@@
      @@@@@@@@@@@@@@@%     =-=@@@@@@@@#-    :#@%- :@%+@@@@@@@@@@@@
      @@@@@@@@@@@@@@-     = @@@@@%      :#%+  :#@@-@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@+       @@@@:    :*+    +@%+:@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@#       :@+          +@+  *@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@      +@         :%-  +@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@%+=   :=*@%*@-             %@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@:                         -@@@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@+  +@@@+-@+          :@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@%= =@@ @@@@+       *@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@%-:@:@@@@@@+      %@@@@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@%:+#@@@@@@@*    :*@@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@#+--+#@@@*     :=#@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%* -=        -#@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%-    **=-    :*@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+   +@@@@@@@@@%#%@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%  :@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%: *@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+:@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*@@@@@@@@@@@@@@
{RESET}"""

# ── i18n ─────────────────────────────────────────────────────
LANG = "en"  # default

STRINGS = {
    "es": {
        "lang_prompt":     "Selecciona idioma / Select language (es/en)",
        "subtitle":        "Asistente de Instalación v1.0.3-patch1",
        "tagline":         "Gestor Autónomo de WhatsApp para Hermes Agent",
        "profile":         "Perfil",
        "target":          "Destino",
        # Prerequisite
        "prereq_title":    "Requisito Previo",
        "prereq_warn":     "¡IMPORTANTE! Antes de instalar Andoriña, debes haber configurado WhatsApp en Hermes.",
        "prereq_detail":   "Ejecuta 'hermes gateway start' y escanea el QR con tu móvil PRIMERO.",
        "prereq_found":    "bridge.js encontrado.",
        "prereq_missing":  "bridge.js NO encontrado. Hermes no tiene el gateway de WhatsApp configurado.",
        "prereq_abort":    "Configura WhatsApp en Hermes primero y vuelve a ejecutar el instalador.",
        "prereq_ask":      "¿Ya has configurado WhatsApp en Hermes?",
        # Step 1
        "s1_title":        "Región e Identidad",
        "s1_cc":           "Prefijo de país (ej. 34 para España)",
        "s1_admin":        "Tu número de WhatsApp (admin)",
        "s1_ok":           "Identidad configurada.",
        # Step 2
        "s2_title":        "Google Contacts",
        "s2_linked":       "Google Contacts ya está vinculado.",
        "s2_relink":       "¿Re-vincular la cuenta de Google?",
        "s2_info1":        "Vincula tu cuenta de Google para buscar contactos por nombre.",
        "s2_info2":        "Se abrirá una ventana del navegador — solo inicia sesión y autoriza.",
        "s2_ask":          "¿Vincular Google Contacts ahora?",
        "s2_ok":           "¡Google Contacts vinculado correctamente!",
        "s2_fail":         "No se pudo verificar la vinculación. Puedes reintentar con: python3 scripts/auth.py",
        "s2_skip":         "Omitido. El agente no podrá buscar contactos por nombre.",
        "s2_later":        "Puedes vincular en cualquier momento con: python3 scripts/auth.py",
        "s2_browser":      "Abriendo navegador para inicio de sesión seguro...",
        # Step 3
        "s3_title":        "Rendimiento",
        "s3_info":         "Estos límites controlan cuánto contexto usa el agente IA.",
        "s3_ctx":          "Ventana de contexto (tokens)",
        "s3_umem":         "Límite de memoria de usuario (chars)",
        "s3_smem":         "Límite de memoria de sistema (chars)",
        "s3_ok":           "Configuración guardada.",
        # Step 4
        "s4_title":        "Desplegando Archivos",
        "s4_ok":           "SKILL.md + {n} scripts desplegados.",
        "s4_fail":         "Error en el despliegue: {e}",
        # Step 5
        "s5_title":        "Registrando Hooks de Bandeja",
        "s5_ok":           "Hooks de bandeja registrados en config.yaml.",
        "s5_exists":       "Los hooks ya están presentes.",
        "s5_noconf":       "config.yaml no encontrado — hooks no registrados.",
        "s5_fail":         "Error al registrar hooks: {e}",
        # Step 6
        "s6_title":        "Motor de Memoria (Qdrant)",
        "s6_info":         "Qdrant da al agente memoria a largo plazo entre conversaciones.",
        "s6_ask":          "¿Configurar Qdrant portable?",
        "s6_skip":         "Omitido. El agente funcionará sin memoria persistente.",
        "s6_notfound":     "setup_portable.py no encontrado en los scripts desplegados.",
        # Step 7
        "s7_title":        "Inicio Automático",
        "s7_info":         "Arranca Hermes gateway + Qdrant automáticamente al iniciar sesión.",
        "s7_ask":          "¿Activar inicio automático?",
        "s7_skip":         "Omitido. Tendrás que arrancar los servicios a mano.",
        "s7_notfound":     "setup_autostart.py no encontrado en los scripts desplegados.",
        # Step 8
        "s8_title":        "Parcheo del Puente WhatsApp",
        "s8_info":         "Añade soporte multimedia y listado de grupos al puente.",
        "s8_ask":          "¿Parchear y reiniciar el puente de WhatsApp?",
        "s8_skip":         "Omitido. Algunas funciones (audio, grupos) podrían no funcionar.",
        "s8_notfound":     "patch_bridge.py no encontrado.",
        # Step 9
        "s9_title":        "Optimización de SOUL",
        "s9_ok":           "SOUL.md optimizado para Andoriña.",
        "s9_skip":         "Optimización de SOUL omitida: {e}",
        # Final
        "done":            "¡INSTALACIÓN DE ANDORIÑA COMPLETADA! 🕊️",
        "ready":           "Tu asistente está listo para volar.",
        "quick":           "Comandos rápidos:",
        "cmd_agent":       "Iniciar el agente",
        "cmd_gw":          "Iniciar el puente de WhatsApp",
        "cmd_auth":        "Vincular Google Contacts",
        "cmd_diag":        "Diagnóstico completo del sistema",
    },
    "en": {
        "lang_prompt":     "Selecciona idioma / Select language (es/en)",
        "subtitle":        "Setup Assistant v1.0.3-patch1",
        "tagline":         "Autonomous WhatsApp Manager for Hermes Agent",
        "profile":         "Profile",
        "target":          "Target",
        # Prerequisite
        "prereq_title":    "Prerequisite Check",
        "prereq_warn":     "IMPORTANT! You must configure WhatsApp in Hermes BEFORE installing Andoriña.",
        "prereq_detail":   "Run 'hermes gateway start' and scan the QR code with your phone FIRST.",
        "prereq_found":    "bridge.js found.",
        "prereq_missing":  "bridge.js NOT found. Hermes does not have the WhatsApp gateway configured.",
        "prereq_abort":    "Configure WhatsApp in Hermes first, then re-run this installer.",
        "prereq_ask":      "Have you already configured WhatsApp in Hermes?",
        # Step 1
        "s1_title":        "Region & Identity",
        "s1_cc":           "Country prefix (e.g. 34 for Spain)",
        "s1_admin":        "Your WhatsApp number (admin)",
        "s1_ok":           "Identity configured.",
        # Step 2
        "s2_title":        "Google Contacts",
        "s2_linked":       "Google Contacts already linked.",
        "s2_relink":       "Re-link Google account?",
        "s2_info1":        "Link your Google account to search contacts by name.",
        "s2_info2":        "This opens a browser window — just log in and authorize.",
        "s2_ask":          "Link Google Contacts now?",
        "s2_ok":           "Google Contacts linked successfully!",
        "s2_fail":         "Could not verify linking. Retry later with: python3 scripts/auth.py",
        "s2_skip":         "Skipped. The agent won't be able to search contacts by name.",
        "s2_later":        "You can link anytime with: python3 scripts/auth.py",
        "s2_browser":      "Opening browser for secure login...",
        # Step 3
        "s3_title":        "Performance Tuning",
        "s3_info":         "These limits control how much context the AI agent uses.",
        "s3_ctx":          "Context window (tokens)",
        "s3_umem":         "User memory limit (chars)",
        "s3_smem":         "System memory limit (chars)",
        "s3_ok":           "Configuration saved.",
        # Step 4
        "s4_title":        "Deploying Skill Files",
        "s4_ok":           "SKILL.md + {n} scripts deployed.",
        "s4_fail":         "Deployment failed: {e}",
        # Step 5
        "s5_title":        "Registering Inbox Hooks",
        "s5_ok":           "Inbox hooks registered in config.yaml.",
        "s5_exists":       "Hooks already present.",
        "s5_noconf":       "config.yaml not found — hooks not registered.",
        "s5_fail":         "Hook registration failed: {e}",
        # Step 6
        "s6_title":        "Memory Engine (Qdrant)",
        "s6_info":         "Qdrant gives the agent long-term memory across conversations.",
        "s6_ask":          "Setup Qdrant portable?",
        "s6_skip":         "Skipped. Agent will work without persistent memory.",
        "s6_notfound":     "setup_portable.py not found in deployed scripts.",
        # Step 7
        "s7_title":        "Autostart on Boot",
        "s7_info":         "Starts Hermes gateway + Qdrant automatically on login.",
        "s7_ask":          "Enable autostart?",
        "s7_skip":         "Skipped. You'll need to start services manually.",
        "s7_notfound":     "setup_autostart.py not found in deployed scripts.",
        # Step 8
        "s8_title":        "WhatsApp Bridge Patching",
        "s8_info":         "Adds multimedia support and group listing to the bridge.",
        "s8_ask":          "Patch and restart the WhatsApp bridge?",
        "s8_skip":         "Skipped. Some features (audio, groups) may not work.",
        "s8_notfound":     "patch_bridge.py not found.",
        # Step 9
        "s9_title":        "SOUL Optimization",
        "s9_ok":           "SOUL.md optimized for Andoriña.",
        "s9_skip":         "SOUL optimization skipped: {e}",
        # Final
        "done":            "ANDORIÑA SETUP COMPLETE! 🕊️",
        "ready":           "Your assistant is ready to fly.",
        "quick":           "Quick commands:",
        "cmd_agent":       "Start the agent",
        "cmd_gw":          "Start WhatsApp bridge",
        "cmd_auth":        "Link Google Contacts",
        "cmd_diag":        "Full system diagnosis",
    }
}

def t(key, **kwargs):
    """Translate a key using the current language."""
    s = STRINGS.get(LANG, STRINGS["en"]).get(key, key)
    if kwargs:
        return s.format(**kwargs)
    return s

# ── Helpers ──────────────────────────────────────────────────
def hr():
    print(f"   {GRAY}{'━' * 58}{RESET}")

def step(num, title):
    if num == "⚠":
        s = ""
    else:
        s = "PASO" if LANG == "es" else "STEP"
    print(f"\n   {MAGENTA}{'━' * 58}{RESET}")
    print(f"   {BOLD}{WHITE}{s} {num}{RESET}  {CYAN}{title}{RESET}")
    print(f"   {MAGENTA}{'━' * 58}{RESET}")

def ok(msg):
    print(f"   {GREEN}✅ {msg}{RESET}")

def warn(msg):
    print(f"   {YELLOW}⚠️  {msg}{RESET}")

def fail(msg):
    print(f"   {RED}❌ {msg}{RESET}")

def info(msg):
    print(f"   {GRAY}ℹ️  {msg}{RESET}")

def ask(prompt, default=""):
    label = f" [{default}]" if default else ""
    return input(f"   {WHITE}👉 {prompt}{DIM}{label}{RESET}: ").strip() or default

def confirm(prompt, default="y"):
    label = "S/n" if LANG == "es" and default == "y" else "s/N" if LANG == "es" else "Y/n" if default == "y" else "y/N"
    ans = input(f"   {WHITE}👉 {prompt} ({label}){RESET}: ").strip().lower() or default
    return ans in ("y", "s", "yes", "si", "sí")

def read_env(env_path):
    if not env_path.exists(): return {}
    env = {}
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    except: pass
    return env

def write_env(env_path, updates):
    text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    for k, v in updates.items():
        pat = rf"^{k}=.*"
        repl = f"{k}={v}"
        if re.search(pat, text, flags=re.MULTILINE):
            text = re.sub(pat, repl, text, flags=re.MULTILINE)
        else:
            if text and not text.endswith("\n"): text += "\n"
            text += f"{repl}\n"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(text, encoding="utf-8")

# ── Agent Auto-Detection ─────────────────────────────────────
def detect_agents():
    """Scan for Hermes agent profiles."""
    agents = []
    home = Path.home()
    # Check hidden dirs in $HOME with 'skills' subdirectory
    for p in sorted(home.iterdir()):
        if p.name.startswith(".") and p.is_dir() and (p / "skills").is_dir():
            agents.append(p)
    # Check $HOME/.hermes/profiles/
    profiles_dir = home / ".hermes" / "profiles"
    if profiles_dir.is_dir():
        for p in sorted(profiles_dir.iterdir()):
            if p.is_dir() and (p / "skills").is_dir():
                agents.append(p)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for a in agents:
        r = a.resolve()
        if r not in seen:
            seen.add(r)
            unique.append(a)
    return unique

# ── Main ─────────────────────────────────────────────────────
def main():
    global LANG
    import shutil

    # ── Welcome & Language ───────────────────────────────────
    os.system("clear" if os.name != "nt" else "cls")
    print(LOGO)
    print(f"   {BOLD}{WHITE}A N D O R I Ñ A{RESET}")
    hr()
    lang_input = input(f"   {WHITE}👉 {t('lang_prompt')} [en]{RESET}: ").strip().lower() or "en"
    LANG = "es" if lang_input in ("es", "español", "spanish") else "en"

    # ── Agent Auto-Detection ─────────────────────────────────
    HERMES_HOME = None
    if not os.environ.get("HERMES_HOME"):
        agents = detect_agents()
        if agents:
            msg_detect = "Agentes detectados" if LANG == "es" else "Detected Agents"
            print(f"\n   {BOLD}{WHITE}🤖 {msg_detect}:{RESET}")
            for i, a in enumerate(agents):
                name = a.name.lstrip(".")
                print(f"      {CYAN}{i+1}){RESET} {name} {GRAY}({a}){RESET}")
            msg_manual = "Ingreso manual" if LANG == "es" else "Manual entry"
            print(f"      {CYAN}0){RESET} {msg_manual}")
            msg_select = "Selecciona agente" if LANG == "es" else "Select agent"
            choice = ask(msg_select, "1")
            try:
                idx = int(choice)
                if 1 <= idx <= len(agents):
                    HERMES_HOME = agents[idx - 1]
                else:
                    raise ValueError
            except ValueError:
                msg_path = "Ruta completa del agente" if LANG == "es" else "Full agent path"
                manual = ask(msg_path, str(Path.home() / ".hermes"))
                HERMES_HOME = Path(manual)
        else:
            msg_path = "Ruta completa del agente" if LANG == "es" else "Full agent path"
            manual = ask(msg_path, str(Path.home() / ".hermes"))
            HERMES_HOME = Path(manual)
    else:
        HERMES_HOME = Path(os.environ["HERMES_HOME"])

    # Export for child processes (auth.py, etc.)
    os.environ["HERMES_HOME"] = str(HERMES_HOME)

    # Path Discovery
    skills_root = HERMES_HOME / "skills"
    category = "messaging"
    if (skills_root / "message").exists() and not (skills_root / "messaging").exists():
        category = "message"

    hermes_base = skills_root / category / "andorina"
    scripts_dir = hermes_base / "scripts"
    env_file    = hermes_base / ".env"
    soul_file   = HERMES_HOME / "SOUL.md"

    # Discover bridge path
    main_hermes = HERMES_HOME
    if main_hermes.parent.name == "profiles":
        main_hermes = main_hermes.parent.parent
    bridge_path = main_hermes / "hermes-agent" / "scripts" / "whatsapp-bridge" / "bridge.js"

    print()
    print(f"   {BOLD}{WHITE}A N D O R I Ñ A{RESET}   {DIM}{t('subtitle')}{RESET}")
    print(f"   {DIM}{t('tagline')}{RESET}")
    hr()
    print(f"   {GRAY}{t('profile')}: {HERMES_HOME}{RESET}")
    print(f"   {GRAY}{t('target')}:  {hermes_base}{RESET}")
    hr()
    print()

    # ── PREREQUISITE: WhatsApp must be configured in Hermes ──
    step("⚠", t("prereq_title"))
    print(f"   {YELLOW}{BOLD}{t('prereq_warn')}{RESET}")
    print(f"   {GRAY}{t('prereq_detail')}{RESET}")
    print()
    if bridge_path.exists():
        ok(t("prereq_found"))
    else:
        fail(t("prereq_missing"))
        print(f"   {GRAY}   → {bridge_path}{RESET}")
        print()
        if not confirm(t("prereq_ask"), "n"):
            print()
            fail(t("prereq_abort"))
            print()
            sys.exit(1)
        else:
            warn(t("prereq_detail"))

    env = read_env(env_file)
    updates = {}

    # ── STEP 1: Region ───────────────────────────────────────
    step(1, t("s1_title"))
    cc = ask(t("s1_cc"), env.get("DEFAULT_COUNTRY_CODE", "34"))
    updates["DEFAULT_COUNTRY_CODE"] = cc.replace("+", "").lstrip("0")

    admin = ask(t("s1_admin"), env.get("WHATSAPP_ALLOWED_USERS", ""))
    if admin:
        updates["WHATSAPP_ALLOWED_USERS"] = admin.replace("+", "").replace(" ", "")

    ok(t("s1_ok"))

    # ── STEP 2: Google Contacts ──────────────────────────────
    step(2, t("s2_title"))

    # Write identity data FIRST so auth.py can find the .env
    hermes_base.mkdir(parents=True, exist_ok=True)
    write_env(env_file, updates)

    has_refresh = bool(env.get("GOOGLE_CONTACTS_REFRESH_TOKEN"))

    if has_refresh:
        ok(t("s2_linked"))
        if confirm(t("s2_relink"), "n"):
            info(t("s2_browser"))
            subprocess.run([sys.executable, str(SOURCE_DIR / "scripts" / "auth.py")])
    else:
        info(t("s2_info1"))
        info(t("s2_info2"))
        if confirm(t("s2_ask")):
            info(t("s2_browser"))
            subprocess.run([sys.executable, str(SOURCE_DIR / "scripts" / "auth.py")])
            env = read_env(env_file)
            if env.get("GOOGLE_CONTACTS_REFRESH_TOKEN"):
                ok(t("s2_ok"))
            else:
                warn(t("s2_fail"))
        else:
            info(t("s2_skip"))
            info(t("s2_later"))

    # ── STEP 3: Performance ──────────────────────────────────
    step(3, t("s3_title"))
    info(t("s3_info"))
    print()

    ctx  = ask(t("s3_ctx"), env.get("ANDORINA_TARGET_CONTEXT", "75000"))
    umem = ask(t("s3_umem"), env.get("ANDORINA_TARGET_USER_MEM", "5000"))
    smem = ask(t("s3_smem"), env.get("ANDORINA_TARGET_SYS_MEM", "5000"))

    perf_updates = {
        "ANDORINA_TARGET_CONTEXT": ctx,
        "ANDORINA_TARGET_USER_MEM": umem,
        "ANDORINA_TARGET_SYS_MEM": smem,
    }
    # Only set bridge URL if not already configured by the user
    if not env.get("WHATSAPP_BRIDGE_URL"):
        perf_updates["WHATSAPP_BRIDGE_URL"] = "http://localhost:3000"
    updates.update(perf_updates)
    write_env(env_file, updates)
    ok(t("s3_ok"))

    # ── STEP 4: Deploy ───────────────────────────────────────
    step(4, t("s4_title"))
    try:
        hermes_base.mkdir(parents=True, exist_ok=True)
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (hermes_base / "state").mkdir(parents=True, exist_ok=True)

        shutil.copy2(SOURCE_DIR / "SKILL.md", hermes_base / "SKILL.md")
        count = 0
        for script in (SOURCE_DIR / "scripts").glob("*.py"):
            shutil.copy2(script, scripts_dir / script.name)
            (scripts_dir / script.name).chmod(0o755)
            count += 1

        ok(t("s4_ok", n=count))
    except Exception as e:
        fail(t("s4_fail", e=e))

    # ── STEP 5: Hooks ────────────────────────────────────────
    step(5, t("s5_title"))
    try:
        hook = scripts_dir / "hook_inbox.py"
        os.environ["HERMES_HOME"] = str(HERMES_HOME)
        hermes_cmd = os.environ.get("HERMES_CMD", HERMES_HOME.name.lstrip(".") or "hermes")
        os.environ["HERMES_CMD"] = hermes_cmd

        config_file = HERMES_HOME / "config.yaml"
        if config_file.exists():
            content = config_file.read_text(encoding="utf-8")
            hook_cmd = f"python3 '{hook}'"
            if hook_cmd not in content:
                lines = content.splitlines()
                idx = -1
                for i, l in enumerate(lines):
                    if l.strip().startswith("hooks:"):
                        idx = i
                        break
                new_hook = [
                    f"  - event: message_received",
                    f'    command: "{hook_cmd}"',
                    f"  - event: whatsapp:message",
                    f'    command: "{hook_cmd}"'
                ]
                if idx == -1:
                    lines.append("hooks:")
                    lines.extend(new_hook)
                else:
                    # Handle both "hooks: []" and "hooks: {}" empty formats
                    if "[]" in lines[idx] or "{}" in lines[idx]:
                        lines[idx] = "hooks:"
                    for j, h in enumerate(new_hook):
                        lines.insert(idx + 1 + j, h)
                config_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
                ok(t("s5_ok"))
            else:
                ok(t("s5_exists"))
        else:
            warn(t("s5_noconf"))
    except Exception as e:
        fail(t("s5_fail", e=e))

    # ── STEP 6: Qdrant ───────────────────────────────────────
    step(6, t("s6_title"))
    info(t("s6_info"))
    if confirm(t("s6_ask")):
        qdrant_setup = scripts_dir / "setup_portable.py"
        if qdrant_setup.exists():
            subprocess.run([sys.executable, str(qdrant_setup)])
        else:
            warn(t("s6_notfound"))
    else:
        info(t("s6_skip"))

    # ── STEP 7: Autostart ────────────────────────────────────
    step(7, t("s7_title"))
    info(t("s7_info"))
    if confirm(t("s7_ask")):
        try:
            hermes_cmd = os.environ.get("HERMES_CMD", HERMES_HOME.name.lstrip(".") or "hermes")
            subprocess.run([hermes_cmd, "gateway", "install"], capture_output=True)
            subprocess.run([hermes_cmd, "gateway", "start"], capture_output=True)
        except:
            pass
            
        autostart_setup = scripts_dir / "setup_autostart.py"
        if autostart_setup.exists():
            subprocess.run([sys.executable, str(autostart_setup)])
        else:
            warn(t("s7_notfound"))
    else:
        info(t("s7_skip"))

    # ── STEP 8: Bridge Patch ─────────────────────────────────
    step(8, t("s8_title"))
    info(t("s8_info"))
    if not bridge_path.exists():
        warn(t("prereq_missing"))
        info(t("s8_skip"))
    elif confirm(t("s8_ask")):
        patch_script = SOURCE_DIR / "patch_bridge.py"
        if patch_script.exists():
            subprocess.run([sys.executable, str(patch_script)])
        else:
            warn(t("s8_notfound"))
    else:
        info(t("s8_skip"))

    # ── STEP 9: SOUL Optimization ────────────────────────────
    step(9, t("s9_title"))
    try:
        owner_num = env.get("WHATSAPP_ALLOWED_USERS", "your owner")
        anchoring = f"""
# --- ANDORINA IDENTITY BEGIN ---
## 🕊️ WHATSAPP PROTOCOL (MANDATORY)
If the user asks you to send, read, or manage ANYTHING related to WhatsApp:
1. DO NOT use native tools like `send_message` or `cronjob`. They will fail.
2. ALWAYS use your `skill_view` tool to read the `andorina` skill manual FIRST to learn the correct terminal commands.
3. PERSONA: You are the AI assistant of {owner_num}. Speak naturally with them. If messaging third parties, introduce yourself. If told "Literal", send ONLY the exact text.
# --- ANDORINA IDENTITY END ---
"""
        content = soul_file.read_text(encoding="utf-8") if soul_file.exists() else "# HERMES SOUL\n"
        if "# --- ANDORINA IDENTITY BEGIN ---" in content:
            content = re.sub(
                r"# --- ANDORINA IDENTITY BEGIN ---.*?# --- ANDORINA IDENTITY END ---",
                "", content, flags=re.DOTALL
            ).strip()
        
        # Prepend to the very top of the SOUL file for maximum LLM attention
        soul_file.write_text(anchoring.strip() + "\n\n" + content, encoding="utf-8")
        ok(t("s9_ok"))
    except Exception as e:
        warn(t("s9_skip", e=e))

    # ── Final Summary ────────────────────────────────────────
    print()
    hr()
    print(f"\n   {GREEN}{BOLD}🎉 {t('done')}{RESET}\n")
    print(f"   {WHITE}{t('ready')}{RESET}")
    print(f"   {GRAY}{t('profile')}:  {HERMES_HOME}{RESET}")
    print(f"   {GRAY}{t('target')}:   {hermes_base}{RESET}")
    print()
    print(f"   {DIM}{t('quick')}{RESET}")
    print(f"   {CYAN}hermes{RESET}                    → {t('cmd_agent')}")
    print(f"   {CYAN}hermes gateway start{RESET}      → {t('cmd_gw')}")
    print(f"   {CYAN}python3 scripts/auth.py{RESET}   → {t('cmd_auth')}")
    print(f"   {CYAN}python3 scripts/diag.py{RESET}   → {t('cmd_diag')}")
    hr()
    print()

if __name__ == "__main__":
    main()
