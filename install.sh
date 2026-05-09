#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🕊️ ANDORIÑA SKILL — OFFICIAL INSTALLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 🎨 REFINED PALETTE
C_CYAN='\033[38;5;51m'
C_WHITE='\033[1;37m'
C_GRAY='\033[38;5;244m'
C_GREEN='\033[38;5;76m'
C_YELLOW='\033[38;5;226m'
C_MAGENTA='\033[38;5;201m'
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
    M_WELCOME="Iniciando instalación oficial de Andoriña..."
    M_STEPS="EJECUTANDO TAREAS DE SISTEMA"
    M_STEP1="Configurando dependencias de Python"
    M_STEP2="Configurando motor de la skill"
    M_STEP3="Finalizando optimización de SOUL.md"
    M_CONF="CONFIGURACIÓN"
    M_PROMPT_CC="Introduce tu prefijo de país (ej: 34):"
    M_PROMPT_NUM="Introduce tu número de WhatsApp (Admin):"
    M_PROMPT_GOO="¿Deseas configurar Google Contacts ahora? (s/n):"
    M_PROMPT_CID="Introduce CLIENT_ID:"
    M_PROMPT_SEC="Introduce CLIENT_SECRET:"
    M_GOO_WAIT="ENTRANDO EN MODO AUTENTICACIÓN GOOGLE..."
    M_FINISHING="Aplicando cambios finales..."
    M_SUCCESS="INSTALACIÓN COMPLETADA CON ÉXITO"
    M_THANKS="Gracias por confiar en AndoriñaAI. Tu asistente está listo para volar."
else
    M_WELCOME="Starting official Andoriña installation..."
    M_STEPS="EXECUTING SYSTEM TASKS"
    M_STEP1="Configuring Python dependencies"
    M_STEP2="Configuring skill engine"
    M_STEP3="Finalizing SOUL.md optimization"
    M_CONF="CONFIGURATION"
    M_PROMPT_CC="Enter your country prefix (e.g. 34):"
    M_PROMPT_NUM="Enter your WhatsApp number (Admin):"
    M_PROMPT_GOO="Do you want to setup Google Contacts now? (y/n):"
    M_PROMPT_CID="Enter CLIENT_ID:"
    M_PROMPT_SEC="Enter CLIENT_SECRET:"
    M_GOO_WAIT="ENTERING GOOGLE AUTHENTICATION MODE..."
    M_FINISHING="Applying final changes..."
    M_SUCCESS="INSTALLATION COMPLETED SUCCESSFULLY"
    M_THANKS="Thank you for trusting AndoriñaAI. Your assistant is ready to fly."
fi

echo -e "\n   ${C_GRAY}>> ${M_WELCOME}${C_RESET}\n"
sleep 0.5

# 3. INTERACTIVE QUESTIONS
echo -e "   ${BOLD}${M_CONF}${C_RESET}"
echo -e "   ${C_GRAY}----------------------------------------------------------${C_RESET}"
echo -ne "   ${C_WHITE}📱 ${M_PROMPT_CC} ${C_RESET}"
read -r USER_CC
USER_CC=${USER_CC:-34}

echo -ne "   ${C_WHITE}📱 ${M_PROMPT_NUM} ${C_RESET}"
read -r USER_PHONE

echo -ne "   ${C_WHITE}🔑 ${M_PROMPT_GOO} ${C_RESET}"
read -r DO_GOOGLE

if [[ "$DO_GOOGLE" == "y" || "$DO_GOOGLE" == "s" ]]; then
    echo -ne "   ${C_GRAY}   ${M_PROMPT_CID} ${C_RESET}"
    read -r GOOGLE_CID
    echo -ne "   ${C_GRAY}   ${M_PROMPT_SEC} ${C_RESET}"
    read -r GOOGLE_SEC
fi
echo -e "   ${C_GRAY}----------------------------------------------------------${C_RESET}\n"

# 4. EXECUTION
echo -e "   ${BOLD}${M_STEPS}${C_RESET}"
echo -e "   ${C_GRAY}----------------------------------------------------------${C_RESET}"

# Step 1: Python Deps
echo -ne "   ${C_WHITE}● ${M_STEP1}${C_RESET} ... "
python3 -m pip install -r requirements.txt > /dev/null 2>&1 || python3 -m pip install requests > /dev/null 2>&1
echo -e "${C_GREEN}Done${C_RESET}"

# Step 2: Run setup.py engine (Non-interactive mode for Google)
echo -ne "   ${C_WHITE}● ${M_STEP2}${C_RESET} ... "
python3 setup.py << EOF > /dev/null 2>&1
$USER_CC
$USER_PHONE
$GOOGLE_CID
$GOOGLE_SEC
y
EOF
echo -e "${C_GREEN}Done${C_RESET}"

# Step 3: Optional Google OAuth (Interactive)
if [[ "$DO_GOOGLE" == "y" || "$DO_GOOGLE" == "s" ]]; then
    echo -e "\n   ${C_MAGENTA}🌐 ${M_GOO_WAIT}${C_RESET}"
    hr
    python3 scripts/auth.py
    hr
fi

# Step 4: Final Touch
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
