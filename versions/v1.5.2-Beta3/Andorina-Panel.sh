#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  Andoriña — Panel de Control (Launcher silencioso)
#  Doble clic para abrir el panel. No abre terminal.
# ═══════════════════════════════════════════════════════════
DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8888
LOG="$DIR/GUI/.server.log"

if ! command -v python3 &> /dev/null; then
    echo "Python 3 no está instalado. Por favor, instálalo antes de continuar."
    exit 1
fi

# Kill previous (fuser not available on all distros — portable fallback chain)
fuser -k ${PORT}/tcp >/dev/null 2>&1 || \
  pkill -f "server.py --port ${PORT}" >/dev/null 2>&1 || \
  { PID=$(lsof -ti tcp:${PORT} 2>/dev/null); [ -n "$PID" ] && kill "$PID" 2>/dev/null; } || \
  { PID=$(ss -tlnp 2>/dev/null | grep ":${PORT}" | grep -oP 'pid=\K[0-9]+' | head -1); [ -n "$PID" ] && kill "$PID" 2>/dev/null; } || true

# Auto-install critical runtime dep if missing (filelock required by safe_json.py)
python3 -c "from filelock import FileLock" 2>/dev/null || \
  python3 -m pip install --user --quiet filelock 2>>"$LOG" || true

# ── Resolve HERMES_HOME for multi-profile support ──────────────────────────────
# Read HERMES_AGENT_PATH written by the installer into .env (same directory as this script)
ENV_FILE="$DIR/.env"
if [ -f "$ENV_FILE" ]; then
    HERMES_AGENT_PATH_VAL=$(grep -m1 '^HERMES_AGENT_PATH=' "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)
    if [ -n "$HERMES_AGENT_PATH_VAL" ]; then
        export HERMES_HOME="$HERMES_AGENT_PATH_VAL"
    fi
fi
# Fallback: default Hermes profile
if [ -z "$HERMES_HOME" ]; then
    export HERMES_HOME="$HOME/.hermes"
fi

# Start silently
nohup python3 "$DIR/GUI/server.py" --port $PORT > "$LOG" 2>&1 &

# Wait for server to be ready (up to 10s)
for i in $(seq 1 20); do
    python3 -c "import socket; s=socket.socket(); s.connect(('localhost', $PORT))" 2>/dev/null && break
    sleep 0.5
done

# Open browser (uses system default — respects Edge, Firefox, etc.)
URL="http://localhost:${PORT}"
if [ -n "$WAYLAND_DISPLAY" ] || [ -n "$DISPLAY" ]; then
    xdg-open "$URL" >/dev/null 2>&1 || sensible-browser "$URL" >/dev/null 2>&1 || python3 -c "import webbrowser; webbrowser.open('$URL')" >/dev/null 2>&1
else
    echo "No display detected. Open manually: $URL"
fi
