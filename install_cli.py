#!/usr/bin/env python3
"""
🕊️ Andoriña — CLI Install Wizard (v1.6)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Interactive terminal wizard to install Andoriña in headless,
VPS, server, or Docker environments. No GUI dependency.

Uso:
  python3 install_cli.py                  # Wizard interactivo
  python3 install_cli.py --docker          # Modo Docker (saltos inteligentes)
  python3 install_cli.py --non-interactive --config install.json  # CI/CD
"""

import sys
import os
import json
import subprocess
import time
import tempfile
from pathlib import Path

# ── Ensure we can import setup_lib ───────────────────────────────────────
SOURCE_DIR = Path(__file__).parent
sys.path.insert(0, str(SOURCE_DIR))
from setup_lib import (
    detect_environment,
    read_env, write_env, check_write_permission,
    get_andorina_dir,
    deploy_files, register_hooks, init_rbac, optimize_soul,
    check_deps, install_deps,
)

# ── Colors ───────────────────────────────────────────────────────────────
CYAN    = "\033[38;5;51m"
WHITE   = "\033[1;37m"
GRAY    = "\033[38;5;244m"
GREEN   = "\033[38;5;76m"
YELLOW  = "\033[38;5;226m"
RED     = "\033[38;5;196m"
MAGENTA = "\033[38;5;201m"
ORANGE  = "\033[38;5;214m"
DIM     = "\033[2m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

PROGRESS_FILE = Path(tempfile.gettempdir()) / "andorina_install_progress.json"

# ── i18n ──────────────────────────────────────────────────────────────────
LANG = "en"

STRINGS = {
    "es": {
        "title":            "Asistente de Instalación CLI v1.6",
        "detecting":        "Detectando entorno...",
        "mode_docker":      "Docker detectado",
        "mode_headless":    "Headless (sin interfaz gráfica)",
        "mode_desktop":     "Escritorio (entorno gráfico)",
        "resume_found":     "Se encontró una instalación interrumpida. ¿Reanudar desde el paso {step}?",
        "step":             "PASO",
        "of":               "de",
        "done":             "¡INSTALACIÓN COMPLETADA! 🕊️",
        "aborted":          "Instalación cancelada por el usuario.",
        "skip_google":      "Omitido Google Contacts (sin navegador en headless).",
        "skip_autostart":   "Omitido autostart (no disponible en Docker).",
        "press_enter":      "Presiona Enter para continuar...",
        "choose_agent":     "Selecciona agente Hermes:",
        "manual_path":      "Ruta manual",
        "no_agents":        "No se detectaron agentes Hermes. Introduce la ruta manualmente.",
        "ask_cc":           "Prefijo de país (ej. 34 para España)",
        "ask_admin":        "Tu número de WhatsApp (admin, sin prefijo)",
        "ask_ctx":          "Ventana de contexto (tokens)",
        "ask_umem":         "Límite de memoria de usuario (chars)",
        "ask_smem":         "Límite de memoria de sistema (chars)",
        "ok_env":           "Entorno detectado correctamente.",
        "ok_identity":      "Identidad configurada.",
        "ok_perf":          "Configuración de rendimiento guardada.",
        "ok_deploy":        "Archivos desplegados correctamente.",
        "ok_hooks":         "Hooks registrados.",
        "ok_patch":         "Bridge parcheado.",
        "ok_rbac":          "Estructura RBAC inicializada.",
        "ok_soul":          "SOUL.md optimizado.",
        "fail":             "Error",
        "retry":            "¿Reintentar?",
        "skip":             "¿Saltar este paso?",
        "abort":            "¿Abortar instalación?",
        "step_identity":    "Región e Identidad",
        "step_google":      "Google Contacts",
        "step_perf":        "Rendimiento",
        "step_deploy":      "Desplegando Archivos",
        "step_hooks":       "Registrando Hooks",
        "step_patch":       "Parcheo del Bridge",
        "step_rbac":        "Inicializando RBAC",
        "step_soul":        "Optimizando SOUL",
        "step_deps":        "Instalando Dependencias",
        "step_last":        "Finalizando",
    },
    "en": {
        "title":            "CLI Setup Wizard v1.6",
        "detecting":        "Detecting environment...",
        "mode_docker":      "Docker detected",
        "mode_headless":    "Headless (no graphical interface)",
        "mode_desktop":     "Desktop (graphical environment)",
        "resume_found":     "Found interrupted installation. Resume from step {step}?",
        "step":             "STEP",
        "of":               "of",
        "done":             "INSTALLATION COMPLETE! 🕊️",
        "aborted":          "Installation cancelled by user.",
        "skip_google":      "Skipped Google Contacts (no browser in headless mode).",
        "skip_autostart":   "Skipped autostart (not available in Docker).",
        "press_enter":      "Press Enter to continue...",
        "choose_agent":     "Select Hermes agent:",
        "manual_path":      "Manual path",
        "no_agents":        "No Hermes agents detected. Enter path manually.",
        "ask_cc":           "Country prefix (e.g. 34 for Spain)",
        "ask_admin":        "Your WhatsApp number (admin, without prefix)",
        "ask_ctx":          "Context window (tokens)",
        "ask_umem":         "User memory limit (chars)",
        "ask_smem":         "System memory limit (chars)",
        "ok_env":           "Environment detected successfully.",
        "ok_identity":      "Identity configured.",
        "ok_perf":          "Performance settings saved.",
        "ok_deploy":        "Files deployed successfully.",
        "ok_hooks":         "Hooks registered.",
        "ok_patch":         "Bridge patched.",
        "ok_rbac":          "RBAC structure initialized.",
        "ok_soul":          "SOUL.md optimized.",
        "fail":             "Error",
        "retry":            "Retry?",
        "skip":             "Skip this step?",
        "abort":            "Abort installation?",
        "step_identity":    "Region & Identity",
        "step_google":      "Google Contacts",
        "step_perf":        "Performance",
        "step_deploy":      "Deploying Files",
        "step_hooks":       "Registering Hooks",
        "step_patch":       "Bridge Patching",
        "step_rbac":        "Initializing RBAC",
        "step_soul":        "Optimizing SOUL",
        "step_deps":        "Installing Dependencies",
        "step_last":        "Finalizing",
    }
}

