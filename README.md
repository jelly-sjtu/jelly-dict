# jelly dict

jelly dict는 GitHub에서 내려받아 사용하는 macOS용 로컬 단어장 도구입니다.

영어와 일본어 단어를 빠르게 조회해 Excel 단어장에 저장하고, 필요하면 Excel 내용을 기준으로 Anki `.apkg` 파일을 만들어 줍니다.

패키징된 `.app` 또는 `.dmg` 배포는 제공하지 않습니다. 초기 설정과 실행은 저장소에 포함된 `.command` 스크립트를 통해 진행합니다.

앱의 기준 데이터는 Excel 파일입니다. 조회 결과는 Excel에 저장되고, Anki 내보내기는 그 Excel 내용을 기준으로 다시 만들어집니다.

## 할 수 있는 것

- 영어/일본어 단어 조회
- Excel 단어장 저장
- 최근 단어 확인
- 메인 화면 안에서 영어 단어장/일본어 단어장 검색
- 선택한 단어 삭제
- Anki `.apkg` 내보내기
- 사진이나 스크린샷에서 OCR로 단어 후보 뽑기
- 선택 기능으로 TTS 음성 포함 Anki 카드 만들기

## 실행하기

초기 설정은 반드시 Finder에서 `Quick Start.command`를 더블클릭해서 진행합니다.

의존성 버전, Playwright WebKit, macOS 권한 문제를 일관되게 처리하기 위해 수동 설치나 직접 실행은 지원하지 않습니다.

- 처음 설치 + 실행: `Quick Start.command`
- 설치 후 실행만: `Run jelly dict.command`

macOS가 처음 실행 때 경고를 띄우면 파일을 우클릭한 뒤 `열기`를 선택하세요.

`Quick Start.command`는 앱 실행에 필요한 Python 환경과 패키지를 확인하고, 필요한 경우 사용자의 동의를 받은 뒤 설치합니다. 시스템 Python을 강제로 수정하지 않으며, 권장 방식은 앱 폴더 안의 전용 `.venv`를 사용하는 것입니다.

macOS에서 자주 터지는 초기 문제도 같이 확인합니다.

- 앱 파일 구조가 원래 배포본과 같은지
- macOS 여부
- Python 3.11 이상
- `pip`와 `venv` 사용 가능 여부
- 앱 폴더 쓰기 권한
- 디스크 여유 공간
- 폴더 이동으로 깨진 기존 `.venv`
- 필수 Python 패키지 존재 여부와 버전
- Playwright WebKit 설치 상태
- macOS 격리 속성 경고
- Rosetta 실행 경고

파일이 빠졌거나 폴더 구조가 바뀐 상태면 Quick Start가 설치를 중단합니다. 의도한 수정이 아니라면 새로 다운로드하거나, git으로 받은 경우 `git pull` 후 다시 실행하는 편이 안전합니다.

Quick Start는 가장 먼저 라이선스 동의를 받습니다. 앱 자체는 MIT 라이선스이고, PySide6, Playwright, Kokoro, VOICEVOX 같은 외부 구성요소는 각자의 라이선스와 약관을 따릅니다. 앱의 설치, 실행, 생성물 사용으로 발생하는 책임은 관련 라이선스와 약관에 따라 사용자에게 있습니다.

설치가 필요하면 설치 방식도 물어봅니다.

- 권장: 전용 가상환경 사용
- 선택: 현재 로컬 Python에 설치

특별한 이유가 없으면 전용 가상환경을 고르면 됩니다. 앱 폴더 안의 `.venv`에만 설치되기 때문에 기존 Python 환경을 덜 건드립니다. 로컬 Python 설치는 이미 Python 환경을 직접 관리하고 있을 때만 고르는 편이 낫습니다.

VOICEVOX를 쓰려면 VOICEVOX 앱/엔진을 따로 켜서 `127.0.0.1:50021`에서 동작하게 해야 합니다.

## 기본 사용 흐름

