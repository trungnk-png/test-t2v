#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/runtime_env.sh"
PYTHON="${VENV_DIR}/bin/python"
if [[ ! -x "$PYTHON" || ! -f "${COMFYUI_DIR}/main.py" ]]; then
  echo "Chưa cài môi trường. Chạy: bash ${SCRIPT_DIR}/setup.sh" >&2
  exit 1
fi
COMFY_PORT="${COMFY_PORT:-8188}"
export COMFY_URL="${COMFY_URL:-http://127.0.0.1:${COMFY_PORT}}"
comfy_pid=""
web_pid=""
cleanup() {
  for child in "$web_pid" "$comfy_pid"; do
    if [[ -n "$child" ]]; then kill "$child" 2>/dev/null || true; fi
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
# Reuse ComfyUI if it is already available.
if ! curl -fsS --max-time 3 "${COMFY_URL}/system_stats" >/dev/null; then
  if [[ "$COMFY_URL" != "http://127.0.0.1:${COMFY_PORT}" ]]; then
    echo "Không kết nối được ComfyUI tại ${COMFY_URL}" >&2
    exit 1
  fi
  (cd "$COMFYUI_DIR"; exec "$PYTHON" main.py --listen 0.0.0.0 --port "$COMFY_PORT") &
  comfy_pid=$!
  ready=0
  for ((attempt=0; attempt<180; attempt++)); do
    if ! kill -0 "$comfy_pid" 2>/dev/null; then
      echo "ComfyUI đã dừng; xem lỗi phía trên." >&2
      exit 1
    fi
    if curl -fsS --max-time 2 "${COMFY_URL}/system_stats" >/dev/null 2>&1; then ready=1; break; fi
    sleep 1
  done
  if [[ "$ready" != 1 ]]; then echo "ComfyUI chưa sẵn sàng sau khi chờ." >&2; exit 1; fi
fi
echo "Demo: http://localhost:${WEB_PORT:-8000} — Ctrl+C để dừng"
PYTHON_BIN="$PYTHON" bash "${SCRIPT_DIR}/run_web.sh" &
web_pid=$!
if [[ -n "$comfy_pid" ]]; then
  wait -n "$comfy_pid" "$web_pid"
else
  wait "$web_pid"
fi
