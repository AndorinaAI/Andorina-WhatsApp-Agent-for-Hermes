#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  🕊️ ANDORIÑA SKILL INSTALLER (v1.6)
#  Punto de entrada único. Auto-detecta el entorno:
#    • Desktop → sugiere wizard web (Andorina-Panel.sh)
#    • Headless/VPS → wizard CLI (install_cli.py)
#    • Docker → detecta contenedores con Hermes y permite elegir
# ═══════════════════════════════════════════════════════════════

cd "$(dirname "$0")" || exit 1
# No set -e — queremos manejar errores explícitamente para no cortar el flujo
# ante fallos esperables (Docker no instalado, etc.)

# 🎨 COLORS
C_CYAN='\033[38;5;51m'
C_WHITE='\033[1;37m'
C_GRAY='\033[38;5;244m'
C_GREEN='\033[38;5;76m'
C_RED='\033[38;5;196m'
C_YELLOW='\033[38;5;226m'
C_ORANGE='\033[38;5;214m'
C_RESET='\033[0m'
BOLD='\033[1m'

hr() { echo -e "${C_GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"; }

# ── 1. Show logo ──────────────────────────────────────────────────────────
clear
echo -e "\n   ${C_CYAN}A N D O R I Ñ A${C_RESET}"
hr
echo -e "   ${BOLD}${C_WHITE}Installer v1.6${C_RESET} — ${C_GRAY}Universal Entry Point${C_RESET}"
hr
echo ""

# ── 2. Pre-flight: Python 3 ───────────────────────────────────────────────
echo -ne "   ${C_WHITE}● Python 3 ...${C_RESET} "
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${C_RED}NOT FOUND${C_RESET}"
    echo -e "   ${C_RED}Python 3 es obligatorio. Instálalo e inténtalo de nuevo.${C_RESET}"
    exit 1
fi
echo -e "${C_GREEN}$(python3 --version 2>&1)${C_RESET}"

# ── 3. Detect environment ──────────────────────────────────────────────────
echo -e "\n   ${C_WHITE}● Detectando entorno...${C_RESET}"

ENV_JSON=$(python3 -c "
import json, os, sys
sys.path.insert(0, '.')
from setup_lib import detect_environment, detect_agents
info = detect_environment()
info['agents'] = detect_agents()
print(json.dumps(info, ensure_ascii=False))
" 2>/tmp/andorina_env_error.log || echo '{"mode":"unknown","agents":[],"error":"python_failed"}')
if echo "$ENV_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(1 if d.get('error') else 0)" 2>/dev/null; then
    echo -e "   ${C_RED}❌ Error detectando entorno. Revisa /tmp/andorina_env_error.log${C_RESET}"
    echo -e "   ${C_GRAY}Continuando en modo CLI genérico...${C_RESET}"
fi

MODE=$(echo "$ENV_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('mode','unknown'))")
AGENTS_COUNT=$(echo "$ENV_JSON" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('agents',[])))")

echo -e "   ${C_GREEN}Modo detectado: ${BOLD}${MODE}${C_RESET}"
echo -e "   ${C_GRAY}Agentes Hermes encontrados: ${AGENTS_COUNT}${C_RESET}"

# ── 4. Docker: detect containers with Hermes ──────────────────────────────
DOCKER_CONTAINERS=""
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    # Only check running containers. Use timeout to avoid hangs.
    for name in $(docker ps --format '{{.Names}}' 2>/dev/null); do
        for check_path in /data/.hermes/skills /app/.hermes/skills /root/.hermes/skills; do
            if timeout 3 docker exec "$name" test -d "$check_path" 2>/dev/null; then
                DOCKER_CONTAINERS="${DOCKER_CONTAINERS}${name}
"
                break
            fi
        done
    done
fi

