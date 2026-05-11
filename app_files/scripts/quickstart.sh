#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PUBLIC_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
APP_DIR="${REPO_ROOT}/jelly_dict"
VENV_DIR="${APP_DIR}/.venv"
INSTALL_MODE_FILE="${APP_DIR}/.install_mode"
SETUP_STATE_FILE="${APP_DIR}/.quickstart_ok"

WITH_TTS=0
RUN_AFTER=0
CHECK_ONLY=0
INSTALL_MODE=""
LICENSE_ACCEPTED=0

usage() {
  cat <<'USAGE'
Usage: scripts/quickstart.sh [--run] [--tts] [--mode venv|local]

Options:
  --run   Install/update dependencies, then start jelly dict.
  --tts   Also install optional TTS Python dependencies.
  --mode  Choose dependency target. venv is recommended.
  --accept-license
         Confirm license/responsibility notice non-interactively.
  --check Validate the local environment without installing.
  -h, --help
         Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run)
      RUN_AFTER=1
      shift
      ;;
    --tts)
      WITH_TTS=1
      shift
      ;;
    --check)
      CHECK_ONLY=1
      shift
      ;;
    --mode)
      if [[ $# -lt 2 ]]; then
        echo "--mode requires venv or local" >&2
        exit 2
      fi
      INSTALL_MODE="$2"
      shift 2
      ;;
    --accept-license)
      LICENSE_ACCEPTED=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -d "${APP_DIR}" ]]; then
  echo "jelly dict 앱 파일 구조가 원래 배포본과 다릅니다." >&2
  echo "필수 폴더를 찾을 수 없습니다: ${APP_DIR}" >&2
  echo >&2
  echo "의도한 수정이 아니라면 재다운로드하거나, git으로 받은 경우 git pull 후 다시 실행하세요." >&2
  echo "현재 폴더를 직접 옮기거나 일부 파일만 복사한 경우에는 지원하지 않습니다." >&2
  exit 1
fi

cd "${APP_DIR}"

saved_install_mode() {
  if [[ -f "${INSTALL_MODE_FILE}" ]]; then
    local mode
    mode="$(tr -d '[:space:]' < "${INSTALL_MODE_FILE}")"
    if [[ "${mode}" == "venv" || "${mode}" == "local" ]]; then
      printf '%s\n' "${mode}"
      return
    fi
  fi
  printf 'venv\n'
}

if [[ -z "${INSTALL_MODE}" ]]; then
  INSTALL_MODE="$(saved_install_mode)"
fi

if [[ "${INSTALL_MODE}" != "venv" && "${INSTALL_MODE}" != "local" ]]; then
  echo "Invalid install mode: ${INSTALL_MODE}" >&2
  echo "Use --mode venv or --mode local." >&2
  exit 2
fi

save_install_mode() {
  printf '%s\n' "${INSTALL_MODE}" > "${INSTALL_MODE_FILE}"
}