def t(key, **kwargs):
    s = STRINGS.get(LANG, STRINGS["en"]).get(key, key)
    if kwargs:
        return s.format(**kwargs)
    return s

# ── Progress persistence ──────────────────────────────────────────────────

def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"completed": [], "agent_path": "", "cc": "34", "admin": "",
            "ctx": "75000", "umem": "5000", "smem": "5000", "lang": "en",
            "is_docker": False}

def save_progress(state: dict):
    try:
        PROGRESS_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    except (PermissionError, OSError):
        pass  # non-fatal — no se puede persistir progreso en este entorno

def clear_progress():
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()

# ── UI Helpers ─────────────────────────────────────────────────────────────

def hr():
    print(f"   {GRAY}{'━' * 58}{RESET}")

def step_header(num, total, title):
    print(f"\n   {MAGENTA}{'━' * 58}{RESET}")
    print(f"   {BOLD}{WHITE}{t('step')} {num}/{total}{RESET}  {CYAN}{title}{RESET}")
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
    try:
        return input(f"   {WHITE}👉 {prompt}{DIM}{label}{RESET}: ").strip() or default
    except (EOFError, KeyboardInterrupt):
        return default

def confirm(prompt, default="y"):
    label = "S/n" if LANG == "es" and default == "y" else "s/N" if LANG == "es" else "Y/n" if default == "y" else "y/N"
    try:
        ans = input(f"   {WHITE}👉 {prompt} ({label}){RESET}: ").strip().lower() or default
    except (EOFError, KeyboardInterrupt):
        ans = "n"
    return ans in ("y", "s", "yes", "si", "sí")

def handle_failure(msg):
    fail(f"{t('fail')}: {msg}")
    print()
    if confirm(t("retry"), "y"):
        return "retry"
    if confirm(t("skip"), "n"):
        return "skip"
    return "abort"

# ── Step implementations ──────────────────────────────────────────────────

