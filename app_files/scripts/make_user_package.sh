#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_FILES_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PUBLIC_ROOT="$(cd "${APP_FILES_ROOT}/.." && pwd)"
OUT_DIR="${PUBLIC_ROOT}/dist/jelly-dict"
APP_FILES="${OUT_DIR}/app_files"

if [[ -e "${OUT_DIR}" ]]; then
  echo "Output already exists: ${OUT_DIR}" >&2
  echo "Move or delete that folder first, then run this script again." >&2
  exit 1
fi

mkdir -p "${APP_FILES}"

cp "${PUBLIC_ROOT}/Quick Start.command" "${OUT_DIR}/"
cp "${PUBLIC_ROOT}/Run jelly dict.command" "${OUT_DIR}/"
cp "${PUBLIC_ROOT}/README.md" "${OUT_DIR}/"

rsync -a \
  --exclude ".DS_Store" \
  --exclude ".venv/" \
  --exclude ".jelly_dict/" \
  --exclude ".pytest_cache/" \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  --exclude "*.xlsx" \
  --exclude "*.apkg" \
  --exclude "*.tsv" \
  --exclude "*.log" \
  "${APP_FILES_ROOT}/jelly_dict/" "${APP_FILES}/jelly_dict/"

rsync -a \
  --exclude ".DS_Store" \
  --exclude "make_user_package.sh" \
  --exclude "__pycache__/" \
  "${APP_FILES_ROOT}/scripts/" "${APP_FILES}/scripts/"

for doc in LICENSE THIRD_PARTY_NOTICES.md; do
  if [[ -f "${APP_FILES_ROOT}/${doc}" ]]; then
    cp "${APP_FILES_ROOT}/${doc}" "${APP_FILES}/"
  fi
done

chmod +x "${OUT_DIR}/Quick Start.command" "${OUT_DIR}/Run jelly dict.command"
chmod +x "${APP_FILES}/scripts/quickstart.sh" "${APP_FILES}/scripts/run.sh"

echo "Created: ${OUT_DIR}"
echo
echo "Top-level files:"
find "${OUT_DIR}" -maxdepth 1 -print | sort
