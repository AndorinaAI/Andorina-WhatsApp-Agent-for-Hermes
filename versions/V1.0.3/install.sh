#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🕊️ ANDORIÑA SKILL (v1.0.3)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Ensure we are operating in the script's directory
cd "$(dirname "$0")" || exit 1
# 🎨 REFINED PALETTE
C_CYAN='\033[38;5;51m'
C_WHITE='\033[1;37m'
C_GRAY='\033[38;5;244m'
C_GREEN='\033[38;5;76m'
C_YELLOW='\033[38;5;226m'
C_MAGENTA='\033[38;5;201m'
C_RED='\033[38;5;196m'
C_RESET='\033[0m'
BOLD='\033[1m'

# 🕊️ THE LOGO
read -r -d '' LOGO << 'EOF'
@@@@@@@@@@@@@@@@@@@@@@@ @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@ +@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@ @%@@@@@@@@@@@@@@@@@@@@@@@@@@@@%+#@@@@@
@@@@@@@@@@@@@@@@@@@@ #@=%@@@@@@@@@@@@@@@@@@@@@@@%+ +-@@@@@@@
@@@@@@@@@@@@@@@@@@@  @ @#@@@@@@@@@@@@@@@@@@@%+  +@@-@@@@@@@@
@@@@@@@@@@@@@@@@@@  @ +@*@@@@@@@@@@@@@@@%-   +@@@+:@@@@@@@@@
@@@@@@@@@@@@@@@@@  #  @ @@@@@@@@@@@@#-   :#@@%-- @@@@@@@@@@@
@@@@@@@@@@@@@@@%     =-=@@@@@@@@#-    :#@%- :@%+@@@@@@@@@@@@
@@@@@@@@@@@@@@@-     = @@@@@%      :#%+  :#@@-@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@+       @@@@:    :*+    +@%+:@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@#       :@+          +@+  *@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@      +@         :%-  +@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@%+=   :=*@%*@-             %@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@:                         -@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@%:     =-::                 #@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@+  +@@@+-@+          :@@@@@@@@@@@@@@@@@@@@@@@@@@@@
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
EOF

# UTILS
function hr() {
    echo -e "${C_GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
}

# 1. INITIAL DISPLAY & LANGUAGE
clear
echo -e "\n   ${C_CYAN}${LOGO}${C_RESET}\n"
hr
echo -e "   ${BOLD}SELECT INSTALLATION LANGUAGE / IDIOMA DE INSTALACIÓN${C_RESET}"
echo -e "   ${C_GRAY}1)${C_RESET} English"
echo -e "   ${C_GRAY}2)${C_RESET} Español"
echo -ne "\n   ${BOLD}Choice / Opción [1]: ${C_RESET}"
read -r L_CHOICE

# 2. STRINGS
if [[ "$L_CHOICE" == "2" ]]; then
    M_WELCOME="Iniciando instalación de Andoriña..."
    M_STEPS="EJECUTANDO TAREAS DE SISTEMA"
    M_STEP1="Verificando entorno de Python"
    M_STEP2="Configurando motor de la skill"
    M_STEP3="Finalizando optimización de SOUL.md"
    M_CONF="CONFIGURACIÓN"
    M_PROMPT_CC="Introduce tu prefijo de país (ej: 34):"
    M_PROMPT_NUM="Introduce tu número de WhatsApp (Admin):"
    M_PROMPT_GOO="¿Deseas configurar Google Contacts ahora? (s/n):"
    M_WARN_GOO="ℹ️  Si dices NO, el agente no podrá buscar contactos por nombre."
    M_PROMPT_CID="Introduce CLIENT_ID:"
    M_PROMPT_SEC="Introduce CLIENT_SECRET:"
    M_GOO_WAIT="ENTRANDO EN MODO AUTENTICACIÓN GOOGLE..."
    M_PROMPT_QDR="¿Deseas instalar/iniciar Qdrant Memory? (s/n) [s]:"
    M_WARN_QDR="ℹ️  Si dices NO, deberás arrancarlo a mano o el agente sufrirá amnesia."
    M_PROMPT_AUT="¿Deseas activar el Auto-Arranque? (s/n) [s]:"
    M_WARN_AUT="ℹ️  Si dices NO, deberás abrir la terminal en cada reinicio."
    M_PROMPT_PAT="¿Deseas parchear y reiniciar el puente de WhatsApp? (s/n) [s]:"
    M_WARN_PAT="ℹ️  Si dices NO, el envío de audios y archivos multimedia fallará."
    M_STEP4="Parcheando y reiniciando puente de WhatsApp"
    M_FINISHING="Aplicando cambios finales..."
    M_SUCCESS="INSTALACIÓN COMPLETADA CON ÉXITO"
    M_THANKS="Gracias por confiar en AndoriñaAI. Tu asistente está listo para volar."
