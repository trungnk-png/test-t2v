#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/runtime_env.sh"
for required in git curl ffmpeg ffprobe; do
  if ! command -v "$required" >/dev/null 2>&1; then
    echo "Thiếu $required. Cài: sudo apt-get install -y git curl python3 python3-venv python3-pip ffmpeg" >&2
    exit 1
  fi
done
bash "${SCRIPT_DIR}/install_comfyui.sh"
MODEL_ROOT="${COMFYUI_DIR}/models" bash "${SCRIPT_DIR}/download_models.sh"
echo "Setup hoàn tất. Chạy: bash ${SCRIPT_DIR}/run.sh"
