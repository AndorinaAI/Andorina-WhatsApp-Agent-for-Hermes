#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🕊️ ANDORIÑA SKILL INSTALLER (v1.5.2-Beta4)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# This script is the main entry point for installation.
# It performs pre-flight checks and then delegates the full interactive
# setup to setup.py, which handles all user prompts internally.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Ensure we are operating in the script's directory
cd "$(dirname "$0")" || exit 1

# 🎨 COLORS
C_CYAN='\033[38;5;51m'
C_WHITE='\033[1;37m'
C_GRAY='\033[38;5;244m'
C_GREEN='\033[38;5;76m'
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

function hr() {
    echo -e "${C_GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
}

# ─────────────────────────────────────────────────────────────
# 1. PRE-FLIGHT: Show logo & verify Python
# ─────────────────────────────────────────────────────────────
clear
echo -e "\n   ${C_CYAN}${LOGO}${C_RESET}\n"
hr
echo -e "   ${BOLD}${C_WHITE}A N D O R I Ñ A${C_RESET}   v1.5.2-Beta4"
hr

echo -ne "\n   ${C_WHITE}● Checking Python 3 ...${C_RESET} "
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${C_RED}NOT FOUND${C_RESET}"
    echo -e "   ${C_RED}Python 3 is required. Please install it and try again.${C_RESET}"
    exit 1
fi
PYVER=$(python3 --version 2>&1)
echo -e "${C_GREEN}${PYVER}${C_RESET}\n"

# ─────────────────────────────────────────────────────────────
# 2. PRE-FLIGHT: Hermes Agent version check
# ─────────────────────────────────────────────────────────────
MIN_HERMES="0.16.0"
echo -ne "   ${C_WHITE}● Checking Hermes Agent version ...${C_RESET} "
HERMES_VER=$(python3 -c "
import importlib.metadata, sys
try:
    print(importlib.metadata.version('hermes-agent'))
except Exception:
    sys.exit(1)
" 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$HERMES_VER" ]; then
    echo -e "${C_RED}NOT FOUND${C_RESET}"
    echo -e "   ${C_RED}Hermes Agent is not installed. Install it first:${C_RESET}"
    echo -e "   ${C_GRAY}https://hermes-agent.nousresearch.com${C_RESET}"
    exit 1
fi

python3 -c "
from packaging.version import Version
import sys
sys.exit(0 if Version('$HERMES_VER') >= Version('$MIN_HERMES') else 1)
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${C_RED}v${HERMES_VER} (required >= ${MIN_HERMES})${C_RESET}"
    echo -e ""
    echo -e "   ${C_YELLOW}⚠️  Andoriña v1.5.2+ requires Hermes Agent >= ${MIN_HERMES}.${C_RESET}"
    echo -ne "   ${C_WHITE}● Update Hermes now? [Y/n]${C_RESET} "
    read -r REPLY
    if [[ "$REPLY" =~ ^[Nn]$ ]]; then
        echo -e "   ${C_GRAY}Run: hermes update — then re-run this installer.${C_RESET}"
    else
        echo -e "   ${C_CYAN}Updating Hermes...${C_RESET}"
        hermes update
        echo -e ""
        echo -e "   ${C_GREEN}Hermes updated. Please re-run install.sh.${C_RESET}"
    fi
    exit 1
fi
echo -e "${C_GREEN}v${HERMES_VER} ✓${C_RESET}"

# ─────────────────────────────────────────────────────────────
# 3. PRE-FLIGHT: Disk space check
# ─────────────────────────────────────────────────────────────
echo -ne "   ${C_WHITE}● Checking disk space ...${C_RESET} "
FREE_GB=$(python3 -c "import shutil, pathlib; print(f'{shutil.disk_usage(pathlib.Path.home()).free / 1024**3:.1f}')")
python3 -c "import sys; sys.exit(0 if float('$FREE_GB') >= 5 else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${C_YELLOW}${FREE_GB}GB free${C_RESET}"
    echo -e "   ${C_YELLOW}⚠️  Low disk space. At least 5GB recommended. Hermes may crash if the disk fills up.${C_RESET}"
else
    echo -e "${C_GREEN}${FREE_GB}GB free ✓${C_RESET}"
fi

# ─────────────────────────────────────────────────────────────
# 4. MAIN SETUP: Delegate entirely to setup.py (interactive)
# ─────────────────────────────────────────────────────────────
# setup.py handles ALL user interaction: language selection,
# identity, Google Contacts, performance tuning, deployment,
# hooks, Qdrant, autostart, bridge patching, and SOUL.
# We run it in the foreground so the user sees every prompt.
python3 setup.py

if [ $? -ne 0 ]; then
    echo -e "\n   ${C_RED}❌ Setup failed. Check the output above for details.${C_RESET}"
    exit 1
fi

# ─────────────────────────────────────────────────────────────
# 3. DONE
# ─────────────────────────────────────────────────────────────
echo ""
hr
echo -e "   ${C_GREEN}${BOLD}Thank you for trusting AndoriñaAI ❤️${C_RESET}"
hr
echo ""