if [ -n "$DOCKER_CONTAINERS" ]; then
    echo ""
    echo -e "   ${C_ORANGE}🐳 Contenedores Docker con Hermes detectados:${C_RESET}"
    I=1
    CONTAINER_ARRAY=()
    while IFS= read -r cname; do
        echo -e "     ${C_CYAN}${I})${C_RESET} ${cname}"
        CONTAINER_ARRAY+=("$cname")
        ((I++))
    done <<< "$DOCKER_CONTAINERS"
    echo -e "     ${C_CYAN}0)${C_RESET} Instalar en el sistema local (no Docker)"
    echo ""
    echo -ne "   ${C_WHITE}👉 ¿En qué contenedor instalar Andoriña? [0]${C_RESET} "
    read -r DOCKER_CHOICE
    if [[ "$DOCKER_CHOICE" =~ ^[0-9]+$ ]] && [ "$DOCKER_CHOICE" -ge 1 ] 2>/dev/null && [ "$DOCKER_CHOICE" -le "${#CONTAINER_ARRAY[@]}" ]; then
        SELECTED_CONTAINER="${CONTAINER_ARRAY[$((DOCKER_CHOICE-1))]}"
        echo -e "   ${C_GREEN}Instalando en contenedor: ${SELECTED_CONTAINER}${C_RESET}"
        echo ""
        hr
        echo -e "   ${C_WHITE}Ejecutando instalador dentro del contenedor...${C_RESET}"
        hr
        
        # Copy installer to container and run it
        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        CONTAINER_TMP="/tmp/andorina_install"
        if ! docker exec "$SELECTED_CONTAINER" mkdir -p "$CONTAINER_TMP" 2>/dev/null; then
            echo -e "   ${C_RED}❌ No se pudo crear directorio en contenedor.${C_RESET}"
            exit 1
        fi
        if ! docker cp "$SCRIPT_DIR/." "$SELECTED_CONTAINER:$CONTAINER_TMP/" 2>/dev/null; then
            echo -e "   ${C_RED}❌ No se pudieron copiar archivos al contenedor.${C_RESET}"
            exit 1
        fi
        
        # Detect container shell
        CONTAINER_SHELL="bash"
        docker exec "$SELECTED_CONTAINER" which bash >/dev/null 2>&1 || CONTAINER_SHELL="sh"
        
        echo -e "   ${C_GRAY}Copiado a ${CONTAINER_TMP}. Ejecutando install_cli.py...${C_RESET}"
        docker exec -it -e HERMES_HOME="${HERMES_HOME:-/data/.hermes}" "$SELECTED_CONTAINER" \
            "$CONTAINER_SHELL" -c "cd $CONTAINER_TMP && python3 install_cli.py --docker"
        EXIT_CODE=$?
        echo ""
        if [ $EXIT_CODE -eq 0 ]; then
            echo -e "   ${C_GREEN}✅ Instalación completada en contenedor ${SELECTED_CONTAINER}.${C_RESET}"
        fi
        exit $EXIT_CODE
    fi
fi

# ── 5. Route to appropriate installer ──────────────────────────────────────
echo ""
hr

if [ "$MODE" = "desktop" ] && [ -f "Andorina-Panel.sh" ]; then
    echo -e "   ${C_GREEN}🖥️  Entorno gráfico detectado.${C_RESET}"
    echo -e "   ${C_GRAY}Se recomienda el wizard web (más visual e intuitivo).${C_RESET}"
    echo ""
    echo -ne "   ${C_WHITE}👉 ¿Usar wizard web (GUI)? [S/n]${C_RESET} "
    read -r REPLY
    if [[ ! "$REPLY" =~ ^[Nn]$ ]]; then
        echo -e "   ${C_CYAN}Abriendo Panel Web...${C_RESET}"
        exec bash Andorina-Panel.sh
    fi
fi

# Default: CLI wizard (funciona en todos los entornos)
echo -e "   ${C_CYAN}Iniciando wizard CLI interactivo...${C_RESET}"
hr
echo ""

python3 install_cli.py
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "\n   ${C_RED}❌ Instalación fallida o cancelada.${C_RESET}"
    exit $EXIT_CODE
fi

echo ""
hr
echo -e "   ${C_GREEN}${BOLD}Thank you for trusting AndoriñaAI ❤️${C_RESET}"
hr
echo ""