def run_step_identity(state, env_file):
    """Paso 1: Región e Identidad."""
    cc = ask(t("ask_cc"), state.get("cc", "34"))
    admin = ask(t("ask_admin"), state.get("admin", ""))
    if not admin:
        return False, "Número de admin es obligatorio."
    updates = {
        "DEFAULT_COUNTRY_CODE": cc.replace("+", "").lstrip("0"),
        "WHATSAPP_ALLOWED_USERS": admin.replace("+", "").replace(" ", ""),
    }
    hermes_base = get_andorina_dir(Path(state["agent_path"]))
    try:
        hermes_base.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return False, (f"No se pudo crear el directorio de la skill:\n"
                       f"  {hermes_base}\n"
                       f"  Ejecuta: sudo chown -R $USER:$USER {Path(state['agent_path'])}")
    if not write_env(env_file, updates):
        return False, (f"No se pudo escribir en el .env de la skill:\n"
                       f"  {env_file}\n"
                       f"  Verifica los permisos con: ls -la {Path(env_file).parent}")
    state["cc"] = cc
    state["admin"] = admin
    save_progress(state)
    return True, t("ok_identity")

def _start_tunnel_for_google(state):
    """Inicia un túnel Cloudflare temporal y muestra QR + URL para acceder al Panel Web.
    Retorna (ok, url) o (False, error_msg)."""
    import urllib.parse

    # Intentar importar el módulo tunnel
    tunnel_script = SOURCE_DIR / "scripts" / "utils" / "tunnel.py"
    if not tunnel_script.exists():
        return False, "Módulo tunnel no encontrado."

    # Iniciar el túnel como subprocess para no bloquear
    info("Iniciando túnel Cloudflare temporal (gratuito)...")
    info("Descargando cloudflared si es necesario...")

    # Ejecutar el túnel en background y capturar la URL
    try:
        sys.path.insert(0, str(SOURCE_DIR / "scripts" / "utils"))
        from tunnel import start_tunnel, active_url as _tunnel_active_url, stop_tunnel as _tunnel_stop
    except ImportError:
        return False, "No se pudo importar el módulo tunnel.py."

    # Verificar que el panel esté corriendo o iniciarlo
    panel_running = False
    try:
        import socket
        s = socket.socket()
        s.connect(('localhost', 8888))
        s.close()
        panel_running = True
    except Exception:
        pass

    if not panel_running:
        info("Iniciando Panel Web en puerto 8888...")
        panel_script = SOURCE_DIR / "GUI" / "server.py"
        if panel_script.exists():
            subprocess.Popen([sys.executable, str(panel_script), "--port", "8888"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           start_new_session=True)
            time.sleep(2)
        else:
            return False, "GUI/server.py no encontrado."

    ok_tunnel, result = start_tunnel(port=8888)
    if not ok_tunnel:
        return False, f"Error al iniciar túnel: {result}"

    url = result
    if not url:
        # Esperar un poco a que aparezca la URL
        for _ in range(10):
            time.sleep(1)
            from tunnel import active_url
            if active_url:
                url = active_url
                break

    if not url:
        _tunnel_stop()
        return False, "No se pudo obtener URL del túnel."

    # Mostrar QR + URL
    print()
    print(f"   {CYAN}{'─' * 56}{RESET}")
    print(f"   {BOLD}{WHITE}🌐 Panel Web accesible desde internet:{RESET}")
    print(f"   {GREEN}{url}{RESET}")
    print(f"   {CYAN}{'─' * 56}{RESET}")
    print()

    # Intentar mostrar QR ASCII
    try:
        import qrcode
    except ImportError:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--user", "--quiet", "qrcode"],
                          capture_output=True, timeout=30)
            import qrcode
        except Exception:
            pass

    try:
        qr = qrcode.QRCode(border=2)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        print()
    except Exception:
        info("💡 Instala 'qrcode' para ver QR en terminal: pip install --user qrcode")

    print(f"   {GRAY}📱 Abre el enlace de arriba (o escanea el QR) desde otro dispositivo.{RESET}")
    print(f"   {GRAY}   En el Panel Web, ve a Contacts → 'Vincular cuenta'.{RESET}")
    print(f"   {GRAY}   Cuando termines, vuelve aquí y presiona Enter.{RESET}")
    print()

    return True, url