else
    M_WELCOME="Starting Andoriña installation..."
    M_STEPS="EXECUTING SYSTEM TASKS"
    M_STEP1="Verifying Python environment"
    M_STEP2="Configuring skill engine"
    M_STEP3="Finalizing SOUL.md optimization"
    M_CONF="CONFIGURATION"
    M_PROMPT_CC="Enter your country prefix (e.g. 34):"
    M_PROMPT_NUM="Enter your WhatsApp number (Admin):"
    M_PROMPT_GOO="Do you want to setup Google Contacts now? (y/n):"
    M_WARN_GOO="ℹ️  If NO, the agent won't be able to search contacts by name."
    M_PROMPT_CID="Enter CLIENT_ID:"
    M_PROMPT_SEC="Enter CLIENT_SECRET:"
    M_GOO_WAIT="ENTERING GOOGLE AUTHENTICATION MODE..."
    M_PROMPT_QDR="Do you want to setup Qdrant Memory? (y/n) [y]:"
    M_WARN_QDR="ℹ️  If NO, you must start it manually or the agent will have amnesia."
    M_PROMPT_AUT="Do you want to enable Autostart? (y/n) [y]:"
    M_WARN_AUT="ℹ️  If NO, you'll need to start the agent manually on every reboot."
    M_PROMPT_PAT="Do you want to patch/restart the Bridge? (y/n) [y]:"
    M_WARN_PAT="ℹ️  If NO, sending audio and multimedia files will fail."
    M_STEP4="Patching and restarting WhatsApp Bridge"
    M_FINISHING="Applying final changes..."
    M_SUCCESS="INSTALLATION COMPLETED SUCCESSFULLY"
    M_THANKS="Thank you for trusting AndoriñaAI. Your assistant is ready to fly."
fi

echo -e "\n   ${C_GRAY}>> ${M_WELCOME}${C_RESET}\n"
sleep 0.5

# 3. INTERACTIVE QUESTIONS
echo -e "   ${BOLD}${M_CONF}${C_RESET}"
echo -e "   ${C_GRAY}----------------------------------------------------------${C_RESET}"

# Agent Auto-Detection
AGENT_DIRS=($(
    find "$HOME" -maxdepth 1 -type d -name ".*" -exec test -d "{}/skills" \; -print 2>/dev/null
    find "$HOME/.hermes/profiles" -maxdepth 1 -mindepth 1 -type d -exec test -d "{}/skills" \; -print 2>/dev/null
))
PROFILE_NAME="hermes"

