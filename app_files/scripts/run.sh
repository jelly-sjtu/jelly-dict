#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
APP_DIR="${REPO_ROOT}/jelly_dict"
VENV_DIR="${APP_DIR}/.venv"
INSTALL_MODE_FILE="${APP_DIR}/.install_mode"

INSTALL_MODE="venv"
if [[ -f "${INSTALL_MODE_FILE}" ]]; then
  saved_mode="$(tr -d '[:space:]' < "${INSTALL_MODE_FILE}")"
  if [[ "${saved_mode}" == "venv" || "${saved_mode}" == "local" ]]; then
    INSTALL_MODE="${saved_mode}"
  fi
fi

if [[ "${INSTALL_MODE}" == "venv" ]]; then
  if [[ ! -d "${VENV_DIR}" ]]; then
    echo "Virtual environment not found: ${VENV_DIR}" >&2
    echo "Run first:" >&2
    echo "  ${REPO_ROOT}/scripts/quickstart.sh" >&2
    exit 1
  fi

  if [[ ! -f "${VENV_DIR}/bin/activate" ]] || ! grep -Fq "VIRTUAL_ENV=\"${VENV_DIR}\"" "${VENV_DIR}/bin/activate"; then
    echo "Virtual environment was created for a different folder." >&2
    echo "Run Quick Start and allow dependency installation to recreate it." >&2
    echo "  ${REPO_ROOT}/scripts/quickstart.sh" >&2
    exit 1
  fi
fi

cd "${APP_DIR}"

if [[ "${INSTALL_MODE}" == "venv" ]]; then
  # shellcheck source=/dev/null
  source "${VENV_DIR}/bin/activate"
  exec python -m app.main
fi

exec python3 -m app.main