def run_step_google(state, env_file):
    """Paso 2: Google Contacts.
    Desktop: abre navegador → callback localhost.
    Headless: inicia túnel Cloudflare → QR + URL → vincular desde Panel Web."""
    env = read_env(env_file)
    has_refresh = bool(env.get("GOOGLE_CONTACTS_REFRESH_TOKEN"))
    if has_refresh:
        ok("Google Contacts ya vinculado.")
        return True, ""

    is_headless = state.get("is_docker") or not os.environ.get("DISPLAY")

    if is_headless:
        info("Modo headless detectado: no se puede abrir navegador en este equipo.")
        info("Se puede iniciar un túnel Cloudflare temporal para vincular Google Contacts")
        info("desde otro dispositivo (móvil, tablet, otro PC) accediendo al Panel Web.")
        print()
        if confirm("¿Iniciar túnel Cloudflare para vincular Google Contacts ahora?"):
            ok_tunnel, result = _start_tunnel_for_google(state)
            if not ok_tunnel:
                warn(result)
                info("Puedes intentarlo más tarde desde el Panel Web → Contacts.")
            else:
                info("Una vez vinculado, cierra el panel en tu otro dispositivo.")
                input(f"   {WHITE}👉 Presiona Enter cuando hayas terminado de vincular Google Contacts...{RESET}")

                # Detener el túnel
                try:
                    sys.path.insert(0, str(SOURCE_DIR / "scripts" / "utils"))
                    from tunnel import stop_tunnel
                    stop_tunnel()
                    info("Túnel detenido.")
                except Exception:
                    pass

                # Verificar si se guardaron los tokens
                env = read_env(env_file)
                if env.get("GOOGLE_CONTACTS_REFRESH_TOKEN"):
                    ok("Google Contacts vinculado correctamente.")
                else:
                    warn("No se detectó el token. ¿Autorizaste en Google?")
                    info("Puedes reintentar más tarde desde el Panel Web → Contacts.")
        else:
            info("Omitido. Puedes vincular más tarde desde el Panel Web → Contacts.")
        return True, ""
    else:
        info("Se abrirá el navegador para iniciar sesión en Google.")

    if confirm("¿Vincular Google Contacts ahora?"):
        r = subprocess.run([sys.executable, str(SOURCE_DIR / "scripts" / "utils" / "auth.py")])
        env = read_env(env_file)
        if env.get("GOOGLE_CONTACTS_REFRESH_TOKEN"):
            ok("Google Contacts vinculado.")
        else:
            warn("No se pudo verificar. Reintenta más tarde con: python3 scripts/utils/auth.py")
            info("También puedes vincular desde el Panel Web → Contacts → Vincular cuenta.")
    else:
        info("Omitido. Puedes vincular más tarde con: python3 scripts/utils/auth.py")
    return True, ""

def run_step_performance(state, env_file):
    """Paso 3: Rendimiento."""
    env = read_env(env_file)
    ctx  = ask(t("ask_ctx"), state.get("ctx", env.get("ANDORINA_TARGET_CONTEXT", "75000")))
    umem = ask(t("ask_umem"), state.get("umem", env.get("ANDORINA_TARGET_USER_MEM", "5000")))
    smem = ask(t("ask_smem"), state.get("smem", env.get("ANDORINA_TARGET_SYS_MEM", "5000")))
    updates = {
        "ANDORINA_TARGET_CONTEXT": ctx,
        "ANDORINA_TARGET_USER_MEM": umem,
        "ANDORINA_TARGET_SYS_MEM": smem,
    }
    if not env.get("WHATSAPP_BRIDGE_URL"):
        updates["WHATSAPP_BRIDGE_URL"] = "http://localhost:3000"
    write_env(env_file, updates)
    state["ctx"] = ctx
    state["umem"] = umem
    state["smem"] = smem
    save_progress(state)
    return True, t("ok_perf")

def run_step_deps(state, env_file=None):
    """Paso 3.5: Instalar dependencias Python."""
    missing = check_deps()
    if not missing:
        return True, "Todas las dependencias instaladas."
    info(f"Instalando {len(missing)} dependencias: {', '.join(missing)}")
    ok_deps = install_deps()
    if ok_deps:
        return True, "Dependencias instaladas."
    return False, "Error instalando dependencias."

def run_step_deploy(state, env_file=None):
    """Paso 4: Desplegar archivos."""
    ok_deploy = deploy_files(state["agent_path"], str(SOURCE_DIR))
    if ok_deploy:
        return True, t("ok_deploy")
    return False, "Error al desplegar archivos."

def run_step_hooks(state, env_file=None):
    """Paso 5: Registrar hooks."""
    ok_hooks = register_hooks(state["agent_path"])
    if ok_hooks:
        return True, t("ok_hooks")
    return False, "Error al registrar hooks."