write_setup_state() {
  {
    printf 'quickstart_ok=1\n'
    printf 'mode=%s\n' "${INSTALL_MODE}"
    printf 'app_dir=%s\n' "${APP_DIR}"
    printf 'updated_at=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  } > "${SETUP_STATE_FILE}"
}

print_layout_recovery_hint() {
  cat <<EOF

jelly dict 앱 파일 구조가 원래 배포본과 다릅니다.
이 상태에서 설치를 계속하는 것은 권장하지 않습니다.

의도한 수정이 아니라면 아래 중 하나로 복구하세요.
  - 다운로드 받은 압축/폴더를 새로 받기
  - git으로 받은 경우: git pull 후 다시 실행
  - 일부 파일만 복사했다면 전체 폴더를 다시 복사

정상적인 최상위 구조:
  jelly-dict/
  ├── Quick Start.command
  ├── Run jelly dict.command
  ├── README.md
  └── app_files/
EOF
}

verify_public_layout() {
  local failed=0

  echo
  echo "앱 파일 구조 확인 중..."

  for path in \
    "${PUBLIC_ROOT}/Quick Start.command" \
    "${PUBLIC_ROOT}/Run jelly dict.command" \
    "${PUBLIC_ROOT}/README.md" \
    "${PUBLIC_ROOT}/app_files" \
    "${REPO_ROOT}/scripts/quickstart.sh" \
    "${REPO_ROOT}/scripts/run.sh" \
    "${APP_DIR}/app/main.py" \
    "${APP_DIR}/requirements.txt"; do
    if [[ ! -e "${path}" ]]; then
      echo "  ✗ 없음: ${path}"
      failed=1
    fi
  done

  for path in \
    "${PUBLIC_ROOT}/Quick Start.command" \
    "${PUBLIC_ROOT}/Run jelly dict.command" \
    "${REPO_ROOT}/scripts/quickstart.sh" \
    "${REPO_ROOT}/scripts/run.sh"; do
    if [[ -e "${path}" && ! -x "${path}" ]]; then
      echo "  ✗ 실행 권한 없음: ${path}"
      failed=1
    fi
  done

  if [[ -f "${PUBLIC_ROOT}/dev.md" ]]; then
    echo "  ✗ dev.md가 최상위 공개 폴더에 있습니다"
    failed=1
  fi

  if [[ "${failed}" -eq 0 ]]; then
    echo "  ✓ 앱 파일 구조 정상"
  else
    print_layout_recovery_hint
  fi

  return "${failed}"
}

venv_matches_current_location() {
  [[ -f "${VENV_DIR}/bin/activate" ]] || return 1
  grep -Fq "VIRTUAL_ENV=\"${VENV_DIR}\"" "${VENV_DIR}/bin/activate"
}

python_command() {
  if [[ "${INSTALL_MODE}" == "venv" ]]; then
    printf 'python\n'
  else
    printf 'python3\n'
  fi
}

check_python_packages() {
  "$(python_command)" - <<'PY'
import importlib.util
from importlib import metadata
import re
import sys

modules = ["PySide6", "openpyxl", "bs4", "lxml", "playwright", "genanki", "keyring", "Vision"]
missing = [name for name in modules if importlib.util.find_spec(name) is None]
if missing:
    print("  ✗ missing Python packages: " + ", ".join(missing))
    sys.exit(1)

checks = [
    ("PySide6", "PySide6", (6, 7), (6, 8), "6.7.*"),
    ("openpyxl", "openpyxl", (3, 1), None, ">=3.1"),
    ("beautifulsoup4", "bs4", (4, 12), None, ">=4.12"),
    ("lxml", "lxml", (5, 0), None, ">=5.0"),
    ("playwright", "playwright", (1, 45), None, ">=1.45"),
    ("genanki", "genanki", (0, 13), None, ">=0.13"),
    ("keyring", "keyring", (24,), None, ">=24"),
    ("pyobjc-framework-Vision", "Vision", (10, 0), None, ">=10.0"),
]

def version_tuple(value):
    parts = re.findall(r"\d+", value)
    return tuple(int(part) for part in parts[:3])

bad = []
for dist_name, module_name, minimum, maximum, spec in checks:
    if importlib.util.find_spec(module_name) is None:
        bad.append(f"{module_name} missing")
        continue
    try:
        installed = metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        bad.append(f"{dist_name} metadata missing")
        continue
    parsed = version_tuple(installed)
    if parsed < minimum or (maximum is not None and parsed >= maximum):
        bad.append(f"{dist_name} {installed} does not satisfy {spec}")

if bad:
    print("  ✗ Python package version mismatch:")
    for item in bad:
        print("    - " + item)
    sys.exit(1)

print("  ✓ required Python packages and versions")
PY
}

check_playwright_webkit() {
  "$(python_command)" - <<'PY'
import importlib.util
from pathlib import Path

if importlib.util.find_spec("playwright") is None:
    raise SystemExit(1)

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    path = Path(p.webkit.executable_path)
    if not path.exists():
        raise SystemExit(1)
print("  ✓ Playwright WebKit")
PY
}

check_tts_packages() {
  "$(python_command)" - <<'PY'
import importlib.util
from importlib import metadata
import re
import sys

required = ["soundfile"]
missing = [name for name in required if importlib.util.find_spec(name) is None]
if missing:
    print("  ✗ missing TTS Python packages: " + ", ".join(missing))
    sys.exit(1)

checks = [
    ("kokoro", "kokoro", (0, 3), ">=0.3"),
    ("soundfile", "soundfile", (0, 12), ">=0.12"),
]

def version_tuple(value):
    parts = re.findall(r"\d+", value)
    return tuple(int(part) for part in parts[:3])

bad = []
for dist_name, module_name, minimum, spec in checks:
    if importlib.util.find_spec(module_name) is None:
        bad.append(f"{module_name} missing")
        continue
    try:
        installed = metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        bad.append(f"{dist_name} metadata missing")
        continue
    if version_tuple(installed) < minimum:
        bad.append(f"{dist_name} {installed} does not satisfy {spec}")

if bad:
    print("  ✗ TTS package version mismatch:")
    for item in bad:
        print("    - " + item)
    sys.exit(1)

print("  ✓ TTS Python packages and versions")
PY
}

print_license_notice() {
  echo "라이선스 확인"
  echo "  jelly dict는 MIT License 조건으로 제공됩니다."
  echo "  외부 패키지와 선택 TTS 음성은 각각의 라이선스/약관을 따릅니다."
  echo "  이 앱의 설치, 실행, 생성물 사용으로 발생하는 책임은 관련 라이선스와 약관에 따라 사용자에게 있습니다."
  echo "  자세한 내용은 app_files/THIRD_PARTY_NOTICES.md를 확인하세요."
  echo
}

accept_license_or_exit() {
  local answer

  print_license_notice
  read -r -p "위 내용을 확인했고 동의합니까? [y/N] " answer
  answer="$(printf '%s' "${answer}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${answer}" != "y" && "${answer}" != "yes" ]]; then
    echo "동의하지 않아 설치를 중단합니다."
    exit 1
  fi
}

check_python_version() {
  python3 - <<'PY'
import sys

required = (3, 11)
current = sys.version_info[:2]
if current < required:
    print(f"  ✗ python3 >= {required[0]}.{required[1]} required, found {sys.version.split()[0]}")
    raise SystemExit(1)
print(f"  ✓ python3 version OK: {sys.version.split()[0]}")
PY
}

check_disk_space() {
  local available_kb

  available_kb="$(df -Pk "${APP_DIR}" | awk 'NR == 2 {print $4}')"
  if [[ -z "${available_kb}" ]]; then
    echo "  ! disk space check skipped"
    return
  fi

  if (( available_kb < 1048576 )); then
    echo "  ! free disk space is under 1 GB; dependency install may fail"
  else
    echo "  ✓ free disk space OK"
  fi
}

check_quarantine_warning() {
  local target="${REPO_ROOT}/.."

  if command -v xattr >/dev/null 2>&1 && xattr -p com.apple.quarantine "${target}" >/dev/null 2>&1; then
    echo "  ! macOS quarantine attribute detected on the app folder"
    echo "    If double-click fails, right-click the .command file and choose Open."
  fi
}

check_system_requirements() {
  local failed=0
  local os_name

  os_name="$(uname -s 2>/dev/null || true)"
  if [[ "${os_name}" != "Darwin" ]]; then
    echo "  ✗ macOS required. Current system: ${os_name:-unknown}"
    failed=1
  else
    if command -v sw_vers >/dev/null 2>&1; then
      echo "  ✓ macOS: $(sw_vers -productVersion)"
    else
      echo "  ✓ macOS detected"
    fi
  fi

  echo "  architecture: $(uname -m 2>/dev/null || echo unknown)"
  if [[ "$(sysctl -in sysctl.proc_translated 2>/dev/null || echo 0)" == "1" ]]; then
    echo "  ! running under Rosetta; native arm64/x86_64 Python is usually more stable"
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "  ✗ python3 not found"
    failed=1
  elif ! check_python_version; then
    failed=1
  fi

  if command -v python3 >/dev/null 2>&1 && ! python3 -m pip --version >/dev/null 2>&1; then
    echo "  ✗ python3 pip is not available"
    failed=1
  elif command -v python3 >/dev/null 2>&1; then
    echo "  ✓ python3 pip"
  fi

  if [[ "${INSTALL_MODE}" == "venv" ]] && command -v python3 >/dev/null 2>&1; then
    if ! python3 -m venv --help >/dev/null 2>&1; then
      echo "  ✗ python3 venv module is not available"
      failed=1
    else
      echo "  ✓ python3 venv"
    fi
  fi

  if [[ ! -w "${APP_DIR}" ]]; then
    echo "  ✗ app folder is not writable: ${APP_DIR}"
    failed=1
  else
    echo "  ✓ app folder writable"
  fi

  check_disk_space
  check_quarantine_warning

  return "${failed}"
}

check_environment() {
  local failed=0
  local can_check_packages=0

  echo "Checking environment..."
  echo "  install mode: ${INSTALL_MODE}"

  if ! check_system_requirements; then
    failed=1
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "  ✗ python3 not found"
    failed=1
  else
    echo "  ✓ python3: $(python3 --version 2>&1)"
  fi

  if [[ "${INSTALL_MODE}" == "venv" ]]; then
    if [[ ! -d "${VENV_DIR}" ]]; then
      echo "  ✗ virtual environment missing: ${VENV_DIR}"
      failed=1
    elif ! venv_matches_current_location; then
      echo "  ✗ virtual environment was created for a different folder"
      echo "    rerun Quick Start and allow dependency installation to recreate it"
      failed=1
    else
      echo "  ✓ virtual environment: ${VENV_DIR}"
    fi
  else
    echo "  ✓ using local Python environment"
  fi

  if [[ ! -f requirements.txt ]]; then
    echo "  ✗ requirements.txt missing"
    failed=1
  else
    echo "  ✓ requirements.txt"
  fi

  if [[ "${INSTALL_MODE}" == "venv" && -d "${VENV_DIR}" ]] && venv_matches_current_location; then
    # shellcheck source=/dev/null
    source "${VENV_DIR}/bin/activate"
    can_check_packages=1
  elif [[ "${INSTALL_MODE}" == "local" ]]; then
    can_check_packages=1
  fi

  if [[ "${can_check_packages}" -eq 1 ]]; then
    if check_python_packages; then
      :
    else
      failed=1
    fi

    if check_playwright_webkit; then
      :
    else
      echo "  ✗ Playwright WebKit missing"
      failed=1
    fi

    if [[ "${WITH_TTS}" -eq 1 ]]; then
      if check_tts_packages; then
        :
      else
        failed=1
      fi

      if command -v ffmpeg >/dev/null 2>&1; then
        echo "  ✓ ffmpeg"
      else
        echo "  ✗ ffmpeg missing"
        failed=1
      fi
    fi
  fi

  return "${failed}"
}

if ! verify_public_layout; then
  exit 1
fi

if [[ "${CHECK_ONLY}" -eq 1 ]]; then
  check_environment
  exit $?
fi

if [[ "${LICENSE_ACCEPTED}" -ne 1 ]]; then
  accept_license_or_exit
fi
save_install_mode

if [[ "${INSTALL_MODE}" == "venv" ]]; then
  if [[ -d "${VENV_DIR}" ]] && ! venv_matches_current_location; then
    echo "Recreating virtual environment for the current folder: ${VENV_DIR}"
    rm -rf "${VENV_DIR}"
  fi

  if [[ ! -d "${VENV_DIR}" ]]; then
    echo "Creating virtual environment: ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
  fi

  # shellcheck source=/dev/null
  source "${VENV_DIR}/bin/activate"
fi

"$(python_command)" -m pip install --upgrade pip
"$(python_command)" -m pip install -r requirements.txt

if [[ "${WITH_TTS}" -eq 1 ]]; then
  "$(python_command)" -m pip install -r requirements-tts.txt
fi

"$(python_command)" -m playwright install webkit

echo
if ! check_environment; then
  echo
  echo "Environment check failed. Review the messages above and rerun quickstart."
  exit 1
fi

if ! verify_public_layout; then
  exit 1
fi

echo
echo "Ready."
echo "Run the app with:"
echo "  ${REPO_ROOT}/scripts/run.sh"

write_setup_state

if [[ "${RUN_AFTER}" -eq 1 ]]; then
  exec "${REPO_ROOT}/scripts/run.sh"
fi