1. 메인 입력창에 단어를 입력합니다.
2. `자동 감지`, `English`, `日本語` 중 하나를 고릅니다.
3. 조회합니다.
4. 저장 전 미리보기를 켜둔 경우 내용을 확인하고 저장합니다.
5. 저장된 단어는 아래 단어장 영역에서 확인합니다.

사진에서 단어를 뽑고 싶으면 사진 아이콘을 누르거나 이미지를 붙여넣으면 됩니다. OCR 후보가 나오면 필요한 단어를 선택하고 조회하면 됩니다. 여러 후보를 선택하면 1초 간격으로 순서대로 조회합니다.

## Anki 내보내기

메인 화면에서 영어 단어장 또는 일본어 단어장으로 전환한 뒤 `Anki 내보내기`를 누르면 `.apkg` 파일을 만듭니다.

같은 단어를 다시 내보내도 Anki에서 중복 카드가 계속 생기지 않도록 모델 ID와 note GUID를 안정적으로 유지합니다.

TTS를 켜면 단어 음성이나 예문 음성을 미리 생성해서 `.apkg`에 같이 넣습니다. 생성된 mp3는 다음 내보내기 속도를 위해 로컬 캐시에 보관합니다. 같은 mp3가 `.apkg` 안에 중복으로 들어가지는 않습니다.

## 데이터는 어디에 저장되나

단어장은 기본적으로 `~/Documents/jelly-dict/` 아래 Excel 파일로 저장됩니다. 설정에서 위치를 바꿀 수 있습니다.

앱 설정, 캐시, 로그는 앱 실행 폴더의 `.jelly_dict/` 폴더에 저장됩니다. 테스트나 별도 실행 환경에서는 `JELLY_DICT_HOME`으로 위치를 바꿀 수 있습니다.

붙여넣은 OCR 이미지는 `.jelly_dict/ocr_clipboard/`에 임시 파일로만 저장됩니다. OCR을 지우거나, 새 OCR로 교체하거나, 앱을 닫거나, 다음 앱 시작 시 삭제됩니다.

API 키는 파일에 저장하지 않고 macOS Keychain에만 저장합니다.

## 네트워크 사용

자동 업로드, 원격 DB, 텔레메트리는 없습니다.

네트워크는 사용자가 직접 실행한 작업에서만 발생합니다.

- 단어 조회: 네이버 사전
- Google Vision OCR을 선택한 경우: Google Cloud Vision API
- VOICEVOX TTS: 로컬 `127.0.0.1:50021`
- AnkiConnect: 로컬 `127.0.0.1:8765`
- Kokoro TTS: 최초 1회 모델 다운로드
- edge-tts: 외부 CLI가 Microsoft TTS 엔드포인트 사용

기본 OCR은 Apple Vision이라 로컬에서 처리됩니다. Google Vision을 선택하면 이미지가 Google Vision API로 전송됩니다.

## TTS 메모

TTS는 기본값이 꺼짐입니다. 설정의 `Anki / TTS`에서 켤 수 있습니다.

Kokoro는 영어/일본어를 모두 지원합니다. VOICEVOX는 일본어 전용이고, 캐릭터별 약관에 따라 Anki 덱 설명에 크레딧이 들어갑니다. edge-tts는 외부 CLI 옵션입니다.

생성한 Anki 파일은 개인 학습용으로 쓰는 것을 기준으로 합니다. 인터넷에 공유할 경우 사용하는 음성 엔진의 라이선스를 따로 확인해야 합니다.

## 문제가 생겼을 때

먼저 `Quick Start.command`를 다시 실행해 주세요. 이 스크립트는 Python, 가상환경, 필수 패키지, Playwright WebKit, 권한, 디스크 공간, 앱 파일 구조를 다시 점검합니다.

그래도 해결되지 않으면 GitHub Issues에 아래 정보를 함께 올려 주세요.

- macOS 버전
- Python 버전
- Intel Mac / Apple Silicon Mac 여부
- `Quick Start.command` 실행 로그
- 오류가 난 화면 또는 메시지

## 라이선스

MIT 라이선스입니다. 외부 의존성 정보는 [app_files/THIRD_PARTY_NOTICES.md](app_files/THIRD_PARTY_NOTICES.md)에 정리되어 있습니다.