def run_step_patch(state, env_file=None):
    """Paso 6: Parchear bridge."""
    # Buscar bridge.js — múltiples ubicaciones para cubrir Docker/VPS
    agent_path = Path(state["agent_path"])
    main_hermes = agent_path
    if main_hermes.parent.name == "profiles":
        main_hermes = main_hermes.parent.parent
    candidates = [
        main_hermes / "hermes-agent" / "scripts" / "whatsapp-bridge" / "bridge.js",
        main_hermes / "gateway" / "bridge.js",
        main_hermes / "gateway" / "src" / "bridge.js",
        main_hermes / "scripts" / "whatsapp-bridge" / "bridge.js",
    ]
    bridge_path = None
    for c in candidates:
        if c.is_file():
            bridge_path = c
            break
    # Fallback: recursive search
    if not bridge_path:
        for search_root in [main_hermes / "hermes-agent", main_hermes / "gateway"]:
            if search_root.is_dir():
                for p in search_root.rglob("bridge.js"):
                    if p.is_file():
                        bridge_path = p
                        break
            if bridge_path:
                break

    if not bridge_path:
        return True, "Bridge no encontrado — omitiendo parcheo (se hará al iniciar)."

    # V2.0-F5: Plugin platform — no patches to apply.
    # The legacy patch scripts are deprecated and do nothing.
    _log("   ℹ️  V2.0 Plugin Platform — patches not required.")
    return True, t("ok_patch")

def run_step_rbac(state, env_file=None):
    """Paso 7: Inicializar RBAC."""
    ok_rbac = init_rbac(state["agent_path"], state.get("admin", ""))
    if ok_rbac:
        # Also run soul_sync
        sync_script = get_andorina_dir(Path(state["agent_path"])) / "scripts" / "security" / "soul_sync.py"
        if sync_script.exists():
            env = dict(os.environ)
            env["HERMES_HOME"] = state["agent_path"]
            subprocess.run([sys.executable, str(sync_script)], capture_output=True, timeout=15, env=env)
        return True, t("ok_rbac")
    return False, "Error al inicializar RBAC."

def run_step_soul(state, env_file=None):
    """Paso 8: Optimizar SOUL.md."""
    owner_num = state.get("admin", "your owner")
    ok_soul = optimize_soul(state["agent_path"], owner_num)
    if ok_soul:
        return True, t("ok_soul")
    return False, "Error al optimizar SOUL.md."

# ── Orden de pasos ────────────────────────────────────────────────────────
STEPS = [
    ("identity", run_step_identity, "step_identity"),
    ("google",   run_step_google,   "step_google"),
    ("deps",     run_step_deps,     "step_deps"),
    ("perf",     run_step_performance, "step_perf"),
    ("deploy",   run_step_deploy,   "step_deploy"),
    ("hooks",    run_step_hooks,    "step_hooks"),
    ("patch",    run_step_patch,    "step_patch"),
    ("rbac",     run_step_rbac,     "step_rbac"),
    ("soul",     run_step_soul,     "step_soul"),
]

# ── Main ──────────────────────────────────────────────────────────────────