if [ ${#AGENT_DIRS[@]} -gt 0 ]; then
    echo -e "   ${C_WHITE}🤖 Detected Agents / Agentes Detectados:${C_RESET}"
    for i in "${!AGENT_DIRS[@]}"; do
        path="${AGENT_DIRS[$i]}"
        name=$(basename "$path")
        name=${name#.} # remove leading dot
        echo -e "      ${C_CYAN}$((i+1)))${C_RESET} $name (${C_GRAY}$path${C_RESET})"
    done
    echo -e "      ${C_CYAN}0)${C_RESET} Manual Entry / Ingreso Manual"
    echo -ne "\n   ${C_WHITE}👉 Select Agent / Selecciona un Agente [1]: ${C_RESET}"
    read -r AGENT_CHOICE
    AGENT_CHOICE=${AGENT_CHOICE:-1}

    if [[ "$AGENT_CHOICE" != "0" ]] && [[ "$AGENT_CHOICE" =~ ^[0-9]+$ ]] && [ "$AGENT_CHOICE" -le ${#AGENT_DIRS[@]} ]; then
        idx=$((AGENT_CHOICE-1))
        export HERMES_HOME="${AGENT_DIRS[$idx]}"
        name=$(basename "$HERMES_HOME")
        export HERMES_CMD="${name#.}"
    else
        echo -ne "   ${C_WHITE}✏️  Type full path to agent / Escribe la ruta completa del agente (e.g., /opt/hermes): ${C_RESET}"
        read -r MANUAL_PATH
        export HERMES_HOME=${MANUAL_PATH:-"$HOME/.hermes"}
        name=$(basename "$HERMES_HOME")
        export HERMES_CMD="${name#.}"
    fi
else
    echo -ne "   ${C_WHITE}✏️  Type full path to agent / Escribe la ruta completa del agente (e.g., /opt/hermes) [$HOME/.hermes]: ${C_RESET}"
    read -r MANUAL_PATH
    export HERMES_HOME=${MANUAL_PATH:-"$HOME/.hermes"}
    name=$(basename "$HERMES_HOME")
    export HERMES_CMD="${name#.}"
fi
echo -e "   ${C_GRAY}   >> Path: $HERMES_HOME | Cmd: $HERMES_CMD${C_RESET}\n"

echo -ne "   ${C_WHITE}📱 ${M_PROMPT_CC} ${C_RESET}"
read -r USER_CC
USER_CC=${USER_CC:-34}

echo -ne "   ${C_WHITE}📱 ${M_PROMPT_NUM} ${C_RESET}"
read -r USER_PHONE

echo -e "\n   ${C_CYAN}🌐 Google Contacts API (https://console.cloud.google.com/)${C_RESET}"
echo -e "   ${C_YELLOW}${M_WARN_GOO}${C_RESET}"
echo -ne "   ${C_WHITE}🔑 ${M_PROMPT_GOO} ${C_RESET}"
read -r DO_GOOGLE

if [[ "$DO_GOOGLE" == "y" || "$DO_GOOGLE" == "s" ]]; then
    echo -ne "   ${C_GRAY}   ${M_PROMPT_CID} ${C_RESET}"
    read -r GOOGLE_CID
    echo -ne "   ${C_GRAY}   ${M_PROMPT_SEC} ${C_RESET}"
    read -r GOOGLE_SEC
fi

echo -e "\n   ${C_YELLOW}${M_WARN_QDR}${C_RESET}"
echo -ne "   ${C_WHITE}🧠 ${M_PROMPT_QDR} ${C_RESET}"
read -r DO_QDRANT
DO_QDRANT=${DO_QDRANT:-y}

echo -e "\n   ${C_YELLOW}${M_WARN_AUT}${C_RESET}"
echo -ne "   ${C_WHITE}🖥️  ${M_PROMPT_AUT} ${C_RESET}"
read -r DO_AUTO
DO_AUTO=${DO_AUTO:-y}

echo -e "\n   ${C_YELLOW}${M_WARN_PAT}${C_RESET}"
echo -ne "   ${C_WHITE}🔧 ${M_PROMPT_PAT} ${C_RESET}"
read -r DO_PATCH
DO_PATCH=${DO_PATCH:-y}

echo -e "   ${C_GRAY}----------------------------------------------------------${C_RESET}\n"

# 4. EXECUTION
echo -e "   ${BOLD}${M_STEPS}${C_RESET}"
echo -e "   ${C_GRAY}----------------------------------------------------------${C_RESET}"

# Step 1: Verify Python (Zero-dependency check)
echo -ne "   ${C_WHITE}● ${M_STEP1}${C_RESET} ... "
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${C_RED}Failed. Python 3 is not installed or not in PATH.${C_RESET}"
    echo -e "   Please install python3 to continue."
    exit 1
fi
echo -e "${C_GREEN}Done${C_RESET}"

# Step 2: Run setup.py engine (Non-interactive mode for Google)
echo -ne "   ${C_WHITE}● ${M_STEP2}${C_RESET} ... "
python3 setup.py << EOF > .install_log 2>&1
$USER_CC
$USER_PHONE
$GOOGLE_CID
$GOOGLE_SEC



$DO_QDRANT
$DO_AUTO
EOF

if [ $? -ne 0 ]; then
    echo -e "${C_RED}Failed. Check .install_log${C_RESET}"
else
    echo -e "${C_GREEN}Done${C_RESET}"
fi

# Step 3: Optional Google OAuth (Interactive)
if [[ "$DO_GOOGLE" == "y" || "$DO_GOOGLE" == "s" ]]; then
    echo -e "\n   ${C_MAGENTA}🌐 ${M_GOO_WAIT}${C_RESET}"
    hr
    python3 scripts/auth.py
    hr
fi

# Step 4: Bridge Patch (Visible for QR)
if [[ "$DO_PATCH" == "y" || "$DO_PATCH" == "s" ]]; then
    echo -e "\n   ${C_CYAN}🔧 ${M_STEP4}${C_RESET}"
    hr
    # Dynamically find the deployed bridge_health.py
    # setup.py deployed it to $HERMES_HOME/skills/(messaging|message)/andorina/scripts/
    CATEGORY="messaging"
    if [ -d "$HERMES_HOME/skills/message" ] && [ ! -d "$HERMES_HOME/skills/messaging" ]; then
        CATEGORY="message"
    fi
    HEALTH_SCRIPT="$HERMES_HOME/skills/$CATEGORY/andorina/scripts/bridge_health.py"
    
    if [ -f "$HEALTH_SCRIPT" ]; then
        python3 "$HEALTH_SCRIPT"
    else
        # Fallback to local script if not yet deployed (unlikely)
        python3 scripts/bridge_health.py
    fi
    hr
fi

# Step 5: Final Touch
echo -ne "   ${C_WHITE}● ${M_STEP3}${C_RESET} ... "
echo -e "${C_GREEN}Done${C_RESET}"
echo -e "   ${C_GRAY}----------------------------------------------------------${C_RESET}"

echo -e "\n   ${C_GRAY}${M_FINISHING}${C_RESET}"
sleep 1

# 5. SUCCESS SCREEN
clear
echo -e "\n   ${C_CYAN}${LOGO}${C_RESET}\n"
hr
echo -e "   ${C_GREEN}${BOLD}${M_SUCCESS}${C_RESET}"
hr
echo -e "\n   ${C_WHITE}${M_THANKS}${C_RESET}\n"
hr
echo ""
