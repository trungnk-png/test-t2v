#!/usr/bin/env bash
# Shared by setup and launcher; also works when this folder is copied alone.
T2V_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "${COMFYUI_DIR:-}" ]]; then
  if [[ ! -d "${T2V_DIR}/ComfyUI" && -d "${T2V_DIR}/../ComfyUI/.git" ]]; then
    COMFYUI_DIR="${T2V_DIR}/../ComfyUI"
  else
    COMFYUI_DIR="${T2V_DIR}/ComfyUI"
  fi
fi
COMFYUI_DIR="$(realpath -m -- "$COMFYUI_DIR")"
export COMFYUI_DIR
export VENV_DIR="${VENV_DIR:-${COMFYUI_DIR}/.venv}"
VENV_DIR="$(realpath -m -- "$VENV_DIR")"