def main():
    global LANG

    os.system("clear" if os.name != "nt" else "cls")
    print(f"   {CYAN}A N D O R I Ñ A{RESET}")
    hr()
    print(f"   {BOLD}{WHITE}{t('title')}{RESET}")
    hr()
    print()

    # ── Detectar entorno ───────────────────────────────────────────────
    info(t("detecting"))
    env_info = detect_environment()
    time.sleep(0.5)

    mode_icons = {"docker": "🐳", "headless": "🖥️ ", "desktop": "🖥️ "}
    print(f"   {GREEN}{mode_icons.get(env_info['mode'], '•')}  "
          f"Modo: {BOLD}{env_info['mode'].upper()}{RESET}")
    print(f"   {GRAY}   SO: {env_info['platform']}  |  "
          f"Python: {env_info['python_version']}  |  "
          f"Home: {env_info['home']}{RESET}")
    ok(t("ok_env"))
    print()

    # ── Selección de agente ──────────────────────────────────────────────
    state = load_progress()
    LANG = state.get("lang", "en")
    state["is_docker"] = env_info["is_docker"]

    # Elegir idioma
    lang_input = input(f"   {WHITE}👉 Idioma / Language (es/en) [en]{RESET}: ").strip().lower() or "en"
    LANG = "es" if lang_input in ("es", "español", "spanish") else "en"
    state["lang"] = LANG

    # Resume
    if state.get("completed"):
        last_step = state["completed"][-1] if state["completed"] else "identity"
        if confirm(t("resume_found", step=last_step), "y"):
            info(f"Reanudando desde {last_step}...")
        else:
            state["completed"] = []
            save_progress(state)

    # Agent path
    if not state.get("agent_path"):
        candidates = env_info["hermes_candidates"]
        if candidates:
            print(f"\n   {BOLD}{WHITE}🤖 {t('choose_agent')}{RESET}")
            for i, c in enumerate(candidates):
                name = Path(c).name.lstrip(".")
                print(f"      {CYAN}{i+1}){RESET} {name} {GRAY}({c}){RESET}")
            print(f"      {CYAN}0){RESET} {t('manual_path')}")
            choice = ask("Selecciona", "1")
            try:
                idx = int(choice)
                if 1 <= idx <= len(candidates):
                    state["agent_path"] = candidates[idx - 1]
            except ValueError:
                pass
        if not state.get("agent_path"):
            state["agent_path"] = ask("Ruta completa del agente Hermes",
                                       env_info["hermes_candidates"][0] if env_info["hermes_candidates"] else str(Path.home() / ".hermes"))
    save_progress(state)

    agent_path = Path(state["agent_path"])
    hermes_base = get_andorina_dir(agent_path)
    env_file = hermes_base / ".env"

    # ── Verificar permisos de escritura ANTES de empezar ─────────────────
    ok_perm, msg_perm = check_write_permission(agent_path)
    if not ok_perm:
        fail(msg_perm)
        print(f"   {GRAY}Agente: {state['agent_path']}{RESET}")
        print(f"   {GRAY}Destino: {hermes_base}{RESET}")
        print()
        if confirm("¿Reintentar tras arreglar permisos?" if LANG == "es" else "Retry after fixing permissions?", "y"):
            ok_perm, msg_perm = check_write_permission(agent_path)
        if not ok_perm:
            fail("No se puede continuar sin permisos de escritura." if LANG == "es" else "Cannot continue without write permissions.")
            return 1

    try:
        hermes_base.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        fail(msg_perm or f"Sin permisos para crear {hermes_base}")
        return 1

    print(f"   {GRAY}Agente: {state['agent_path']}{RESET}")
    print(f"   {GRAY}Destino: {hermes_base}{RESET}")
    print()

    # ── Ejecutar pasos ─────────────────────────────────────────────────
    total = len(STEPS)
    start_idx = 0

    # Skip already-completed steps
    completed = set(state.get("completed", []))
    for i, (key, fn, label_key) in enumerate(STEPS):
        if key in completed:
            continue
        start_idx = i
        break
    else:
        start_idx = total  # all done

    for i in range(start_idx, total):
        key, fn, label_key = STEPS[i]
        step_header(i + 1, total, t(label_key))

        while True:
            success, msg = fn(state, str(env_file))
            if success:
                if msg:
                    ok(msg)
                state.setdefault("completed", []).append(key)
                save_progress(state)
                break
            else:
                action = handle_failure(msg)
                if action == "retry":
                    continue
                elif action == "skip":
                    state.setdefault("completed", []).append(key)
                    save_progress(state)
                    break
                else:
                    fail(t("aborted"))
                    return 1

    # ── Finalizar ──────────────────────────────────────────────────────
    clear_progress()
    print()
    hr()
    print(f"\n   {GREEN}{BOLD}🎉 {t('done')}{RESET}\n")
    print(f"   {WHITE}Tu asistente está listo.{RESET}")
    print(f"   {GRAY}Perfil:  {state['agent_path']}{RESET}")
    print(f"   {GRAY}Skill:   {hermes_base}{RESET}")
    print()
    print(f"   {DIM}Comandos rápidos:{RESET}")
    print(f"   {CYAN}hermes gateway start{RESET}      → Iniciar puente WhatsApp")
    print(f"   {CYAN}python3 {hermes_base}/Andorina-Panel.sh{RESET}  → Panel Web")
    print(f"   {CYAN}python3 {hermes_base}/scripts/utils/diag.py{RESET} → Diagnóstico")
    hr()
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())