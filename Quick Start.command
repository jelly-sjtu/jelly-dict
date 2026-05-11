#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

SUPPORT_DIR="${SCRIPT_DIR}"
if [[ ! -x "${SUPPORT_DIR}/scripts/quickstart.sh" && -x "${SCRIPT_DIR}/app_files/scripts/quickstart.sh" ]]; then
  SUPPORT_DIR="${SCRIPT_DIR}/app_files"
fi

if [[ ! -x "${SUPPORT_DIR}/scripts/quickstart.sh" || ! -x "${SUPPORT_DIR}/scripts/run.sh" ]]; then
  echo "jelly dict 실행 파일을 찾지 못했습니다."
  echo "현재 위치: ${SCRIPT_DIR}"
  echo
  echo "다운로드한 폴더 구조가 깨졌을 수 있습니다."
  read -r -p "Press Enter to close..." _
  exit 1
fi

echo "jelly dict quick start"
echo

ask_yes_no() {
  local prompt="$1"
  local default="$2"
  local answer
  local suffix

  if [[ "${default}" == "yes" ]]; then
    suffix="[Y/n]"
  else
    suffix="[y/N]"
  fi

  read -r -p "${prompt} ${suffix} " answer
  answer="$(printf '%s' "${answer}" | tr '[:upper:]' '[:lower:]')"

  if [[ -z "${answer}" ]]; then
    [[ "${default}" == "yes" ]]
    return
  fi

  [[ "${answer}" == "y" || "${answer}" == "yes" ]]
}

accept_license_or_exit() {
  echo "라이선스 확인"
  echo "  jelly dict는 MIT License 조건으로 제공됩니다."
  echo "  외부 패키지와 선택 TTS 음성은 각각의 라이선스/약관을 따릅니다."
  echo "  이 앱의 설치, 실행, 생성물 사용으로 발생하는 책임은 관련 라이선스와 약관에 따라 사용자에게 있습니다."
  echo "  자세한 내용은 app_files/THIRD_PARTY_NOTICES.md를 확인하세요."
  echo

  if ! ask_yes_no "위 내용을 확인했고 동의합니까?" "no"; then
    echo
    echo "동의하지 않아 설치/실행을 중단합니다."
    read -r -p "Press Enter to close..." _
    exit 1
  fi
}

choose_install_mode() {
  local answer

  echo
  echo "설치 방식을 선택하세요."
  echo "  1) 전용 가상환경 사용 (권장)"
  echo "     이 앱 폴더 안의 .venv에만 설치합니다."
  echo "  2) 현재 로컬 Python에 설치"
  echo "     이미 쓰는 Python 환경에 패키지를 설치합니다."
  echo

  while true; do
    read -r -p "선택 [1/2, 기본 1] " answer
    case "${answer}" in
      ""|1)
        printf 'venv\n'
        return
        ;;
      2)
        printf 'local\n'
        return
        ;;
      *)
        echo "1 또는 2를 입력하세요."
        ;;
    esac
  done
}

accept_license_or_exit

echo "현재 환경을 먼저 확인합니다."
if "${SUPPORT_DIR}/scripts/quickstart.sh" --check; then
  echo
  echo "환경 확인 완료."
  if ask_yes_no "바로 실행할까요?" "yes"; then
    "${SUPPORT_DIR}/scripts/run.sh"
  fi
  echo
  echo "Done. You can close this window."
  read -r -p "Press Enter to close..." _
  exit 0
fi

echo
echo "설치 또는 업데이트가 필요합니다."

if ask_yes_no "의존성을 설치/업데이트할까요?" "yes"; then
  install_mode="$(choose_install_mode)"
  args=(--mode "${install_mode}" --run)

  if ask_yes_no "TTS 기능도 설치할까요?" "no"; then
    args=(--mode "${install_mode}" --tts --run)

    if ! command -v ffmpeg >/dev/null 2>&1; then
      if command -v brew >/dev/null 2>&1; then
        if ask_yes_no "TTS mp3 처리를 위해 ffmpeg도 Homebrew로 설치할까요?" "yes"; then
          brew install ffmpeg
        fi
      else
        echo
        echo "Homebrew가 없어 ffmpeg는 자동 설치하지 못했습니다."
        echo "TTS를 쓸 거면 나중에 ffmpeg를 따로 설치하세요."
      fi
    fi
  fi

  "${SUPPORT_DIR}/scripts/quickstart.sh" --accept-license "${args[@]}"
else
  "${SUPPORT_DIR}/scripts/run.sh"
fi

echo
echo "Done. You can close this window."
read -r -p "Press Enter to close..." _
