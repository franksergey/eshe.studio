#!/usr/bin/env bash
# ----------------------------------------------------------------------
# start-debug.sh
# ----------------------------------------------------------------------
# Это скрипт для автоматизированного запуска сессии дебага. Он запускает
# debugpy, а затем ждёт, пока debugpy инициализируется. Потом выводит
# сообщение, чтобы VS Code начал подключение к сессии.
# ----------------------------------------------------------------------

# Exit on any error, treat unset variables as errors, and propagate
# failures through pipelines.
set -euo pipefail

# Listenning port for debugpy (default 5678). Can be overrided.
PORT=${PORT:-5678}

(
    while ! grep -q ":$(printf '%04X' "$PORT")..* 0A" /proc/net/tcp; do
        sleep 0.1
    done
    echo "DEBUGGER: Ready and waiting for client connection on port $PORT"
) &

export PYTHONUNBUFFERED=x

# Launch the bot under debugpy.
#   -Xfrozen_modules=off : makes a huge help to debugpy
#   --listen 0.0.0.0:${PORT} --wait-for-client : wait for VS Code to attach
#   -m app : run the `app` module as the entry point
uv run --active --dev python -Xfrozen_modules=off -m \
    debugpy --listen 0.0.0.0:$PORT --wait-for-client -m server
